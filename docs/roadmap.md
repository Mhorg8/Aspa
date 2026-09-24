# ASPA Product Roadmap

This roadmap defines the planned development phases for **ASPA**, a mobile-first fitness and wellness application focused on workout planning, workout tracking, progress analytics, nutrition, and Iran-specific user needs.

The goal is to keep the product focused, ship a usable MVP quickly, and only add complexity when the previous phase is stable.

---

## Phase 0 — Product Definition and Project Foundation

**Status: In progress — backend foundation complete; frontend and remaining product work pending.**

Checklist legend: `[x]` is implemented and verified in this repository. `[ ]` is
pending or cannot yet be verified.

### Goal

Create the technical and product foundation before feature development begins.

### Product Requirements

- [x] Define the MVP scope. See **MVP Definition** below.
- [x] Define primary target users: Persian-speaking fitness and wellness users in Iran.
- [x] Define the core user journey. See **MVP Definition** below.
- [ ] Finalize product naming and branding direction. The ASPA name is selected;
      the branding direction is not documented yet.
- [x] Define Persian-first and RTL UX requirements throughout the roadmap.
- [x] Define supported platforms:
  - [x] Android first.
  - [x] iOS support planned from the beginning.
- [ ] Define the initial analytics event taxonomy and event properties.
- [ ] Consolidate privacy and data-handling rules into an approved policy.
      Individual privacy requirements exist in later phases.
- [ ] Define measurable success targets for MVP and beta.

### Frontend

- [ ] Create the React Native + Expo project.
- [ ] Configure TypeScript.
- [ ] Configure Expo Router.
- [ ] Configure Persian and RTL support.
- [ ] Create the base design system:
  - [ ] colors
  - [ ] typography
  - [ ] spacing
  - [ ] buttons
  - [ ] inputs
  - [ ] cards
  - [ ] dialogs
  - [ ] loading states
  - [ ] error states
- [ ] Configure:
  - [ ] TanStack Query
  - [ ] Zustand
  - [ ] React Hook Form
  - [ ] Zod
- [ ] Configure environment handling.
- [ ] Add development, staging, and production configurations.
- [ ] Create the initial navigation structure.

### Backend

- [x] Create the FastAPI project.
- [x] Use the agreed modular-monolith structure.
- [x] Configure:
  - [x] FastAPI
  - [x] Pydantic
  - [x] pydantic-settings
  - [x] SQLAlchemy 2.x
  - [x] asyncpg
  - [x] Alembic
  - [x] PostgreSQL
  - [x] Redis
- [x] Create application configuration and environment handling.
- [x] Use the shared API prefix `/api`.
- [x] Add health endpoints:
  - [x] `/health` liveness endpoint.
  - [x] `/ready` readiness endpoint with PostgreSQL and Redis checks.
- [x] Configure structured JSON logging.
- [x] Configure global exception handling.
- [x] Create the initial async database connection layer.
- [x] Create and verify the initial Alembic migration setup.
- [x] Configure OpenAPI with API and error schemas.
- [x] Define a consistent API error response format.

### DevOps / Infrastructure

- [x] Create the main repository.
- [ ] Configure branch protection in the Git hosting platform.
- [x] Configure backend CI for pushes and pull requests.
- [x] Add:
  - [x] Ruff linting
  - [x] Ruff formatting checks
  - [x] strict Pyright type checking
  - [x] unit and integration tests
  - [x] Docker image build validation
- [x] Create the backend Dockerfile with locked dependencies and a non-root user.
- [x] Create local Docker Compose services for:
  - [x] PostgreSQL
  - [x] Redis
  - [x] backend
- [x] Create isolated PostgreSQL and Redis integration-test services.
- [x] Create `.env.example` without real secrets.
- [x] Define local, test, staging, and production configuration templates.
- [x] Create basic deployment and rollback documentation.

### Testing Requirements

