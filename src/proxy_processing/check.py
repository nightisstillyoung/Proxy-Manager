import asyncio
import struct
import traceback
from functools import partial
from typing import Coroutine
import logging
import aiohttp
from aiohttp_proxy import ProxyConnector

from configs.config import checker_config
from proxy_processing.utils import on_timeout, mark_and_measure_latency
from proxy_processing.models import Protocol, ProxyModel
from base_utils import sync_compatible

SOCKS4_REQUEST_GRANTED = 0x5A
SOCKS_VERSION = 4

SOCKS5_VERSION = 0x05
SOCKS5_AUTH_NONE = 0x00
SOCKS5_AUTH_PASSWORD = 0x02
SOCKS5_AUTH_UNACCEPTABLE = 0xFF
SOCKS5_CMD_CONNECT = 0x01
SOCKS5_ATYP_IPV4 = 0x01
SOCKS5_ATYP_DOMAINNAME = 0x03
SOCKS5_ATYP_IPV6 = 0x04
SOCKS5_REPLY_SUCCEEDED = 0x00

logger = logging.getLogger(__name__)


class UnsupportedError(Exception):
    """Custom class for handling various errors during bytes check"""
    pass


@on_timeout(timeout=checker_config["timeout"], retries=checker_config["retries"])
@mark_and_measure_latency("socks4")
async def check_socks4_proxy(
        host: str,
        port: int,
        username: str = None,
        password: str = None
) -> bool:
    """
        socks4(a) proxy checker function.
        First packet to server: VER(1) CMD(1) DSTPORT(2) DSTIP(4) ID(variable)
            * VER: 0x04 = SOCKS4(a)
            * CMD: 0x01 = establish a TCP/IP stream connection
            * DSTPORT: 2-byte port number (in network byte order)
            * DSTIP: IPv4 Address, 4 bytes (in network byte order)
            * ID: UserID
        Response: 0x5A = Request granted
    :param host: ip string
    :param port: port integer
    :param username:
    :param password:
    :return:
    """
    try:
        # open connection with proxy server
        reader, writer = await asyncio.open_connection(host, port)

        # create field UserID
        user_id = b""
        if username:
            user_id = username.encode()
            if password:
                user_id += b":" + password.encode()
        user_id += b"\0"

        # send SOCKS4 request
        request = struct.pack(">BBH", SOCKS_VERSION, 1, 80)
        request += b"\x01\x01\x01\x01"  # some non-existent ip
        request += user_id
        writer.write(request)
        await writer.drain()

        # get response
        response = await reader.read(8)

        if len(response) < 2:
            # not enough data to read the status
            writer.close()
            await writer.wait_closed()
            return False

        status = response[1]

        # close connection
        writer.close()
        await writer.wait_closed()

        return status == SOCKS4_REQUEST_GRANTED

    except asyncio.TimeoutError:
        return False
    except (ConnectionRefusedError, OSError):
        return False
    except Exception:
        logger.exception(f"Error with proxy socks4://{host}:{port}")
        return False


@on_timeout(timeout=checker_config["timeout"], retries=checker_config["retries"])
@mark_and_measure_latency("socks5")
async def check_socks5_proxy(host: str, port: int, username=None, password=None) -> bool:
    """
    socks5(a) proxy checker function.
    First packet to server: VER(1) CMD(1) RSV(1) ATYP(1) DST.ADDR(variable) DST.PORT(2)
        * VER: 0x05 = SOCKS5*
        * CMD: 0x01 = establish a TCP/IP stream connection
        * RSV: 0x00 = reserved
        * ATYP: Address type of following address
            - 0x01 = IPv4 address
            - 0x03 = Domain name (first byte contains the length of the domain name)
            - 0x04 = IPv6 address
        * DST.ADDR: Destination address, variable length depending on ATYP field value.
        * DST.PORT: Destination port number in network byte order, 2 bytes

    Response:
        * VER: Protocol version (should be set to 0x05 for SOCKS5)
        * REP: 0x00 = succeeded
        * RSV: x00 = reserved byte
        * ATYP, BND.ADDR and BND.PORT fields similar to those in the client's request,
            representing the bound address and port on which the client should connect.
    :param host: ip string
    :param port: port integer
    :param username:
    :param password:
    :return:
    """
    try:
        # create connection to proxy server
        reader, writer = await asyncio.open_connection(host, port)

        # send SOCKS5 hello
        if username and password:
            # if username&password, sends auth methods USERNAME/PASSWORD and NONE
            greeting = struct.pack("!BB", SOCKS5_VERSION, 2)
            greeting += struct.pack("!BB", SOCKS5_AUTH_NONE, SOCKS5_AUTH_PASSWORD)
        else:
            # or only NONE
            greeting = struct.pack("!BB", SOCKS5_VERSION, 1)
            greeting += struct.pack("!B", SOCKS5_AUTH_NONE)
        writer.write(greeting)
        await writer.drain()

        # get greeting answer
        response = await reader.read(2)
        version, chosen_auth = struct.unpack("!BB", response)

        if version != SOCKS5_VERSION:
            raise UnsupportedError("Unsupported socks5 version")

        if chosen_auth == SOCKS5_AUTH_PASSWORD:
            # send auth data
            auth_request = struct.pack("!BB", 1, len(username))
            auth_request += username.encode() + b"\x00"
            auth_request += struct.pack("!B", len(password))
            auth_request += password.encode()
            writer.write(auth_request)
            await writer.drain()

            # get auth answer
            auth_response = await reader.read(2)
            auth_version, auth_status = struct.unpack("!BB", auth_response)
            if auth_status != 0:
                raise UnsupportedError("Auth error")

        elif chosen_auth != SOCKS5_AUTH_NONE:
            raise UnsupportedError("Unsupported auth method")

        # send socks request
        request = struct.pack("!BBB", SOCKS5_VERSION, SOCKS5_CMD_CONNECT, 0)
        request += struct.pack("!B", SOCKS5_ATYP_IPV4)
        request += b"\x01\x01\x01\x01"  # Фиктивный IPv4 адрес
        request += struct.pack("!H", 80)  # Фиктивный порт
        writer.write(request)
        await writer.drain()

        # get response
        response = await reader.read(4)
        version, reply, _, _ = struct.unpack("!BBBB", response)

        if version != SOCKS5_VERSION:
            raise UnsupportedError("Unsupported socks5 version")

        # get remain parts of the response
        if reply == SOCKS5_REPLY_SUCCEEDED:
            # read address and port
            addr_type = (await reader.read(1))[0]
            if addr_type == SOCKS5_ATYP_IPV4:
                await reader.read(4)
            elif addr_type == SOCKS5_ATYP_DOMAINNAME:
                addr_len = (await reader.read(1))[0]
                await reader.read(addr_len)
            elif addr_type == SOCKS5_ATYP_IPV6:
                await reader.read(16)
            await reader.read(2)

        # close connection
        writer.close()
        await writer.wait_closed()

        return reply == SOCKS5_REPLY_SUCCEEDED

    except asyncio.TimeoutError:
        return False
    except (ConnectionRefusedError, OSError, UnsupportedError, struct.error):
        return False
    except Exception:
        logger.exception(f"Error with proxy socks5://{host}:{port}")
        return False


