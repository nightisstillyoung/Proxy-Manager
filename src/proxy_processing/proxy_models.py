from sqlalchemy import String, Index
from sqlalchemy.orm import Mapped, mapped_column
from typing import Annotated
from datetime import datetime
from enum import Enum
from models import BaseModel


class Protocol(Enum):
    """Enumeration of all available protocols"""
    socks4 = "socks4"
    socks5 = "socks5"
    http = "http"
    https = "https"


class Status(Enum):
    """Enumerate of all available proxy statuses"""
    alive = "alive"
    dead = "dead"


# ====Reusable table types====
int_primary_key = Annotated[int, mapped_column(primary_key=True)]
proxy_credential = Annotated[str, mapped_column(String(length=256), default="")]


class ProxyModel(BaseModel):
    __tablename__ = "proxy"

    __table_args__ = (
        Index('idx_proxy_ip_port_username_password', 'ip', 'port', 'username', 'password', unique=True),
    )

    id: Mapped[int_primary_key]
    ip: Mapped[str] = mapped_column(String(length=15), nullable=False, index=True)
    port: Mapped[str] = mapped_column(String(length=5))  # 0-65536

    username: Mapped[proxy_credential]  # auth credentials
    password: Mapped[proxy_credential]

    added_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow)
    last_check_at: Mapped[datetime] = mapped_column(nullable=True)

    status: Mapped[Status] = mapped_column(nullable=True)

    # boolean implementation is better than protocols[list[str]]
    socks4: Mapped[bool] = mapped_column(nullable=True)
    socks5: Mapped[bool] = mapped_column(nullable=True)
    http: Mapped[bool] = mapped_column(nullable=True)
    https: Mapped[bool] = mapped_column(nullable=True)

    # todo: add ForeignKey for User model (when proper auth will be done)

    @property
    def credentials(self) -> str:
        """Returns username:password@ string"""
        return f"{self.username}:{self.password}@" if self.username != "" else ""

    @property
    def ip_port(self) -> str:
        """Returns IP:port string"""
        return f"{self.ip}:{self.port}"

    @property
    def credentials_ip_port(self) -> str:
        """Returns user:password@IP:port string"""
        return f"{self.credentials}{self.ip}:{self.port}"

    @property
    def proto(self) -> str:
        """Returns formated string with first working protocol"""
        if self.socks5:
            return "socks5://"
        elif self.socks4:
            return "socks4://"
        elif self.https:
            return "https://"
        elif self.http:
            return "http://"
        else:
            return ""

    def set_protocols_list(self, new_protocols: list[str]) -> None:
        """
        List of working protocols for this proxy. Rewrites existing info.
        :param new_protocols: list of working protocols
        :return: None
        """
        self.socks5 = bool(new_protocols.count("socks5"))
        self.socks4 = bool(new_protocols.count("socks4"))
        self.https = bool(new_protocols.count('https'))
        self.http = bool(new_protocols.count("http"))

    @property
    def protocols_list(self) -> list[str]:
        """Generates list of working protocols"""
        res: list[str] = []

        if self.socks5:
            res.append("socks5")

        if self.socks4:
            res.append("socks4")

        if self.https:
            res.append("https")

        if self.http:
            res.append("http")

        return res


    def get_with_all_protocols(self) -> list[str] | None:
        """
        Returns list with all possible variations of this proxy_processing
        depends on protocols
        """

        return [f"{p}://{self.credentials}{self.ip_port}" for p in self.protocols_list]

    def get_with_proto(self, protocol: str) -> str:
        """
        Returns proxy with forced protocol
        :param protocol: protocol to set with proxy
        :return:
        """
        return f"{protocol}://{self.credentials}{self.ip_port}"

    def __repr__(self) -> str:
        """Returns full proxy_processing url"""
        return f"{self.proto}{self.credentials}{self.ip_port}"