- [ ] Frontend must build successfully. No frontend project exists yet.
- [x] Backend starts successfully in Docker.
- [x] Database migrations run successfully and have no detected schema drift.
- [ ] CI must pass on pull requests. The workflow is configured, but no remote CI run
      is available in this repository yet.
- [x] `/health` and `/ready` return healthy status in the running stack.
- [x] Backend quality gates pass locally: Ruff, formatting, Pyright, and 29 tests.

### Exit Criteria

Phase 0 is complete when:

- [ ] Both developers have confirmed they can run the project locally.
- [ ] The mobile application can communicate with FastAPI. The frontend is pending.
- [x] PostgreSQL and Redis are available locally through Docker Compose.
- [x] Backend CI is configured to run automatically on pushes and pull requests.
- [x] Backend project structure, architecture, and deployment are documented.

---

# Phase 1 — Authentication and User Foundation

### Goal

Allow users to register, authenticate, and maintain a basic ASPA profile.

### Product Requirements

Users must be able to:

- enter an Iranian phone number
- request an OTP
- verify the OTP
- create an account
- stay signed in
- log out
- edit basic profile information

### Frontend

Create:

- splash screen
- onboarding screen
- phone-number login screen
- OTP verification screen
- basic profile setup
- profile screen
- logout flow

Requirements:

- Persian phone-number validation
- loading states
- OTP resend timer
- API error handling
- secure token storage
- automatic session restoration
- RTL-compatible forms
- keyboard-safe layouts

### Backend

Create modules:

```text
auth/
users/
```

Authentication features:

- Iranian phone-number normalization
- OTP generation
- OTP expiration
- OTP retry limits
- OTP rate limiting
- Redis-backed OTP storage
- access tokens
- refresh tokens
- logout / refresh-token invalidation
- authenticated-user dependency

User features:

- create user
- read current user
- update user profile
- account status

Initial user fields may include:

```text
id
phone_number
display_name
birth_date
gender
height
weight
created_at
updated_at
```

Only collect fields actually needed by the product.

### Infrastructure

- Connect SMS provider abstraction.
- Use a fake/local SMS provider for development.
- Configure secrets for staging.
- Add Redis monitoring.

### Security Requirements

- OTPs must expire.
- OTP attempts must be rate-limited.
- Tokens must not be logged.
- Refresh tokens must be handled securely.
- Secrets must come from environment/secrets management.
- User enumeration should be minimized.

### Testing Requirements

Backend:

- request OTP
- invalid phone number
- expired OTP
- invalid OTP
- successful login
- token refresh
- authenticated request
- unauthorized request

Frontend:

- login happy path
- incorrect OTP
- expired OTP
- reconnect after app restart

### Exit Criteria

A new user can install ASPA, authenticate using a phone number, create a profile, close the app, reopen it, and remain authenticated.

---

# Phase 2 — Exercise Library

### Goal

Create the core exercise database used by workout plans and workout tracking.

### Product Requirements

Users must be able to:

- browse exercises
- search exercises
- filter by muscle group
- filter by equipment
- view exercise details

Administrators must eventually be able to maintain the exercise catalog.

### Frontend

Create:

- exercise list
- search
- filter UI
- exercise detail screen
- exercise image/video support
- muscle and equipment labels
- reusable exercise selector

Exercise detail should support:

- Persian name
- English name
- instructions
- primary muscles
- secondary muscles
- equipment
- media

### Backend

Create modules:

```text
exercises/
```

Entities:

```text
Exercise
MuscleGroup
Equipment
ExerciseMuscle
```

Example fields:

```text
exercise

id
name_fa
name_en
description_fa
description_en
equipment_id
difficulty
image_key
video_key
is_active
created_at
updated_at
```

Endpoints:

```text
GET /api/exercises
GET /api/exercises/{id}
GET /api/muscle-groups
GET /api/equipment
```

Support:

- pagination
- search
- filtering
- sorting

### Storage Requirements

Use S3-compatible storage for:

- exercise images
- exercise videos

Do not store large media directly in PostgreSQL.

### Testing Requirements

- pagination
- search
- filtering
- invalid exercise ID
- inactive exercise behavior

