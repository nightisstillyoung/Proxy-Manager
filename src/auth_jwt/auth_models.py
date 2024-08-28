from sqlalchemy import String, JSON, func
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from logging import getLogger, Logger

from models import BaseModel, int_primary_key

logger: Logger = getLogger(__name__)




class UserModel(BaseModel):
    __tablename__ = "user"

    id: Mapped[int_primary_key]
    username: Mapped[str] = mapped_column(String(length=40), nullable=False)
    password: Mapped[str] = mapped_column(String(length=60), comment="bcrypt hashed password with salt", nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow)
    expire_at: Mapped[datetime] = mapped_column(nullable=True, comment="Time when user's account expires")
    last_login_at: Mapped[datetime] = mapped_column(nullable=True)
    active: Mapped[bool] = mapped_column(default=True)


    privileges: Mapped[JSON] = mapped_column(nullable=False, default='[]', comment="Future option", type_=JSON)


    def __repr__(self) -> str:
        return f"{self.id}:{self.username}"


