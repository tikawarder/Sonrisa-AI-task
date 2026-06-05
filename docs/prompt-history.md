# Prompt History

All implementation prompts, decisions, and corrections made during the project.

---

## 2026-06-05 — /brief: scope + architecture

**Prompt:** Parse the PM brief, identify ambiguities, produce `brief-interpretation.md` and `architecture.md`.

**Received:** 8 ambiguities documented with interpretations, concrete definitions of "important event" and "flexible channel", scope table, system diagram, 5-table schema, 14 API endpoints, tech stack table.

**Questioned / rejected:**

- Alpha Vantage for market data — dropped. Free tier is 5 req/min, useless. Brief lists it as an example, not a requirement.
- `categories` table in schema — dropped. `keywords TEXT[]` on the alert covers this without an extra join table.
- "Plugin registry with dynamic import" for channels — replaced with ABC + factory dict. A registry is 200 lines of infrastructure for 3 known channel types.
- Asked: does the system need NewsAPI or is RSS-only enough to start? Chose RSS-only — no API key registration needed, works immediately. NewsAPI stays as optional extension.
- Asked: which LLM provider? OpenAI was the default — switched to Gemini (existing API key).

**Corrections:** Added `event_hash` and `relevance_score` to `matched_events` — both missing from first draft.

---

## 2026-06-05 — /implement: db-schema

**Prompt:** SQLAlchemy 2.0 models, docker-compose, requirements.txt, pytest conftest + model tests.

**Received:** 22 files — 5 models, Alembic setup, docker-compose with 4 services, 6 model tests.

**Questioned / rejected:**

- Asked: why Docker, why not a monolith? Docker is unavoidable — Celery needs Redis, Redis isn't installed natively. Valid question, accepted Docker.
- Asked: can each phase be tested independently? Yes — `docker-compose up db redis` + `pytest tests/test_models.py` runs standalone. Confirmed before moving on.
- `alembic/script.py.mako` missing from output — caught. Without it `alembic revision` throws MakoException. Added.
- `pytest.ini` missing — caught. pytest can't resolve `src` package without `pythonpath = .`.
- Asked: is Alembic overkill for a 24h task? Yes — removed entirely. `Base.metadata.create_all()` is sufficient, replaced with `src/db/init_db.py`. Logged in decision-log.md.
- Flagged `sessionmaker(bind=connection)` as potentially deprecated in SQLAlchemy 2.0 — verified with a manual isolation test before accepting.

**Corrections:** Removed Alembic (5 files), added `init_db.py`, added `pytest.ini`.

---

## 2026-06-05 — /implement: event-sources

**Prompt:** EventSource ABC + RSSSource implementation using feedparser. Event as Pydantic model. Unit tests with mocked network calls.

**Received:** `src/sources/base.py` (Event model + ABC), `src/sources/rss.py` (RSSSource), `tests/test_event_sources.py` (6 tests).

**Questioned / rejected:**

- Initial `rss.py` used `feed.feed` and `feed.entries` attribute access. **Caught by tests:** plain dict mocks don't support attribute access — 3 tests failed immediately. Fixed to `feed.get("feed", {})` and `feed.get("entries", [])` — works with both feedparser's real `FeedParserDict` and plain dict mocks.
- `asyncio_mode = auto` in `pytest.ini` caused a warning — `pytest-asyncio` not installed and not needed yet. Removed.

**Corrections:** `feed.feed` → `feed.get("feed", {})` throughout `rss.py`. Tests confirmed: 6/6 pass.

---

## 2026-06-05 — /implement: alert-matcher

**Prompt:** KeywordMatcher + LLMRelevanceScorer (Gemini) + AlertMatcher orchestrator. AlertConfig dataclass to decouple from ORM. Unit tests with mocked LLM.

**Received:** `src/matching/matcher.py` with 5 classes, `tests/test_alert_matcher.py` with 14 tests.

**Questioned / rejected:**

- `google.generativeai` was used in the initial output — **caught by warning:** package is fully deprecated, replaced by `google-genai`. Switched to `from google import genai` with the new `Client` API. Updated `requirements.txt` accordingly. Good catch — old package receives no bug fixes.
- Considered splitting into `keyword.py` + `llm.py` + `matcher.py`. Rejected — three small classes in one file is cleaner for this scope. Splitting would add files without adding clarity.

**Corrections:** Replaced deprecated `google.generativeai` with `google-genai` SDK. Updated mock pattern in tests to match new `Client.models.generate_content()` API. 14/14 pass, no warnings.

---

## 2026-06-05 — /implement: notification-dispatcher

**Prompt:** NotificationChannel ABC + EmailChannel (smtplib+Jinja2), SlackChannel (slack-sdk), WebhookChannel (httpx). NotificationDispatcher with CHANNEL_REGISTRY. Tests mocking all external calls.

**Received:** `src/notifications/base.py`, 3 channel implementations, `src/notifications/dispatcher.py`, 12 tests.

