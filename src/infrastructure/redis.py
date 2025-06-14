from fastapi import Request

from redis.asyncio import Redis

from src.core.config import settings

redis: Redis | None = None


async def create_redis() -> Redis:
    redis_url = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}"
    redis = await Redis.from_url(redis_url, encoding="utf-8", decode_responses=True)
    return redis


async def get_redis(request: Request) -> Redis:
    return request.app.state.redis
