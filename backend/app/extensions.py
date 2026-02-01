from flask_pymongo import PyMongo
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf import CSRFProtect
from flask import request
from flask_login import AnonymousUserMixin
import os


mongo = PyMongo()
db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()


@login_manager.user_loader
def load_user(user_id):
    from app.models.user_model import User
    return User.query.get(int(user_id))


class DevUser(AnonymousUserMixin):
    @property
    def is_authenticated(self):
        if request.path.startswith("/auth/login") or request.path.startswith("/auth/register"):
            return False
        return True

    @property
    def id(self):
        return 1  # temp


if os.getenv("DEV_SKIP_AUTH") == "1":
    login_manager.anonymous_user = DevUser

