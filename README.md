# Real-Time Analytics & Reporting Platform

A production-grade SaaS analytics platform built with Django REST Framework, Celery, Redis, and Django Channels. Think lightweight Mixpanel/Metabase.

---

## Architecture

```
realtime_platform/
├── common/                   # Shared base classes reused across all apps
│   ├── api/base_api_view.py  # BaseAPIView — success/error response helpers
│   ├── auth/jwt_service.py   # JWT access + refresh token management
│   ├── boilerplate/          # Pagination classes
│   ├── decorators/           # @auth_guard, @require_role, @validate_request
│   ├── exceptions.py         # AppException hierarchy + custom exception handler
│   ├── middleware.py         # CorrelationID + RequestLogging middleware
│   ├── models.py             # Abstract BaseModel (uuid, timestamps, soft-delete)
│   ├── permissions.py        # DRF permission classes (role hierarchy)
│   ├── repositories/         # BaseRepository — generic CRUD operations
│   └── service/              # BaseService — response wrapper helpers
│
└── apps/
    ├── accounts/             # Auth, organizations, RBAC, API keys
    ├── ingestion/            # Event ingestion (API/batch/CSV), data sources
    ├── dashboards/           # Dashboards, widgets, saved queries
    ├── alerts/               # Alert rules, notification channels, history
    └── websockets/           # Django Channels consumers (live updates)
```

**Design Pattern:** Routers → Views → Services → Repositories → Models

Each app follows: `models.py` → `repositories.py` → `services.py` → `serializers.py` → `views.py` → `urls.py`

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | Django 4.2 + Django REST Framework |
| Database | PostgreSQL (Aiven cloud) |
| Task Queue | Celery + Redis |
| Scheduler | Celery Beat |
| Real-Time | Django Channels + channels_redis |
| Auth | JWT (python-jose) |
| API Keys | SHA-256 hashed, prefix-lookup |

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your values
```

### 3. Start Redis (required for Celery + Channels)

```bash
docker-compose up redis -d
# or: docker run -p 6379:6379 redis:7-alpine
```

### 4. Run migrations

```bash
python manage.py migrate
python manage.py createsuperuser
```

### 5. Start all processes with tmux

Use tmux to run each process in a separate pane/window so they all stay alive:

```bash
# Create a new tmux session
tmux new-session -s platform

# Pane 1 — ASGI server (HTTP + WebSockets)
daphne -b 0.0.0.0 -p 8000 realtime_platform.asgi:application

# Split and open Pane 2 — Celery worker
# Ctrl+B then % (vertical split) or " (horizontal split)
celery -A realtime_platform worker --loglevel=info --concurrency=4

# Pane 3 — Celery Beat (alert evaluation, scheduled reports)
celery -A realtime_platform beat --loglevel=info
```

**Quick tmux cheatsheet:**
- `Ctrl+B %` — vertical split
- `Ctrl+B "` — horizontal split
- `Ctrl+B <arrow>` — switch pane
- `Ctrl+B d` — detach (session keeps running)
- `tmux attach -t platform` — re-attach

### Alternative: gunicorn (HTTP only, no WebSockets)

If you don't need WebSockets, gunicorn is simpler:

```bash
gunicorn realtime_platform.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 4 \
  --timeout 120 \
  --access-logfile -
```

For **WebSocket support** you must use Daphne (ASGI), not gunicorn (WSGI).

---

## API Reference

### Authentication

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/auth/register/` | Register + create organization |
| POST | `/api/v1/auth/login/` | Login → access token + refresh cookie |
| POST | `/api/v1/auth/refresh/` | Refresh access token |
| POST | `/api/v1/auth/logout/` | Revoke refresh token |
| GET | `/api/v1/auth/me/` | Current user profile |
| PATCH | `/api/v1/auth/me/` | Update profile |
| POST | `/api/v1/auth/me/password/` | Change password |
| POST | `/api/v1/auth/invite/accept/` | Accept org invite |

### Organization & Members

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/api/v1/org/` | JWT | Get current organization |
| PATCH | `/api/v1/org/` | JWT Admin+ | Update organization |
| GET | `/api/v1/org/members/` | JWT | List members |
| POST | `/api/v1/org/members/invite/` | JWT Admin+ | Invite member |
| PATCH | `/api/v1/org/members/<uuid>/role/` | JWT Admin+ | Update role |
| DELETE | `/api/v1/org/members/<uuid>/` | JWT Admin+ | Remove member |

