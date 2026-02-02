import os
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

if not os.environ.get("GAE_ENV") and os.path.exists(".env"):
    from dotenv import load_dotenv
    load_dotenv()


def _running_on_gae() -> bool:
    return bool(os.environ.get("GAE_ENV")) or bool(os.environ.get("GAE_INSTANCE"))


def _build_cloudsql_postgres_uri(db_user: str, db_password: str, db_name: str, instance_conn_name: str) -> str:
    return (
        f"postgresql+psycopg://{db_user}:{db_password}@/"
        f"{db_name}?host=/cloudsql/{instance_conn_name}"
    )


def _strip_or_none(v: str | None) -> str | None:
    if v is None:
        return None
    v = v.strip()
    return v if v else None


def _csv_set(v: str | None) -> set[str]:
    v = _strip_or_none(v)
    if not v:
        return set()
    return {x.strip().lower() for x in v.split(",") if x.strip()}


def _normalize_mongo_uri(uri: str | None) -> str | None:
    uri = _strip_or_none(uri)
    if not uri:
        return None

    uri = uri.replace("\r", "").replace("\n", "").replace("%0A", "").replace("%0a", "")

    parts = urlsplit(uri)
    if parts.query:
        q = parse_qsl(parts.query, keep_blank_values=True)
        cleaned = []
        for k, v in q:
            if isinstance(v, str):
                v = v.replace("\r", "").replace("\n", "").strip()
            cleaned.append((k, v))
        uri = urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(cleaned), parts.fragment))

    return uri


class Config:
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    DB_NAME = _strip_or_none(os.getenv("DB_NAME"))
    DB_USER = _strip_or_none(os.getenv("DB_USER"))
    INSTANCE_CONNECTION_NAME = _strip_or_none(os.getenv("INSTANCE_CONNECTION_NAME"))
    GCS_BUCKET = _strip_or_none(os.getenv("GCS_BUCKET"))
    ADMIN_EMAILS = set()

    if _running_on_gae():
        from app.security.secrets import get_secret

        SECRET_KEY = _strip_or_none(get_secret("SECRET_KEY"))
        MONGO_URI = _normalize_mongo_uri(get_secret("MONGO_URI"))
        DB_PASSWORD = _strip_or_none(get_secret("DB_PASSWORD"))
        ADMIN_EMAILS = _csv_set(get_secret("ADMIN_EMAILS"))

        if DB_NAME and DB_USER and INSTANCE_CONNECTION_NAME and DB_PASSWORD:
            SQLALCHEMY_DATABASE_URI = _build_cloudsql_postgres_uri(
                db_user=DB_USER,
                db_password=DB_PASSWORD,
                db_name=DB_NAME,
                instance_conn_name=INSTANCE_CONNECTION_NAME,
            )
        else:
            SQLALCHEMY_DATABASE_URI = None
    else:
        SECRET_KEY = _strip_or_none(os.getenv("SECRET_KEY"))
        MONGO_URI = _normalize_mongo_uri(os.getenv("MONGO_URI"))
        ADMIN_EMAILS = _csv_set(os.getenv("ADMIN_EMAILS"))
        SQLALCHEMY_DATABASE_URI = _strip_or_none(os.getenv("SQLALCHEMY_DATABASE_URI") or os.getenv("DATABASE_URL")
        )


