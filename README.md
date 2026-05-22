# Real-Time Analytics & Reporting Platform

A production-ready analytics SaaS built for a Senior Full Stack Engineer assessment. Think a lightweight Mixpanel or Metabase — organizations can ingest events from multiple sources, build custom dashboards, set threshold alerts, and get live WebSocket updates as data flows in.

**Live demo:** https://realtime-platform-indol.vercel.app  
**Backend:** https://realtime-platform.onrender.com

---

## What's Built

**Auth & Multi-Tenancy**
JWT access tokens with refresh token rotation (HTTP-only cookie), invite-based team onboarding, and a four-level role hierarchy (Owner → Admin → Analyst → Viewer). Every query is scoped to the organization at the DB layer — no data leaks between tenants.

**Event Ingestion**
Single events, batch events, CSV uploads, and webhook receivers. All payloads go through Pydantic validation before hitting the DB. API keys are per-org and can be rotated or revoked independently.

**Dashboards**
Create dashboards, attach widgets, configure time ranges, and share via a public token. Dashboard templates cover common use cases out of the box. Auto-refresh is configurable.

**Alerts**
Define threshold rules (e.g. "error_rate > 5% for 10 minutes"), evaluated by Celery Beat on a schedule. Notifications go out via in-app, email, or webhook. Rules can be muted and the full trigger history is queryable.

**Real-Time**
WebSocket connections for live dashboard refresh, alert push notifications, and a live event stream tail — all authenticated via JWT query param.

---

## Project Structure

```
realtime_platform/
├── backend/
│   ├── apps/
│   │   ├── accounts/       # auth, users, orgs, API keys
│   │   ├── alerts/         # rules, channels, history
│   │   ├── dashboards/     # dashboards, widgets, templates
│   │   ├── ingestion/      # events, batch, CSV, webhooks
│   │   └── websockets/     # channels consumers
│   ├── common/
│   ├── realtime_platform/  # settings, urls, asgi
│   ├── .env.example
│   └── Procfile
├── frontend/
│   ├── app/                # Next.js App Router pages
│   ├── components/
│   ├── hooks/
│   ├── lib/
│   ├── stores/             # Zustand
│   └── .env.example
├── docker-compose.yml
└── requirements.txt
```

---

## Architecture

The backend follows a clean layered pattern — nothing in the views does business logic, nothing in the services touches HTTP:

```
URLs → Views → Services → Repositories → Models
```

Frontend is built around a dashboard workspace pattern:

```
App Router pages → React Query (data) → Zustand (workspace state) → Recharts + realtime panels
```

---

## Tech Stack

| Layer | Tools |
|---|---|
| Backend framework | Django 4.2 + Django REST Framework |
| Real-time | Django Channels + Daphne (ASGI) |
| Task queue | Celery + Celery Beat |
| Cache / broker | Redis |
| Database | PostgreSQL (prod) / SQLite (local dev) |
| Validation | Pydantic v2 |
| Frontend | Next.js 14 App Router, React 18, TypeScript |
| Styling | Tailwind CSS |
| State | Zustand |
| Data fetching | TanStack Query (React Query) |
| Charts | Recharts |

---

## Local Setup

### 1. Install backend dependencies

```bash
pip install -r requirements.txt
```

### 2. Start infrastructure

```bash
docker compose up -d redis postgres
```

SQLite works fine for local dev — if you want to skip Postgres, set `DB_ENGINE=sqlite` and only start Redis.

### 3. Configure the backend

```bash
cd backend
cp .env.example .env
```

Key vars to check:

```
DB_ENGINE=sqlite          # or postgres
REDIS_URL=redis://127.0.0.1:6379/0
FRONTEND_URL=http://localhost:3000
```

### 4. Migrate and create a superuser

```bash
cd backend
python manage.py migrate
python manage.py createsuperuser
```

### 5. Start backend services

The project uses WebSockets, so it must run as ASGI via Daphne — not gunicorn.

```bash
# Terminal 1 — ASGI server
daphne -b 0.0.0.0 -p 8000 realtime_platform.asgi:application

# Terminal 2 — Celery worker
celery -A realtime_platform worker --loglevel=info

# Terminal 3 — Celery beat (alert evaluation, scheduled tasks)
celery -A realtime_platform beat --loglevel=info
```

