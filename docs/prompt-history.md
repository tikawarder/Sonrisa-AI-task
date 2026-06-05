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
