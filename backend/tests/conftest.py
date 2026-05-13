import os
import tempfile

import pytest

os.environ["SAFEINTAKE_DATA_DIR"] = tempfile.mkdtemp(prefix="safeintake-test-")
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app.main import create_app  # noqa: E402
from app.models import db  # noqa: E402


@pytest.fixture
def app():
    app = create_app()
    app.config.update(TESTING=True)
    with app.app_context():
        db.drop_all()
        db.create_all()
    yield app


@pytest.fixture
def client(app):
    return app.test_client()
