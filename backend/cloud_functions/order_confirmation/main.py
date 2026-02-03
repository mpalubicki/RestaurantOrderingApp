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

    if not order_id:
        return jsonify({"error": "missing_order_id"}), 400

    doc = {
        "order_id": order_id,
        "user_email": data.get("user_email"),
        "total_amount": data.get("total_amount"),
        "currency": data.get("currency", "GBP"),
        "items": data.get("items", []),
        "received_at": datetime.now(timezone.utc).isoformat(),
        "source": "restaurant-app",
    }

    try:
        db.collection("order_confirmations").document(str(order_id)).set(doc)
        return jsonify({"ok": True}), 200
    except Exception as e:
        print("FIRESTORE WRITE FAILED:", repr(e))
        return jsonify({"error": "firestore_write_failed", "details": repr(e)}), 500
