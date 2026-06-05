# Decision Log

---

## 2026-06-05 — What counts as an "important" event?

**Chosen:** Keyword match OR LLM relevance score ≥ user-defined threshold (default 0.7).
**Why:** Keyword-only misses synonyms. LLM-only wastes tokens on irrelevant events. Hybrid gives users control; score is numeric and testable.

---

## 2026-06-05 — How to implement "flexible channels"?

**Chosen:** ABC + factory dict. Not a plugin registry.
**Why:** A registry is 200+ lines for 3 known types. One `send()` interface is sufficient — adding a channel = one new file.

---

## 2026-06-05 — Event sources

**Chosen:** RSS-only for prototype; NewsAPI optional extension.
**Why:** RSS needs no API key. Market data excluded — brief lists it as an example, not a requirement.

---

## 2026-06-05 — LLM provider

**Chosen:** Gemini 2.0 Flash (`google-generativeai`).
**Why:** Existing API key. Swapping providers = one class change.

---

## 2026-06-05 — Push vs pull model

**Chosen:** Push — Celery worker polls every 5 minutes and sends notifications automatically.
**Why:** Email and Slack notifications can't be pull-based — you can't wait for the user to open the app. The brief explicitly asks for notifications, which requires a background process.

---

## 2026-06-05 — Polling interval

**Chosen:** Celery task every 5 minutes.
**Why:** Fits NewsAPI rate limits. 5-min latency is acceptable for news alerts.

---

## 2026-06-05 — PostgreSQL only

**Chosen:** PostgreSQL for dev and tests.
**Why:** `ARRAY` and `JSONB` are PostgreSQL-specific. SQLite fallback would require two code paths. Docker already required for Redis.

---

## 2026-06-05 — Alembic vs create_all()

**Chosen:** `Base.metadata.create_all()` via `src/db/init_db.py`.
**Why:** No existing data to migrate. Alembic adds 5 files for zero benefit in a 24h prototype.
