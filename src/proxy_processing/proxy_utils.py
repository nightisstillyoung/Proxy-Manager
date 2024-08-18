import asyncio
from functools import wraps
from proxy_processing.regex import proxy_expression
from configs.config import checker_config


def parse_proxy_dict_from_string(proxy_str: str) -> dict | str:
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


def on_timeout(timeout: float | int, retries: int = 3):
    """
    Set timeout and retries on async function
    Timeout also applies if response is tuple with False second argument,
    Ex: ("socks4", False) means that proxy check failed and we re-check it again
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(retries):
                try:
                    res = await asyncio.wait_for(func(*args, **kwargs), timeout)
                    # Example: ("socks4", False) means that proxy check failed
                    if isinstance(res, tuple) and not res[1]:
                        continue
                    return res
                except Exception as e:
                    if attempt == retries - 1:
                        raise e
            return await func(*args, **kwargs)

        return wrapper

    return decorator


def on_proto(protocol: str):
    """
    Registers protocol on check function
    bool -> ("protocol", bool)
    Ex:
    @on_proto("socks4")
    async def some_check(proxy) -> bool:
        ...

    res = await some_check(proxy)
    print(res)
    # ("socks4", True)
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            res = await func(*args, **kwargs)
            return protocol, res

        return wrapper

    return decorator
