import pytest
from app import create_app
from app.extensions import db
from config import Config


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    SECRET_KEY = "test-secret-key"


class TestConfigWithCSRF(TestConfig):
    WTF_CSRF_ENABLED = True


@pytest.fixture
def app():
    app = create_app(TestConfig)

    with app.app_context():
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def app_with_csrf():
    app = create_app(TestConfigWithCSRF)

    with app.app_context():
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client_with_csrf(app_with_csrf):
    return app_with_csrf.test_client()
