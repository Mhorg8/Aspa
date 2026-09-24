from typing import cast

from fastapi import Request
from redis.asyncio import Redis

from app.core.config import get_settings


def create_redis() -> Redis:
    return Redis.from_url(  # pyright: ignore[reportUnknownMemberType]
        get_settings().redis_url,
        decode_responses=True,
        socket_connect_timeout=2,
        socket_timeout=2,
    )


async def get_redis(request: Request) -> Redis:
    return cast(Redis, request.app.state.redis)
