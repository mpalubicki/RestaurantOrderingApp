import os
from app.security.secrets import get_secret

class Config:
    # Detect App Engine standard
    if os.environ.get("GAE_ENV") == "standard":
        MONGO_URI = get_secret("MONGO_URI")
        SECRET_KEY = get_secret("FLASK_SECRET_KEY")
    else:
        MONGO_URI = os.environ.get("MONGO_URI")
        SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")

    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///local.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
