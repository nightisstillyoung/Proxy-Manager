from sqlalchemy import select, and_, delete, or_, func, Select, Result
from datetime import datetime
from functools import singledispatch

from database import async_session_maker
from proxy_processing.models import ProxyModel
from proxy_processing.schemas import SAdvancedSearch
from base_utils import sync_compatible


@sync_compatible
async def update_with_check_timestamp(proxy_model: ProxyModel) -> None:
    """Updates proxy with timestamp"""
    proxy_model.last_check_at = datetime.utcnow()
    await update(proxy_model)


@singledispatch
@sync_compatible
async def update(proxy_model: ProxyModel) -> None:
    """Updates proxy"""
    async with async_session_maker() as session:
        await session.merge(proxy_model)
        await session.commit()


async def get_all() -> list[ProxyModel] | None:
    """Returns all proxies stored in database"""
    async with async_session_maker() as session:
        query = select(ProxyModel)
        result = await session.execute(query)
        return result.scalars().all()


async def purge_all() -> None:
    """Purges all proxies from database"""
    async with async_session_maker() as session:
        stmt = delete(ProxyModel)
        await session.execute(stmt)
        await session.commit()


async def purge_dead() -> None:
    """Purges only dead proxies"""
    async with async_session_maker() as session:
        stmt = delete(ProxyModel).where(or_(ProxyModel.status == "dead", ProxyModel.status == None))
        await session.execute(stmt)
        await session.commit()


async def get_sorted_by(sorted_by, limit: int = -1) -> list[ProxyModel]:
    """
    Returns sorted proxies with limit.
    :param sorted_by: Model.value
    :param limit: limit of proxies to return
    :return: list of ORM objects
    """
    async with async_session_maker() as session:
        query = select(ProxyModel).order_by(sorted_by)

        if limit > 0:
            query = query.limit(limit)

        result = await session.execute(query)
        return result.scalars().all()


@sync_compatible
async def get_alive(time_limit: int = 0) -> list[ProxyModel]:
    """
    Returns alive proxies where last_check_at > time_limit
    :param time_limit: - unix timestamp (default: 0)
    :return:
    """
    async with async_session_maker() as session:
        query = select(ProxyModel).where(ProxyModel.status == "alive")

        if time_limit:
            query = query.where(ProxyModel.last_check_at > datetime.fromtimestamp(time_limit))

        result = await session.execute(query)
        return result.scalars().all()


@sync_compatible
async def get_model_by_dict(proxy_dict: dict) -> ProxyModel | None:
    """Search proxy in database using information from dict"""
    async with async_session_maker() as session:
        query = select(ProxyModel).where(
            and_(
                ProxyModel.ip == proxy_dict["ip"],
                ProxyModel.port == proxy_dict["port"],
                ProxyModel.username == proxy_dict.get("username", ""),
                ProxyModel.password == proxy_dict.get("password", "")
            )
        )
        result = await session.execute(query)
        proxy_model = result.scalars().first()

        return proxy_model


@sync_compatible
async def get_model_by_id(id_: int) -> ProxyModel | None:
    """Returns model by id"""
    async with async_session_maker() as session:
        proxy_model = await session.get(ProxyModel, id_)
        return proxy_model


async def count_rows() -> int:
    """Counts rows in ProxyModel table"""
    async with async_session_maker() as session:
        query = select(func.count(ProxyModel.id))
        result = await session.execute(query)
        return result.scalar()


async def get_min_max_latency() -> dict[str, float | int]:
    """
    Returns dict with information about maximal and minial latency of proxies
    {
    "min": float,
    "max": float
    }
    """
    async with async_session_maker() as session:
        query: Select = select(
            func.min(ProxyModel.latency).label("latency_min"),
            func.max(ProxyModel.latency).label("latency_max")
        )
        result: Result = await session.execute(query)

        result: dict[str, float | int] = dict(result.mappings().one().items())

        return result



async def insert_many(proxies: list[ProxyModel]) -> list[ProxyModel]:
    """Inserts list of proxies in one transaction for better performance."""
    if not proxies:
        return []
    async with async_session_maker() as session:
        session.add_all(proxies)
        await session.commit()
        return proxies


async def get_filtered_by(condition) -> list[ProxyModel]:
    """
    Filters proxy by condition
    Example:
        `proxies: list[ProxyModel] = await get_filtered_by(ProxyModel.status == "alive")`
    """
    async with async_session_maker() as session:
        query = select(ProxyModel).filter(condition)
        result = await session.execute(query)
        return result.scalars().all()


async def search_with_multiple_params(search_query: SAdvancedSearch) -> list[ProxyModel]:
    async with async_session_maker() as session:
        query: Select = select(ProxyModel)

        and_conditions: list = []

        # protocols
        if len(search_query.protocols):
            or_conditions: list = []

            if search_query.socks5:
                or_conditions.append(ProxyModel.socks5 == True)
            if search_query.socks4:
                or_conditions.append(ProxyModel.socks4 == True)
            if search_query.http:
                or_conditions.append(ProxyModel.http == True)
            if search_query.https:
                or_conditions.append(ProxyModel.https == True)

            if len(or_conditions):
                and_conditions.append(or_(*or_conditions))

        # status
        # if all statuses selected, we do not apply this filter
        if not (search_query.not_checked and search_query.alive and search_query.dead):
            or_conditions: list = []
            if search_query.alive:
                or_conditions.append(ProxyModel.status == "alive")
            if search_query.dead:
                or_conditions.append(ProxyModel.status == "dead")
            if search_query.not_checked:
                or_conditions.append(ProxyModel.status == None)

            if len(or_conditions):
                and_conditions.append(or_(*or_conditions))

        # limit
        if search_query.limit > 0:
            query: Select = query.limit(search_query.limit)

        # latency
        if search_query.latency < 999:
            and_conditions.append(ProxyModel.latency <= search_query.latency)

        # unite them all
        if len(and_conditions):
            query: Select = query.where(and_(*and_conditions))

        result = await session.execute(query)
        return result.scalars().all()


async def update_many(proxies: list[ProxyModel]) -> list[ProxyModel]:
    """Updates many proxies in one time for better performance."""
    if not proxies:
        return []
    async with async_session_maker() as session:
        for proxy in proxies:
            await session.merge(proxy)
        await session.commit()
        return proxies


async def get_by_ip(ip: str) -> list[ProxyModel]:
    """Returns proxies sorted by ip"""
    async with async_session_maker() as session:
        query = select(ProxyModel).where(ProxyModel.ip == ip)
        result = await session.execute(query)

        return result.scalars().all()
