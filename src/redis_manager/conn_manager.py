from redis.asyncio import Redis as AsyncRedis
from redis import Redis
from configs.config import redis_config


def get_async_conn() -> AsyncRedis:
    return AsyncRedis(**redis_config)


def get_conn() -> Redis:
    return Redis(**redis_config)
