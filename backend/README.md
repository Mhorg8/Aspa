# ASPA Backend

FastAPI modular monolith for ASPA.

Docker uses Python 3.14.7, PostgreSQL 18.6, and Redis 8.10.1.
Local tooling targets Python 3.14 through `.python-version`.

## Configuration

Copy `.env.example` to `.env`, then generate a secret with:

```bash
uv run --no-project python -c 'import secrets; print(secrets.token_hex(32))'
```

Set `JWT_SECRET_KEY` to that value. Missing, short, and documented placeholder
secrets prevent startup. `.env` is ignored by Git and excluded from Docker builds.
Keep credentials out of source control.

## Docker development

```bash
docker compose up --build -d --wait
docker compose logs -f api
```

Compose provides service hostnames for database and Redis connections, applies
Alembic migrations, then starts the API. Dependencies come from `uv.lock` and the
API runs as a non-root user. PostgreSQL and Redis host ports bind to loopback.

For a production deployment with multiple API replicas, run `alembic upgrade head`
once in a deployment job, then launch replicas with the Dockerfile's Uvicorn command.
The supplied Compose credentials are for local development only. Configure deployment
credentials and TLS separately. Only trust proxy headers from your own reverse proxy:
authentication rate limiting uses the resolved client IP.

## Local development

1. Install [uv](https://docs.astral.sh/uv/) and configure `.env` as above.
   For the host-run API, `DATABASE_URL` and `REDIS_URL` must use `localhost`,
   as shown in `.env.example`, rather than Docker service names.
2. Start PostgreSQL and Redis: `docker compose up -d postgres redis`.
3. Install dependencies: `uv sync --locked`.
4. Apply migrations: `uv run alembic upgrade head`.
5. Run the API: `uv run uvicorn app.main:app --reload`.

OpenAPI is available at `http://localhost:8000/docs`. Run checks with:

```bash
uv run ruff check .
uv run ruff format --check .
uv run pyright
uv run pytest
```

Pyright checks application code and migrations in strict mode. Tests treat warnings
as errors. CI runs the same checks, including integration tests. Add dependencies
with `uv add` / `uv add --dev` and commit both `pyproject.toml` and `uv.lock`.

## Integration tests

Unit tests run without services. Database tests skip unless the following variables
are supplied. Use the isolated test stack; do not point tests at development data:

```bash
docker compose -f docker-compose.test.yml up -d --wait
TEST_DATABASE_URL=postgresql+asyncpg://aspa:aspa@127.0.0.1:55432/aspa_test \
TEST_REDIS_URL=redis://127.0.0.1:56379/0 \
uv run pytest
docker compose -f docker-compose.test.yml down
```

Tests apply real Alembic migrations to `aspa_test` and roll back test transactions.
PostgreSQL test storage is temporary. The test Compose project is separate from the
development stack; stopping it does not affect development containers or volumes.

## Auth API

- `POST /api/auth/register` creates a user and returns an access token.
- `POST /api/auth/login` accepts email/password JSON and returns an access token.
- `GET /api/users/me` returns the authenticated user using `Authorization: Bearer <token>`.

Routes use the stable `/api` prefix without a version segment. Health probes remain
at `/health` and `/ready`. API errors use `{\"error\": {\"code\", \"message\", \"details\"?}}`.

Registration and login share a Redis-backed limit of 20 requests per client IP per
60 seconds (configurable in `.env`). Excess requests return 429 with `Retry-After`.
If Redis is unavailable, authentication returns 503 rather than bypassing the limit.
Tokens must contain `sub`, `iat`, and `exp`. Authentication failures return the Bearer
challenge header. Password hashing runs in a thread pool to avoid blocking the event loop.