@on_timeout(timeout=checker_config["timeout"], retries=checker_config["retries"])
async def check_http_proxy(
        host: str,
        port: int,
        username: str = None,
        password: str = None,
        secured: bool = False
) -> bool:
    """
    http(s) proxy checker function. Tries to get http(s)://httpbin.org/get
    """
    protocol = "https" if secured else "http"

    proxy_url = f"{protocol}://{host}:{port}"
    if username and password:
        proxy_url = f"{protocol}://{username}:{password}@{host}:{port}"

    async with aiohttp.ClientSession(connector=ProxyConnector.from_url(proxy_url)) as session:
        try:
            # add custom header to test that http proxy actually proxies our request or just return its own
            async with session.get(
                    f"{protocol}://httpbin.org/get",
                    headers={"X-Test": "check me"},
                    timeout=5
            ) as response:
                if response.status == 200:
                    # if it's bugged or some unknown gateway
                    return "check me" in await response.text()
                else:
                    return False
        except (aiohttp.ClientError, asyncio.TimeoutError):
            return False
        except Exception:
            logger.exception(f"Error with proxy {protocol}://{host}:{port}")
            return False


# register both variations of the same function
check_https_proxy = mark_and_measure_latency("https")(
    partial(
        check_http_proxy,
        secured=True)
)
check_http_proxy = mark_and_measure_latency("http")(check_http_proxy)


@sync_compatible
async def check_proxy(proxy_model: ProxyModel) -> ProxyModel:
    """Runs checks on proxy, updates database and returns updated ProxyModel"""
    if proxy_model.protocols_list:
        protocols: list[str] = proxy_model.protocols_list
    else:
        protocols: list[str] = [p.value for p in list(Protocol)]

    # create params for checker functions
    params = {
        "host": proxy_model.ip,
        "port": int(proxy_model.port),
    }

    # optional
    if proxy_model.username != "":
        params["username"] = proxy_model.username
        params["password"] = proxy_model.password

    # creating coro pool with checkers
    background_tasks: list[Coroutine] = []

    if protocols.count("http"):
        background_tasks.append(check_http_proxy(**params))

    if protocols.count("https"):
        background_tasks.append(check_https_proxy(**params))

    if protocols.count("socks4"):
        background_tasks.append(check_socks4_proxy(**params))

    if protocols.count("socks5"):
        background_tasks.append(check_socks5_proxy(**params))

    # run together all coroutines
    logger.debug(f"Run {protocols} for {proxy_model}")
    # ex: (True, 'socks4', 0.27976512908935547)
    # which means that check function succeed to connect via socks4 proto with 0.279... seconds latency
    result: list[tuple[bool, str, float] | Exception] = await asyncio.gather(*background_tasks, return_exceptions=True)

    logger.debug(f"Got result {result} for {proxy_model}")

    working_protocols: list[str] = []
    for r in result:
        if isinstance(r, TimeoutError):
            logger.debug(f"{proxy_model} Timeout")
            continue
        elif isinstance(r, Exception):
            tb_str = traceback.format_exception(etype=type(r), value=r, tb=r.__traceback__)
            traceback_str = "".join(tb_str)
            logging.error("Error in proxy checker: %s\nTraceroute: %s", str(r), traceback_str)
            continue

        assert type(r) is tuple
        assert len(r) == 3

        # Ex: ("socks4", True)
        if r[0]:
            working_protocols.append(r[1])
            # sets minimal latency
            proxy_model.latency = r[2] if proxy_model.latency is None else min(proxy_model.latency, r[2])

    # update proxy status
    if working_protocols:
        proxy_model.protocols_list = working_protocols
        proxy_model.status = "alive"

    else:
        proxy_model.status = "dead"
        proxy_model.protocols_list = []

    logger.debug(f"Working protocols for {proxy_model.credentials_ip_port} are {proxy_model.protocols_list}")
    return proxy_model