### 6. Frontend setup

```bash
cd frontend
npm install
cp .env.example .env.local
```

Two modes:

- **Mock demo** (no backend needed): keep `NEXT_PUBLIC_USE_MOCK_DATA=true`
- **Live API**: set `NEXT_PUBLIC_USE_MOCK_DATA=false` and fill in:

```
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_WS_BASE_URL=ws://localhost:8000
NEXT_PUBLIC_ACCESS_TOKEN=<your jwt>
NEXT_PUBLIC_ORG_SLUG=<your org slug>
```

```bash
npm run dev
# → http://localhost:3000
```

---

## Deployment

The `backend/Procfile` defines three processes:

```
web:    daphne -b 0.0.0.0 -p $PORT realtime_platform.asgi:application
worker: celery -A realtime_platform worker --loglevel=info
beat:   celery -A realtime_platform beat --loglevel=info
```

Recommended production setup: Daphne behind Nginx or a managed reverse proxy, Redis for both Celery and Channels, separate worker and beat dynos, PostgreSQL for persistence.

---

## API Walkthrough (Verified Requests & Responses)

Everything below was manually tested against the live deployment. Base URL: `https://realtime-platform.onrender.com`

---

### Module 1 — Auth & Multi-Tenancy

#### Register

```bash
curl -X POST https://realtime-platform.onrender.com/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test1234",
    "first_name": "Test",
    "last_name": "User",
    "org_name": "Demo Corp"
  }'
```

```json
{
  "success": true,
  "code": 201,
  "data": {
    "user": {
      "uuid": "c31707ec-1ef1-4927-8afb-1a5f716dc8a1",
      "email": "test@example.com",
      "first_name": "Test",
      "last_name": "User",
      "full_name": "Test User",
      "is_email_verified": false,
      "created_at": "2026-05-22T15:07:11.677460Z"
    },
    "organization": {
      "uuid": "9c7159f7-124b-4d2e-be12-7f10e9ac201f",
      "name": "Demo Corp",
      "slug": "demo-corp",
      "created_at": "2026-05-22T15:07:13.240266Z"
    },
    "access_token": "<jwt>",
    "refresh_token": "<refresh_jwt>"
  },
  "message": "Registration successful."
}
```

> Copy `access_token` → `TOKEN` and `organization.slug` → `ORG` for the requests below.

---

#### Login

```bash
curl -X POST https://realtime-platform.onrender.com/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -c cookies.txt \
  -d '{"email": "test@example.com", "password": "Test1234"}'
```

```json
{
  "success": true,
  "code": 200,
  "data": {
    "user": { "uuid": "c31707ec-...", "email": "test@example.com", "full_name": "Test User" },
    "organization": { "slug": "demo-corp" },
    "access_token": "<jwt>"
  },
  "message": "Login successful."
}
```

---

#### Get Current User

```bash
curl https://realtime-platform.onrender.com/api/v1/auth/me/ \
  -H "Authorization: Bearer $TOKEN"
```

```json
{
  "success": true,
  "code": 200,
  "data": {
    "uuid": "c31707ec-1ef1-4927-8afb-1a5f716dc8a1",
    "email": "test@example.com",
    "full_name": "Test User",
    "is_email_verified": false,
    "created_at": "2026-05-22T15:07:11.677460Z"
  },
  "message": "Request was successful."
}
```

---

#### Refresh Token

```bash
curl -X POST https://realtime-platform.onrender.com/api/v1/auth/refresh/ \
  -b cookies.txt -c cookies.txt
```

```json
{
  "success": true,
  "code": 200,
  "data": { "access_token": "<new_jwt>" },
  "message": "Token refreshed."
}
```

---

#### Organization Details

```bash
curl https://realtime-platform.onrender.com/api/v1/org/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Org-Slug: $ORG"
```

```json
{
  "success": true,
  "code": 200,
  "data": {
    "uuid": "9c7159f7-124b-4d2e-be12-7f10e9ac201f",
    "name": "Demo Corp",
    "slug": "demo-corp",
    "created_at": "2026-05-22T15:07:13.240266Z"
  }
}
```

