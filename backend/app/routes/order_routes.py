from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from backend.app.services.order_service import (
    get_cart, add_to_cart, update_cart_line, remove_cart_line, clear_cart, cart_totals
)


order_bp = Blueprint("orders", __name__)


@order_bp.route("/orders", methods=["GET"])
@login_required
def orders():
    cart = get_cart()
    items, total = cart_totals(cart)
    return render_template("cart.html", cart_items=items, total=total)


@order_bp.route("/orders/add", methods=["POST"])
@login_required
def orders_add():
    menu_item_id = request.form.get("menu_item_id", "")
    variant_id = request.form.get("variant_id", "")
    qty = request.form.get("qty", "1")

    if not menu_item_id or not variant_id:
        flash("Could not add item to cart (missing item/variant).", "danger")
        return redirect(url_for("menu.menu"))

    add_to_cart(menu_item_id, variant_id, qty)
    flash("Added to cart.", "success")
    return redirect(url_for("menu.menu"))


@order_bp.route("/orders/update", methods=["POST"])
@login_required
def orders_update():
    line_id = request.form.get("line_id", "")
    qty = request.form.get("qty", "1")

    if not line_id:
        flash("Could not update cart item.", "danger")
        return redirect(url_for("orders.orders"))

    update_cart_line(line_id, qty)
    flash("Cart updated.", "success")
    return redirect(url_for("orders.orders"))


@order_bp.route("/orders/remove", methods=["POST"])
@login_required
def orders_remove():
    line_id = request.form.get("line_id", "")
    if not line_id:
        flash("Could not remove cart item.", "danger")
        return redirect(url_for("orders.orders"))

    remove_cart_line(line_id)
    flash("Item removed.", "success")
    return redirect(url_for("orders.orders"))


@order_bp.route("/orders/clear", methods=["POST"])
@login_required
def orders_clear():
    clear_cart()
    flash("Cart emptied.", "success")
    return redirect(url_for("orders.orders"))
