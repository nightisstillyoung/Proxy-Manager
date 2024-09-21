import asyncio
from typing import Annotated, Any
import logging
import brotli
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Response, Depends
from redis.asyncio import Redis as AsyncRedis
from sqlalchemy import null
from datetime import datetime

from auth_jwt.dependencies import check_auth
from proxy_processing.exceptions import ProxyProcessingError, NoFormatStringError, UnknownFormatType, \
    CheckIsRunningError, NoProxiesError
from proxy_processing.models import ProxyModel
from proxy_processing.schemas import SProxy, SAdvancedSearch
from proxy_processing import repository as proxy_repo
from proxy_processing.utils import predict_check_time, parse_proxy_dict_from_string
from proxy_processing.regex import ip_expr
from redis_manager.conn_manager import get_async_conn
from tasks.tasks import process_proxy_worker
from tasks.manager import async_celery_manager, celery_manager
from base_schemas import SResponseAPI
from websocket import ws_manager
from base_utils import model_to_pydantic


router = APIRouter(
    prefix="/proxies",
    tags=["proxies"],
    dependencies=[Depends(check_auth)]
)

logger = logging.getLogger(__name__)


@router.post("/add", response_model=SResponseAPI, response_model_exclude_unset=True, tags=["checker"])
async def add_proxies(
        proxies: list[str]
):
    """
    Adds new proxies to database and celery queue for further check
    Returns list of incorrect proxies (if exist):
    "incorrect_proxies": list[str]
    """

    # check that list is not empty
    if not len(proxies):
        raise NoProxiesError()

    # remove duplicated strings
    proxies = list(set(proxies))


    # we use two different lists for db optimization
    # store model with provided protocol to return then proxy with protocol to user
    to_update: list[tuple[ProxyModel, str] | None] = []

    # key - unique index to prevent duplicate inserts
    proxies_to_add_unique: dict[str, tuple[ProxyModel, str]] = {}


    bad_proxies: list[str] = []
    valid_proxies: list[tuple[ProxyModel, str] | None] = []

    for i in proxies:
        # validation
        if isinstance(proxy := parse_proxy_dict_from_string(i), str):
            # add proxy to redis BAD channel
            logger.info(f"Incorrect format in: {proxy}")
            bad_proxies.append(proxy)
            continue

        requested_protocol: str | None = proxy.pop("protocol", None)

        # if proxy exists
        proxy_model: ProxyModel | None = await proxy_repo.get_model_by_dict(proxy)

        if proxy_model is not None:
            # proxy exists
            if requested_protocol:
                # provided proxy string by client contains protocol

                if getattr(proxy_model, requested_protocol):
                    # client passed proxy with protocol which is already in database
                    # or last check returned False on this protocol
                    # that means client asked to do re-check
                    logger.info(f"Not adding to db exact the same proxy: {proxy}")
                else:
                    # renew proxy with new protocols
                    logger.debug(f"Added requested protocol {requested_protocol} for {proxy_model.credentials_ip_port}")
                    proxy_model.protocols_list = list({*proxy_model.protocols_list, requested_protocol})

                    to_update.append((proxy_model, requested_protocol))
            else:
                # proxy already exists in database and client didn't pass new protocols
                logger.info(f"Bypassed exact the same proxy without protocol: {proxy}")
                # so we just bypass it too

            assert proxy_model is not None
            valid_proxies.append((proxy_model, requested_protocol))
        else:
            # if there is no proxy in database we add it
            logger.debug(f"Added new proxy {proxy}")
            unique_index: str = proxy.pop("unique_index")
            if proxies_to_add_unique.get(unique_index) is not None:
                logger.warning("Duplicate proxy %s", i)
                continue
            proxy_model: ProxyModel = ProxyModel(**proxy)
            assert proxy_model is not None
            proxies_to_add_unique[unique_index] = (
                    proxy_model,
                    requested_protocol
                )
            valid_proxies.append((proxy_model, requested_protocol))

    # update proxies
    await proxy_repo.update_many([i[0] for i in to_update])

    # convert dict to list
    to_add: list[tuple[ProxyModel, str | None]] = []
    for key, value in list(proxies_to_add_unique.items()):
        to_add.append(
            value
        )

    # and insert them in database
    await proxy_repo.insert_many([i[0] for i in to_add])


    logger.info(f"Inserted {len(to_add)} new proxies, {len(to_update)} updated")

    # reset initial len
    initial_len: int = await async_celery_manager.update_initial_len(len(proxies))

    # add proxies to celery
    for p in valid_proxies:
        process_proxy_worker.delay(p[0].id, p[1])

    logger.info(f"Set {initial_len=}")

    return {"status": 0, "data": {"incorrect_proxies": bad_proxies}}


