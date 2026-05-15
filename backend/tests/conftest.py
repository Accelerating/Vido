import os
import pytest
from fastapi.testclient import TestClient

os.environ["VIDO_TEST"] = "1"


@pytest.fixture
def app():
    from app.database import init_db, get_db
    init_db(test=True)
    from app.main import create_app
    application = create_app()
    yield application
    # Cleanup test db
    from app.database import close_db
    close_db()
    os.remove("test_vido.db")
    if os.path.exists("test_vido.db-shm"):
        os.remove("test_vido.db-shm")
    if os.path.exists("test_vido.db-wal"):
        os.remove("test_vido.db-wal")


@pytest.fixture
def client(app):
    return TestClient(app)
