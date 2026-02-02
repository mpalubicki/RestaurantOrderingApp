from flask import Blueprint, render_template, request, redirect, session, url_for
from flask_wtf.csrf import validate_csrf
from werkzeug.exceptions import BadRequest


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
    return render_template("index.html")


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