---

#### Org Members

```bash
curl https://realtime-platform.onrender.com/api/v1/org/members/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Org-Slug: $ORG"
```

```json
{
  "success": true,
  "code": 200,
  "data": [
    {
      "uuid": "a9c6aee0-2ca9-4f1b-a27a-b103a25ebe9a",
      "user": { "email": "test@example.com", "full_name": "Test User" },
      "role": "owner",
      "joined_at": "2026-05-22T15:07:13.284500Z",
      "is_active": true
    }
  ]
}
```

---

#### Invite a Member

```bash
curl -X POST https://realtime-platform.onrender.com/api/v1/org/members/invite/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Org-Slug: $ORG" \
  -H "Content-Type: application/json" \
  -d '{"email": "viewer@example.com", "role": "viewer"}'
```

---

#### Create an API Key

```bash
curl -X POST https://realtime-platform.onrender.com/api/v1/api-keys/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Org-Slug: $ORG" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Key"}'
```

```json
{
  "success": true,
  "code": 201,
  "data": {
    "uuid": "473dd9d5-147c-4373-8d1a-ffa9c0b4ef5c",
    "name": "Test Key",
    "key_prefix": "rpk_gqolzusH",
    "full_key": "rpk_gqolzusHE0b8RW-5Tym4ybhHH-dO83sQAEheqxsC2xrvFjLNMNC86A",
    "expires_at": null,
    "created_at": "2026-05-22T15:13:08.911031Z"
  },
  "message": "Store this key securely — it will not be shown again."
}
```

> Save `full_key` as `API_KEY`. It won't be shown again.

---

### Module 2 — Event Ingestion

#### Single Event

```bash
curl -X POST https://realtime-platform.onrender.com/api/v1/ingest/events/ \
  -H "X-Api-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "event_name": "page_view",
    "properties": {"path": "/pricing", "plan": "growth"}
  }'
```

```json
{
  "success": true,
  "code": 201,
  "data": {
    "id": 1,
    "uuid": "0656d6ce-74d0-4917-be54-542c1ac7e150",
    "event_name": "page_view",
    "properties": {"path": "/pricing", "plan": "growth"},
    "timestamp": "2026-05-22T15:45:52.538349Z",
    "ingested_at": "2026-05-22T15:45:53.094423Z"
  },
  "message": "Event ingested."
}
```

---

#### Batch Events

```bash
curl -X POST https://realtime-platform.onrender.com/api/v1/ingest/batch/ \
  -H "X-Api-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "events": [
      {"event_name": "signup_clicked", "properties": {"cta": "hero"}},
      {"event_name": "checkout_started", "properties": {"cart_value": 149.0}}
    ]
  }'
```

```json
{
  "success": true,
  "code": 201,
  "data": {"ingested": 2, "total": 2},
  "message": "2 events ingested."
}
```

---

#### Query Events

```bash
curl "https://realtime-platform.onrender.com/api/v1/ingest/query/events/?page=1" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Org-Slug: $ORG"
```

```json
{
  "links": {"next": null, "previous": null},
  "count": 3,
  "total_pages": 1,
  "results": [
    {
      "id": 3,
      "uuid": "7a14516e-e638-4a8e-aad2-f6c1c839db80",
      "event_name": "checkout_started",
      "properties": {"cart_value": 149.0},
      "timestamp": "2026-05-22T15:47:46.632332Z"
    },
    {
      "id": 2,
      "uuid": "42fff3e5-8196-4080-8d56-fe57ca95e9c8",
      "event_name": "signup_clicked",
      "properties": {"cta": "hero"},
      "timestamp": "2026-05-22T15:47:46.632300Z"
    },
    {
      "id": 1,
      "uuid": "0656d6ce-74d0-4917-be54-542c1ac7e150",
      "event_name": "page_view",
      "properties": {"path": "/pricing", "plan": "growth"},
      "timestamp": "2026-05-22T15:45:52.538349Z"
    }
  ]
}
```

---

#### CSV Upload