### Exit Criteria

Users can efficiently browse, search, filter, and inspect the exercise catalog.

---

# Phase 3 — Workout Plan Builder

### Goal

Allow users to create reusable training routines.

### Product Requirements

Users must be able to:

- create a workout plan
- add training days
- add exercises
- configure sets
- configure rep targets
- configure rest times
- reorder exercises
- edit plans
- duplicate plans
- archive/delete plans

### Frontend

Create:

- workout plans list
- create-plan flow
- training-day editor
- exercise selector
- exercise reorder UI
- set/rep editor
- rest-time editor
- plan detail screen
- edit plan screen

Example:

```text
Push Day

Bench Press
4 × 8-10
Rest: 120 sec

Incline Dumbbell Press
3 × 10-12
Rest: 90 sec
```

### Backend

Create module:

```text
workout_plans/
```

Entities:

```text
WorkoutPlan
WorkoutPlanDay
WorkoutPlanExercise
```

Required functionality:

- CRUD workout plans
- CRUD training days
- add/remove exercises
- exercise ordering
- duplicate workout plan
- ownership validation

### Validation Requirements

- Users must not modify another user's plan.
- Sets must be positive.
- Rep ranges must be valid.
- Rest time must be bounded.
- Invalid exercise references must be rejected.

### Testing Requirements

- create plan
- edit plan
- reorder exercise
- duplicate plan
- unauthorized plan access
- invalid exercise

### Exit Criteria

A user can create and save a complete weekly training routine.

---

# Phase 4 — Live Workout Tracking

### Goal

Deliver the core ASPA experience: actually performing and recording workouts.

This is the most important MVP phase.

### Product Requirements

Users must be able to:

- start a workout
- choose a workout plan or start an empty workout
- log sets
- log reps
- log weight
- optionally log RPE/RIR
- mark sets complete
- use a rest timer
- add exercises during a workout
- remove exercises
- finish a workout
- cancel a workout
- see previous performance

### Frontend

Create the active workout experience.

Features:

- active workout screen
- exercise sections
- add set
- remove set
- edit reps
- edit weight
- RPE/RIR input
- completed-set state
- rest timer
- workout duration timer
- previous workout values
- add exercise
- replace exercise
- finish workout confirmation
- cancel workout confirmation

### Offline Requirements

Workout tracking must be offline-first.

Use local SQLite storage.

During an active workout:

```text
User action
   ↓
SQLite
   ↓
UI update
   ↓
Sync queue
   ↓
FastAPI
```

A temporary network failure must not lose workout data.

### Backend

Create module:

```text
workouts/
```

Entities:

```text
Workout
WorkoutExercise
WorkoutSet
```

Suggested fields:

```text
Workout

id
client_id
user_id
workout_plan_id
started_at
completed_at
duration_seconds
status
created_at
updated_at
```

```text
WorkoutSet

id
client_id
workout_exercise_id
set_number
weight
reps
rpe
rir
completed_at
```

### Sync Requirements

Mobile-generated `client_id` values should be used for idempotency.

Repeated synchronization of the same workout must not create duplicates.

Support:

```text
POST /api/workouts
PATCH /api/workouts/{id}
POST /api/workouts/{id}/complete
GET /api/workouts
GET /api/workouts/{id}
```

Potentially add a dedicated sync endpoint if needed.

### Testing Requirements

Test:

- online workout
- temporary network failure
- app background/foreground
- sync retry
- duplicate sync attempt
- editing sets
- completing workout
- cancelling workout
- previous performance retrieval

### Exit Criteria

A user can complete an entire workout with no internet connection and the workout safely synchronizes when connectivity returns.

---

# Phase 5 — Progress and Workout Analytics

### Goal

Give users a reason to return by showing measurable improvement.

### Product Requirements

Users should see:

- workout history
- exercise history
- personal records
- training volume
- workout frequency
- estimated 1RM
- body-weight history
- progress trends

### Frontend

Create:

- workout history screen
- workout detail/history view
- progress dashboard
- exercise progress screen
- PR indicators
- charts
- body-weight chart

Example metrics:

```text
Weekly workouts
Weekly training volume
Bench press progress
Estimated 1RM
Personal records
Workout duration
```

### Backend

Create module:

```text
analytics/
```

Initial analytics can be calculated using PostgreSQL.

Do not introduce ClickHouse yet.

Endpoints may include:

```text
GET /api/analytics/overview
GET /api/analytics/exercises/{id}
GET /api/analytics/volume
GET /api/analytics/personal-records
```

Implement:

- volume calculations
- estimated 1RM
- PR detection
- weekly training frequency
- exercise history

### Performance Requirements

- Avoid N+1 queries.
- Add indexes based on real query patterns.
- Paginate history endpoints.
- Cache expensive queries only when needed.

### Testing Requirements

Validate analytics calculations with deterministic test data.

### Exit Criteria

A user can clearly see whether their training performance is improving.

---

# Phase 6 — Body Progress Tracking

### Goal

Allow users to track physical changes alongside workout performance.

### Product Requirements

Users must be able to log:

- weight
- waist
- chest
- arms
- hips
- thighs
- optional custom measurements
- progress photos

### Frontend

Create:

- measurement entry
- measurement history
- body-weight chart
- progress photo capture/upload
- progress photo timeline

### Backend

Create/update module:

```text
progress/
```

Entities:

```text
BodyMeasurement
ProgressPhoto
```

Store photo files in S3-compatible object storage.

PostgreSQL should store:

```text
object_key
measurement_date
metadata
```

not image binaries.

### Privacy Requirements

Progress photos must be private by default.

Use authenticated or signed access.

Never expose predictable public object paths for private media.

### Exit Criteria

Users can track body changes securely over time.

---

# Phase 7 — Nutrition MVP

### Goal

Add basic calorie and macronutrient tracking without turning ASPA into an oversized nutrition platform.

### Product Requirements

Users must be able to:

- search food
- log food
- create meals
- view daily calories
- view protein
- view carbohydrates
- view fat

### Iran-Specific Requirement

The food catalog should prioritize:

- common Iranian meals
- Iranian breads
- Iranian dairy
- Iranian packaged foods
- local serving units
- common Persian search terms

Examples:

```text
سنگک
بربری
قرمه سبزی
قیمه
جوجه کباب
کباب کوبیده
عدس پلو
ماست
دوغ
```

### Frontend

Create:

- nutrition dashboard
- food search
- food details
- meal logging
- daily macro summary
- recent foods
- favorite foods

### Backend

Create modules:

```text
foods/
nutrition/
```

Entities:

```text
Food
FoodServing
NutritionDay
Meal
MealItem
```

Example food fields:

```text
name_fa
name_en
brand
barcode
serving_size
serving_unit
calories
protein
carbohydrates
fat
fiber
source
```

### Exit Criteria

Users can track basic daily nutrition with useful Iranian food coverage.

---

# Phase 8 — Beta Readiness

### Goal

Prepare ASPA for a controlled group of real users.

### Product Requirements

Before beta:

- no critical workout-data-loss bugs
- onboarding must be understandable
- core APIs must be stable
- basic privacy policy must exist
- user feedback mechanism must exist

### Frontend

Add:

- onboarding improvements
- empty states
- skeleton loaders
- consistent error handling
- crash reporting
- feedback flow
- update-required flow
- network-status handling
- polished Persian copy

### Backend

Add:

- request IDs
- audit logging where appropriate
- stricter rate limiting
- account deletion
- user data export strategy
- production logging
- database backups
- API metrics
- background-job monitoring

### Observability

Add:

- Prometheus
- Grafana
- Loki
- OpenTelemetry where valuable
- error tracking

Monitor:

```text
API latency
5xx errors
login failures
OTP failures
workout sync failures
database connections
Redis availability
worker failures
```

### Beta Testing Requirements

Run testing with real users.

Track:

