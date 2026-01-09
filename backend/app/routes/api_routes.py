

from flask import Blueprint, jsonify
from .services.menu_service import get_all_menu_items

api_bp = Blueprint("api", __name__, url_prefix="/api")

@api_bp.route("/status", methods=["GET"])
def status():
    return jsonify({"status": "API online"})

@api_bp.route("/menu", methods=["GET"])
def api_menu():
    items = get_all_menu_items()
    return jsonify(items)
