from flask import Blueprint, render_template, request, redirect, url_for
from backend.app.services.order_service import (
    get_cart, cart_totals, add_to_cart, update_cart_line, remove_cart_line, clear_cart
)

order_bp = Blueprint("orders", __name__)

@order_bp.route("/orders", methods=["GET"])
def orders():
    cart = get_cart()
    cart_items, cart_total = cart_totals(cart)
    return render_template("cart.html", cart_items=cart_items, cart_total=cart_total)


@order_bp.route("/orders/add", methods=["POST"])
def orders_add():
    menu_item_id = request.form.get("menu_item_id")
    variant_id = request.form.get("variant_id")
    qty = request.form.get("qty", 1)

    if menu_item_id and variant_id:
        add_to_cart(menu_item_id, variant_id, qty)

    return redirect(url_for("orders.orders"))


@order_bp.route("/orders/update", methods=["POST"])
def orders_update():
    line_id = request.form.get("line_id")
    qty = request.form.get("qty", 1)

    if line_id:
        update_cart_line(line_id, qty)

    return redirect(url_for("orders.orders"))


@order_bp.route("/orders/remove", methods=["POST"])
def orders_remove():
    line_id = request.form.get("line_id")
    if line_id:
        remove_cart_line(line_id)

    return redirect(url_for("orders.orders"))


@order_bp.route("/orders/clear", methods=["POST"])
def orders_clear():
    clear_cart()
    return redirect(url_for("orders.orders"))
