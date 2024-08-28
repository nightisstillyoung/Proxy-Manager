from typing import Any
from datetime import datetime, timedelta
import jwt
import bcrypt

from configs.config import jwt_config, private_key, public_key


def encode_jwt(
        payload: dict,
        algorithm: str = jwt_config["algorithm"],
        expire_hours: int | None = jwt_config["expire_hours"],
        expire_timedelta: timedelta | None = None,
) -> str:
    to_encode: dict = payload.copy()
    now: datetime = datetime.utcnow()

    if expire_timedelta is not None:
        expires: datetime = now + expire_timedelta
    else:
        expires: datetime = now + timedelta(hours=expire_hours)

    to_encode.update(
        iat=now.timestamp(),
        exp=expires.timestamp()
    )

    return jwt.encode(to_encode, private_key, algorithm)


def decode_jwt(
        payload: str | bytes,
        algorithm: str = jwt_config["algorithm"]
) -> Any:
    return jwt.decode(payload, public_key, algorithm)


def hash_pwd(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def check_pwd(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
