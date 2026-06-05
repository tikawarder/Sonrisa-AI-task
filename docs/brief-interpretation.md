# Brief Interpretation — Scope Definition

**Task:** Feature Design & Build from a Vague Brief
**Date:** 2026-06-05
**Author:** Tamás Biró

---

## 1. Original Brief (verbatim)

> "We want users to be able to set up alerts so they get notified when something important happens
> in the world — like breaking news, market movements, natural disasters, that kind of thing.
> Should work for both email and Slack. Make it flexible enough that we can add more channels later.
> We need an admin view too."

---

## 2. Identified Ambiguities

| # | Ambiguity | What the brief says | What it leaves undefined |
|---|-----------|---------------------|--------------------------|
| 1 | **What is "important"?** | "something important happens" | No definition of importance; no threshold, no criteria |
| 2 | **Where does event data come from?** | "breaking news, market movements, natural disasters" | No API, feed, or source specified |
| 3 | **Who are the users?** | "users can set up alerts" | No auth model; no distinction between users and admins |
| 4 | **What is the admin view?** | "We need an admin view too" | No scope: CRUD? Analytics? User management? |
| 5 | **What triggers a notification?** | Implied: when something happens | Real-time? Polling? Webhook? |
| 6 | **What does "flexible" mean?** | "can add more channels later" | Interface contract? Plugin system? Config-driven? |
| 7 | **Alert deduplication** | Not mentioned | Should users get the same alert twice? How is dedup handled? |
| 8 | **Notification content format** | Not mentioned | Plain text? HTML? Rich Slack blocks? |

---

## 3. Chosen Interpretations and Rationale

### Ambiguity 1 — What is "important"?

**Definition chosen:**

An event is considered **important** if it matches at least one of the following criteria:
1. **Keyword match** — The event title or description contains one or more user-defined keywords (exact or case-insensitive substring match).
2. **LLM relevance score ≥ threshold** — An LLM (gemini-2.5-flash) scores the event's relevance to the user's alert topic on a 0.0–1.0 scale. The user sets a threshold (default: 0.7). If the score meets or exceeds the threshold, the event is considered important.

**Why this definition:**
- Pure keyword matching is deterministic, fast, cheap, and explainable — but rigid (misses synonyms, context).
- LLM scoring adds semantic understanding without requiring complex NLP infrastructure.
- User-defined threshold gives control without requiring Sonrisa to make a product decision.
- This is measurable and testable: a unit test can verify that a score of 0.65 with threshold 0.7 is rejected.
- Market movements and financial data were excluded — they require paid real-time APIs (Bloomberg, Alpha Vantage) that are out of scope for a 24h prototype.

### Ambiguity 2 — Where does event data come from?

**Chosen:** RSS feeds via `feedparser` (zero-cost, no API key). NewsAPI documented as an optional extension but excluded from the prototype.

**Why:**
- RSS needs no API key registration — works immediately in a 24h task.
- RSS is universally available (BBC, Reuters, government emergency feeds).
- NewsAPI has a free tier but requires registration; adding it is a one-class change when needed.
- Market data (stocks, crypto) explicitly excluded: requires paid APIs, complex parsing, different latency requirements. Mentioned in brief as an example ("like"), not a requirement.

### Ambiguity 3 — Who are the users?

**Chosen:** Simple JWT-based auth. Single-tenant. Two roles: `user` (manages own alerts) and `admin` (manages all).

**Why:**
- Multi-tenant SaaS requires org isolation, billing, and subdomain routing — far beyond 24h scope.
- JWT is stateless, easy to implement, and the expected pattern for FastAPI APIs.
- Two roles is the minimum needed to separate the admin view from the user view.

### Ambiguity 4 — What is the admin view?

**Chosen:** CRUD-only admin panel (list/create/edit/delete for alerts, users, notification channels) + event log (read-only, last 100 events). No analytics, no charts.

**Why:**
- The brief says "admin view" — not "analytics dashboard". CRUD is the minimum viable interpretation.
- Adding charts/metrics would add significant complexity for zero additional clarity on the brief's intent.
- An event log is necessary for debugging (did the alert fire? why not?) and adds real operational value with minimal code.

### Ambiguity 5 — What triggers a notification?

