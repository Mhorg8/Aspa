import os
from collections.abc import AsyncIterator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# Tests must never read deployment credentials from .env.
os.environ["JWT_SECRET_KEY"] = "test-only-secret-not-for-deployment-0123456789"
os.environ["ENVIRONMENT"] = "test"

from app.main import app
from app.modules.auth.rate_limit import limit_auth_requests


@pytest_asyncio.fixture
async def client() -> AsyncIterator[AsyncClient]:
    async def no_rate_limit() -> None:
        pass

    app.dependency_overrides[limit_auth_requests] = no_rate_limit
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app, raise_app_exceptions=False),
            base_url="http://test",
        ) as client:
            yield client
    finally:
        app.dependency_overrides.clear()
