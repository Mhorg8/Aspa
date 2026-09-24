# ASPA Tech Stack

ASPA is a mobile-first fitness and wellness app for Iranian users, focused on workout planning, tracking, progress analytics, nutrition, and more... .

## Mobile

* React Native
* Expo
* TypeScript
* Expo Router
* TanStack Query
* Zustand
* SQLite for offline workout tracking

## Web / Admin

* Next.js
* TypeScript
* Tailwind CSS
* shadcn/ui

Used for the admin dashboard, landing page, content management, and future web features.

## Backend

* Python
* FastAPI
* Pydantic
* SQLAlchemy
* Alembic
* REST API

FastAPI will provide the main API for both the mobile app and admin panel.

## Data

* PostgreSQL — primary database
* Redis — caching, OTP, rate limiting, and background jobs
* Ceph S3 / MinIO — images, videos, and progress photos

## Background Processing

* Celery or Dramatiq
* Redis as the message broker

Used for notifications, analytics processing, media processing, and other asynchronous tasks.

## Infrastructure

* Docker
* Kubernetes when scaling requires it
* Nginx / Traefik
* CI/CD with GitHub Actions

## Monitoring

* Prometheus
* Grafana
* Loki
* OpenTelemetry

## Future Integrations

* Iranian SMS/OTP providers
* Iranian payment gateways
* Requset workout routines from verified coaches

## Architecture

```text
React Native / Expo
        │
        ▼
     FastAPI
        │
 ┌──────┼───────┐
 ▼      ▼       ▼
Postgres Redis  S3/Ceph
```

The initial architecture should remain a **modular monolith** rather than microservices to keep development and operations simple.