@router.post("/continue_check", response_model=SResponseAPI, response_model_exclude_unset=True, tags=["checker"])
async def continue_check():
    """
    Starts proxy check for proxies where status is null
    Returns progress info:
    "progress": get_progress()
    """

    # get proxies list
    proxies: list[ProxyModel] = await proxy_repo.get_filtered_by(ProxyModel.status == null())

    if len(proxies) == 0:
        return {"status": 0, "data": None}

    # set initial queue len in redis
    redis_conn: AsyncRedis = get_async_conn()
    await redis_conn.set("initial_len", len(proxies), predict_check_time(len(proxies)))

    logger.info(f"Set initial_len={len(proxies)}")

    # add proxies to celery
    for p in proxies:
        process_proxy_worker.delay(p.id, None)

    # get actual progress
    progress: dict[str, int | float] = await async_celery_manager.get_progress()

    return {"status": 0, "data": {"progress": progress}}


@router.post("/convert/to_obj", response_model=SResponseAPI, response_model_exclude_unset=True, tags=["convert"])
def convert(proxies: list[str]):
    """
    Converts list of proxies (strings) to list of parsed dicts and list of invalid proxies
        "valid": list[str],
        "invalid": list[str]
    """
    valid: list[dict] = []
    invalid: list[str] = []

    for i in proxies:
        # validation
        if isinstance(proxy := parse_proxy_dict_from_string(i), str):
            # adds proxy to redis BAD channel
            invalid.append(proxy)
        else:
            valid.append(proxy)

    return {
        "status": 0,
        "data": {
            "valid": valid,
            "invalid": invalid
        }
    }


@router.post("/rerun", response_model=SResponseAPI, response_model_exclude_unset=True, tags=["checker"])
async def re_run_check(limit: int = -1):
    """
    Restart check for all proxies in database.
    limit: int - cut database output, ordered by status. alive proxies superior to dead ones. -1 = infinite
    WARNING: too many proxies can get your memory out
    returns progress
    "progress": get_progress()
    """

    # get all proxies from database sorted by status (alive > dead)
    proxies: list[ProxyModel] = await proxy_repo.get_sorted_by(ProxyModel.status, limit=limit)

    if len(proxies) == 0:
        return {"status": 0, "data": None}

    # set initial queue len in redis
    await async_celery_manager.update_initial_len(len(proxies))

    # get new len for logs
    redis_conn: AsyncRedis = get_async_conn()
    initial_len: int = await redis_conn.get("initial_len")
    logger.info(f"initial_len={initial_len}")

    # add proxies to celery
    for p in proxies:
        process_proxy_worker.delay(p.id, None)

    progress: dict[str, int | float] = await async_celery_manager.get_progress()

    return {"status": 0, "data": {"progress": progress}}


@router.get("/{mode}/download", tags=["get"])
async def download(mode: str) -> Response:
    """
    Downloads proxies
    :param mode: 'alive' only or 'all'
    :return: Response with .txt file generated
    """

    # get proxies from database
    if mode == "alive":
        proxies: list[ProxyModel] = await proxy_repo.get_alive()
        # convert them to one string with newline separator
        # including protocol
        content: str = '\n'.join(str(p) for p in proxies)
    else:
        proxies: list[ProxyModel] = await proxy_repo.get_all()
        # dead proxies do not have any protocol, so we return only credentials + ip:port
        content: str = '\n'.join(p.credentials_ip_port for p in proxies)

    # create headers
    headers: dict[str, str] = {"Content-Disposition": f"attachment; filename={datetime.utcnow()}.txt"}

    # compress it using brotli because brotli is better for text files
    content: bytes = brotli.compress(content.encode())
    headers["Content-Encoding"] = "br"

    return Response(content, media_type="text/plain", headers=headers)


@router.post("/stop", response_model=SResponseAPI, response_model_exclude_unset=True, tags=["checker"])
def stop():
    """Clears celery queue, but does not cancel active tasks"""
    celery_manager.purge_queues()
    return {"status": 0}


@router.get("/search", response_model=SResponseAPI, response_model_exclude_unset=True, tags=["get", "search"])
async def search_ip(
        ip: Annotated[
            str,
            Query(pattern=ip_expr)
        ]
):
    """
    Search proxies by ip
    Returns list of proxy objects: list[ProxyModel] -> list[dict[str, Any]]
    """
    proxies: list[ProxyModel] = await proxy_repo.get_by_ip(ip)
    return {"status": 0, "data": [model_to_pydantic(m, SProxy) for m in proxies]}