```bash
# Create a test CSV
cat > test_events.csv <<EOF
event_name,path,plan
page_view,/home,free
page_view,/pricing,growth
signup_clicked,/landing,pro
EOF

# Upload it
curl -X POST https://realtime-platform.onrender.com/api/v1/ingest/csv/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Org-Slug: $ORG" \
  -F "file=@test_events.csv"
```

```json
{
  "success": true,
  "code": 201,
  "data": {
    "id": 1,
    "uuid": "10f5b97d-6d3d-44d2-bd9f-1605ace0e5cf",
    "status": "pending",
    "file_name": "test_events.csv",
    "total_records": 0,
    "processed_records": 0,
    "failed_records": 0,
    "created_at": "2026-05-22T15:54:08.034268Z"
  },
  "message": "CSV upload queued for processing."
}
```

---

#### Webhook Ingestion

```bash
# List sources first to get SOURCE_UUID
curl https://realtime-platform.onrender.com/api/v1/ingest/sources/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Org-Slug: $ORG"

# Then post to that source
curl -X POST https://realtime-platform.onrender.com/api/v1/ingest/webhook/$SOURCE_UUID/ \
  -H "Content-Type: application/json" \
  -d '{
    "events": [
      {"event_name": "deploy_completed", "properties": {"service": "billing"}}
    ]
  }'
```

---

#### Timeseries Query

```bash
curl "https://realtime-platform.onrender.com/api/v1/ingest/query/timeseries/?event_name=page_view&interval=hour" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Org-Slug: $ORG"
```

---

### Module 3 — Dashboards

#### Create a Dashboard

```bash
curl -X POST https://realtime-platform.onrender.com/api/v1/dashboards/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Org-Slug: $ORG" \
  -H "Content-Type: application/json" \
  -d '{"name": "My First Dashboard", "description": "Testing dashboard creation"}'
```

```json
{
  "success": true,
  "code": 201,
  "data": {
    "id": 1,
    "uuid": "d3401423-2518-44a5-9110-4d7a7ad5b44b",
    "name": "My First Dashboard",
    "description": "Testing dashboard creation",
    "is_public": false,
    "share_token": null,
    "refresh_interval": 0,
    "layout": [],
    "widget_count": 0,
    "widgets": [],
    "created_at": "2026-05-22T15:56:39.705137Z"
  }
}
```

> Save `uuid` as `DASHBOARD_UUID`.

---

#### Overview KPIs

```bash
curl https://realtime-platform.onrender.com/api/v1/dashboards/overview/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Org-Slug: $ORG"
```

---

#### Dashboard Templates

```bash
curl https://realtime-platform.onrender.com/api/v1/dashboards/templates/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Org-Slug: $ORG"
```

---

#### Create a Public Share Link

```bash
curl -X POST https://realtime-platform.onrender.com/api/v1/dashboards/$DASHBOARD_UUID/share/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Org-Slug: $ORG"
```

```json
{
  "success": true,
  "code": 200,
  "data": {
    "share_token": "IhSmdLbnUr7CELNZGhDL1dGF7zFPJ1jt2rPhMNJqtFU",
    "is_public": true
  }
}
```

Public URL: `https://realtime-platform-indol.vercel.app/public/<share_token>`

---

### Module 4 — Alerts

#### Create an Alert Rule

```bash
curl -X POST https://realtime-platform.onrender.com/api/v1/alerts/rules/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Org-Slug: $ORG" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "High page views",
    "event_name": "page_view",
    "condition": "count",
    "threshold": 1,
    "window_minutes": 60,
    "severity": "warning",
    "condition_operator": "gt",
    "threshold_value": 100
  }'
```

```json
{
  "success": true,
  "code": 201,
  "data": {
    "id": 1,
    "uuid": "31b07ddc-29ed-4d54-acc3-a689e45d43ee",
    "name": "High page views",
    "event_name": "page_view",
    "condition_operator": "gt",
    "threshold_value": 100.0,
    "window_minutes": 60,
    "status": "active",
    "muted_until": null,
    "last_evaluated_at": null,
    "last_triggered_at": null,
    "channels": [],
    "created_at": "2026-05-22T16:01:48.038390Z"
  }
}
```

