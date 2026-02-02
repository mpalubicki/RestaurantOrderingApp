import os
import uuid
from datetime import timedelta
from google.cloud import storage
from flask import current_app


def _bucket_name() -> str:
    b = current_app.config.get("GCS_BUCKET")
    if not b:
        raise RuntimeError("Missing GCS_BUCKET configuration.")
    return b


def upload_menu_image(file_storage, folder: str = "menu") -> str:
    client = storage.Client()
    bucket = client.bucket(_bucket_name())

    filename = (file_storage.filename or "").strip()
    ext = ""
    if "." in filename:
        ext = "." + filename.rsplit(".", 1)[-1].lower()

    if ext not in (".jpg", ".jpeg", ".png", ".webp"):
        ext = ".jpg"

    object_name = f"{folder}/{uuid.uuid4().hex}{ext}"
    blob = bucket.blob(object_name)

    blob.upload_from_file(file_storage.stream, content_type=file_storage.mimetype)

    blob.make_public()

    return blob.public_url
