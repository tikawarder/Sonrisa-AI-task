# Tech Stack — Decisions and Rationale

## Chosen Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Backend | Python + FastAPI | Sonrisa's preferred language for AI roles; async support; minimal boilerplate |
| ORM | SQLAlchemy 2.0 | Mature, type-safe, works with PostgreSQL and SQLite for testing |
| Database | PostgreSQL | Reliable, supports JSONB for flexible alert configs |
| Task queue | Celery + Redis | Industry standard for async jobs; polling + notification dispatch |
| Event source | NewsAPI + RSS (feedparser) | NewsAPI for breaking news; RSS for flexibility; both are free-tier accessible |
| Email | Python smtplib + Jinja2 templates | No external SDK dependency for basic SMTP |
| Slack | slack-sdk | Official Slack SDK, well-maintained |
| Admin UI | FastAPI + Jinja2 templates | Zero frontend build step; simple CRUD is enough |
| AI/LLM | OpenAI SDK (gpt-4o-mini) | Cheapest capable model for relevance scoring; Anthropic SDK as fallback |
| Testing | pytest + httpx | pytest is Python standard; httpx for async FastAPI testing |
| Container | Docker + docker-compose | Reproducible dev environment; required for Celery + Redis + Postgres |

## Key Design Decision: Extensible Channels

We use a simple abstract base class — NOT a full plugin system:

```python
class NotificationChannel(ABC):
    @abstractmethod
    def send(self, recipient: str, subject: str, body: str) -> bool: ...
```

**Why not a plugin registry?** Over-engineering for a 24h task. Three concrete classes
(EmailChannel, SlackChannel, WebhookChannel) implementing this interface is sufficient
and demonstrates the pattern without adding unnecessary complexity.

## What We Deliberately Did NOT Use

- LangChain / LlamaIndex — overkill for a simple relevance scoring call; adds hidden complexity
- Celery Beat for scheduling — using simple polling loop instead (fewer moving parts)
- React/Vue frontend — Jinja2 templates are sufficient for an admin CRUD view
- Redis Streams for real-time — 5-minute polling is acceptable for news alerts
