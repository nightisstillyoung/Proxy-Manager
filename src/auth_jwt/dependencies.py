from datetime import datetime
from typing import Annotated
from fastapi import Header, Form, Cookie
from jwt import InvalidAlgorithmError, DecodeError, InvalidSignatureError

from auth_jwt.auth_models import UserModel
from auth_jwt.exceptions import (
    AuthException,
    WrongCredentials,
    TokenAuthError,
    UserInactive,
    ChangePasswordError,
    TokenExpired,
    InvalidToken
)
from auth_jwt.utils import decode_jwt, encode_jwt, check_pwd
from auth_jwt.repository import AuthRepo
from configs.config import jwt_config


async def validate_auth_user(
        username: Annotated[str, Form()],
        password: Annotated[str, Form()]
) -> str:
    """Validate login form"""

    # trying to get user from database with passed credentials
    if not (user := await AuthRepo.get_user(username, for_login=True)):
        raise WrongCredentials()

    # check if password is valid
    if not check_pwd(password, user.password):
        raise WrongCredentials()

    # and return jwt token
    return encode_jwt(payload={
        "sub": user.id,
        "username": username,
    })


async def check_auth(auth: str = Cookie(default=None), x_api_token: str = Header(default=None)) -> UserModel:
    # base validation
    if x_api_token is not None:  # jwt toke from cookie and those that user use in his script is the same
        auth = x_api_token

    if auth is None or auth.count(".") != 2:
        raise AuthException()

    try:
        # decode token and get payload
        payload: dict = decode_jwt(auth)
    except (InvalidAlgorithmError, DecodeError, InvalidSignatureError):
        raise InvalidToken()

    # get id and username from token
    id_: int | None = payload.get("sub")
    username: str | None = payload.get("username")

    # user can set infinite token
    if jwt_config["expire_hours"] > 0 and (
            not payload.get("exp")
            or
            payload["exp"] < datetime.utcnow().timestamp()
    ):
        raise TokenExpired()

    # no username?!
    if not username:
        raise AuthException()

    # check auth
    user: UserModel | None = await AuthRepo.get_user(id_)

    # another username, but same password
    if user is None or user.username != username:
        raise TokenAuthError()
    elif not user.active:
        raise UserInactive()

    return user
