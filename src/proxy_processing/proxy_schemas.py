from datetime import datetime

from proxy_processing.proxy_models import Protocol
from schemas import SBase


class SProxy(SBase):
    """Pydantic model that represents proxy"""
    id: int
    ip: str
    port: str
    username: str | None
    password: str | None
    added_at: datetime
    last_check_at: datetime | None
    status: str | None
    socks5: bool | None
    socks4: bool | None
    https: bool | None
    http: bool | None

    def __repr__(self) -> str:
        return f"{self.ip}:{self.port}"


class SAdvancedSearch(SBase):
    """Pydantic model to validate advanced search query"""
    # protocols list need to count how many of them
    protocols: list[Protocol] = [p.value for p in list(Protocol)]

    socks5: bool = False
    socks4: bool = False
    http: bool = False
    https: bool = False

    alive: bool = False
    dead: bool = False
    not_checked: bool = False

    limit: int = -1  # -1 means infinite

    format_type: str = "url"  # default is url
    format_string: str | None = None


    def __repr__(self) -> str:
        return str(self.model_dump())