**Chosen:** Celery worker polls NewsAPI and RSS feeds every **5 minutes**. No webhooks, no real-time streaming.

**Why:**
- Polling is simpler to implement, debug, and test than webhooks.
- 5-minute latency is acceptable for news alerts (not financial trading).
- Celery + Redis is the industry-standard pattern for this; avoids reinventing a scheduler.
- WebSocket/SSE would require a persistent connection layer — unjustifiable complexity for a prototype.

### Ambiguity 6 — What does "flexible" mean?

**Chosen:** Abstract base class `NotificationChannel` with three concrete implementations (Email, Slack, Webhook). No plugin registry, no dynamic loading.

**Why:**
- "Flexible enough to add more channels" → the minimum viable pattern is an interface/ABC.
- A full plugin registry (entry points, dynamic import, config-driven loading) is over-engineering for 3 known channel types.
- The ABC pattern is the correct Go/Python idiom for extensibility without premature abstraction.
- Adding a new channel = create a new class implementing `send()`. That is documented, testable, and reviewable.

### Ambiguity 7 — Alert deduplication

**Chosen:** Each matched event is stored with a hash of `(alert_id, event_url, event_published_date)`. If the hash exists in the database, the notification is suppressed.

**Why:**
- Without dedup, a user would receive the same news article in every polling cycle.
- This is the simplest deterministic dedup strategy — no fuzzy matching needed.

### Ambiguity 8 — Notification content format

**Chosen:** Plain text with a structured template for email (HTML via Jinja2); plain text with one Slack attachment block for Slack.

**Why:**
- HTML email via Jinja2 requires no external SDK and is readable without a browser.
- Slack Block Kit is expressive but complex — a single attachment block is sufficient and readable.

---

## 4. Concrete Definition: "Important Event"

An event `E` is important for alert `A` if:

```
keyword_match(E, A.keywords) == True
OR
llm_relevance_score(E, A.topic) >= A.threshold
```

Where:
- `keyword_match` = case-insensitive substring match of any keyword in `A.keywords` against `E.title + E.description`
- `llm_relevance_score` = 0.0–1.0 float returned by gemini-2.5-flash given the event text and alert topic
- `A.threshold` = user-configurable float, default `0.7`

This definition is **measurable** (numeric score), **testable** (unit tests with mock LLM), and **explainable** (keyword match is transparent to users).

---

## 5. Concrete Definition: "Flexible"

Flexible means: **adding a new notification channel requires writing exactly one class** that implements a single `send(subject, body)` method. The channel's destination (email address, Slack token, webhook URL) is stored in its `config` field at creation time — not passed per call.

No changes to the dispatcher, no config file edits, no registry updates needed. This is the entire extension contract.

---

## 6. Scope Boundaries

### In Scope

| Feature | Details |
|---------|---------|
| Alert CRUD | Users create/edit/delete alerts with keywords, topic, threshold |
| Event detection | NewsAPI + RSS polling every 5 minutes via Celery |
| Relevance scoring | LLM (gpt-4o-mini) optional relevance filter |
| Email notifications | SMTP via Python smtplib, HTML templates |
| Slack notifications | slack-sdk, single attachment block |
| Extensible channels | Abstract base class; webhook channel as 3rd example |
| Admin UI | CRUD for alerts, users, channels; read-only event log |
| Basic auth | JWT tokens; user + admin roles |
| Alert deduplication | Hash-based, stored in DB |
| Docker setup | docker-compose for PostgreSQL + Redis + app |
| Tests | pytest suite for core components |

### Out of Scope

| Feature | Reason |
|---------|--------|
| Real-time market data | Requires paid APIs; different latency/reliability requirements |
| Social media monitoring | Rate limits, auth complexity, content policy issues |
| Mobile push notifications | Requires FCM/APNS — separate SDK, device token management |
| Multi-tenant SaaS | Org isolation, billing, routing — beyond 24h scope |
| Analytics dashboard | Not implied by "admin view" |
| Natural language alert setup | LLM-generated alert configs add complexity without clear user value |
| WebSocket / real-time UI updates | Polling is sufficient for news; streaming adds infra complexity |
| Retry / dead-letter queue | Basic error logging sufficient for prototype |