---

#### Trigger an Alert (send events past the threshold)

```bash
for i in 1 2 3; do
  curl -s -X POST https://realtime-platform.onrender.com/api/v1/ingest/events/ \
    -H "X-Api-Key: $API_KEY" \
    -H "Content-Type: application/json" \
    -d '{"event_name": "page_view", "properties": {"path": "/test"}}'
done
```

Each call returns a `201` with the ingested event. Celery Beat will evaluate the rule on its next run and fire an alert if the count crosses the threshold.

---

#### Alert History

```bash
curl https://realtime-platform.onrender.com/api/v1/alerts/history/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Org-Slug: $ORG"
```

---

#### Mute an Alert Rule

```bash
curl -X POST https://realtime-platform.onrender.com/api/v1/alerts/rules/$RULE_UUID/mute/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Org-Slug: $ORG"
```

---

### Module 5 — WebSockets

All WebSocket connections require the JWT access token as a query param.

```bash
npm install -g wscat

# Live event stream
wscat -c "wss://realtime-platform.onrender.com/ws/events/stream/?token=$TOKEN"

# Dashboard auto-refresh
wscat -c "wss://realtime-platform.onrender.com/ws/dashboards/$DASHBOARD_UUID/?token=$TOKEN"

# Alert notifications
wscat -c "wss://realtime-platform.onrender.com/ws/alerts/?token=$TOKEN"
```

Events pushed by the server:

| Event | When |
|---|---|
| `event.new` | A new event is ingested |
| `dashboard.refresh` | Dashboard data updates |
| `alert.triggered` | An alert rule fires |
| `alert.notification` | In-app notification delivered |

---

### Module 6 — Frontend

Open the live app: https://realtime-platform-indol.vercel.app

| Feature | Where |
|---|---|
| Login / Register | `/login`, `/register` |
| KPI cards | After login |
| Dashboard gallery + search | Workspace |
| Timeseries chart | Select an event name |
| Live event stream panel | Workspace |
| Alert feed | Workspace |
| Public dashboard | `/public/<share_token>` |
| API playground | Workspace (bottom) |

---

## Running Tests

```bash
cd backend
python manage.py check
python manage.py test apps.ingestion apps.dashboards
```

---

## Complete API Reference

### Auth
| Method | Endpoint |
|---|---|
| POST | `/api/v1/auth/register/` |
| POST | `/api/v1/auth/login/` |
| POST | `/api/v1/auth/refresh/` |
| POST | `/api/v1/auth/logout/` |
| GET | `/api/v1/auth/me/` |
| POST | `/api/v1/auth/invite/accept/` |

### Org & API Keys
| Method | Endpoint |
|---|---|
| GET | `/api/v1/org/` |
| GET | `/api/v1/org/members/` |
| POST | `/api/v1/org/members/invite/` |
| GET | `/api/v1/api-keys/` |
| POST | `/api/v1/api-keys/` |
| POST | `/api/v1/api-keys/<uuid>/rotate/` |

### Ingestion
| Method | Endpoint |
|---|---|
| POST | `/api/v1/ingest/events/` |
| POST | `/api/v1/ingest/batch/` |
| POST | `/api/v1/ingest/webhook/<source_uuid>/` |
| POST | `/api/v1/ingest/csv/` |
| GET | `/api/v1/ingest/query/events/` |
| GET | `/api/v1/ingest/query/event-names/` |
| GET | `/api/v1/ingest/query/timeseries/` |

### Dashboards
| Method | Endpoint |
|---|---|
| GET | `/api/v1/dashboards/overview/` |
| GET | `/api/v1/dashboards/templates/` |
| GET, POST | `/api/v1/dashboards/` |
| POST | `/api/v1/dashboards/<uuid>/share/` |
| GET | `/api/v1/dashboards/public/<token>/` |

### Alerts
| Method | Endpoint |
|---|---|
| GET, POST | `/api/v1/alerts/rules/` |
| POST | `/api/v1/alerts/rules/<uuid>/mute/` |
| GET | `/api/v1/alerts/history/` |
| GET, POST | `/api/v1/alerts/channels/` |