from typing import Annotated
from fastapi import Header, Cookie, Form

from auth.auth_schemas import SLogin
from auth.exceptions import AuthError
from auth.auth_utils import valid_session
from configs.config import AUTH


def login_data_dependency(
        username: Annotated[str, Form()],
        password: Annotated[str, Form()],
        user_agent: str | None = Header(default=None),
        session: str | None = Cookie(default=None)
) -> SLogin:
    """Dependency for login params"""
    return SLogin(username=username, password=password, user_agent=user_agent, session=session)


async def auth_data_dependency(
        user_agent: str | None = Header(default=None),
        session: str | None = Cookie(default=None),
        x_user_session: str | None = Header(default=None)  # for secured requests from scripts to our API
) -> str:
    """
    Checks if user is logged in.
    :param user_agent: User-Agent header
    :param session: session Cookie
    :param x_user_session: or, if user made request via API in his script, he can send just X-User-Session header, which is equal to session Cookie
    :return: returns vali session string or raises AuthError("Not logged in")
    """
    if not AUTH:
        return "off"

    if user_agent is None or (session is None and x_user_session is None):
        raise AuthError("Not logged in")

    if not await valid_session(
            session if session is not None else x_user_session,
            user_agent
    ):
        raise AuthError("Not logged in")

    return session or x_user_session
