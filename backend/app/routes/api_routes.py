from datetime import datetime, timezone
from bson import ObjectId

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from app.extensions import mongo, db
from app.models.sql_order_model import Order
from app.services.menu_service import get_menu_boxes
from app.services.translate_service import translate_text
from app.services.storage_service import upload_menu_image, delete_gcs_object
from app.services.order_service import (
    get_cart,
    add_to_cart,
    update_cart_line,
    remove_cart_line,
    clear_cart,
    cart_totals,
    checkout_to_sql_order,
    notify_order_confirmation_by_order_id
)

from app.services.admin_service import get_recent_orders_for_admin, get_order_for_admin
from app.services.datastore_service import (
    list_order_confirmations,
    get_order_confirmation,
    delete_order_confirmation,
)

api_bp = Blueprint("api", __name__, url_prefix="/api")


def _is_admin() -> bool:
    return bool(getattr(current_user, "is_admin", False))


def _admin_only():
    if not _is_admin():
        return jsonify({"error": "admin_required"}), 403
    return None


def _iso(dt):
    if not dt:
        return None
    try:
        return dt.isoformat()
    except Exception:
        return str(dt)


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


@api_bp.route("/admin/upload-menu-image", methods=["POST"])
@login_required
def api_admin_upload_menu_image():
    guard = _admin_only()
    if guard:
        return guard

    if "file" not in request.files:
        return jsonify({"error": "Missing file field 'file'"}), 400

    f = request.files["file"]
    if not f or not f.filename:
        return jsonify({"error": "No file selected"}), 400

    result = upload_menu_image(f, folder="menu")

    if isinstance(result, str):
        url = result
        object_name = None
    else:
        url = result.get("url")
        object_name = result.get("object_name")

    if not url:
        return jsonify({"error": "Upload succeeded but URL missing"}), 500

    mongo.db.uploaded_images.insert_one({
        "url": url,
        "object_name": object_name,
        "uploaded_at": datetime.now(timezone.utc),
        "active": True,
    })

    return jsonify({"url": url, "object_name": object_name})


@api_bp.route("/cart", methods=["GET"])
@login_required
def api_get_cart():
    cart = get_cart()
    items, total = cart_totals(cart)
    return jsonify({
        "items": items,
        "total": round(float(total), 2)
    })


@api_bp.route("/cart/items", methods=["POST"])
@login_required
def api_add_cart_item():
    payload = request.get_json(silent=True) or {}
    menu_item_id = (payload.get("menu_item_id") or "").strip()
    variant_id = (payload.get("variant_id") or "").strip()
    qty = payload.get("qty", 1)

    if not menu_item_id or not variant_id:
        return jsonify({"error": "menu_item_id and variant_id required"}), 400

    before = get_cart()
    before_items = len(before.get("items", []) or [])

    add_to_cart(menu_item_id, variant_id, qty)

    after = get_cart()
    after_items = len(after.get("items", []) or [])

    if after_items == before_items and before_items == 0:
        return jsonify({"error": "item_not_found"}), 404

    items, total = cart_totals(after)
    return jsonify({
        "ok": True,
        "items": items,
        "total": round(float(total), 2)
    })


@api_bp.route("/cart/items/<line_id>", methods=["PATCH"])
@login_required
def api_update_cart_item(line_id: str):
    payload = request.get_json(silent=True) or {}
    qty = payload.get("qty", None)

    if qty is None:
        return jsonify({"error": "qty required"}), 400

    update_cart_line(line_id, qty)
    cart = get_cart()
    items, total = cart_totals(cart)
    return jsonify({
        "ok": True,
        "items": items,
        "total": round(float(total), 2)
    })


@api_bp.route("/cart/items/<line_id>", methods=["DELETE"])
@login_required
def api_delete_cart_item(line_id: str):
    remove_cart_line(line_id)
    cart = get_cart()
    items, total = cart_totals(cart)
    return jsonify({
        "ok": True,
        "items": items,
        "total": round(float(total), 2)
    })


@api_bp.route("/cart/clear", methods=["POST"])
@login_required
def api_clear_cart():
    clear_cart()
    return jsonify({"ok": True})


@api_bp.route("/cart/checkout", methods=["POST"])
@login_required
def api_checkout():
    try:
        order_id = checkout_to_sql_order()
        return jsonify({"ok": True, "order_id": order_id})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@api_bp.route("/orders", methods=["GET"])
