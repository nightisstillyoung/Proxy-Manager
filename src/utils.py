import asyncio
from asyncio import CancelledError, AbstractEventLoop
from functools import wraps
from typing import Any, TypeVar

from schemas import SBase
from models import BaseModel


# that value is pydantic model, inherited from SBase parent class
T = TypeVar('T', bound=SBase)


async def coroutine_error_handler(func):
    """
    Decorator that handles CancelledError and returns None in that case
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            res = await func(*args, **kwargs)
        except CancelledError:
            return
        except Exception as e:
            raise e
        else:
            return res

    return wrapper


def get_or_create_eventloop() -> AbstractEventLoop:
    """Creates or gets even loop"""
    try:
        return asyncio.get_event_loop()
    except RuntimeError as ex:
        if "There is no current event loop in thread" in str(ex):
            loop: AbstractEventLoop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop
        else:
            raise


def sync_compatible(async_func):
    """
    Decorator that makes an async function available in sync code
    """

    @wraps(async_func)
    def wrapper(*args, **kwargs) -> Any:
        if asyncio.iscoroutinefunction(async_func) and asyncio.get_event_loop().is_running():
            # returns Coroutine if we are in async context
            return async_func(*args, **kwargs)

        # if we are in sync context, using event loop
        loop: AbstractEventLoop = get_or_create_eventloop()
        try:
            return loop.run_until_complete(async_func(*args, **kwargs))
        except RuntimeError as e:
            if str(e) == 'Event loop is closed':
                # If loop is closed, creating a new one
                loop: AbstractEventLoop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                return loop.run_until_complete(async_func(*args, **kwargs))
            else:
                raise e
        except Exception as e:
            raise e

    return wrapper


def model_to_pydantic(model: BaseModel, pd_model: T) -> T:
    """Converts ORM model to Pydantic model"""
    return pd_model.model_validate(model, from_attributes=True)
