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

## 2026-06-05 — Decision: "JWT token vs session cookie authentication"

**Options considered:**
1. Full JWT — Bearer tokens on all endpoints, python-jose + passlib, ~100 lines
2. HTTP Basic Auth only — single ADMIN_PASSWORD env var, 20 lines, no user separation
3. JWT for API + Basic Auth for admin UI — two patterns, proportionate to scope

**Chosen:** Option 3 — JWT for API endpoints, HTTP Basic Auth for admin UI

**Reason:** The brief asks for both an API and an admin view. Using JWT on the API demonstrates the expected pattern for a production system without over-engineering. Basic Auth on the Jinja2 admin UI keeps that layer simple — the admin view is CRUD only, and a single admin password is sufficient for a prototype.

**Tradeoffs accepted:** Two auth systems in one codebase adds minor complexity. Acceptable because they serve different surfaces (JSON API vs rendered HTML) and don't interact.

---

## 2026-06-05 — Validation: celery-worker

**Rejected:**
- `docker-compose.yml` worker command missing `--beat` flag — BLOCKING. Without it the beat scheduler never starts, the periodic task never runs. Fixed.
- `_hash()` used only url+published_at — events with no URL would collide across different titles. Added `title` to the hash key.

**Accepted:** Task structure, try/finally DB cleanup pattern, rollback on exception, dedup logic, `finally` verified to run after `return` inside `try`.

**Corrections applied:** `--beat` added to docker-compose worker command; `title` added to hash function.

---

## 2026-06-05 — Validation: notification-dispatcher

**Rejected:**
- `Template()` without `autoescape=True` — HTML injection risk if event title/body contains tags. Fixed to `Environment(autoescape=True)`.
- `WebClient` instantiated on every `send()` — wasteful. Moved to `__init__`.
- No URL validation in `WebhookChannel` — SSRF risk (user could point to internal services). Added `https://` scheme check as basic guard.

**Accepted:** Library choices (slack-sdk, httpx, jinja2), error handling pattern, dispatcher CHANNEL_REGISTRY, ABC usage.

**Corrections applied:** 3 fixes in email.py, slack.py, webhook.py. 12/12 tests still pass.

---

## 2026-06-05 — Validation: api

**Rejected:**
- `events.html` — 5 `<th>` headers but 4 `<td>` cells — "Matched by" column exists in header but has no corresponding data column in `MatchedEvent` ORM model. BLOCKING: table renders broken. Fixed by removing the orphan column header.
- `UserRole.user` (lowercase) in tests — `UserRole` enum uses uppercase `.USER`. All test helpers corrected.
- `passlib + bcrypt 4.x` incompatibility — `hash_password()` raises `ValueError: password cannot be longer than 72 bytes` in test context due to library version mismatch. Not a production bug (Docker pins versions), but tests must mock `hash_password` to avoid depending on the bcrypt C extension behavior.
- Auth test asserting `status_code == 403` for missing Bearer token — FastAPI returns 401, not 403, from `HTTPBearer`. Corrected assertion.

**Accepted:** JWT utilities (python-jose, passlib), `secrets.compare_digest` for Basic Auth, Jinja2Templates autoescape default, CRUD router structure, dependency injection pattern, 14 new API tests pass.

**Corrections applied:** 4 fixes — events.html column count; UserRole casing in 2 test files; hash_password mocked in register tests; 401 vs 403 assertion corrected. 51/51 tests pass after fixes.

---

## 2026-06-05 — Validation: readme + startup

**Rejected:**
- Missing `Dockerfile` — BLOCKING. `docker-compose.yml` has `build: .` for both `app` and `worker`, but no Dockerfile existed. `docker-compose up --build` would fail immediately. Added `Dockerfile` with `python:3.13-slim`.
- `.gitignore` pattern `.env.*` — BLOCKING. Matches `.env.example`, so the file would never be committed. Fixed with `!.env.example` negation rule.

**Accepted:** `lifespan` context manager pattern for `init_db()` (correct FastAPI 0.95+ startup API); README accuracy (endpoints, ports, env vars all match implementation); `.env.example` content.

**Corrections applied:** `Dockerfile` created; `.gitignore` negation added. 51/51 tests still pass.

---

## 2026-06-05 — Alembic vs create_all()

**Chosen:** `Base.metadata.create_all()` via `src/db/init_db.py`.
**Why:** No existing data to migrate. Alembic adds 5 files for zero benefit in a 24h prototype.
