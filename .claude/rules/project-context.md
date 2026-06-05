# Project Context — Alert Notification System

## Original PM Brief (verbatim)

"We want users to be able to set up alerts so they get notified when something important happens
in the world — like breaking news, market movements, natural disasters, that kind of thing.
Should work for both email and Slack. Make it flexible enough that we can add more channels later.
We need an admin view too."

## Identified Ambiguities

1. **What is "important"?** — Not defined. Could be keyword match, LLM classification, or category-based.
2. **Where does event data come from?** — No API or source specified.
3. **Who are the users?** — No auth model defined (single tenant? multi-tenant?).
4. **What is the admin view?** — No scope: CRUD only? Analytics? User management?
5. **What triggers a notification?** — Real-time? Polling? Webhook?

## Chosen Interpretations (documented decisions)

- **"Important"** = user-defined keywords/topics + optional LLM relevance score (0–1). User sets threshold.
- **Event sources** = NewsAPI (breaking news) + RSS feeds (flexible, pluggable). No real-time market data (out of scope — requires paid APIs and adds complexity beyond 24h window).
- **Users** = simple auth (API key or basic JWT). Single-tenant for this prototype.
- **Admin view** = CRUD for alerts, users, notification channels, and a simple event log. No analytics.
- **Trigger mechanism** = Celery polling every 5 minutes. Not real-time (justified: avoids webhook complexity, sufficient for news).

## Scope Boundaries

### In scope
- Alert creation/management (keywords, categories, schedule)
- Event detection via NewsAPI + RSS
- Email notification (SMTP)
- Slack notification (slack-sdk)
- Extensible channel architecture (abstract base class)
- Admin UI (FastAPI + Jinja2)
- Basic auth

### Out of scope
- Real-time market data (stocks, crypto)
- Social media monitoring
- Mobile push notifications
- Multi-tenant SaaS
- Complex analytics dashboard
- Natural language alert setup
