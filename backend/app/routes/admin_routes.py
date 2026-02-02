from datetime import datetime, timezone
from bson import ObjectId

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app.extensions import mongo
from app.services.storage_service import upload_menu_image, delete_gcs_object
from app.services.admin_service import get_recent_orders_for_admin


admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def _require_admin():
    if not getattr(current_user, "is_admin", False):
        flash("You do not have permission to access admin pages.", "danger")
        return redirect(url_for("main.index"))
    return None


@admin_bp.route("/", methods=["GET"])
@login_required
def admin_home():
    guard = _require_admin()
    if guard:
        return guard
    return render_template("admin_menu.html")


@admin_bp.route("/upload-menu-image", methods=["GET", "POST"])
@login_required
def upload_menu_image_page():
    guard = _require_admin()
    if guard:
        return guard

    if request.method == "POST":
        f = request.files.get("image")
        if not f or not f.filename:
            flash("Please choose an image file.", "warning")
            return redirect(url_for("admin.upload_menu_image_page"))

        try:
            result = upload_menu_image(f, folder="menu")

            if isinstance(result, str):
                url = result
                object_name = None
            else:
                url = result.get("url")
                object_name = result.get("object_name")

            if not url:
                raise RuntimeError("Upload succeeded but no URL was returned.")

            mongo.db.uploaded_images.insert_one({
                "url": url,
                "object_name": object_name,
                "uploaded_at": datetime.now(timezone.utc),
                "active": True,
            })

            flash("Uploaded successfully and added to image library.", "success")
            return render_template("admin_upload_menu_image.html", uploaded_url=url)

        except Exception as e:
            flash(f"Upload failed: {e}", "danger")
            return redirect(url_for("admin.upload_menu_image_page"))

    images = list(
        mongo.db.uploaded_images.find({"active": True})
        .sort("uploaded_at", -1)
        .limit(200)
    )

    slots = mongo.db.homepage_slots.find_one({"_id": "homepage"}) or {
        "_id": "homepage",
        "slot1": None,
        "slot2": None,
        "slot3": None,
        "slot4": None,
    }

    return render_template("admin_upload_menu_image.html", images=images, slots=slots)


@admin_bp.route("/homepage-slots", methods=["POST"])
@login_required
def update_homepage_slots():
    guard = _require_admin()
    if guard:
        return guard

    def parse_image_id(value: str):
        v = (value or "").strip()
        if v == "":
            return None
        try:
            return ObjectId(v)
        except Exception:
            return None

    slot1 = parse_image_id(request.form.get("slot1"))
    slot2 = parse_image_id(request.form.get("slot2"))
    slot3 = parse_image_id(request.form.get("slot3"))
    slot4 = parse_image_id(request.form.get("slot4"))

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

    flash("Homepage image slots updated.", "success")
    return redirect(url_for("admin.upload_menu_image_page"))


@admin_bp.route("/images/hide", methods=["POST"])
@login_required
def hide_uploaded_image():
    guard = _require_admin()
    if guard:
        return guard

    image_id = (request.form.get("image_id") or "").strip()
    if not image_id:
        flash("Missing image id.", "warning")
        return redirect(url_for("admin.upload_menu_image_page"))

    mongo.db.uploaded_images.update_one(
        {"_id": ObjectId(image_id)},
        {"$set": {"active": False}}
    )

    flash("Image hidden from library.", "success")
    return redirect(url_for("admin.upload_menu_image_page"))


@admin_bp.route("/images/delete", methods=["POST"])
@login_required
def delete_uploaded_image():
    guard = _require_admin()
    if guard:
        return guard

    image_id = (request.form.get("image_id") or "").strip()
    if not image_id:
        flash("Missing image id.", "warning")
        return redirect(url_for("admin.upload_menu_image_page"))

    oid = ObjectId(image_id)
    doc = mongo.db.uploaded_images.find_one({"_id": oid})
    if not doc:
        flash("Image not found.", "warning")
        return redirect(url_for("admin.upload_menu_image_page"))

    try:
        if doc.get("object_name"):
            delete_gcs_object(doc["object_name"])
    except Exception as e:
        flash(f"Bucket delete failed: {e}", "danger")
        return redirect(url_for("admin.upload_menu_image_page"))

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

    flash("Image deleted from bucket and library.", "success")
    return redirect(url_for("admin.upload_menu_image_page"))


@admin_bp.route("/orders", methods=["GET"])
@login_required
def orders_dashboard():
    guard = _require_admin()
    if guard:
        return guard

    orders = get_recent_orders_for_admin(limit=50)
    return render_template("admin_orders.html", orders=orders)
