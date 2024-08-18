import asyncio
import re
import pytest

from src.auth.auth_utils import save_session, to_hash, valid_session, finish_session
from src.redis_manager.conn_manager import get_conn

##############################
# tests auth utils
# hash gen, session ge, validations
##############################

username = "Admin"
password = "Password"
user_agent = "Mozilla/5.0 (Windows NT 10.0; rv:109.0) Gecko/20100101 Firefox/115.0"


def is_sha256_hash(string: str) -> bool:
    sha256_pattern = re.compile(r'^[a-fA-F0-9]{64}$')
    match = sha256_pattern.match(string)
    return bool(match)


def test_to_hash():
    """Tests hash function"""
    session: str = to_hash(username + password + user_agent)

    assert isinstance(session, str)

    assert len(session) == 64

    assert is_sha256_hash(session)


@pytest.mark.asyncio
async def test_save_session():
    """Tests that session is actually saved"""
    session: str = to_hash(username + password + user_agent)

    await save_session(session, user_agent, -1)

    r = get_conn()

    assert r.get("session") is not None

    await asyncio.sleep(0.5)


@pytest.mark.asyncio
async def test_valid_session():
    """Tests that session is valid"""
    session: str = to_hash(username + password + user_agent)

    assert await valid_session(session, user_agent)


@pytest.mark.asyncio
async def test_invalid_session():
    """Tests invalid sessions"""

    # test hash
    session: str = to_hash(username + password + user_agent + "wrong string")
    assert await valid_session(session, user_agent) is False

    # test SALT
    session: str = to_hash(username + password + user_agent, salt="some random text")
    assert await valid_session(session, user_agent) is False

    # valid session, but wrong User-Agent
    session: str = to_hash(username + password + user_agent)
    assert await valid_session(session, "Not valid User-Agent") is False

    # invalid session, but same User-Agent
    session: str = to_hash(username + password + user_agent + "wrong string")
    assert await valid_session(session, user_agent) is False


@pytest.mark.asyncio
async def test_finish_session():
    """Tests that session is properly cleaned from redis"""

    # get value before finish
    r = get_conn()
    assert r.get("session") is not None

    await finish_session()

    # after finish
    assert r.get("session") is None


@pytest.mark.asyncio
async def test_temporary_session():
    session: str = to_hash(username + password + user_agent)

    # 1 second to expire
    await save_session(session, user_agent, 1)

    assert await valid_session(session, user_agent) is True

    await asyncio.sleep(1.5)

    assert await valid_session(session, user_agent) is False
