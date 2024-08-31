from celery import Celery
from redis import Redis
from redis.asyncio import Redis as AsyncRedis

from proxy_processing.utils import predict_check_time
from redis_manager.conn_manager import get_conn, get_async_conn
from tasks.tasks import broker
from abc import ABC


class AbstractCeleryManager(ABC):
    """
    Abstract class that provides methods to control and inspect celery
    """
    def __init__(self, celery: Celery):
        self.broker = celery
        self.inspector = celery.control.inspect()

    def purge_queues(self) -> None:
        """Purges celery queue"""
        self.broker.control.purge()

    @property
    def active_tasks_len(self) -> int:
        """Returns active (running) tasks"""
        counter: int = 0
        if active := self.inspector.active():
            for worker, tasks in active.items():
                counter += len(tasks)

        return counter

    @property
    def reserved_tasks_len(self) -> int:
        """Returns reserved (scheduled) tasks"""
        counter: int = 0
        if reserved := self.inspector.reserved():
            for worker, tasks in reserved.items():
                counter += len(tasks)

        return counter


class AsyncCeleryManager(AbstractCeleryManager):
    """Async class to control celery tasks queue"""
    def __init__(self, celery, *args, **kwargs):
        super().__init__(celery)
        self.async_redis: AsyncRedis = get_async_conn()

    async def get_redis_celery_len(self) -> int:
        """
        Returns amount of tasks from redis
        NOTE: Celery stores tasks not only in redis, but also +- 4 in reserved mode for every worker.
        So, actual formular should be redis['celery'] + workers + workers*4
        """
        return int(await self.async_redis.llen("celery") | 0)

    async def set_redis_initial_len(self, value: int) -> None:
        await self.async_redis.set("initial_len", value, predict_check_time(value))

    async def get_initial_len(self) -> int:
        return int(await self.async_redis.get("initial_len") or 0)

    async def get_current_len(self) -> int:
        """Returns total tasks in redis + celery"""
        return await self.get_redis_celery_len() + self.active_tasks_len + self.reserved_tasks_len

    async def update_initial_len(self, additional_proxies_len: int = 0) -> int:
        current_len: int = await self.get_current_len()
        await self.set_redis_initial_len(additional_proxies_len + current_len)
        return additional_proxies_len + current_len

    async def get_progress(self) -> dict[str, int | float]:
        context: dict[str, int | float] = {
            "current_len": await self.get_current_len()
        }

        # how many proxies was pushed initially
        # if there is no value in redis, we use current len
        context["initial_len"] = int(await self.get_initial_len() or context["current_len"])

        # width calc
        context["progressbar_width"] = 100 - (
            (100 * context["current_len"] / context["initial_len"]) if context["initial_len"] > 0 else 0
        )

        # value_now
        context["value_now"] = context["initial_len"] - context["current_len"]

        # if last check is finished, the list with fresh good proxies in cache is no longer required,
        if context["progressbar_width"] >= 100:
            await self.async_redis.expire("good_proxies", 120)

        return context




class CeleryManager(AbstractCeleryManager):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.redis: Redis = get_conn()

    def get_redis_celery_len(self) -> int:
        return int(self.redis.llen('celery') or 0)



async_celery_manager: AsyncCeleryManager = AsyncCeleryManager(broker)
celery_manager: CeleryManager = CeleryManager(broker)  # for sync endpoints

