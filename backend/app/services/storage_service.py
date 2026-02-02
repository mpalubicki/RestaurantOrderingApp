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


def upload_menu_image(file_storage, folder: str = "menu") -> str:
    client = storage.Client()
    bucket_name = _bucket_name()
    bucket = client.bucket(bucket_name)

    ext = _safe_extension(getattr(file_storage, "filename", None))
    object_name = f"{folder}/{uuid.uuid4().hex}{ext}"

    blob = bucket.blob(object_name)

    blob.upload_from_file(
        file_storage.stream,
        content_type=getattr(file_storage, "mimetype", "image/jpeg"),
        rewind=True,  # ensures stream position is correct
    )

    return f"https://storage.googleapis.com/{bucket_name}/{object_name}"
