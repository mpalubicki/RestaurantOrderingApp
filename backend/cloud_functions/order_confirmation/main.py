import json
from datetime import datetime, timezone
from flask import Request, jsonify

from google.cloud import firestore

db = firestore.Client()

def order_confirmation(request: Request):
    if request.method == "GET":
        return jsonify({"ok": True, "message": "Function live. Send POST with JSON."}), 200

    if request.method != "POST":
        return jsonify({"error": "method_not_allowed"}), 405

    data = request.get_json(silent=True) or {}

    order_id = data.get("order_id")
    user_email = data.get("user_email")
    total_amount = data.get("total_amount")
    currency = data.get("currency", "GBP")
    items = data.get("items", [])

    if not order_id:
        return jsonify({"error": "missing_order_id"}), 400

    doc = {
        "order_id": order_id,
        "user_email": user_email,
        "total_amount": total_amount,
        "currency": currency,
        "items": items,
        "received_at": datetime.now(timezone.utc).isoformat(),
        "source": "restaurant-app",
    }

    db.collection("order_confirmations").document(str(order_id)).set(doc)

    return jsonify({"ok": True})
