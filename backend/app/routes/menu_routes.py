from flask import Blueprint, render_template

menu_bp = Blueprint("menu", __name__)

@menu_bp.route("/menu", methods=["GET", "POST"])
def menu():
    return render_template("menu.html")