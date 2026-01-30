from flask import Blueprint, render_template
from ..services.menu_service import get_menu_boxes

menu_bp = Blueprint("menu", __name__)

@menu_bp.route("/menu", methods=["GET", "POST"])
def menu():
    menu_by_category = get_menu_boxes(group_by_category=True)
    return render_template("menu.html", menu_by_category=menu_by_category)
