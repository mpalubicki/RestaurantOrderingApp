from flask import Blueprint

api_bp = Blueprint("api", __name__, url_prefix="/api")

@api_bp.route("/status")
def status():
    return {"status": "API online"}