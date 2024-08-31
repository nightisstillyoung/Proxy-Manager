import asyncio
import time
from functools import wraps
from typing import Callable, TypeVar, cast, Coroutine, Awaitable

from proxy_processing.regex import proxy_expression
from configs.config import checker_config

T = TypeVar("T")
RT = TypeVar("RT")


def parse_proxy_dict_from_string(proxy_str: str) -> dict[str, str | bool | list] | str:
    if not isinstance(proxy_str, str):
        return str(proxy_str)

    _ = proxy_expression.match(proxy_str)
    if _ is None:
        return proxy_str  # in case of invalid format we return it as is

    # gets match dict and removes all keys where value is None
    proxy_dict: dict = {k: v for k, v in _.groupdict().items() if v is not None}

    if proxy_dict.get("protocol") is not None:
        proxy_dict[proxy_dict["protocol"]] = True

    return proxy_dict


def predict_check_time(length: int) -> float | int:
    return length * checker_config["timeout"] * checker_config["retries"]


def on_timeout(timeout: float | int, retries: int = 3) -> Callable[..., Callable[..., Coroutine[T, T, RT]]]:
    """
    Set timeout and retries on async function
    Timeout also applies if response is tuple with False second argument,
    Ex: ("socks4", False) means that proxy check failed and we re-check it again
    """

    def decorator(func: Callable[..., Coroutine[T, T, RT]]) -> Callable[..., Coroutine[T, T, RT]]:
        @wraps(func)
        async def wrapper(*args: T, **kwargs: T) -> RT:
            for attempt in range(retries):
                try:
                    res: RT = await asyncio.wait_for(func(*args, **kwargs), timeout)
                    # Example: ("socks4", False) means that proxy check failed
                    if isinstance(res, tuple) and not res[1]:
                        continue
                    return res
                except Exception as e:
                    if attempt == retries - 1:
                        raise e

        return wrapper

    return decorator


def mark_and_measure_latency(protocol: str) -> Callable[..., Callable[..., Coroutine[T, T, tuple[RT, str, float]]]]:
    """
    Registers protocol on check function and measure latency of proxy
    bool -> (bool, protocol: str, latency: float (ms))
    Ex:
    @mark_and_measure_latency("socks4")
    async def some_check(proxy) -> bool:
        ...

    res = await some_check(proxy)
    print(res)
    # (True, "socks4", 1000.11)
    """

    def decorator(func: Callable[..., Coroutine[T, T, RT]]) -> Callable[..., Coroutine[T, T, tuple[RT, str, float]]]:
        @wraps(func)
        async def wrapper(*args: T, **kwargs: T) -> tuple[RT, str, float]:
            start_time: float = time.time()
            res: RT = await func(*args, **kwargs)
            latency: float = time.time() - start_time
            return res, protocol, latency * 1000  # convert latency from seconds to ms

        return cast(Callable[..., Coroutine[T, T, tuple[RT, str, float]]], wrapper)

    return decorator