@router.post("/search/advanced",
             response_model=SResponseAPI,
             response_model_exclude_unset=True,
             tags=["get", "search", "advanced"],)
async def advanced_search(search_query: SAdvancedSearch):
    """
    Makes deep search in database and returns formatted proxies
    Returns list of formatted strings: list[ProxyModel] -> list[str]
    """

    # get proxy models by prepared query
    proxy_models: list[ProxyModel] = await proxy_repo.search_with_multiple_params(search_query)
    proxies: list[str] = []

    # format proxies model -> str
    if search_query.format_type == "normal":
        proxies = [p.credentials_ip_port for p in proxy_models]
    elif search_query.format_type == "url":
        proxies = [str(p) for p in proxy_models]
    elif search_query.format_type == "custom":
        if search_query.format_string is None:
            raise NoFormatStringError()
        # user wants custom formatting
        for p in proxy_models:
            _ = search_query.format_string\
                .replace("%protocol%", p.proto)\
                .replace("%credentials%", p.credentials)\
                .replace("%username%", p.username)\
                .replace("%password%", p.password)\
                .replace("%ip%", p.ip)\
                .replace("%port%", p.port)\
                .replace("%id%", str(p.id))\
                .replace("%status%", p.status.value)\
                .replace("%added_at%", str(p.added_at))\
                .replace("%last_check_at%", str(p.last_check_at))
            proxies.append(_)

    # unknown formatting option
    else:
        raise UnknownFormatType()

    return {"status": 0, "data": proxies}


@router.get("/all", response_model=SResponseAPI, response_model_exclude_unset=True)
async def get_all_proxies():
    """
    Returns all proxies stored in database
    Returns list of proxy objects: list[ProxyModel] -> list[dict[str, Any]]
    """
    proxies: list[ProxyModel] = await proxy_repo.get_all()
    return {"status": 0, "data": [model_to_pydantic(m, SProxy) for m in proxies]}


@router.get("/alive", response_model=SResponseAPI, response_model_exclude_unset=True)
async def get_alive_proxies(time_limit: int = 0):
    """
    Returns all good (alive) proxies
    Returns list of proxy objects: list[ProxyModel] -> list[dict[str, Any]]
    """
    proxies = await proxy_repo.get_alive(time_limit)
    return {"status": 0, "data": [model_to_pydantic(m, SProxy) for m in proxies]}


@router.get("/progress", response_model=SResponseAPI, response_model_exclude_unset=True)
async def get_progress_data():
    """Returns len of current queue and initial len"""
    # inspects redis list and celery active tasks
    # returns dict with information for progressbar (see frontend/js/progressbar.js)
    progress: dict[str, int | float] = await async_celery_manager.get_progress()
    return {
        "status": 0,
        "data": {
            "progress": progress
        }
    }


@router.get("/purge/all", response_model=SResponseAPI, response_model_exclude_unset=True, tags=["database"])
async def purge_all():
    """Purges all proxies from database"""
    progress: dict[str, Any] = await async_celery_manager.get_progress()

    # to prevent bugs we do not purge anything while check is going
    if progress["current_len"] > 0:
        raise CheckIsRunningError()

    await proxy_repo.purge_all()
    return {"status": 0, "data": []}


@router.get("/purge/dead", response_model=SResponseAPI, response_model_exclude_unset=True, tags=["database"])
async def purge_dead():
    """Purges dead proxies from database"""
    progress: dict[str, Any] = await async_celery_manager.get_progress()

    # to prevent bugs we do not purge anything while check is going
    if progress["current_len"] > 0:
        raise CheckIsRunningError()

    await proxy_repo.purge_dead()
    return {"status": 0, "data": []}


@router.websocket("/ws/good")
async def websocket_endpoint_good(websocket: WebSocket):
    """Websocket to get good proxies asap as they have been checked"""
    await ws_manager.connect(websocket)

    logger.info(f"Connected websocket {hash(websocket)}")

    # fresh checked proxies has been stored in redis
    # after checker finishes its work, script sets 2 minutes expire on good_proxies list (redis)
    redis_conn: AsyncRedis = get_async_conn()

    try:
        while True:
            if await redis_conn.llen("good_proxies"):
                data: str | None = await redis_conn.lpop("good_proxies")
                if data is not None:
                    await ws_manager.send_message(data, websocket)
            else:
                await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        logger.info(f"Disconnected websocket {hash(websocket)}")
        ws_manager.disconnect(websocket)
