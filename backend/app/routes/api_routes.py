from flask import Blueprint, jsonify, request
from app.services.menu_service import get_menu_boxes
from app.services.translate_service import translate_text


api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/status", methods=["GET"])
def status():
    return jsonify({"status": "API online"})


@api_bp.route("/menu", methods=["GET"])
def api_menu():
    lang = (request.args.get("lang") or "en").strip().lower()
    items = get_menu_boxes(group_by_category=True, target_language=lang)
    return jsonify(items)


@api_bp.route("/translate", methods=["POST"])
def api_translate():
    payload = request.get_json(silent=True) or {}
    text = (payload.get("text") or "").strip()
    target = (payload.get("target_language") or "it").strip()

    if not text:
        return jsonify({"error": "Missing 'text'"}), 400

    translated = translate_text(text=text, target_language=target)
    return jsonify({
        "input": text,
        "target_language": target,
        "translated": translated
    })