@login_required
def api_list_orders():
    orders = (
        Order.query
        .filter_by(user_id=int(current_user.get_id()))
        .order_by(Order.created_at.desc())
        .all()
    )

    results = []
    for o in orders:
        results.append({
            "order_id": o.id,
            "status": o.status,
            "currency": o.currency,
            "total_amount": float(o.total_amount or 0),
            "created_at": _iso(o.created_at),
            "items_count": len(o.order_items or []),
        })

    return jsonify({"orders": results})


@api_bp.route("/orders/<int:order_id>", methods=["GET"])
@login_required
def api_order_detail(order_id: int):
    o = Order.query.filter_by(id=order_id, user_id=int(current_user.get_id())).first()
    if not o:
        return jsonify({"error": "not_found"}), 404

    items = []
    for it in (o.order_items or []):
        items.append({
            "name": it.name,
            "variant_label": it.variant_label,
            "qty": it.qty,
            "unit_price": float(it.unit_price or 0),
            "line_total": float(it.line_total or 0),
            "menu_item_id": it.menu_item_id,
            "variant_id": it.variant_id,
        })

    return jsonify({
        "order_id": o.id,
        "status": o.status,
        "currency": o.currency,
        "total_amount": float(o.total_amount or 0),
        "created_at": _iso(o.created_at),
        "items": items,
    })


@api_bp.route("/admin/orders", methods=["GET"])
@login_required
def api_admin_orders():
    guard = _admin_only()
    if guard:
        return guard

    results = get_recent_orders_for_admin(limit=50)

    safe = []
    for r in results:
        safe.append({
            "order_id": r.get("order_id"),
            "created_at": _iso(r.get("created_at")),
            "total": float(r.get("total") or 0),
            "user_first_name": r.get("user_first_name", ""),
            "user_last_name": r.get("user_last_name", ""),
            "order_items": r.get("order_items", []),
        })

    return jsonify({"orders": safe})


@api_bp.route("/images/homepage", methods=["GET"])
def api_get_homepage_images():
    slots = mongo.db.homepage_slots.find_one({"_id": "homepage"}) or {}
    ids = [slots.get("slot1"), slots.get("slot2"), slots.get("slot3"), slots.get("slot4")]

    valid_ids = [i for i in ids if i]
    selected = {}

    if valid_ids:
        for doc in mongo.db.uploaded_images.find({"_id": {"$in": valid_ids}, "active": True}):
            selected[str(doc["_id"])] = doc

    out = []
    for i in ids:
        if i and str(i) in selected:
            doc = selected[str(i)]
            out.append({
                "id": str(doc["_id"]),
                "url": doc.get("url"),
                "object_name": doc.get("object_name"),
            })
        else:
            out.append(None)

    return jsonify({"slots": out})


@api_bp.route("/admin/images/homepage", methods=["PATCH"])
@login_required
def api_set_homepage_images():
    guard = _admin_only()
    if guard:
        return guard

    data = request.get_json(silent=True) or {}

    def parse_oid(v):
        if v is None:
            return None
        s = str(v).strip()
        if not s:
            return None
        try:
            return ObjectId(s)
        except Exception:
            return None

    slot1 = parse_oid(data.get("slot1"))
    slot2 = parse_oid(data.get("slot2"))
    slot3 = parse_oid(data.get("slot3"))
    slot4 = parse_oid(data.get("slot4"))

    mongo.db.homepage_slots.update_one(
        {"_id": "homepage"},
        {"$set": {
            "slot1": slot1,
            "slot2": slot2,
            "slot3": slot3,
            "slot4": slot4,
            "updated_at": datetime.now(timezone.utc),
        }},
        upsert=True,
    )

    return jsonify({"ok": True})


@api_bp.route("/admin/images/library", methods=["GET"])
@login_required
def api_admin_images_library():
    guard = _admin_only()
    if guard:
        return guard

    docs = list(
        mongo.db.uploaded_images.find({"active": True})
        .sort("uploaded_at", -1)
        .limit(200)
    )

    out = []
    for d in docs:
        out.append({
            "id": str(d.get("_id")),
            "url": d.get("url"),
            "object_name": d.get("object_name"),
            "uploaded_at": _iso(d.get("uploaded_at")),
            "active": bool(d.get("active", True)),
        })

    return jsonify({"images": out})


