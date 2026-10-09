import pytest

import app as application


@pytest.fixture
def test_app(tmp_path):
    application.DB_PATH = tmp_path / "test.db"
    application.app.config.update(TESTING=True)
    application.init_db()
    yield application.app


@pytest.fixture
def client(test_app):
    return test_app.test_client()
