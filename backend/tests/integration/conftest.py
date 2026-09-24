import os
import subprocess
from collections.abc import AsyncIterator
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from redis.asyncio import Redis
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.session import get_db_session
from app.integrations.redis import get_redis
from app.main import app


@pytest.fixture(scope="session")
def migrated_database() -> str:
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set TEST_DATABASE_URL and TEST_REDIS_URL to run integration tests")
    if make_url(url).database != "aspa_test":
        pytest.fail("Integration tests require the dedicated aspa_test database")
    if not os.environ.get("TEST_REDIS_URL"):
        pytest.fail("TEST_REDIS_URL is required with TEST_DATABASE_URL")
    subprocess.run(
        ["alembic", "upgrade", "head"],
        env={**os.environ, "DATABASE_URL": url},
        check=True,
        timeout=30,
    )
    return url


@pytest_asyncio.fixture
async def db_session(migrated_database: str) -> AsyncIterator[AsyncSession]:
    engine = create_async_engine(migrated_database)
    try:
        async with engine.connect() as connection:
            transaction = await connection.begin()
            sessions = async_sessionmaker(
                connection, expire_on_commit=False, join_transaction_mode="create_savepoint"
            )
            async with sessions() as session:
                yield session
            await transaction.rollback()
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def integration_client(db_session: AsyncSession) -> AsyncIterator[AsyncClient]:
    redis = Redis.from_url(os.environ["TEST_REDIS_URL"], decode_responses=True)
    # Unique client keys expire naturally; no FLUSHDB or shared-state deletion.
    client_id = str(uuid4())

    async def session_override() -> AsyncIterator[AsyncSession]:
        yield db_session

    async def redis_override() -> Redis:
        return redis

    app.dependency_overrides[get_db_session] = session_override
    app.dependency_overrides[get_redis] = redis_override
    app.state.redis = redis
    try:
        transport = ASGITransport(app=app, client=(client_id, 12345))
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client
    finally:
        app.dependency_overrides.clear()
        await redis.aclose()