**Questioned / rejected:**

- Original ABC signature from tech-stack.md had `send(recipient, subject, body)`. **Changed:** recipient is part of the channel config — passing it again as a method parameter is redundant. `send(subject, body)` is cleaner. The channel knows its own recipient. Documented as deliberate deviation.
- Considered merging all 3 channels into one file. Rejected — each channel is an independent extension point. One file per channel matches the extensibility contract.

**Corrections:** ABC signature simplified. 12/12 pass.

**Post-validate corrections (/validate run):**
- `Template()` → `Environment(autoescape=True)` — HTML injection fix in email.py.
- `WebClient` moved to `__init__` — was recreated on every send().
- SSRF guard added to WebhookChannel — rejects non-https URLs.

---

## 2026-06-05 — /implement: celery-worker

**Prompt:** Celery app setup + `fetch_and_dispatch` periodic task. Glues together RSSSource → AlertMatcher → NotificationDispatcher → DB persistence. Hash-based dedup. Tests with mocked DB and pipeline components.

**Received:** `src/workers/celery_app.py`, `src/workers/tasks.py`, `tests/test_worker_task.py` (5 tests).

**Questioned / rejected:**

- Test asserted `commit()` called when no alerts exist — wrong. Task returns early before any DB writes when `db_alerts` is empty. Fixed assertion to `assert_not_called()`. The task logic is correct; the test assumption was wrong.
- Considered separate Celery Beat process in docker-compose. Kept `worker --beat` combined for simplicity — adding a 5th service adds complexity with no benefit for a prototype.

**Corrections:** Fixed one wrong test assertion. 5/5 pass.

---

## 2026-06-05 — /implement api

**Prompt:** Implement the full API layer: JWT auth utilities, FastAPI dependencies, all routers (auth, alerts, channels, admin), Jinja2 admin templates, tests.

**What I received:** 11 files — `src/api/auth.py`, `deps.py`, `main.py`, `schemas.py`, `routers/{auth,alerts,channels,admin}.py`, `src/templates/admin/{base,index,alerts,events}.html`, `tests/test_api_{auth,alerts}.py`.

**What I rejected:**
- `events.html` — "Matched by" header column had no matching `<td>`. `MatchedEvent` ORM has no `matched_by` field. BLOCKING. Removed orphan column.
- `UserRole.user` lowercase in test helpers — enum is `UserRole.USER`. Corrected in both test files.
- `hash_password()` called directly in register tests — fails at test time due to `passlib/bcrypt 4.x` version mismatch (`ValueError: password cannot be longer than 72 bytes`). Not a production bug. Mocked `hash_password` in test fixtures.
- Test asserting `status_code == 403` for missing Bearer token — FastAPI `HTTPBearer` returns `401`, not `403`. Corrected assertion.
- Initial `Alert(...)` constructor missing `is_active=True` and `created_at` — SQLAlchemy `default=` and `server_default=` don't populate Python-level attributes until after DB flush. Added explicit values in `create_alert` and `register` router functions.

**What I accepted:** JWT using python-jose + passlib, `secrets.compare_digest` for Basic Auth, Jinja2Templates autoescape (FastAPI default for `.html`), dependency injection pattern, router structure matching architecture.md, SSRF guard in webhook channel (carried forward).

**Corrections made:** 5 fixes applied during validation. 51/51 tests pass.

---

## 2026-06-05 — integration: startup and admin UI fixes

**Prompt given:** Run the app end-to-end via docker compose, fix whatever breaks.

**What I received:** 3 BLOCKING runtime errors caught during integration testing.

**What I rejected:**
- Missing `pydantic[email]` in requirements.txt — app crashed at import with `ImportError: email-validator is not installed`.
- Missing `python-multipart` in requirements.txt — required by `OAuth2PasswordRequestForm`.
- Old Starlette `TemplateResponse(name, context)` API — removed in Starlette 1.x. All admin routes crashed with `TypeError: unhashable type: 'dict'`. None of this was caught by unit tests because they mock the DB and don't render real templates.

**What I accepted:** Dockerfile structure, lifespan pattern, template content.

**Corrections made:** 2 packages added to requirements.txt; admin router updated to Starlette 1.x API `TemplateResponse(request, name, context)`. All 3 admin routes verified 200 OK.

---

## 2026-06-05 — implement: admin-crud

**Prompt given:** Add HTML CRUD forms to the admin UI so alerts can be created, edited and deleted without using the Swagger UI.

**What I received:** Admin router extended with 4 new POST/GET endpoints; alerts.html updated with create form + action buttons; new alert_edit.html template; 9 new tests.

**What I rejected:** Nothing — implementation was clean on first pass.

**What I accepted:** Form-based POST with `Form(...)` dependencies; checkbox handling (`"on"/"off"`); comma-separated keyword parsing; `303 See Other` redirect after every mutation; `confirm()` dialog on delete.

**Corrections made:** None. 9/9 tests pass, 60/60 total.
