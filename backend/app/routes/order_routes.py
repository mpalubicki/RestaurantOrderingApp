from flask import Blueprint, render_template

order_bp = Blueprint("orders", __name__)

@order_bp.route("/orders")
def orders():
    return render_template("cart.html")