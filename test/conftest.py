import pytest
from app import app, db

@pytest.fixture
def client(tmp_path):
    app.config.from_object("config.TestingConfig")
    with app.app_context():
        db.create_all()
    with app.test_client() as client:
        yield client