- onboarding completion
- first workout creation
- first workout completion
- workout-sync success
- 7-day retention
- crashes
- user feedback

### Exit Criteria

A small group of users can use ASPA for several weeks without critical data-loss or stability problems.

---

# Phase 9 — Public MVP Launch

### Goal

Release the first production-ready version of ASPA.

### MVP Scope

The launch version should contain:

```text
Authentication
User profile

Exercise library

Workout plan builder

Live workout tracking
Offline workout support

Workout history

Progress analytics

Body measurements

Basic nutrition

Persian / RTL experience
```

Do not delay launch for advanced features.

### Frontend

Production requirements:

- app icon
- splash assets
- screenshots
- store listing
- privacy links
- production analytics
- crash reporting
- stable update mechanism

### Backend

Production requirements:

- production migrations
- automated backups
- secure secrets
- proper CORS policy
- HTTPS only
- rate limiting
- monitoring
- alerts
- worker health monitoring
- database performance monitoring

### Infrastructure

Production should support at minimum:

```text
Load Balancer / Reverse Proxy

FastAPI
FastAPI Worker(s)

PostgreSQL
Redis

Background Worker

S3-compatible storage
```

Kubernetes can be used if operationally justified, but the application architecture must not depend on Kubernetes.

### Exit Criteria

ASPA is available to public users and all core user journeys are monitored.

---

# Phase 10 — Retention and Engagement

### Goal

Increase long-term usage after validating the MVP.

Possible features:

### Frontend

- workout streaks
- achievements
- training reminders
- nutrition reminders
- weekly summaries
- goals
- home-screen personalization
- challenge UI
- notification settings

### Backend

Add:

- goals
- achievements
- streak calculation
- scheduled notifications
- weekly summaries
- notification preferences

### Requirements

Do not add gamification until real usage data shows which behaviors should be encouraged.

### Exit Criteria

Retention features are based on observed user behavior rather than assumptions.

---

# Phase 11 — Health Platform Integration

### Goal

Connect ASPA with phone and wearable health ecosystems.

### Android

Integrate:

```text
Health Connect
```

Potential data:

- steps
- body weight
- heart rate
- workouts
- calories
- sleep

### iOS

Integrate:

```text
Apple HealthKit
```

### Frontend

Create:

- health permission screens
- data-source settings
- health-sync status
- permission explanation
- sync-error handling

### Backend

Add health-data ingestion models where server-side storage is necessary.

Do not upload health data unless ASPA actually needs it.

### Privacy Requirements

- explicit user consent
- minimum necessary permissions
- clear explanation of data use
- easy disconnect/revoke flow

### Exit Criteria

Users can optionally connect supported health sources without affecting normal ASPA usage.

---

# Phase 12 — Subscription and Monetization

### Goal

Introduce monetization only after the core product provides enough value.

Possible paid features:

- advanced analytics
- premium workout plans
- advanced nutrition features
- AI recommendations
- coach-created programs
- premium progress insights

### Frontend

Create:

- pricing
- premium feature indicators
- subscription management
- purchase flow
- payment states
- invoice/payment history where needed

### Backend

Create/update:

```text
subscriptions/
payments/
```

Support:

- plans
- subscriptions
- payment sessions
- payment verification
- webhooks
- subscription expiration
- entitlement checks

### Iran-Specific Requirements

Support appropriate Iranian payment providers.

Payment provider logic must be isolated behind an integration interface.

### Exit Criteria

Payments are idempotent, validated server-side, monitored, and users receive the correct entitlements.

---

# Phase 13 — AI and Personalization

### Goal

Use user data to make ASPA more useful without making AI a requirement for the basic product.

Potential features:

- workout-plan generation
- workout progression recommendations
- exercise replacement suggestions
- nutrition suggestions
- weekly summaries
- plateau detection
- personalized coaching

### Backend

Add AI services behind a clear abstraction.

Example:

```text
FastAPI
   ↓
Recommendation Service
   ↓
AI Provider / Models
```

AI output must be validated before being stored or used.

### Frontend

