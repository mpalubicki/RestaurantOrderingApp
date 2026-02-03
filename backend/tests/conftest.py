import os
import pytest


@pytest.fixture()
def app():
    os.environ.pop("GAE_ENV", None)
    os.environ.pop("GAE_INSTANCE", None)

    os.environ["SECRET_KEY"] = "test-secret"
    os.environ["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    os.environ["MONGO_URI"] = "mongodb://localhost:27017/test"  # won't connect unless used
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
