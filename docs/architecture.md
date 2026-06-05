# Architecture — Alert Notification System

**Task:** Feature Design & Build from a Vague Brief
**Date:** 2026-06-05
**Author:** Tamás Biró

---

## 1. System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        FastAPI Application                       │
│                                                                  │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────────────┐ │
│  │  Auth API    │   │  Alerts API  │   │    Admin UI           │ │
│  │  /auth/*     │   │  /alerts/*   │   │  (Jinja2 templates)  │ │
│  └──────────────┘   └──────────────┘   └──────────────────────┘ │
└───────────────────────────┬─────────────────────────────────────┘
                            │ SQLAlchemy ORM
                            ▼
                    ┌───────────────┐
                    │  PostgreSQL   │
                    │  Database     │
                    └───────┬───────┘
                            │
          ┌─────────────────┴──────────────────┐
          │                                    │
          ▼                                    ▼
  ┌───────────────┐                   ┌────────────────┐
  │  Celery       │◄──────────────────│     Redis      │
  │  Workers      │    task queue     │   (broker)     │
  └───────┬───────┘                   └────────────────┘
          │
          ├─── EventFetcher (every 5 min)
          │         ├── NewsAPISource
          │         └── RSSSource
          │
          ├─── AlertMatcher
          │         ├── KeywordMatcher
          │         └── LLMRelevanceScorer (gemini-2.5-flash)
          │
          └─── NotificationDispatcher
                    ├── EmailChannel (smtplib + Jinja2)
                    ├── SlackChannel (slack-sdk)
                    └── WebhookChannel (httpx)
```

---

## 2. Data Flow

### Full pipeline: event detection → alert matching → notification dispatch

```
1. POLL (every 5 min, Celery beat)
   │
   └── RSS feeds: feedparser.parse(url) → list[RawEvent]
       (NewsAPI: optional extension — excluded from prototype; requires API key)

2. NORMALIZE
   │
   └── RawEvent → Event(title, description, url, published_at, source)

3. DEDUPLICATE
   │
   └── hash(alert_id + event_url + published_at) → skip if exists in matched_events

4. MATCH (per active Alert)
   │
   ├── KeywordMatcher: any(kw in event.title + event.description for kw in alert.keywords)
   └── LLMRelevanceScorer: if alert.use_llm → score = gemini-2.5-flash(event_text, alert.topic)
                           → accept if score >= alert.threshold

5. DISPATCH (per matched Alert)
   │
   ├── Load user's NotificationChannel configs
   ├── For each channel: channel.send(recipient, subject, body)
   └── Log result to notification_log (success / failed + error message)
```

---

## 3. Component Responsibilities

### FastAPI Application (`src/api/`)

The API layer handles HTTP requests, enforces authentication, and exposes CRUD endpoints for alerts, users, and notification channel configurations. It also serves the admin UI via Jinja2 templates. Authentication is JWT-based: the `/auth/token` endpoint issues tokens; a dependency checks the `Authorization` header on protected routes. The API does not directly send notifications or fetch events — it only reads and writes database state.

### Celery Workers (`src/workers/`)

The worker layer runs the polling and dispatch pipeline outside the request cycle. A single Celery periodic task (`fetch_and_dispatch`) runs every 5 minutes. It instantiates the event sources, fetches new events, runs the alert matcher, and calls the notification dispatcher. Workers communicate with the database via the same SQLAlchemy models used by the API. This separation ensures that slow network calls (LLM scoring, SMTP) never block API responses.

### Event Sources (`src/sources/`)

Event sources are responsible for fetching raw events from external systems and normalizing them into a common `Event` data model. `NewsAPISource` calls the NewsAPI v2 REST endpoint using an API key from environment variables. `RSSSource` accepts a list of feed URLs and uses `feedparser` to parse them. Both return `list[Event]`. Adding a new source means implementing a single method: `fetch() -> list[Event]`.

### Alert Matcher (`src/matching/`)

The alert matcher takes a list of events and a list of active alerts and returns a list of `(alert, event)` matches. It runs two strategies: keyword matching (fast, deterministic, no external call) and optional LLM relevance scoring (semantic, slower, costs API tokens). The LLM call is only made if `alert.use_llm == True`. The matcher is stateless — it does not write to the database; the worker layer handles deduplication and persistence.

### Notification Dispatcher (`src/notifications/`)

The dispatcher takes a matched `(alert, event)` pair, loads the user's configured notification channels, and calls `channel.send()` for each. The abstract base class `NotificationChannel` defines the contract. The three concrete implementations are `EmailChannel` (smtplib + Jinja2 HTML template), `SlackChannel` (slack-sdk `chat_postMessage`), and `WebhookChannel` (httpx POST with JSON payload). Each `send()` returns a boolean; failures are logged but do not raise exceptions, ensuring one failed channel does not block others.

### Admin UI (`src/templates/`)

The admin UI is a set of Jinja2 HTML templates rendered by FastAPI route handlers. It provides CRUD views for alerts plus a read-only event log showing the last 100 matched events. The UI is intentionally minimal — no JavaScript framework, no async rendering. It is protected by HTTP Basic Auth using the `ADMIN_PASSWORD` environment variable (`secrets.compare_digest` — separate from the JWT auth used by the REST API).

---

## 4. Database Schema Overview

### Tables and Key Relationships

```
users
  id          UUID PK
  email       VARCHAR UNIQUE NOT NULL
  password    VARCHAR NOT NULL          -- bcrypt hash
  role        ENUM('user', 'admin') DEFAULT 'user'
  created_at  TIMESTAMP

alerts
  id          UUID PK
  user_id     UUID FK → users.id
  name        VARCHAR NOT NULL
  keywords    TEXT[]                    -- PostgreSQL array
  topic       TEXT                      -- plain language description for LLM
  use_llm     BOOLEAN DEFAULT FALSE
  threshold   FLOAT DEFAULT 0.7
  is_active   BOOLEAN DEFAULT TRUE
  created_at  TIMESTAMP

notification_channels
  id          UUID PK
  user_id     UUID FK → users.id
  type        ENUM('email', 'slack', 'webhook')
  config      JSONB NOT NULL            -- {"email": "x@y.com"} or {"webhook_url": "..."}
  is_active   BOOLEAN DEFAULT TRUE

matched_events
  id          UUID PK
  alert_id    UUID FK → alerts.id
  event_hash  VARCHAR UNIQUE NOT NULL   -- dedup key
  event_url   TEXT
  event_title TEXT
  event_body  TEXT
  source      VARCHAR
  relevance_score FLOAT                 -- NULL if keyword-only match
  matched_at  TIMESTAMP

notification_log
  id          UUID PK
  matched_event_id UUID FK → matched_events.id
  channel_id  UUID FK → notification_channels.id
  status      ENUM('sent', 'failed')
  error_msg   TEXT                      -- NULL if sent
  sent_at     TIMESTAMP
```

**Key relationships:**
- One `user` has many `alerts` and many `notification_channels`
- One `alert` produces many `matched_events` (one per matching event)
- One `matched_event` produces one `notification_log` entry per active channel

---

## 5. API Endpoints Overview

### Auth
| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/register` | Create user account |
| POST | `/auth/token` | Issue JWT token (login) |

### Alerts
| Method | Path | Description |
|--------|------|-------------|
| GET | `/alerts/` | List own alerts |
| POST | `/alerts/` | Create alert |
| GET | `/alerts/{id}` | Get alert detail |
| PUT | `/alerts/{id}` | Update alert |
| DELETE | `/alerts/{id}` | Delete alert |
| PATCH | `/alerts/{id}/toggle` | Enable/disable alert |

### Notification Channels
| Method | Path | Description |
|--------|------|-------------|
| GET | `/channels/` | List own channels |
| POST | `/channels/` | Add channel (email/Slack/webhook) |
| DELETE | `/channels/{id}` | Remove channel |

### Admin UI (HTTP Basic Auth — ADMIN_PASSWORD)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/admin/` | Dashboard (counts) |
| GET | `/admin/alerts` | List all alerts + create form |
| POST | `/admin/alerts/create` | Create alert (form submit) |
| GET | `/admin/alerts/{id}/edit` | Edit form |
| POST | `/admin/alerts/{id}/edit` | Update alert (form submit) |
| POST | `/admin/alerts/{id}/delete` | Delete alert (form submit) |
| GET | `/admin/events` | Event log (last 100, read-only) |

---

## 6. Extensibility Points

### Adding a new notification channel

1. Create `src/notifications/channels/my_channel.py` implementing `NotificationChannel.send()`
2. Add the channel type to the `ENUM` in the database migration
3. Register it in `src/notifications/dispatcher.py` channel factory

No other files need to change. The dispatcher uses a factory dict:

```python
CHANNEL_REGISTRY = {
    "email": EmailChannel,
    "slack": SlackChannel,
    "webhook": WebhookChannel,
}
```

### Adding a new event source

1. Create `src/sources/my_source.py` implementing `EventSource.fetch() -> list[Event]`
2. Register it in the `fetch_and_dispatch` Celery task

### Adding LLM providers

The `LLMRelevanceScorer` is injected into the `AlertMatcher`. To swap providers, implement a new scorer that returns a `float` for a given `(event_text, topic)` pair and wire it via dependency injection or environment config. Current default: `gemini-2.5-flash` via `google-genai` SDK.

---

## 7. Tech Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Backend | Python 3.11 + FastAPI | Async-native; minimal boilerplate; Sonrisa-preferred for AI roles |
| ORM | SQLAlchemy 2.0 | Type-safe; `Base.metadata.create_all()` on startup; PostgreSQL only |
| Database | PostgreSQL 15 | JSONB for channel configs; TEXT[] for keywords; reliable |
| Task queue | Celery 5 + Redis 7 | Industry standard for async jobs; periodic tasks built-in |
| Event sources | feedparser (RSS) | Zero-cost, no API key; universal format; NewsAPI excluded from prototype |
| Email | smtplib + Jinja2 | No external SDK; standard library; HTML templates |
| Slack | slack-sdk | Official SDK; `chat_postMessage` is stable and well-documented |
| Admin UI | FastAPI + Jinja2 | Zero JS build step; CRUD is all that is needed |
| AI/LLM | google-genai SDK (gemini-2.5-flash) | User has Gemini API key; free tier generous; fast inference |
| Testing | pytest + httpx | pytest is the Python standard; httpx for async FastAPI test client |
| Container | Docker + docker-compose | Reproducible dev; required for Celery + Redis + Postgres |
| Auth | python-jose + bcrypt (direct) | JWT; bcrypt hashing; passlib excluded (unmaintained, bcrypt 4.x incompatibility) |

**Deliberately NOT used:**
- LangChain — adds abstraction over a single `generate_content()` call; unjustifiable
- Celery Beat (DB scheduler) — simple `crontab` in `celery.conf` is sufficient
- React/Vue — Jinja2 is sufficient for admin CRUD; avoids build toolchain entirely
- Redis Streams — polling every 5 min is acceptable; Streams would add consumer group complexity
