import redis

from app.config import settings


redis_client = redis.from_url(
    settings.redis_url,
    decode_responses=True,
)


def check_redis_connection() -> bool:
    try:
        return redis_client.ping()
    except redis.RedisError:
        return False
