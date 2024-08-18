import logging
from hashlib import sha256
from redis.asyncio import Redis as AsyncRedis

from redis_manager.conn_manager import get_async_conn
from configs.config import SALT

logger = logging.getLogger(__name__)


async def save_session(
        session: str,
        user_agent: str,
        exp: int | None
) -> None:
    """
    Saves session.
    WARNING: login data must be validated before calling this function
    :param session: Cookie/API session to save in Redis (key: session)
    :param user_agent: user's User-Agent
    :param exp: seconds, -1 or None for infinite
    :return: None
    """

    if exp <= 0:
        exp = None

    r: AsyncRedis = get_async_conn()

    # create hashed value to store in redis
    # use User Agent in case someone has access to redis server
    # to_hash -> sha256(session + User Agent)
    redis_session_value: str = to_hash(session + user_agent)

    logger.info("Created new session")
    logger.debug(f"{session=}, {user_agent=}, {redis_session_value=}, {exp=}")

    # and set it in redis
    await r.set("session", redis_session_value, exp)


async def valid_session(
        session: str,
        user_agent: str
) -> bool:
    """
    Validates session
    :param session: Cookie/API session to save in Redis (key: session)
    :param user_agent: user's User-Agent
    :return: True - OK, False - not logged
    """
    r: AsyncRedis = get_async_conn()

    logger.debug(f"Validating: {session=}, {user_agent=}")

    # we store session in redis hashed
    # # to_hash -> sha256(session + User Agent)
    if hashed_session := await r.get("session"):
        return hashed_session == to_hash(session + user_agent)
    else:
        return False


async def finish_session() -> None:
    """
    Deletes session key from redis
    """
    r: AsyncRedis = get_async_conn()

    logger.info("Session closed.")

    await r.delete("session")


def to_hash(string: str, salt: str = SALT, rounds: int = 256) -> str:
    """
    Creates hashed string from credentials, using salt
    :param string: some string to hash
    :param salt: secure salt to prevent using of rainbow tables
    :param rounds: how many times run sha256(hash + SALT)
    :return: hashed string
    """

    # basic string
    hash_data: bytes = f"{string}:{salt}".encode("utf-8")

    logger.debug(f"{hash_data=}")

    # hash it 'rounds' times with SALT
    for _ in range(0, rounds):
        hash_data = sha256(
            hash_data + SALT.encode("utf-8")
        ).hexdigest().encode("utf-8")

    logger.debug(f"{hash_data=}")

    # and return it
    return hash_data.decode("utf-8")
