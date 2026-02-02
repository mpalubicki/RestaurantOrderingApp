import uuid
from google.cloud import storage
from flask import current_app

ALLOWED_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def _bucket_name() -> str:
    b = current_app.config.get("GCS_BUCKET")
    if not b:
        raise RuntimeError("Missing GCS_BUCKET configuration.")
    return b


def _safe_extension(filename: str | None) -> str:
    name = (filename or "").strip().lower()
    if "." in name:
        ext = "." + name.rsplit(".", 1)[-1]
        if ext in ALLOWED_EXTS:
            return ext
    return ".jpg"


def upload_menu_image(file_storage, folder: str = "menu") -> dict:
    client = storage.Client()
    bucket_name = _bucket_name()
    bucket = client.bucket(bucket_name)

    ext = _safe_extension(getattr(file_storage, "filename", None))
    object_name = f"{folder}/{uuid.uuid4().hex}{ext}"

    blob = bucket.blob(object_name)
    blob.upload_from_file(
        file_storage.stream,
        content_type=getattr(file_storage, "mimetype", "image/jpeg"),
        rewind=True,
    )

    url = f"https://storage.googleapis.com/{bucket_name}/{object_name}"
    return {"url": url, "object_name": object_name}


def delete_gcs_object(object_name: str) -> None:
    client = storage.Client()
    bucket = client.bucket(_bucket_name())
    bucket.blob(object_name).delete()
