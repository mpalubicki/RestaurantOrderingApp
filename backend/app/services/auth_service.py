from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db
from app.models.user_model import User
from flask import current_app


def create_user_account(
    email: str,
    password: str,
    first_name: str | None = None,
    last_name: str | None = None,
) -> User:
    email = (email or "").strip().lower()
    if not email:
        raise ValueError("Email is required")

    existing = User.query.filter_by(email=email).first()
    if existing:
        raise ValueError("Email already registered")

    password_hash = generate_password_hash(password)

    admin_emails = current_app.config.get("ADMIN_EMAILS") or set()
    is_admin = email in admin_emails

    user = User(
        email=email,
        password_hash=password_hash,
        first_name=(first_name or "").strip() or None,
        last_name=(last_name or "").strip() or None,
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