### API Keys

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/api/v1/api-keys/` | JWT | List API keys |
| POST | `/api/v1/api-keys/` | JWT Admin+ | Create key (returns full key once) |
| DELETE | `/api/v1/api-keys/<uuid>/` | JWT Admin+ | Revoke key |
| POST | `/api/v1/api-keys/<uuid>/rotate/` | JWT Admin+ | Rotate key |

### Data Ingestion (API Key auth via `X-Api-Key` header)

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/ingest/events/` | Ingest single event |
| POST | `/api/v1/ingest/batch/` | Ingest up to 1000 events |
| POST | `/api/v1/ingest/csv/` | Upload CSV (async, JWT) |

**Single event payload:**
```json
{
  "event_name": "page_view",
  "properties": {"url": "/home", "user_id": "abc123"},
  "timestamp": "2024-01-01T12:00:00Z"
}
```

**Batch payload:**
```json
{
  "events": [
    {"event_name": "click", "properties": {"button": "signup"}},
    {"event_name": "page_view", "properties": {"url": "/pricing"}}
  ]
}
```

### Query & Analytics

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/ingest/query/events/` | List events (paginated) |
| GET | `/api/v1/ingest/query/event-names/` | All distinct event names |
| GET | `/api/v1/ingest/query/timeseries/?event_name=page_view&interval=hour` | Time-series aggregation |

### Dashboards

| Method | Endpoint | Description |
|---|---|---|
| GET/POST | `/api/v1/dashboards/` | List / create dashboards |
| GET/PATCH/DELETE | `/api/v1/dashboards/<uuid>/` | Dashboard CRUD |
| POST/DELETE | `/api/v1/dashboards/<uuid>/share/` | Enable/disable public share link |
| GET | `/api/v1/dashboards/public/<token>/` | Public view (no auth) |
| GET/POST | `/api/v1/dashboards/<uuid>/widgets/` | List / create widgets |
| PATCH/DELETE | `/api/v1/dashboards/<uuid>/widgets/<uuid>/` | Widget CRUD |
| GET | `/api/v1/dashboards/<uuid>/widgets/<uuid>/data/` | Execute widget query |
| GET/POST | `/api/v1/dashboards/queries/` | Saved queries |

### Alerts

| Method | Endpoint | Description |
|---|---|---|
| GET/POST | `/api/v1/alerts/rules/` | List / create alert rules |
| GET/PATCH/DELETE | `/api/v1/alerts/rules/<uuid>/` | Rule CRUD |
| POST/DELETE | `/api/v1/alerts/rules/<uuid>/mute/` | Mute / unmute rule |
| GET | `/api/v1/alerts/history/` | Alert history (paginated) |
| GET/POST | `/api/v1/alerts/channels/` | Notification channels |
| DELETE | `/api/v1/alerts/channels/<uuid>/` | Delete channel |

---

## WebSocket Connections

Connect with `?token=<access_token>` in the query string.

| WebSocket URL | Description |
|---|---|
| `ws://host/ws/dashboards/<dashboard_uuid>/` | Live dashboard updates |
| `ws://host/ws/alerts/` | Real-time alert notifications |
| `ws://host/ws/events/stream/` | Live event stream (tail) |

**Message types received:**
- `event.new` — new event ingested
- `alert.triggered` — alert rule fired
- `alert.notification` — notification details
- `dashboard.refresh` — client should re-fetch widget data

---

## Role Hierarchy

| Role | Can Do |
|---|---|
| **Owner** | Everything including transferring ownership |
| **Admin** | Manage members, API keys, notification channels |
| **Analyst** | Create dashboards, alerts, ingest data |
| **Viewer** | Read-only access to dashboards |

---

## Environment Variables

See `.env.example` for all configuration options.

Key variables:
- `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` — PostgreSQL
- `REDIS_URL` — Redis connection (default: `redis://localhost:6379/0`)
- `JWT_SECRET` — Secret key for JWT signing (change in production!)
- `SECRET_KEY` — Django secret key
- `FRONTEND_URL` — Used in invite emails

---

## Alert Rule Example

```json
{
  "name": "High Error Rate",
  "event_name": "api_error",
  "condition_operator": "gt",
  "threshold_value": 50,
  "window_minutes": 10,
  "channel_uuids": ["<notification-channel-uuid>"]
}
```

This triggers when more than 50 `api_error` events occur within any 10-minute window. Celery Beat evaluates all rules every 60 seconds.
