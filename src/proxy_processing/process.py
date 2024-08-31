import logging
from redis import Redis

from redis_manager.conn_manager import get_conn
from proxy_processing.repository import get_model_by_id
from proxy_processing.models import ProxyModel
from proxy_processing.check import check_proxy
from proxy_processing import repository as proxy_db

logger = logging.getLogger(__name__)


def process_proxy(proxy_id: int, protocol: str | None) -> None:
    """
        Runs check(s) for proxy with proxy_id:
        if alive:
            from working results chooses the best proto (socks5 > socks4 > https > http) and pushes in redis
        else:
            updates database with 'dead' sign and sets all protocols to False
    :param proxy_id: proxy id from database
    :param protocol: protocol to check, if None - checks all available protocols
    :return: None
    """

    # get proxy model by id
    proxy_model: ProxyModel | None = get_model_by_id(proxy_id)

    logger.debug(f"Started check for {proxy_model} with protocol {protocol if protocol else 'to find'}")

    # runs checks for all available protocols
    proxy_model: ProxyModel = check_proxy(proxy_model)

    logger.debug(f"Updated data about {proxy_model} ({proxy_model.status})")
    proxy_db.update_with_check_timestamp(proxy_model)

    # after check, we decide what return to user
    if proxy_model.status == "alive":
        if protocol is not None and proxy_model.protocols_list.count(protocol):
            # client gave proxy with working protocol
            proxy_str: str = proxy_model.get_with_proto(protocol)
        elif protocol is None:
            # client asked server to find alive protocols, and we did it
            proxy_str: str = str(proxy_model)
        else:
            # proxy is alive, but client gave it with unsupported proto
            return

        logger.debug(f"Good proxy: {proxy_str}")

        # redis
        redis_conn: Redis = get_conn()
        redis_conn.rpush("good_proxies", proxy_str)
    else:
        logger.debug(f"Bad proxy: {proxy_model}")
