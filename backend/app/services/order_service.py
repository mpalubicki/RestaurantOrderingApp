from uuid import uuid4
from flask import session
from flask_login import current_user
from app.extensions import mongo
from app.services.menu_service import get_menu_boxes
from decimal import Decimal
from app.extensions import db
from app.models.sql_order_model import Order, OrderItem
import os
import requests



def _get_cart_key() -> dict:
    if current_user.is_authenticated:
        return {"user_id": current_user.get_id()}

    cart_id = session.get("cart_id")
    if not cart_id:
        cart_id = str(uuid4())
        session["cart_id"] = cart_id
    return {"_id": cart_id}


def _find_menu_item_and_variant(menu_item_id: str, variant_id: str) -> dict | None:
    grouped = get_menu_boxes(group_by_category=True)
    for _, items in grouped.items():
        for item in items:
            if item.get("id") != menu_item_id:
                continue

            for v in item.get("variants", []):
                if v.get("id") == variant_id:
                    return {
                        "name": item.get("title"),
                        "category": item.get("category"),
                        "variant_label": v.get("label"),
                        "unit_price": float(v.get("price") or 0.0),
                    }
    return None


def get_cart() -> dict:
    cart_key = _get_cart_key()
    cart = mongo.db.carts.find_one(cart_key)

    if not cart:
        cart = {**cart_key, "items": []}
        mongo.db.carts.insert_one(cart)

    return cart


def add_to_cart(menu_item_id: str, variant_id: str, qty: int = 1) -> None:
    qty = max(1, int(qty))

    cart_key = _get_cart_key()
    cart = mongo.db.carts.find_one(cart_key)

    if not cart:
        cart = {**cart_key, "items": []}
        mongo.db.carts.insert_one(cart)

    details = _find_menu_item_and_variant(menu_item_id, variant_id)
    if not details:
        return

    items = cart.get("items", []) or []

    for line in items:
        if line.get("menu_item_id") == menu_item_id and line.get("variant_id") == variant_id:
            line["qty"] = int(line.get("qty", 0)) + qty
            break
    else:
        items.append({
            "_id": str(uuid4()),  # line id
            "menu_item_id": menu_item_id,
            "variant_id": variant_id,
            "name": details["name"],
            "category": details["category"],
            "variant_label": details["variant_label"],
            "unit_price": float(details["unit_price"]),
            "qty": qty
        })

    mongo.db.carts.update_one(
        cart_key,
        {"$set": {"items": items}},
        upsert=True
    )


def update_cart_line(line_id: str, qty: int) -> None:
    qty = int(qty)
    cart_key = _get_cart_key()
    cart = mongo.db.carts.find_one(cart_key) or {**cart_key, "items": []}

    items = cart.get("items", []) or []
    new_items = []

    for line in items:
        if line.get("_id") == line_id:
            if qty > 0:
                line["qty"] = qty
                new_items.append(line)
        else:
            new_items.append(line)

    mongo.db.carts.update_one(
        cart_key,
        {"$set": {"items": new_items}},
        upsert=True
    )


def remove_cart_line(line_id: str) -> None:
    cart_key = _get_cart_key()
    cart = mongo.db.carts.find_one(cart_key) or {**cart_key, "items": []}

    items = [l for l in (cart.get("items", []) or []) if l.get("_id") != line_id]

    mongo.db.carts.update_one(
        cart_key,
        {"$set": {"items": items}},
        upsert=True
    )


def clear_cart() -> None:
    cart_key = _get_cart_key()
    mongo.db.carts.update_one(
        cart_key,
        {"$set": {"items": []}},
        upsert=True
    )


def cart_totals(cart: dict) -> tuple[list[dict], float]:
    cart_items = []
    total = 0.0

    for line in cart.get("items", []) or []:
        unit = float(line.get("unit_price") or 0.0)
        qty = int(line.get("qty") or 0)
        line_total = unit * qty
        total += line_total

        cart_items.append({
            "line_id": line.get("_id"),
            "name": line.get("name"),
            "category": line.get("category"),
            "variant_label": line.get("variant_label"),
            "qty": qty,
            "unit_price": unit,
            "line_total": line_total
        })

    return cart_items, total

def checkout_to_sql_order() -> int:
    cart = get_cart()
    items, total = cart_totals(cart)

    if not items:
        raise ValueError("Your cart is empty.")

    order = Order(
        user_id=int(current_user.get_id()),
        status="created",
        currency="GBP",
        total_amount=Decimal(str(total)).quantize(Decimal("0.01")),
    )
    db.session.add(order)
    db.session.flush()  # gets order.id without committing yet

    for line in items:
        unit = Decimal(str(line["unit_price"])).quantize(Decimal("0.01"))
        qty = int(line["qty"])
        line_total = (unit * qty).quantize(Decimal("0.01"))

        oi = OrderItem(
            order_id=order.id,
            menu_item_id=str(cart_line_lookup(cart, line["line_id"]).get("menu_item_id")),
            variant_id=str(cart_line_lookup(cart, line["line_id"]).get("variant_id")),
            name=line["name"],
            variant_label=line["variant_label"],
            unit_price=unit,
            qty=qty,
            line_total=line_total,
        )
        db.session.add(oi)

    db.session.commit()
    _notify_order_confirmation(order, order.order_items)
    clear_cart()
    return order.id


def cart_line_lookup(cart: dict, line_id: str) -> dict:
    for line in cart.get("items", []) or []:
        if line.get("_id") == line_id:
            return line
    return {}

def _notify_order_confirmation(order, order_items):
    url = os.getenv("ORDER_CONFIRMATION_URL", "").strip()
    if not url:
        return

    user_email = None
    try:
        user_email = getattr(current_user, "email", None)
    except Exception:
        user_email = None

    payload = {
        "order_id": order.id,
        "user_email": user_email,
        "total_amount": float(order.total_amount or 0),
        "currency": order.currency,
        "items": [
            {
                "name": it.name,
                "variant_label": it.variant_label,
                "qty": int(it.qty or 0),
                "unit_price": float(it.unit_price or 0),
                "line_total": float(it.line_total or 0),
            }
            for it in (order_items or [])
        ],
    }

    try:
        requests.post(url, json=payload, timeout=5)
    except Exception:
        pass

