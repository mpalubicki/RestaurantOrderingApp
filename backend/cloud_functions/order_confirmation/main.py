from datetime import datetime, timezone
from flask import Request, jsonify
from google.cloud import datastore

client = datastore.Client()

def order_confirmation(request: Request):
    if request.method == "GET":
        client.put(entity)
        return jsonify({"ok": True, "version": "datastore-v1"}), 200


    if request.method != "POST":
        return jsonify({"error": "method_not_allowed"}), 405

    data = request.get_json(silent=True) or {}
    order_id = data.get("order_id")

    if not order_id:
        return jsonify({"error": "missing_order_id"}), 400

    entity = datastore.Entity(key=client.key("order_confirmations", str(order_id)))
    entity.update({
        "order_id": str(order_id),
        "user_email": data.get("user_email"),
        "total_amount": data.get("total_amount"),
        "currency": data.get("currency", "GBP"),
        "items": data.get("items", []),
        "received_at": datetime.now(timezone.utc).isoformat(),
        "source": "restaurant-app",
    })

    try:
        client.put(entity)
        return jsonify({"ok": True}), 200
    except Exception as e:
        return jsonify({"error": "datastore_write_failed", "details": repr(e)}), 500
