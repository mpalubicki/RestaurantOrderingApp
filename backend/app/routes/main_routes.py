from flask import Blueprint, render_template, request, redirect, session, url_for
from flask_wtf.csrf import validate_csrf
from werkzeug.exceptions import BadRequest
from app.extensions import mongo

main_bp = Blueprint("main", __name__)

SUPPORTED_LANGS = {
    "en": "English",
    "it": "Italiano",
    "fr": "Français",
    "es": "Español",
    "de": "Deutsch",
}


@main_bp.route("/")
def index():
    slots = mongo.db.homepage_slots.find_one({"_id": "homepage"}) or {}
    ids = [slots.get("slot1"), slots.get("slot2"), slots.get("slot3"), slots.get("slot4")]

    selected = {}
    valid_ids = [i for i in ids if i]

    if valid_ids:
        for doc in mongo.db.uploaded_images.find({"_id": {"$in": valid_ids}, "active": True}):
            selected[str(doc["_id"])] = doc

    homepage_slots = []
    for i in ids:
        if i and str(i) in selected:
            homepage_slots.append(selected[str(i)])
        else:
            homepage_slots.append(None)

    return render_template("index.html", homepage_slots=homepage_slots)


@main_bp.route("/set-language", methods=["POST"])
def set_language():
    token = request.form.get("csrf_token", "")
    try:
        validate_csrf(token)
    except Exception:
        raise BadRequest("CSRF validation failed")

    lang = (request.form.get("lang") or "en").strip().lower()
    if lang not in SUPPORTED_LANGS:
        lang = "en"

    session["lang"] = lang

    next_url = request.form.get("next") or url_for("menu.menu")
    return redirect(next_url)
