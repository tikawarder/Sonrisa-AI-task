# Tech Stack — Decisions and Rationale

## Chosen Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Backend | Python + FastAPI | Sonrisa's preferred language for AI roles; async support; minimal boilerplate |
| ORM | SQLAlchemy 2.0 | Mature, type-safe; `Base.metadata.create_all()` on startup; PostgreSQL only |
| Database | PostgreSQL | Reliable, supports JSONB for flexible alert configs |
| Task queue | Celery + Redis | Industry standard for async jobs; polling + notification dispatch |
| Event source | feedparser (RSS) | Zero-cost, no API key; NewsAPI excluded from prototype |
| Email | Python smtplib + Jinja2 templates | No external SDK dependency for basic SMTP |
| Slack | slack-sdk | Official Slack SDK, well-maintained |
| Admin UI | FastAPI + Jinja2 templates | Zero frontend build step; simple CRUD is enough |
| AI/LLM | google-genai SDK (gemini-2.5-flash) | User has Gemini API key; fast inference; free tier |
| Auth | python-jose + bcrypt (direct) | JWT for API; HTTP Basic Auth for admin UI; passlib excluded (bcrypt 4.x incompatibility) |
| Testing | pytest + httpx | pytest is Python standard; httpx for async FastAPI testing |
| Container | Docker + docker-compose | Reproducible dev environment; required for Celery + Redis + Postgres |

## Key Design Decision: Extensible Channels

We use a simple abstract base class — NOT a full plugin system:

```python
class NotificationChannel(ABC):
    @abstractmethod
    def send(self, subject: str, body: str) -> bool: ...
```

**Why not a plugin registry?** Over-engineering for a 24h task. Three concrete classes
(EmailChannel, SlackChannel, WebhookChannel) implementing this interface is sufficient
and demonstrates the pattern without adding unnecessary complexity.

## What We Deliberately Did NOT Use

- LangChain / LlamaIndex — overkill for a simple relevance scoring call; adds hidden complexity
- Celery Beat (DB-backed scheduler) — using `celery worker --beat` (in-process scheduler) instead; sufficient for a single periodic task without a separate beat service
- React/Vue frontend — Jinja2 templates are sufficient for an admin CRUD view
- Redis Streams for real-time — 5-minute polling is acceptable for news alerts
