You are building the backend for **ASPA**, a mobile-first fitness and wellness application.

Use **FastAPI with a modular monolith architecture**.

The project should be easy to develop now, but structured so it can scale as the application grows.

## Tech Stack

Use:

* Python
* FastAPI
* Pydantic
* pydantic-settings
* PostgreSQL
* SQLAlchemy 2.x async
* asyncpg
* Alembic
* Redis
* uv for dependency management
* Ruff for linting and formatting
* Pyright for type checking
* pytest and pytest-asyncio for tests
* Docker

Do not introduce microservices.

Do not over-engineer the architecture with unnecessary Clean Architecture abstractions, ports, adapters, use-case layers, or excessive interfaces.

Use a simple flow:

```text
Router
  ↓
Service
  ↓
Repository when needed
  ↓
SQLAlchemy
  ↓
PostgreSQL
```

Repositories are optional. Only create them when database logic becomes complex or reusable.

## Project Structure

Create the project with this structure:

```text
backend/
├── app/
│   ├── main.py
│   │
│   ├── api/
│   │       └── router.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   ├── exceptions.py
│   │   └── logging.py
│   │
│   ├── db/
│   │   ├── base.py
│   │   └── session.py
│   │
│   ├── modules/
│   │   ├── auth/
│   │   ├── users/
│   │   ├── exercises/
│   │   ├── workouts/
│   │   ├── workout_plans/
│   │   ├── foods/
│   │   ├── nutrition/
│   │   ├── progress/
│   │   ├── analytics/
│   │   └── subscriptions/
│   │
│   ├── integrations/
│   │   ├── redis.py
│   │   ├── storage.py
│   │   ├── sms.py
│   │   └── payments.py
│   │
│   └── workers/
│       └── tasks/
│
├── migrations/
│   └── versions/
│
├── tests/
│   ├── conftest.py
│   ├── auth/
│   ├── users/
│   ├── workouts/
│   └── nutrition/
│
├── scripts/
├── pyproject.toml
├── uv.lock
├── alembic.ini
├── .env.example
├── Dockerfile
└── README.md
```

## Module Structure

Each business module should be self-contained.

Example:

```text
app/modules/workouts/
├── __init__.py
├── router.py
├── schemas.py
├── models.py
├── service.py
├── repository.py
└── dependencies.py
```

Responsibilities:

```text
router.py
FastAPI routes and HTTP concerns only.

schemas.py
Pydantic request and response models.

models.py
SQLAlchemy ORM models.

service.py
Business logic.

repository.py
Complex or reusable database operations.

dependencies.py
Feature-specific FastAPI dependencies.
```

Keep routers thin.

Do not place business logic directly inside routes.

Example:

```python
@router.post("/")
async def create_workout(
    data: WorkoutCreate,
    service: WorkoutServiceDep,
):
    return await service.create(data)
```

Business logic should live in the service layer.

## API Versioning

All API routes should use:

```text
/api
```

Example:

```text
/api/auth
/api/users
/api/exercises
/api/workouts
/api/workout-plans
/api/foods
/api/nutrition
/api/progress
/api/analytics
/api/subscriptions
```

Use a central router:

```python
router = APIRouter(prefix="/api")
```

and include each module router from there.

`main.py` should remain small.

Example:

```python
from fastapi import FastAPI

from app.api.v1.router import router

app = FastAPI(
    title="ASPA API",
    version="1.0.0",
)

app.include_router(router)
```

## Database

Use:

```text
PostgreSQL
SQLAlchemy 2.x
asyncpg
Alembic
```

Use an async engine and `async_sessionmaker`.

Database sessions must be request-scoped or task-scoped.

Do not share one `AsyncSession` between concurrent requests or tasks.

Example structure:

```python
engine = create_async_engine(settings.database_url)

session_factory = async_sessionmaker(
    engine,
    expire_on_commit=False,
)
```

Use Alembic for all schema changes.

Never manually modify the production database schema.

## Configuration

Use `pydantic-settings`.

Configuration belongs in:

```text
app/core/config.py
```

Environment variables should include things such as:

