from typing import Any

from src.proxy_processing import repository as proxy_db
from src.proxy_processing.schemas import SAdvancedSearch
from src.proxy_processing.utils import parse_proxy_dict_from_string

############################################
# this test is only for advanced_search()
# runs in the second test database
# tests complete searches
############################################

TEST_DB_NAME = "test_database"
# fixes error when metadata with name proxy already exists
ProxyModel = proxy_db.ProxyModel

proxies = """
socks5://127.0.0.1:9050
socks5://118.174.14.65:44336
socks5://31.43.33.56:4153
socks5://1.15.62.12:5678
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
http://211.22.151.163:60808
http://200.81.144.13:1080
http://178.212.54.161:1080
https://192.111.137.35:4145
https://109.111.212.78:8080
https://103.234.254.165:80
""".split("\n")
proxies = [i for i in filter(lambda p: p != "", proxies)]  # makes list of proxy strings
p_len = len(proxies)

# mark them as alive
alive_ips = (
    "181.78.8.154",
    "200.81.144.13",
    "118.174.14.65",
    "127.0.0.1"
)

# mark them as dead
dead_ips = (
    "103.234.254.165",
    "46.21.240.185",
    "176.113.73.102",
    "31.43.33.56"
)


async def test_partial_check_simulation():
    """
    Simulates partial check.
    """

    # convert strings to dicts
    proxy_dicts: list[dict[str, Any]] = [parse_proxy_dict_from_string(p) for p in proxies]

    # convert dicts to ORM models
    proxy_models: list[ProxyModel] = []
    for proxy in proxy_dicts:
        # pop protocol as we do in proxy_procession.router.add_proxies()
        proxy.pop("protocol", None)

        proxy_models.append(ProxyModel(**proxy))

    # insert in test database
    await proxy_db.insert_many(proxy_models)


    # set status 'alive' for some proxies with ips from marked_as_alive
    marked_as_alive: list[ProxyModel] = []
    for ip in alive_ips:
        marked_as_alive.extend(await proxy_db.get_by_ip(ip))

    for p in marked_as_alive:
        p.status = "alive"


    # the same as above, but for 'dead' ips
    marked_as_dead: list[ProxyModel] = []
    for ip in dead_ips:
        marked_as_dead.extend(await proxy_db.get_by_ip(ip))

    for p in marked_as_dead:
        p.status = "dead"

    # update test database
    await proxy_db.update_many([*marked_as_alive, *marked_as_dead])



async def test_search_with_multiple_params_by_status():
    # create test search query with only one status param
    search_query: SAdvancedSearch = SAdvancedSearch(alive=True)

    # execute
    results: list[ProxyModel] = await proxy_db.search_with_multiple_params(search_query)

    # and test it
    assert len(results) == len(alive_ips)

    # test query with two statuses (counts as alive OR dead)
    search_query: SAdvancedSearch = SAdvancedSearch(alive=True, dead=True)
    results: list[ProxyModel] = await proxy_db.search_with_multiple_params(search_query)

    # so, the result must be the sum of dead ips and alive ones
    assert len(results) == (len(alive_ips) + len(dead_ips))


async def test_search_with_multiple_params_by_protocol():
    """Tests search query by protocols"""

    # create test query with only one protocol to search
    search_query: SAdvancedSearch = SAdvancedSearch(socks5=True)
    results: list[ProxyModel] = await proxy_db.search_with_multiple_params(search_query)
    assert len(results) == 4

    # same, but for socks4
    search_query: SAdvancedSearch = SAdvancedSearch(socks4=True)
    results: list[ProxyModel] = await proxy_db.search_with_multiple_params(search_query)
    assert len(results) == 10

    # test two protocols (http OR https)
    search_query: SAdvancedSearch = SAdvancedSearch(http=True, https=True)
    results: list[ProxyModel] = await proxy_db.search_with_multiple_params(search_query)
    assert len(results) == 6


async def test_search_with_multiple_params_limit():
    """Tests search with limits"""

    search_query: SAdvancedSearch = SAdvancedSearch(limit=10)
    results: list[ProxyModel] = await proxy_db.search_with_multiple_params(search_query)
    assert len(results) == 10

    search_query: SAdvancedSearch = SAdvancedSearch(limit=-1)
    results: list[ProxyModel] = await proxy_db.search_with_multiple_params(search_query)
    assert len(results) == len(proxies)


async def test_search_with_multiple_params_together():
    """Sets together two or more diverse params like status and protocol"""

    # first, we count how many alive proxies total
    search_query: SAdvancedSearch = SAdvancedSearch(alive=True)
    results: list[ProxyModel] = await proxy_db.search_with_multiple_params(search_query)

    # and separate results by protocols
    # to know how many proxies we should get by query below
    socks4 = 0
    socks5 = 0
    http = 0
    https = 0
    for p in results:
        if p.socks5:
            socks5 += 1
        elif p.socks4:
            socks4 += 1
        elif p.http:
            http += 1
        elif p.https:
            https += 1


    # execute query: ...WHERE status='alive' AND (socks4 IS true OR socks5 IS true)
    search_query: SAdvancedSearch = SAdvancedSearch(alive=True, socks5=True, socks4=True)
    results: list[ProxyModel] = await proxy_db.search_with_multiple_params(search_query)

    # and compare complicated search query with the results from a simple one
    assert len(results) == (socks4 + socks5)


    # test query with 3 statuses at the same time (equal to SELECT without any filters)
    search_query: SAdvancedSearch = SAdvancedSearch(alive=True, dead=True, not_checked=True)
    results: list[ProxyModel] = await proxy_db.search_with_multiple_params(search_query)

    assert len(results) == len(proxies)

    # test getting only unchecked proxies (status is null)
    search_query: SAdvancedSearch = SAdvancedSearch(not_checked=True)
    results: list[ProxyModel] = await proxy_db.search_with_multiple_params(search_query)
    assert len(results) == (len(proxies) - len(alive_ips) - len(dead_ips))
