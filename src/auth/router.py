from typing import Annotated
from fastapi import APIRouter, Depends, Header, Response, Cookie
import logging

from auth.auth_schemas import SLogin
from auth.dependencies import login_data_dependency
from auth.auth_utils import to_hash, save_session, valid_session, finish_session
from configs.config import USERNAME, PASSWORD, EXPIRES
from schemas import SResponseAPI

# Since this application is intended to be used by a single person or a small team, authentication is kept as simple
# as possible to allow for quick local deployment and no setup time.
# session is stored in redis in salt-hashed format
# todo: implement admin panel, registration and privileges control


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


@router.post("/login")
async def login(
        response: Response,
        login_data: SLogin = Depends(login_data_dependency)
) -> None:
    """
    Login endpoint for login form
    :param response: fastapi Response object:
        * 303 HTTP Redirect /login - in case of failure
        * 303 HTTP Redirect /index.html - success
    :param login_data: - multipart/form-data with username and password values
    :return: None
    """

    response.status_code = 303

    # we need user agent
    if login_data.user_agent is None:
        logger.info("Someone tried to log in without User-Agent")
        response.headers["Location"] = "/login"
        return

    # checks credentials
    if login_data.username != USERNAME or login_data.password != PASSWORD:
        logger.info(f"Failed login attempt: {login_data.username} - {login_data.password}")
        response.headers["Location"] = "/login"
        return

    # create value for session cookie
    session_value: str = to_hash(login_data.auth_string)

    # insert it to redis
    exp: int = EXPIRES * 60 * 60  # hours to seconds
    await save_session(session_value, login_data.user_agent, exp)

    # client now is logged in
    response.set_cookie("session", session_value, max_age=exp)
    response.headers["Location"] = "/"

    logger.info(f"Created new {session_value=} which expires in {EXPIRES} hours")


@router.get("/logout")
async def logout(
        response: Response,
        session: Annotated[str | None, Cookie()] = None,
        user_agent: Annotated[str | None, Header()] = None,
) -> Response:
    # in any case we redirect user to login page
    response.status_code = 307
    response.headers["Location"] = "/login"

    # if user is not logged or hasn't U-A
    if session is None or user_agent is None:
        return response

    # user has invalid credentials
    valid: bool = await valid_session(session, user_agent)
    if not valid:
        return response

    # now, we log out
    response.delete_cookie("session")
    await finish_session()

    logger.info(f"Logged out {session=}")

    return response


@router.get("/session")
async def get_api_session(
        session: Annotated[str | None, Cookie()] = None,
        user_agent: Annotated[str | None, Header()] = None,
):
    """
    Returns current session and user_agent
    Session and UA are need for direct api requests
    returns dict:
        session: str
        user_agent: str
    """
    valid: bool = await valid_session(session, user_agent)
    if not valid:
        return {"status": -1, "details": "Session is not valid"}

    return {"status": 0, "data": {
        "session": session,
        "user_agent": user_agent
    }}
