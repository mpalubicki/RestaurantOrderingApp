import os
import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]  # .../backend
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import pytest


@pytest.fixture()
def app():
    os.environ.pop("GAE_ENV", None)
    os.environ.pop("GAE_INSTANCE", None)

    os.environ["SECRET_KEY"] = "test-secret"
    os.environ["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    os.environ["MONGO_URI"] = "mongodb://localhost:27017/test"
    os.environ["WTF_CSRF_ENABLED"] = "False"

    from app import create_app
    from app.extensions import db

    app = create_app()
    app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
    )

    with app.app_context():
        db.create_all()

    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()
