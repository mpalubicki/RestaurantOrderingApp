from flask import Blueprint, render_template, session, request
from ..services.menu_service import get_menu_boxes


menu_bp = Blueprint("menu", __name__)


@menu_bp.route("/menu", methods=["GET", "POST"])
def menu():
    lang = (request.args.get("lang") or session.get("lang") or "en").strip().lower()
    session["lang"] = lang

    menu_by_category = get_menu_boxes(group_by_category=True, target_language=lang)
    return render_template("menu.html", menu_by_category=menu_by_category)
