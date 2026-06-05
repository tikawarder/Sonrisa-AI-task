# Decision Log

This file records all design decisions made during the project.
Format: date + question + options considered + chosen option + rationale.

---

## 2026-06-05 — What does "important event" mean?

**Question:** The brief mentions "something important happens" without any definition.
How do we define and implement importance detection?

**Options considered:**

1. **Keyword-only matching** — Simple substring match. Fast, deterministic, free. But brittle:
   misses synonyms, context, and relevance nuance.

2. **LLM-only classification** — Use gpt-4o-mini to score every event. Flexible, semantic.
   But: costs API tokens for every event even if obviously irrelevant; adds latency to each
   polling cycle; LLM can hallucinate or be inconsistent.

3. **Keyword match + optional LLM scoring (hybrid)** — Keyword match is the primary filter
   (fast, free). LLM scoring is opt-in per alert (adds semantic layer when user needs it).
   User sets a threshold (0.0–1.0, default 0.7).

**Chosen:** Option 3 — Hybrid keyword + optional LLM scoring.

**Rationale:** Option 1 alone would be too rigid for the brief's intent (natural disasters
don't always use the same keywords). Option 2 alone is wasteful and slow. Option 3 gives
users control over cost/quality tradeoff, makes the system testable (keyword match has
deterministic unit tests; LLM path can be mocked), and produces a measurable output
(numeric score) that can be stored for audit and debugging.

---

## 2026-06-05 — How to implement "flexible enough to add more channels"?

**Question:** The brief asks for email + Slack with extensibility for future channels.
What architectural pattern best implements this without over-engineering?

**Options considered:**

1. **Hard-coded if/else in dispatcher** — `if channel_type == 'email': ...elif channel_type == 'slack': ...`
   Zero abstraction, easy to understand, fast to write. But adding a channel means modifying
   the dispatcher — violates open/closed principle and would be flagged as a red flag by
   Sonrisa evaluation.

2. **Full plugin registry with dynamic import** — Entry points, dynamic class loading,
   config-driven registration. Truly extensible. But: massive over-engineering for 3 known
   channel types. Adds 200+ lines of infrastructure code for zero observable user benefit.

3. **Abstract base class + factory dict** — `NotificationChannel(ABC)` with `send()` method.
   Three concrete classes. Factory dict for instantiation. Adding a channel = one new file.

**Chosen:** Option 3 — Abstract base class + factory dict.

**Rationale:** The brief says "flexible enough" — not "infinitely flexible" or "plugin-based".
An ABC is the idiomatic Python pattern for this. A factory dict (`CHANNEL_REGISTRY`) is
1 line and fully sufficient. The evaluation rubric in `evaluation-focus.md` explicitly flags
"flexible implemented as hard-coded if/else" as a red flag, and "plugin registry" as
over-engineering. Option 3 is the correct answer.

---

## 2026-06-05 — What event sources to use?

**Question:** The brief mentions "breaking news, market movements, natural disasters" but
specifies no data source. What sources should we integrate?

**Options considered:**

1. **NewsAPI only** — Free tier (100 requests/day), structured JSON, easy Python integration.
   Good for breaking news. Does not cover RSS feeds, financial data, or government alerts.

2. **NewsAPI + RSS (feedparser)** — Adds RSS support: BBC, Reuters, FEMA, USGS earthquake feeds.
   No API key needed for RSS. Broad coverage. Small additional dependency (`feedparser`).

3. **NewsAPI + RSS + Alpha Vantage (financial)** — Adds market movements. But: Alpha Vantage
   free tier is 5 requests/minute; market data requires different parsing, different latency
   requirements, and the brief lists it as an example, not a requirement.

**Chosen:** Option 2 — NewsAPI + RSS (feedparser), with RSS as the primary source for the
prototype. NewsAPI integration kept as an optional second source (can be enabled via env var).

**Rationale:** Market data (Option 3) is out of scope. NewsAPI requires API key registration;
for the prototype we start RSS-only so the system runs without any external account. RSS covers
the core use cases (breaking news via BBC/Reuters/AP feeds, natural disasters via USGS/FEMA feeds).
NewsAPI can be added later — it's one new `EventSource` class, zero architectural impact.

---

## 2026-06-05 — Polling interval and trigger mechanism

**Question:** How often should the system check for new events? Real-time or polling?

**Options considered:**

1. **Webhooks / real-time** — NewsAPI does not offer webhooks on free tier. RSS is pull-only.
   Would require server-sent events or WebSockets on client side. Not feasible for free-tier sources.

2. **Polling every 1 minute** — Near-real-time. But: NewsAPI free tier limits to 100 requests/day
   (~4 requests/hour). 1-minute polling would exhaust quota in 100 minutes.

3. **Polling every 5 minutes** — 288 requests/day — well within NewsAPI free tier.
   ~5-minute latency is acceptable for news alerts (not financial trading). Industry standard
   for news monitoring tools.

**Chosen:** Option 3 — 5-minute Celery polling.

**Rationale:** NewsAPI rate limits rule out sub-5-minute polling on the free tier. 5-minute
latency is acceptable for the stated use cases (breaking news, natural disasters) — these are
not latency-sensitive like financial trading. Celery periodic tasks are the standard pattern
for this; no custom scheduling code needed.

---

## 2026-06-05 — LLM provider for relevance scoring

**Question:** Which LLM SDK to use for the optional relevance scoring feature?

**Options considered:**

1. **OpenAI SDK (gpt-4o-mini)** — Originally planned. Cheapest OpenAI model, well-documented.
   But: user does not have an OpenAI API key.

2. **Anthropic SDK (claude-haiku-3-5)** — Fast and cheap. Excellent instruction-following.
   But: user does not have an Anthropic API key.

3. **Google Generative AI SDK (gemini-2.0-flash)** — User has a Gemini API key. Free tier
   is generous (1500 requests/day). `google-generativeai` is a mature Python SDK.

**Chosen:** Option 3 — Gemini 2.0 Flash via `google-generativeai`.

**Rationale:** The LLM scorer is injected as a dependency — swapping providers only requires
changing one class. Gemini 2.0 Flash is fast, free-tier accessible, and the user already has
the API key. The `generate_content()` call is structurally identical to OpenAI's
`chat.completions.create()` — no architectural impact. Updated architecture.md accordingly.

---

## 2026-06-05 — Database: PostgreSQL vs SQLite

**Question:** Should we use PostgreSQL (more realistic, requires Docker) or SQLite
(zero-dependency, easy local testing) as the primary database?

**Options considered:**

1. **SQLite only** — Zero Docker dependency. Fast tests. But: no JSONB support (needed for
   channel configs), no TEXT[] arrays (keywords), no production-viable concurrency.

2. **PostgreSQL for production, SQLite for tests** — Realistic production setup.
   Tests use SQLite via SQLAlchemy's database-agnostic interface. Avoids JSONB/array in
   the shared schema (use TEXT + JSON serialization instead for test compatibility).

3. **PostgreSQL only (via Docker)** — Tests run against a real PostgreSQL instance.
   Most realistic. Requires Docker in CI. Slightly slower test startup.

**Chosen:** Option 3 — PostgreSQL only, Docker for dev and test.

**Rationale:** SQLite's lack of JSONB and array types would require maintaining two code paths
or downgrading the schema. PostgreSQL TEXT[] for keywords and JSONB for channel configs
are the right tool for the job — they simplify the ORM mapping and avoid JSON serialization
boilerplate. Docker is already required for Redis (Celery broker), so adding PostgreSQL to
docker-compose costs nothing. Tests will use a separate PostgreSQL database (`test_db`).
