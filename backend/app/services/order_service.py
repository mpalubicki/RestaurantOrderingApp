from uuid import uuid4
from flask import session
from flask_login import current_user
from ..extensions import mongo
from backend.app.services.menu_service import get_menu_boxes


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
