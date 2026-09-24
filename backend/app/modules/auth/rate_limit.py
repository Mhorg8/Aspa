from typing import Annotated, cast

from fastapi import Depends, Request
from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.integrations.redis import get_redis

# One atomic operation ensures a counter cannot be left without an expiration.
_INCREMENT = """
local count = redis.call('INCR', KEYS[1])
if count == 1 then redis.call('EXPIRE', KEYS[1], ARGV[1]) end
return count
"""


async def limit_auth_requests(
    request: Request, redis: Annotated[Redis, Depends(get_redis)]
) -> None:
    settings = get_settings()
    address = request.client.host if request.client else "unknown"
    key = f"aspa:{settings.environment}:auth:ip:{address}"
    try:
        count = cast(
            int,
            await redis.execute_command(  # pyright: ignore[reportUnknownMemberType]
                "EVAL", _INCREMENT, 1, key, settings.auth_rate_limit_window_seconds
            ),
        )
    except RedisError as exc:
        raise AppError("Authentication temporarily unavailable", status_code=503) from exc
    if count > settings.auth_rate_limit_requests:
        raise AppError(
            "Too many authentication attempts",
            status_code=429,
            headers={"Retry-After": str(settings.auth_rate_limit_window_seconds)},
        )
