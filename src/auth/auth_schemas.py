from fastapi import Header, Cookie

from schemas import SBase


class SLogin(SBase):
    username: str
    password: str
    user_agent: str | None = Header(default=None)
    session: str | None = Cookie(default=None)

    def __repr__(self) -> str:
        return f"{self.username}:{self.password} + {self.user_agent}:{self.session}"

    @property
    def auth_string(self) -> str:
        return f"{self.username}:{self.password}:{self.user_agent}"
