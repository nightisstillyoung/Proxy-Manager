from abc import ABC
from typing import Annotated
from annotated_types import MinLen, MaxLen
from pydantic import ConfigDict

from base_schemas import SBase
from datetime import datetime


class AbstractUsernameScheme(SBase, ABC):
    model_config = ConfigDict(strict=True)
    username: Annotated[str, MinLen(3), MaxLen(40)]


class AbstractRawPasswordScheme(SBase, ABC):
    """For inheritance where raw password is used"""
    model_config = ConfigDict(strict=True)
    password: Annotated[str, MinLen(8), MaxLen(64)]


# currently not used
class LoginScheme(AbstractUsernameScheme, AbstractRawPasswordScheme):
    """Login form uses raw password and username only"""

    def __repr__(self) -> str:
        return f"{self.username}:{self.password}"


class UsernameScheme(AbstractUsernameScheme):
    registered_at: datetime | None
    active: bool
    expires: datetime | None = None

    @property
    def temporary(self) -> bool:
        """Is user temporary or not"""
        return self.expires is not None

    def __repr__(self) -> str:
        return self.username


class RegisterUsernameScheme(AbstractUsernameScheme, AbstractRawPasswordScheme):
    expire_at: datetime | None = None
    privileges: list = []

    def active(self) -> bool:
        return self.expire_at > datetime.utcnow()

    def __repr__(self) -> str:
        return f"{self.username}:{self.password}"


class ChangePasswordScheme(SBase):
    password: str
    new_password: Annotated[str, MinLen(8), MaxLen(64)]

    def __repr__(self) -> str:
        return f"{self.old_password} -> {self.new_password}"
