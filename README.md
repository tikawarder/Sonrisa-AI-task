# Alert Notification System

Real-time keyword/topic alert system. Users define alerts → system monitors RSS news feeds every 5 minutes → sends notifications via email or Slack.

Built as part of Sonrisa Task 04: Feature Design & Build from a Vague Brief.

---

## Stack

Python + FastAPI · PostgreSQL · Celery + Redis · feedparser (RSS) · Gemini 2.0 Flash (LLM scoring) · slack-sdk · pytest

---

## Quick Start

**1. Copy and fill in environment variables:**

```bash
cp .env.example .env
```

**2. Start all services:**

```bash
docker-compose up --build
```

This starts:
- `db` — PostgreSQL 15 on port 5432
- `redis` — Redis 7 on port 6379
- `app` — FastAPI on http://localhost:8000
- `worker` — Celery worker + beat scheduler (polls every 5 min)

Database tables are created automatically on first startup.

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | yes | JWT signing key — use a long random string |
| `ADMIN_PASSWORD` | yes | Password for the admin UI (HTTP Basic Auth) |
| `GEMINI_API_KEY` | no | Enables LLM relevance scoring on alerts |
| `RSS_FEED_URLS` | no | Comma-separated RSS feed URLs (default: BBC News) |
| `SMTP_HOST` | no | SMTP server for email notifications |
| `SMTP_PORT` | no | SMTP port (default: 587) |
| `SMTP_USER` | no | SMTP username |
| `SMTP_PASSWORD` | no | SMTP password |
| `SLACK_BOT_TOKEN` | no | Slack bot token for Slack notifications |
| `DATABASE_URL` | no | PostgreSQL URL (default matches docker-compose) |
| `REDIS_URL` | no | Redis URL (default matches docker-compose) |

---

## API

Interactive docs at http://localhost:8000/docs

### Auth
```
POST /auth/register   — create account
POST /auth/token      — get JWT token (form: username + password)
```

### Alerts
```
GET    /alerts/              — list your alerts
POST   /alerts/              — create alert
GET    /alerts/{id}          — get alert
PUT    /alerts/{id}          — update alert
DELETE /alerts/{id}          — delete alert
PATCH  /alerts/{id}/toggle   — enable/disable
```

### Notification Channels
```
GET    /channels/       — list your channels
POST   /channels/       — add channel (email / slack / webhook)
DELETE /channels/{id}   — remove channel
```

Channel config examples:
```json
{"type": "email",   "config": {"email": "you@example.com"}}
{"type": "slack",   "config": {"channel": "#alerts"}}
{"type": "webhook", "config": {"url": "https://your-endpoint.com/hook"}}
```

### Admin UI
http://localhost:8000/admin/ — HTTP Basic Auth (username: anything, password: `ADMIN_PASSWORD`)

---

## Running Tests

```bash
python -m pytest tests/ --ignore=tests/test_models.py
```

`test_models.py` requires a live PostgreSQL instance — skip it for local unit tests.

---

## Architecture Decision Log

See `docs/decision-log.md` for all design decisions and rejections.
See `docs/prompt-history.md` for AI prompt history and corrections.
