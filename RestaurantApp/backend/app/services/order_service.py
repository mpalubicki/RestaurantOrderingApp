from uuid import uuid4
from flask import session
from ..extensions import mongo
from backend.app.services.menu_service import get_menu_boxes


def _get_or_create_cart_id() -> str:
    cart_id = session.get("cart_id")
    if not cart_id:
        cart_id = str(uuid4())
        session["cart_id"] = cart_id
    return cart_id


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
    cart_id = _get_or_create_cart_id()
    cart = mongo.db.carts.find_one({"_id": cart_id})
    if not cart:
        cart = {"_id": cart_id, "items": []}
        mongo.db.carts.insert_one(cart)
    return cart


def add_to_cart(menu_item_id: str, variant_id: str, qty: int = 1) -> None:
    qty = max(1, int(qty))
    cart_id = _get_or_create_cart_id()
    cart = mongo.db.carts.find_one({"_id": cart_id}) or {"_id": cart_id, "items": []}

    details = _find_menu_item_and_variant(menu_item_id, variant_id)
    if not details:
        if "_id" not in cart:
            mongo.db.carts.insert_one(cart)
        return

    items = cart.get("items", [])
    for line in items:
        if line["menu_item_id"] == menu_item_id and line["variant_id"] == variant_id:
            line["qty"] += qty
            break
    else:
        items.append({
            "_id": str(uuid4()),  # line id
            "menu_item_id": menu_item_id,
            "variant_id": variant_id,
            "name": details["name"],
            "category": details["category"],
            "variant_label": details["variant_label"],
            "unit_price": details["unit_price"],
            "qty": qty
        })

    mongo.db.carts.update_one(
        {"_id": cart_id},
        {"$set": {"items": items}},
        upsert=True
    )


def update_cart_line(line_id: str, qty: int) -> None:
    cart = get_cart()
    qty = int(qty)

    items = cart.get("items", [])
    new_items = []
    for line in items:
        if line.get("_id") == line_id:
            if qty > 0:
                line["qty"] = qty
                new_items.append(line)
        else:
            new_items.append(line)

    mongo.db.carts.update_one({"_id": cart["_id"]}, {"$set": {"items": new_items}})


def remove_cart_line(line_id: str) -> None:
    cart = get_cart()
    items = [l for l in (cart.get("items", []) or []) if l.get("_id") != line_id]
    mongo.db.carts.update_one({"_id": cart["_id"]}, {"$set": {"items": items}})


def clear_cart() -> None:
    cart = get_cart()
    mongo.db.carts.update_one({"_id": cart["_id"]}, {"$set": {"items": []}})


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
