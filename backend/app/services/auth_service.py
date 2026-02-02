from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db
from app.models.user_model import User
from flask import current_app


def create_user_account(email: str, password: str, first_name: str, last_name: str) -> User:
    email = (email or "").strip().lower()
    first_name = (first_name or "").strip()
    last_name = (last_name or "").strip()
    password = password or ""

    if not email or not password or not first_name or not last_name:
        raise ValueError("All fields are required.")

    existing = User.query.filter_by(email=email).first()
    if existing:
        raise ValueError("An account with that email already exists.")

    admin_emails = current_app.config.get("ADMIN_EMAILS", set())
    is_admin = (email or "").strip().lower() in admin_emails

    user = User(
        email=email,
        password_hash=password_hash,
        first_name=first_name,
        last_name=last_name,
        is_admin=is_admin,
    )

    db.session.add(user)
    db.session.commit()
    return user


def authenticate_user(email: str, password: str) -> User | None:
    email = (email or "").strip().lower()
    password = password or ""

    user = User.query.filter_by(email=email).first()
    if not user:
        return None

    if not check_password_hash(user.password_hash, password):
        return None

    return user


def get_user_by_id(user_id: str) -> User | None:
    try:
        uid = int(user_id)
    except Exception:
        return None
    return db.session.get(User, uid)

