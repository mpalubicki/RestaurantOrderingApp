from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
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
            public_url = upload_menu_image(f, folder="menu")
            flash(f"Uploaded successfully: {public_url}", "success")
            return render_template("admin_upload_menu_image.html", uploaded_url=public_url)
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


