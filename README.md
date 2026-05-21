# Real-Time Analytics & Reporting Platform

Production-ready analytics SaaS built for the Senior Full Stack Engineer assessment. The project includes a Django/DRF backend, Celery workers, Redis-backed realtime updates via Django Channels, and a polished Next.js frontend workspace.

## What’s Included

- Multi-tenant auth with JWT access tokens, refresh token rotation, invite-based onboarding, RBAC, and org isolation
- Event ingestion via API key, CSV upload, and webhook receiver
- Realtime dashboards, widgets, saved queries, public share links, and live websocket refresh hooks
- Threshold alerts with Celery Beat evaluation, email/webhook/in-app delivery, and alert history
- Professional frontend built with Next.js App Router, React Query, Zustand, Tailwind, and Recharts
- Daphne-first ASGI deployment for HTTP + WebSocket support

## Repo Layout

```text
realtime_platform/
├── backend/
│   ├── apps/
│   │   ├── accounts/
│   │   ├── alerts/
│   │   ├── dashboards/
│   │   ├── ingestion/
│   │   └── websockets/
│   ├── common/
│   ├── realtime_platform/
│   ├── .env.example
│   └── Procfile
├── frontend/
│   ├── app/
│   ├── components/
│   ├── hooks/
│   ├── lib/
│   ├── stores/
│   └── .env.example
├── docker-compose.yml
└── requirements.txt
```

## Architecture

Backend follows a layered flow:

`URLs -> Views -> Services -> Repositories -> Models`

Frontend follows a dashboard workspace pattern:

`App Router pages -> React Query data layer -> Zustand workspace state -> Recharts + realtime panels`

## Backend Stack

- Django 4.2
- Django REST Framework
- Django Channels + Daphne
- Celery + Celery Beat
- Redis
- PostgreSQL or SQLite
- Pydantic validation for ingestion payloads

## Frontend Stack

- Next.js 14 App Router
- React 18 + TypeScript
- Tailwind CSS
- TanStack Query
- Zustand
- Recharts

## Quick Start

### 1. Install backend dependencies

```bash
pip install -r requirements.txt
```

### 2. Start local infra

```bash
docker compose up -d redis postgres
```

If you prefer SQLite locally, keep `DB_ENGINE=sqlite` and only start Redis.

### 3. Configure backend environment

```bash
cd backend
cp .env.example .env
```

Important defaults:

- `DB_ENGINE=sqlite` works immediately for local development
- switch to `DB_ENGINE=postgres` to use the Docker Postgres service
- `REDIS_URL=redis://127.0.0.1:6379/0`
- `FRONTEND_URL=http://localhost:3000`

### 4. Run backend setup

```bash
cd backend
python manage.py migrate
python manage.py createsuperuser
```

### 5. Run backend services

Use Daphne, not gunicorn. This project serves WebSockets and must run as ASGI.

Terminal 1:

```bash
cd backend
daphne -b 0.0.0.0 -p 8000 realtime_platform.asgi:application
```

Terminal 2:

```bash
cd backend
celery -A realtime_platform worker --loglevel=info
```

Terminal 3:

```bash
cd backend
celery -A realtime_platform beat --loglevel=info
```

### 6. Install frontend dependencies

```bash
cd frontend
npm install
```

### 7. Configure frontend environment

```bash
cd frontend
cp .env.example .env.local
```

Two useful modes:

- Mock demo mode: keep `NEXT_PUBLIC_USE_MOCK_DATA=true`
- Live API mode: set `NEXT_PUBLIC_USE_MOCK_DATA=false` and provide:
  - `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`
  - `NEXT_PUBLIC_WS_BASE_URL=ws://localhost:8000`
  - `NEXT_PUBLIC_ACCESS_TOKEN=<jwt access token>`
  - `NEXT_PUBLIC_ORG_SLUG=<organization slug>`

### 8. Run frontend

```bash
cd frontend
npm run dev
```

Frontend runs at `http://localhost:3000`.

## Deployment Notes

### Daphne

Use the included [backend/Procfile](/c:/projects/realtime_platform/backend/Procfile) for process definitions:

- `web`: Daphne ASGI server
- `worker`: Celery worker
- `beat`: Celery Beat scheduler

Recommended production topology:

1. Daphne behind Nginx or a managed reverse proxy
2. Redis for both Celery and Channels
3. Separate worker and beat processes
4. PostgreSQL for production persistence

## API Highlights

### Auth

- `POST /api/v1/auth/register/`
- `POST /api/v1/auth/login/`
- `POST /api/v1/auth/refresh/`
- `POST /api/v1/auth/logout/`
- `GET /api/v1/auth/me/`
- `POST /api/v1/auth/invite/accept/`

### Organization and API Keys

- `GET /api/v1/org/`
- `GET /api/v1/org/members/`
- `POST /api/v1/org/members/invite/`
- `GET /api/v1/api-keys/`
- `POST /api/v1/api-keys/`
- `POST /api/v1/api-keys/<uuid>/rotate/`

### Ingestion

- `POST /api/v1/ingest/events/`
- `POST /api/v1/ingest/batch/`
- `POST /api/v1/ingest/webhook/<source_uuid>/`
- `POST /api/v1/ingest/csv/`
- `GET /api/v1/ingest/query/events/`
- `GET /api/v1/ingest/query/event-names/`
- `GET /api/v1/ingest/query/timeseries/`

### Dashboards

- `GET /api/v1/dashboards/overview/`
- `GET /api/v1/dashboards/templates/`
- `GET/POST /api/v1/dashboards/`
- `POST /api/v1/dashboards/<uuid>/share/`
- `GET /api/v1/dashboards/public/<token>/`

### Alerts

- `GET/POST /api/v1/alerts/rules/`
- `POST /api/v1/alerts/rules/<uuid>/mute/`
- `GET /api/v1/alerts/history/`
- `GET/POST /api/v1/alerts/channels/`

## WebSocket Endpoints

Pass the JWT access token as `?token=<access_token>`.

- `ws://localhost:8000/ws/dashboards/<dashboard_uuid>/`
- `ws://localhost:8000/ws/alerts/`
- `ws://localhost:8000/ws/events/stream/`

Events pushed by the backend include:

- `event.new`
- `dashboard.refresh`
- `alert.triggered`
- `alert.notification`

## Example Payloads

### Single event

```json
{
  "event_name": "page_view",
  "properties": {
    "path": "/pricing",
    "plan": "growth"
  }
}
```

### Batch event ingestion

```json
{
  "events": [
    {
      "event_name": "signup_clicked",
      "properties": {
        "cta": "hero"
      }
    },
    {
      "event_name": "checkout_started",
      "properties": {
        "cart_value": 149.0
      }
    }
  ]
}
```

### Webhook batch

```json
{
  "events": [
    {
      "event_name": "deploy_completed",
      "properties": {
        "service": "billing"
      }
    },
    {
      "event_name": "api_error",
      "properties": {
        "status_code": 502
      }
    }
  ]
}
```

## Backend Improvements Made

- Removed hard-coded production-style database defaults from settings
- Switched local development to safe env-driven config with SQLite fallback
- Added webhook ingestion secured by source-level secrets
- Added Pydantic-backed event validation for single and batch ingestion
- Added dashboard overview and dashboard template endpoints for a richer frontend
- Added Docker Compose for Redis/Postgres local setup
- Added Daphne process config for production-style ASGI deployment
- Added backend tests for ingestion validation and dashboard overview

## Frontend Experience

The new frontend is not a placeholder landing page. It includes:

- KPI overview cards
- Searchable dashboard gallery
- Live event stream panel
- Alert posture and recent history section
- Timeseries + top event visualizations
- Starter dashboard template gallery
- Public shared dashboard route at `/public/[token]`
- Mock mode support for quick demos without backend auth setup

## Validation

Backend validation completed locally:

```bash
cd backend
python manage.py check
python manage.py test apps.ingestion apps.dashboards
```

Frontend build was scaffolded but not executed in this pass because dependencies were not yet installed in the workspace.
