import random
from enum import Enum
from typing import Any
import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.proxy_processing.schemas import SAdvancedSearch
from src.proxy_processing import repository as proxy_db
from src.proxy_processing.utils import parse_proxy_dict_from_string
from src.configs.config import DB_PASS, DB_PORT, DB_HOST, DB_USER

######################################
# tests simple repository methods
# with temporary database
######################################

TEST_DB_NAME = "test_database"
# fixes error when metadata with name proxy already exists
ProxyModel = proxy_db.ProxyModel




# if you want to test your own proxies be sure
# that ips 127.0.0.1 and 1.2.3.4 are reserved for tests bellow
proxies = """
socks5://127.0.0.1:9050
https://1.2.3.4:9050
socks4://118.174.14.65:44336
socks4://31.43.33.56:4153
socks4://1.15.62.12:5678
socks4://186.251.255.245:31337
socks4://177.12.177.2:4153
socks4://8.137.13.191:8080
socks4://50.221.74.130:80
socks4://41.222.8.254:8082
socks4://190.61.47.78:9992
socks4://50.223.38.6:80
socks4://192.252.220.92:17328
socks4://50.169.37.50:80
socks4://34.75.202.63:80
socks4://176.113.73.102:3128
socks4://184.178.172.5:15303
socks4://181.78.8.154:999
socks4://186.250.29.225:8080
socks4://46.21.240.185:1080
socks4://110.78.152.67:4145
socks4://211.22.151.163:60808
socks4://200.81.144.13:1080
socks4://178.212.54.161:1080
socks4://192.111.137.35:4145
socks4://109.111.212.78:8080
socks4://103.234.254.165:80
socks4://72.10.160.93:7883
socks4://37.59.213.49:42604
socks4://194.163.134.71:64144
socks4://186.96.124.242:4153
socks4://170.233.193.129:999
socks4://34.92.88.81:33333
socks4://178.32.112.229:60289
socks4://91.214.31.234:8080
socks4://91.202.72.105:8080
socks4://120.50.40.184:3128
socks4://203.113.114.94:33107
socks4://166.62.121.196:16400
socks4://197.248.75.221:8103
socks4://212.83.143.211:64907
socks4://47.116.210.163:8081
socks4://24.249.199.4:4145
socks4://161.123.154.248:6778
socks4://200.0.247.243:10834
socks4://192.252.209.155:14455
socks4://108.181.132.117:63234
socks4://143.107.199.248:8080
socks4://50.174.7.156:80
socks4://35.178.104.4:80
socks4://103.214.54.90:8080
socks4://103.121.89.75:39267
socks4://184.178.172.3:4145
socks4://72.217.158.202:4145
socks4://192.111.130.2:4145
""".split("\n")
proxies = [i for i in filter(lambda p: p != "", proxies)]  # makes list of proxy strings
p_len = len(proxies)


@pytest.mark.dependcy(depends=["test_parse_proxy_dict_from_string_good", "test_parse_proxy_dict_from_string_bad"])
async def test_insert_many():
    # proxies must be all valid
    proxy_dicts: list[dict[str, Any]] = [parse_proxy_dict_from_string(p) for p in proxies]

    proxy_models: list[ProxyModel] = []

    for proxy in proxy_dicts:
        # pop protocol as we do in proxy_procession.router.add_proxies()
        proxy.pop("protocol", None)

        proxy_models.append(ProxyModel(**proxy))

    assert len(proxy_models) == p_len

    await proxy_db.insert_many(proxy_models)


@pytest.mark.dependency(depends=["test_insert_many"])
async def test_get_all():
    proxy_models: list[ProxyModel] = await proxy_db.get_all()

    assert len(proxy_models) == p_len


async def test_count_rows():
    rows_len: int = await proxy_db.count_rows()
    assert rows_len == len(proxies)


async def test_get_model_by_dict():
    # choose random proxy which exists in database
    proxy_dict: dict[str, Any] = parse_proxy_dict_from_string(random.choice(proxies))

    proxy: ProxyModel = await proxy_db.get_model_by_dict(proxy_dict)

    assert proxy is not None
    assert proxy.ip == proxy_dict["ip"]
    assert proxy.port == proxy_dict["port"]


async def test_get_model_by_id():
    # choose random proxy which exists in database
    proxy_dict: dict[str, Any] = parse_proxy_dict_from_string(random.choice(proxies))
    proxy: ProxyModel = await proxy_db.get_model_by_dict(proxy_dict)

    id_ = proxy.id
    del proxy

    proxy: ProxyModel = await proxy_db.get_model_by_id(id_)

    assert proxy.id == id_


async def test_get_by_ip():
    ip = "1.2.3.4"

    proxy: list[ProxyModel] = await proxy_db.get_by_ip(ip)

    assert proxy
    assert proxy[0].ip == ip


async def test_update_many():
    proxy_models: list[ProxyModel] = await proxy_db.get_all()

    assert proxy_models

    # update information about protocols
    updated_ids: list[int] = []
    for m in proxy_models[:10]:
        m.https = True
        updated_ids.append(m.id)

    await proxy_db.update_many(proxy_models[:10])

    for id_ in updated_ids:
        proxy_model: ProxyModel = await proxy_db.get_model_by_id(id_)

        assert proxy_model.https


async def test_update_with_check_timestamp():
    proxy_models: list[ProxyModel] = await proxy_db.get_all()
    assert proxy_models

    random.shuffle(proxy_models)

    # test alive
    proxy_model: ProxyModel = proxy_models[0]

    assert proxy_model.last_check_at is None

    proxy_model.status = "alive"

    id_ = proxy_model.id
    await proxy_db.update_with_check_timestamp(proxy_model)
    del proxy_model

    proxy_model: ProxyModel = await proxy_db.get_model_by_id(id_)

    assert proxy_model.status.value == "alive"
    assert proxy_model.last_check_at is not None

    # test dead
    proxy_model: ProxyModel = proxy_models[1]

    assert proxy_model.last_check_at is None

    proxy_model.status = "dead"

    id_ = proxy_model.id
    await proxy_db.update_with_check_timestamp(proxy_model)
    del proxy_model

    proxy_model: ProxyModel = await proxy_db.get_model_by_id(id_)

    assert proxy_model.status.value == "dead"
    assert proxy_model.last_check_at is not None


async def test_get_alive():
    proxy_models: list[ProxyModel] = await proxy_db.get_alive()
    assert len(proxy_models) == 1


async def test_get_sorted_by():
    proxy_models: list[ProxyModel] = await proxy_db.get_sorted_by(ProxyModel.ip == "127.0.0.1")

    assert proxy_models[-1].socks5 is True
    assert proxy_models[-1].port == "9050"


async def test_purge_all():
    await proxy_db.purge_all()

    proxy_models: list[ProxyModel] = await proxy_db.get_all()

    assert len(proxy_models) == 0
