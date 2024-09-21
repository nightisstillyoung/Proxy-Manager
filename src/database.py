from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession, AsyncEngine
import logging

from base_utils import Singleton
from configs.config import DB_PASS, DB_NAME, DB_PORT, DB_HOST, DB_USER

# setup logger
logger = logging.getLogger(__name__)

# create session maker
async_engine: AsyncEngine = create_async_engine(
    f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)
async_session_maker: async_sessionmaker = async_sessionmaker(async_engine, expire_on_commit=False)


class DatabaseManager(metaclass=Singleton):
    """Manages database connection for better performance"""

    def __init__(self):
        self._session: AsyncSession | None = None
        self._session_factory: async_sessionmaker = async_session_maker

    async def __aenter__(self) -> AsyncSession:
        logger.info("Enter in context")
        self._session = self._session_factory()
        return self._session

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if isinstance(exc_type, Exception):
            await self.rollback()

        await self._session.close()
        self._session = None
        logger.info("Exit from context")

    async def commit(self) -> None:
        await self._session.commit()
        logger.info("Commit")

    async def rollback(self) -> None:
        await self._session.rollback()
        logger.info("Rollback")


db_manager: DatabaseManager = DatabaseManager()