@api_bp.route("/admin/images/<image_id>/hide", methods=["PATCH"])
@login_required
def api_admin_hide_image(image_id: str):
    guard = _admin_only()
    if guard:
        return guard

    try:
        oid = ObjectId(image_id)
    except Exception:
        return jsonify({"error": "invalid_id"}), 400

    mongo.db.uploaded_images.update_one(
        {"_id": oid},
        {"$set": {"active": False}}
    )

    return jsonify({"ok": True})


@api_bp.route("/admin/images/<image_id>", methods=["DELETE"])
@login_required
def api_admin_delete_image(image_id: str):
    guard = _admin_only()
    if guard:
        return guard

    try:
        oid = ObjectId(image_id)
    except Exception:
        return jsonify({"error": "invalid_id"}), 400

    doc = mongo.db.uploaded_images.find_one({"_id": oid})
    if not doc:
        return jsonify({"error": "not_found"}), 404

    try:
        if doc.get("object_name"):
            delete_gcs_object(doc["object_name"])
    except Exception as e:
        return jsonify({"error": f"bucket_delete_failed: {e}"}), 500

    mongo.db.homepage_slots.update_one(
        {"_id": "homepage"},
        {"$set": {
            "slot1": None,
            "slot2": None,
            "slot3": None,
            "slot4": None,
        }},
        upsert=True,
    )

    mongo.db.uploaded_images.delete_one({"_id": oid})
    return jsonify({"ok": True})


@api_bp.route("/admin/orders/<int:order_id>", methods=["GET"])
@login_required
def api_admin_order_detail(order_id: int):
    guard = _admin_only()
    if guard:
        return guard

    doc = get_order_for_admin(order_id)
    if not doc:
        return jsonify({"error": "order_not_found"}), 404

    return jsonify(doc), 200


@api_bp.route("/admin/orders/<int:order_id>/status", methods=["PATCH"])
@login_required
def api_admin_order_update_status(order_id: int):
    guard = _admin_only()
    if guard:
        return guard

    data = request.get_json(silent=True) or {}
    status = (data.get("status") or "").strip().lower()

    allowed = {"created", "paid", "preparing", "ready", "completed", "cancelled"}
    if status not in allowed:
        return jsonify({"error": "invalid_status", "allowed": sorted(allowed)}), 400

    order = Order.query.filter_by(id=int(order_id)).first()
    if not order:
        return jsonify({"error": "order_not_found"}), 404

    order.status = status
    db.session.commit()

    return jsonify({"ok": True, "order_id": order.id, "status": order.status}), 200


@api_bp.route("/admin/orders/<int:order_id>/notify", methods=["POST"])
@login_required
def api_admin_order_notify(order_id: int):
    guard = _admin_only()
    if guard:
        return guard

    result = notify_order_confirmation_by_order_id(order_id)
    code = 200 if result.get("ok") else 400
    return jsonify(result), code


@api_bp.route("/admin/order-confirmations", methods=["GET"])
@login_required
def api_admin_order_confirmations():
    guard = _admin_only()
    if guard:
        return guard

    limit = request.args.get("limit", "50")
    try:
        docs = list_order_confirmations(limit=int(limit))
    except Exception as e:
        return jsonify({"error": "datastore_read_failed", "details": repr(e)}), 500

    return jsonify({"results": docs}), 200


@api_bp.route("/admin/order-confirmations/<order_id>", methods=["GET"])
@login_required
def api_admin_order_confirmation_detail(order_id: str):
    guard = _admin_only()
    if guard:
        return guard

    doc = get_order_confirmation(order_id)
    if not doc:
        return jsonify({"error": "not_found"}), 404
    return jsonify(doc), 200


@api_bp.route("/admin/order-confirmations/<order_id>", methods=["DELETE"])
@login_required
def api_admin_order_confirmation_delete(order_id: str):
    guard = _admin_only()
    if guard:
        return guard

    try:
        ok = delete_order_confirmation(order_id)
    except Exception as e:
        return jsonify({"error": "datastore_delete_failed", "details": repr(e)}), 500

    if not ok:
        return jsonify({"error": "not_found"}), 404
    return jsonify({"ok": True}), 200