AI should appear as assistance, not unexplained automation.

Users should be able to:

- review
- edit
- accept
- reject

AI-generated plans.

### Requirements

Do not allow an LLM to directly modify critical user data without explicit confirmation.

### Exit Criteria

AI features improve measurable user outcomes or engagement instead of existing only as a marketing feature.

---

# Phase 14 — Advanced Analytics and Scale

### Goal

Introduce specialized infrastructure only when real scale requires it.

Possible changes:

- ClickHouse for event/product analytics
- read replicas
- dedicated workers
- CDN for exercise media
- more aggressive caching
- search engine
- service extraction

### Backend Requirements

Before introducing a new system, identify a measurable bottleneck.

Examples:

```text
PostgreSQL analytics query too slow
→ evaluate ClickHouse

Exercise search limitations
→ evaluate OpenSearch

API module independently scaling
→ consider service extraction
```

Do not introduce infrastructure only because it may be useful later.

### Architecture Principle

Scale based on measurements.

Do not automatically move from:

```text
modular monolith
```

to:

```text
microservices
```

because the user count increases.

Extract services only where operational or organizational boundaries justify it.

---

# Cross-Phase Engineering Requirements

These rules apply throughout the project.

## Backend

- Use FastAPI.
- Use async SQLAlchemy correctly.
- Use Alembic for schema changes.
- Use PostgreSQL as the primary source of truth.
- Use Redis only for temporary/fast state.
- Keep routers thin.
- Put business logic in services.
- Use repositories only when useful.
- Keep modules domain-oriented.
- Maintain API versioning.
- Maintain backward compatibility where practical.
- Use pagination for list endpoints.
- Use database indexes intentionally.
- Validate ownership on user resources.
- Use idempotency for retryable operations.
- Do not store large media in PostgreSQL.

## Frontend

- Use React Native + Expo.
- Use TypeScript.
- Design Persian/RTL first.
- Use TanStack Query for server state.
- Use Zustand for local UI/application state.
- Use SQLite where offline persistence is required.
- Handle loading, empty, offline, and error states.
- Avoid duplicated backend models by generating or deriving frontend API types from OpenAPI when practical.
- Keep feature code grouped by domain.

## Security

- Never commit secrets.
- Use HTTPS in production.
- Rate-limit sensitive endpoints.
- Protect private user data.
- Encrypt traffic.
- Validate all server-side input.
- Do not trust frontend authorization checks.
- Log security-relevant events without leaking secrets.
- Apply least privilege to infrastructure credentials.

## Observability

At minimum monitor:

- availability
- API error rate
- latency
- database health
- Redis health
- background-job failures
- authentication failures
- workout-sync failures

## CI Requirements

Every pull request should run:

### Backend

```bash
uv run ruff check .
uv run ruff format --check .
uv run pyright
uv run pytest
```

### Frontend

```bash
npm run lint
npm run typecheck
npm run test
```

Add build validation where appropriate.

---

# Suggested Release Sequence

```text
Phase 0
Foundation

Phase 1
Authentication + Users

Phase 2
Exercise Library

Phase 3
Workout Plan Builder

Phase 4
Live Workout Tracking

Phase 5
Workout Analytics

Phase 6
Body Progress

Phase 7
Nutrition MVP

Phase 8
Private Beta

Phase 9
Public MVP

Phase 10
Retention

Phase 11
Health Integrations

Phase 12
Subscriptions

Phase 13
AI / Personalization

Phase 14
Advanced Scale
```

---

# MVP Definition

The MVP is complete when a Persian-speaking user can:

1. Register using a phone number.
2. Create a profile.
3. Browse exercises.
4. Create a workout routine.
5. Start a workout.
6. Track sets, reps, and weight.
7. Finish the workout even with unreliable connectivity.
8. View workout history.
9. View basic performance analytics.
10. Track body weight and measurements.
11. Log basic nutrition.
12. Use the entire core flow comfortably in Persian and RTL.

Anything beyond this should be justified by user feedback, retention data, or business needs.
