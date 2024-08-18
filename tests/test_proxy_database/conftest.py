import asyncio

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from src.configs.config import DB_PASS, DB_PORT, DB_HOST, DB_USER
from src.proxy_processing import repository as proxy_db

# fixes error when metadata with name proxy already exists
ProxyModel = proxy_db.ProxyModel

# change environ db name
TEST_DB_NAME = "test_database"


async def create_drop_database():
    # create async engine without db
    engine = create_async_engine(
        f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}",
        isolation_level="AUTOCOMMIT"  # autocommit
    )

    async with engine.connect() as conn:
        try:
            # if test database exists from previous run
            await conn.execute(text(f"DROP DATABASE {TEST_DB_NAME}"))
        except:
            pass

        try:
            # standard db postgres
            await conn.execution_options(database="postgres")

            # create db
            await conn.execute(text(f"CREATE DATABASE {TEST_DB_NAME}"))

            yield TEST_DB_NAME  # just db name

            # wait a bit after close transactions
            await asyncio.sleep(0.1)

            # drop database after all tests
            await conn.execute(text(f"DROP DATABASE {TEST_DB_NAME}"))
        except Exception as e:
            raise e
        finally:
            # close connection anyway
            await conn.close()

    # and close engine
    await engine.dispose()


@pytest.fixture(scope="session", autouse=True)
async def engine():
    """Maintains and returns connection to temporary database"""
    async for db in create_drop_database():
        async_engine = create_async_engine(
            f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{db}"
        )
        yield async_engine

        # close second engine for successful database drop
        await async_engine.dispose()


@pytest.fixture(scope="session", autouse=True)
async def table(engine):
    async with engine.begin() as conn:
        await conn.run_sync(ProxyModel.metadata.create_all)

    yield

    async with engine.begin() as conn:
        await conn.run_sync(ProxyModel.metadata.drop_all)


@pytest.fixture(scope="function", autouse=True)
def session_mock(monkeypatch, engine):
    """Patches session (see src/database.py) so now it connects to test database"""
    test_maker = async_sessionmaker(engine, expire_on_commit=False)
    monkeypatch.setattr(proxy_db, "async_session_maker", test_maker)
