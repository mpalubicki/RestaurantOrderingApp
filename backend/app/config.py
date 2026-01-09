import os
from dotenv import load_dotenv

load_dotenv()

import os

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI")
    SQLALCHEMY_TRACK_MODIFICATIONS = False


    SECRET_KEY = os.getenv("SECRET_KEY")

    # MongoDB (Atlas)
    MONGO_URI = os.environ.get("MONGO_URI")
    # Google Cloud Storage
    GCS_BUCKET = os.getenv("GCS_BUCKET")