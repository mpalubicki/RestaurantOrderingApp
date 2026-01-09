from flask_pymongo import PyMongo
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf import CSRFProtect

mongo = PyMongo()
db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()



@login_manager.user_loader
def load_user(user_id):
    from app.models.user_model import User  # import here to avoid circular import
    return User.query.get(int(user_id))



from flask import request
from flask_login import AnonymousUserMixin

class DevUser(AnonymousUserMixin):
    @property
    def is_authenticated(self):
        # Allow real login/register pages to behave normally
        if request.path.startswith("/auth/login") or request.path.startswith("/auth/register"):
            return False
        return True

    @property
    def id(self):
        return 1  # fake user


# Enable dev mode with always-logged-in user
import os
if os.getenv("DEV_SKIP_AUTH") == "1":
    login_manager.anonymous_user = DevUser
