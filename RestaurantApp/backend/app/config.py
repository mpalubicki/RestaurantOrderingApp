

import os


if not os.environ.get("GAE_ENV") and os.path.exists(".env"):
    from dotenv import load_dotenv
    load_dotenv()

class Config:

    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI")
    SQLALCHEMY_TRACK_MODIFICATIONS = False


    SECRET_KEY = os.getenv("SECRET_KEY")


    MONGO_URI = os.environ.get("MONGO_URI")

    GCS_BUCKET = os.getenv("GCS_BUCKET")