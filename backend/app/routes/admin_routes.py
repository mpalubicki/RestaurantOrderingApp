from datetime import datetime, timezone
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.extensions import mongo
from app.services.storage_service import upload_menu_image
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

    return render_template("admin_upload_menu_image.html")


@admin_bp.route("/orders", methods=["GET"])
@login_required
def orders_dashboard():
    guard = _require_admin()
    if guard:
        return guard

    orders = get_recent_orders_for_admin(limit=50)
    return render_template("admin_orders.html", orders=orders)
