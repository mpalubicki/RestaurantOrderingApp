import os


if not os.environ.get("GAE_ENV") and os.path.exists(".env"):
    from dotenv import load_dotenv
    load_dotenv()


def _running_on_gae() -> bool:
    return bool(os.environ.get("GAE_ENV")) or bool(os.environ.get("GAE_INSTANCE"))


def _build_cloudsql_postgres_uri(db_user: str, db_password: str, db_name: str, instance_conn_name: str) -> str:
    return (
        f"postgresql+psycopg2://{db_user}:{db_password}@/"
        f"{db_name}?host=/cloudsql/{instance_conn_name}"
    )


class Config:
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    DB_NAME = os.getenv("DB_NAME")
    DB_USER = os.getenv("DB_USER")
    INSTANCE_CONNECTION_NAME = os.getenv("INSTANCE_CONNECTION_NAME")

    GCS_BUCKET = os.getenv("GCS_BUCKET")

    if _running_on_gae():
        from app.security.secrets import get_secret

        SECRET_KEY = get_secret("SECRET_KEY")
        MONGO_URI = get_secret("MONGO_URI")

        DB_PASSWORD = get_secret("DB_PASSWORD")

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
        SECRET_KEY = os.getenv("SECRET_KEY")
        MONGO_URI = os.getenv("MONGO_URI")
        SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI")


