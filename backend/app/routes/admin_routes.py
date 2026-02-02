from flask import Blueprint, render_template
from app.security.admin import admin_required


admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

@admin_bp.route("/")
@admin_required
def admin_home():
    return render_template("admin_menu.html")


@admin_bp.route("/menu")
@admin_required
def admin_menu():
    return render_template("admin_menu.html")


@admin_bp.route("/orders")
@admin_required
def admin_orders():
    return render_template("admin_orders.html")
