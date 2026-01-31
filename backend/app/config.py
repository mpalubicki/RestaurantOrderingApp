import os


if not os.environ.get("GAE_ENV") and os.path.exists(".env"):
    from dotenv import load_dotenv
    load_dotenv()


def _running_on_gae() -> bool:
    return bool(os.environ.get("GAE_INSTANCE")) or bool(os.environ.get("GAE_ENV"))


class Config:

    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    if _running_on_gae():
        from app.security.secrets import get_secret
        SECRET_KEY = get_secret("SECRET_KEY")
        MONGO_URI = get_secret("MONGO_URI")

    else:
         SECRET_KEY = os.getenv("SECRET_KEY")
         MONGO_URI = os.environ.get("MONGO_URI")
         GCS_BUCKET = os.getenv("GCS_BUCKET")

   
