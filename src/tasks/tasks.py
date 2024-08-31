import logging
import time

from celery import Celery

from configs.config import REDIS_HOST, REDIS_PORT
from proxy_processing.process import process_proxy
from proxy_processing.models import Protocol



broker = Celery('tasks', broker=f'redis://{REDIS_HOST}:{REDIS_PORT}')
broker.conf.broker_connection_retry_on_startup = True

logger = logging.getLogger(__name__)


@broker.task
def process_proxy_worker(proxy_id: int, protocol: str | None) -> None:
    """
    Starts proxy check using process_proxy enter point
    :param proxy_id: ProxyModel.id
    :param protocol: socks4/5 or http(s)
    :return: None
    """


    # verify if protocol is valid
    if protocol is not None and protocol not in [p.value for p in list(Protocol)]:
        logger.error(f"Invalid protocol: {protocol} for proxy with {proxy_id=}")
        raise ValueError(f"Invalid protocol: {protocol} for proxy with {proxy_id=}")

    # proceed
    logger.debug(f"Processing proxy with args: {proxy_id=}, {protocol=}")
    process_proxy(proxy_id, protocol)

