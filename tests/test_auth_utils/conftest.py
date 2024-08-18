import pytest
from src.redis_manager.conn_manager import get_conn


@pytest.fixture(autouse=True, scope="session")
def clean_session():
    r = get_conn()
    r.delete("session")
    yield
    r.delete("session")