```text
APP_ENV
DATABASE_URL
REDIS_URL
JWT_SECRET
ACCESS_TOKEN_EXPIRE_MINUTES
S3_ENDPOINT
S3_BUCKET
SMS_PROVIDER
```

Never hard-code credentials.

Commit:

```text
.env.example
```

Do not commit real `.env` files.

## Integrations

All external services belong under:

```text
app/integrations/
```

Examples:

```text
Redis
S3 / Ceph
SMS providers
payment gateways
push notification providers
AI providers
```

Business modules should not depend directly on specific vendors.

For example, authentication should use:

```python
await sms.send_otp(phone_number, code)
```

instead of calling a specific SMS provider directly inside `auth/service.py`.

## Redis

Use Redis for:

* OTP codes
* caching
* rate limiting
* distributed locks
* temporary state
* background-job queues

Do not use Redis as the primary database.

## Background Jobs

Long-running or non-critical work should run outside HTTP requests.

Examples:

* sending notifications
* sending SMS
* processing images
* updating analytics
* generating recommendations
* processing health data
* scheduled jobs

Use workers backed by Redis.

Keep worker tasks under:

```text
app/workers/tasks/
```

The API should enqueue work and return instead of blocking unnecessarily.

## Tests

Tests should mirror the business domains.

Example:

```text
tests/
├── conftest.py
├── auth/
│   ├── test_login.py
│   └── test_otp.py
├── workouts/
│   ├── test_create_workout.py
│   ├── test_complete_workout.py
│   └── test_workout_history.py
└── nutrition/
    ├── test_foods.py
    └── test_meals.py
```

Use:

* pytest
* pytest-asyncio

Prefer testing business behavior rather than implementation details.

## Code Quality

Use:

```text
Ruff
Pyright
pytest
```

Expected commands:

```bash
uv run ruff check .
uv run ruff format --check .
uv run pyright
uv run pytest
```

Code should:

* use type hints
* use async correctly
* avoid global mutable state
* avoid giant functions
* avoid circular dependencies
* avoid generic `utils.py` dumping grounds
* avoid unnecessary abstractions
* use dependency injection where it improves testability

## Dependency Management

Use `uv`.

Project dependencies belong in:

```text
pyproject.toml
```

Commit:

```text
uv.lock
```

Do not maintain multiple manually synchronized `requirements.txt` files unless there is a specific deployment requirement.

## ASPA Domains

The application will eventually include:

### Authentication

* Iranian phone-number authentication
* OTP login
* JWT access tokens
* refresh tokens
* rate limiting

### Users

* profile
* height
* weight
* gender where required by product logic
* preferences
* goals

### Exercises

* exercise library
* muscle groups
* equipment
* instructions
* images
* videos

### Workout Plans

* routines
* training days
* exercises
* target reps
* target sets
* rest times

### Workouts

* workout sessions
* exercises
* sets
* reps
* weight
* RPE
* RIR
* duration
* personal records

### Nutrition

* meals
* food logging
* calories
* protein
* carbohydrates
* fats

### Foods

Support Iranian foods and brands.

### Progress

* body weight
* body measurements
* progress photos
* strength progress

### Analytics

Examples:

* training volume
* training frequency
* personal records
* estimated 1RM
* body-weight trends
* muscle-group volume

### Subscriptions

Later support:

* plans
* subscriptions
* Iranian payment gateways
* premium features

## Architecture Principles

Follow these principles:

1. Start as a modular monolith.
2. Organize code by business domain.
3. Keep FastAPI routers thin.
4. Put business logic in services.
5. Add repositories only where they provide real value.
6. Keep infrastructure code separate from business logic.
7. Do not build microservices prematurely.
8. Prefer simple code over theoretically perfect architecture.
9. Make modules independent enough that they could be extracted later if necessary.
10. Keep the codebase friendly for a small development team.
11. Build APIs with mobile clients in mind.
12. Design operations such as workout synchronization to be idempotent.
13. Make database changes only through migrations.
14. Provide good OpenAPI schemas because the frontend will generate TypeScript clients from FastAPI's OpenAPI specification.
15. Maintain strong typing across schemas, services, and database access.

When generating code for this project, preserve this architecture unless there is a strong technical reason to change it.
