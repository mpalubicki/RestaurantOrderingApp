from dataclasses import dataclass
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from ..extensions import mongo


@dataclass
class AuthUser:
    id: str
    email: str
    first_name: str
    last_name: str

    @property
    def is_authenticated(self): return True

    @property
    def is_active(self): return True

    @property
    def is_anonymous(self): return False

    def get_id(self):
        return self.id


def _users_col():
    return mongo.db.users


def create_user_account(email: str, password: str, first_name: str, last_name: str) -> AuthUser:
    email = (email or "").strip().lower()
    first_name = (first_name or "").strip()
    last_name = (last_name or "").strip()

    if not email or not password or not first_name or not last_name:
        raise ValueError("All fields are required.")

    existing = _users_col().find_one({"email": email})
    if existing:
        raise ValueError("An account with that email already exists.")

    doc = {
        "email": email,
        "password_hash": generate_password_hash(password),
        "first_name": first_name,
        "last_name": last_name,
    }

    res = _users_col().insert_one(doc)

    return AuthUser(
        id=str(res.inserted_id),
        email=email,
        first_name=first_name,
        last_name=last_name
    )


def authenticate_user(email: str, password: str) -> AuthUser | None:
    email = (email or "").strip().lower()
    password = password or ""

    doc = _users_col().find_one({"email": email})
    if not doc:
        return None

    if not check_password_hash(doc.get("password_hash", ""), password):
        return None

    return AuthUser(
        id=str(doc["_id"]),
        email=doc.get("email", ""),
        first_name=doc.get("first_name", ""),
        last_name=doc.get("last_name", "")
    )


def get_user_by_id(user_id: str) -> AuthUser | None:
    try:
        oid = ObjectId(user_id)
    except Exception:
        return None

    doc = _users_col().find_one({"_id": oid})
    if not doc:
        return None

    return AuthUser(
        id=str(doc["_id"]),
        email=doc.get("email", ""),
        first_name=doc.get("first_name", ""),
        last_name=doc.get("last_name", "")
    )
