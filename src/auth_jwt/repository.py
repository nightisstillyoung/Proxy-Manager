from typing import overload, Annotated
from annotated_types import MinLen, MaxLen
from sqlalchemy import Select, select
from datetime import datetime

from auth_jwt.schemas import RegisterUsernameScheme
from auth_jwt.exceptions import TokenAuthError
from database import async_session_maker
from auth_jwt.models import UserModel
from auth_jwt.utils import hash_pwd


class AuthRepo:
    """Repository to interact with the database"""

    def __init__(self):
        raise Exception("This is a static class")


    @classmethod
    @overload
    async def get_user(cls, username_or_id: str, for_login: bool = False) -> UserModel | None:
        ...

    @classmethod
    @overload
    async def get_user(cls, username_or_id: int, for_login: bool = False) -> UserModel | None:
        ...

    @classmethod
    async def get_user(cls, username_or_id: str, for_login: bool = False) -> UserModel | None:
        """
        Returns user by id or username
        """
        username: str | None = None
        id_: int | None = None

        if isinstance(username_or_id, str):
            username: str = username_or_id

        elif isinstance(username_or_id, int):
            id_: int = username_or_id
        else:
            raise ValueError(f"username: str or id:int only, passed {type(username_or_id)}")

        async with async_session_maker() as session:

            if username:
                query: Select = select(UserModel).where(UserModel.username == username)
                result = await session.execute(query)
                user: UserModel | None = result.scalar()
            else:
                user: UserModel | None = await session.get(UserModel, id_)

            if user and for_login:
                user.last_login_at = datetime.now()
                await session.merge(user)
                await session.commit()

            return user

    @classmethod
    async def is_user_exists(cls, username: str) -> bool:
        return await cls.get_user(username) is not None

    @classmethod
    async def create_user(cls, user_scheme: RegisterUsernameScheme) -> UserModel:
        async with async_session_maker() as session:
            user_scheme.password = hash_pwd(user_scheme.password)
            user: UserModel = UserModel(**user_scheme.model_dump())
            session.add(user)
            await session.commit()

        return user

    @classmethod
    async def set_new_password(cls, new_password: Annotated[str, MinLen(8), MaxLen(64)], id_: int):
        async with async_session_maker() as session:
            user: UserModel | None = await session.get(UserModel, id_)
            if user is None:
                raise TokenAuthError()

            user.password = hash_pwd(new_password)

            await session.commit()

