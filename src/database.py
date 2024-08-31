from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
import logging

from base_utils import Singleton
from configs.config import DB_PASS, DB_NAME, DB_PORT, DB_HOST, DB_USER

# setup logger
logger = logging.getLogger(__name__)

# create session maker
async_engine = create_async_engine(
    f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)
async_session_maker = async_sessionmaker(async_engine, expire_on_commit=False)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Returns async session"""
    async with async_session_maker() as session:
        yield session


class Database(metaclass=Singleton):
    """Manages database connection for better performance"""
    def __init__(self):
        self._session: AsyncSession | None = None

    def __call__(self, *args, **kwargs):
        if self._session is None:
            self._session = async_session_maker()
            logger.info("DB session created")

        return self._session

    @property
    def session(self):
        if self._session is None:
            self._session = async_session_maker()

        return self._session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def close(self):
        if self._session is not None:
            await self._session.close()
            logger.info("DB session closed")


