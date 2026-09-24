import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from redis.asyncio import Redis
from sqlalchemy import text

from app.api.router import router
from app.core.config import get_settings
from app.core.exceptions import ErrorResponse, error_content, register_exception_handlers
from app.core.logging import configure_logging
from app.db.session import DbSession, engine
from app.integrations.redis import create_redis, get_redis


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncGenerator[None]:
    configure_logging(settings.log_level)
    redis = create_redis()
    application.state.redis = redis
    try:
        yield
    finally:
        try:
            await redis.aclose()
        finally:
            await engine.dispose()


settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="ASPA fitness and wellness REST API",
    lifespan=lifespan,
)
register_exception_handlers(app)
app.include_router(router)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


class ReadinessResponse(BaseModel):
    status: str
    checks: dict[str, str]


@app.get(
    "/ready",
    tags=["health"],
    response_model=ReadinessResponse,
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ErrorResponse}},
)
async def readiness(
    session: DbSession,
    redis: Annotated[Redis, Depends(get_redis)],
) -> ReadinessResponse | JSONResponse:
    checks: dict[str, str] = {}

    async def check_database() -> None:
        await session.execute(text("SELECT 1"))

    async def check_redis() -> None:
        await redis.ping()  # pyright: ignore[reportUnknownMemberType]

    for name, check in (("database", check_database), ("redis", check_redis)):
        try:
            async with asyncio.timeout(settings.readiness_timeout_seconds):
                await check()
            checks[name] = "ok"
        except Exception:  # The response deliberately hides infrastructure details.
            checks[name] = "unavailable"

    if all(result == "ok" for result in checks.values()):
        return ReadinessResponse(status="ready", checks=checks)
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content=error_content(
            "service_unavailable",
            "One or more required services are unavailable",
            [{"location": name, "message": result} for name, result in checks.items()],
        ),
    )
