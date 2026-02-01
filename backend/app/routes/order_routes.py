from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.services.order_service import (
    get_cart, add_to_cart, update_cart_line, remove_cart_line, clear_cart, cart_totals, checkout_to_sql_order
)
from app.models.sql_order_model import Order

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


@order_bp.route("/orders/checkout", methods=["POST"])
@login_required
def checkout():
    try:
        order_id = checkout_to_sql_order()
        flash("Order placed successfully.", "success")
        return redirect(url_for("orders.confirmation", order_id=order_id))
    except ValueError as e:
        flash(str(e), "danger")
        return redirect(url_for("orders.orders"))


@order_bp.route("/orders/confirmation/<int:order_id>", methods=["GET"])
@login_required
def confirmation(order_id: int):
    order = Order.query.filter_by(id=order_id, user_id=int(current_user.get_id())).first_or_404()
    return render_template("order_confirmation.html", order=order)


@order_bp.route("/orders/history", methods=["GET"])
@login_required
def history():
    orders = (
        Order.query
        .filter_by(user_id=int(current_user.get_id()))
        .order_by(Order.created_at.desc())
        .all()
    )
    return render_template("order_history.html", orders=orders)
