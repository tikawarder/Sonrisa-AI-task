# Prompt History

This file records all implementation prompts used during the project, including what was accepted,
what was rejected, and corrections made. Format per `.claude/rules/process.md`.

---

## 2026-06-05 — Planning Session: /brief

**Prompt given:**

```
Read the file at docs/task-04-feature-design-and-build.docx and also read .claude/rules/project-context.md.

Produce:
1. docs/brief-interpretation.md — scope definition with ambiguities, interpretations, and rationale
2. docs/architecture.md — system architecture with component responsibilities, schema, API endpoints, extensibility points
3. Log this session as first entry in docs/prompt-history.md

After writing both files, summarize in Hungarian what decisions were made and flag anything
that needs confirmation before implementation starts.
```

**What I received:**

Two complete documents: `brief-interpretation.md` covering all 8 identified ambiguities with
rationale for each interpretation, a concrete measurable definition of "important event" and
"flexible channel", and a scope table. `architecture.md` covering system diagram, data flow
pipeline, component responsibilities, DB schema (5 tables), API endpoints (14 routes), 3
extensibility points, and a tech stack table.

**What I rejected / questioned:**

- Initial draft included "market movements" in scope with a note about using Alpha Vantage API.
  **Rejected:** Alpha Vantage free tier has 5 requests/minute — insufficient for any real use,
  and the brief lists market movements as one example of "that kind of thing", not a requirement.
  Moved to out-of-scope with explicit rationale.

- Initial schema included a `categories` table for categorizing events.
  **Rejected:** Over-engineering. Keywords + LLM topic description cover this without an
  extra join table. Kept the schema flat.

- First version of the channel extensibility section described a "plugin registry with dynamic
  import". **Rejected:** This is the trap documented in `belso-csapdak.md`. A simple factory
  dict `CHANNEL_REGISTRY = {"email": EmailChannel, ...}` is the correct answer. Revised.

**What I accepted:**

- 5-table schema (users, alerts, notification_channels, matched_events, notification_log)
- Abstract base class pattern for NotificationChannel
- LLM relevance scoring as optional (use_llm flag per alert)
- Celery + Redis for polling, not Celery Beat DB scheduler
- JWT auth with two roles (user, admin)
- Admin view = CRUD + read-only event log (last 100)

**Corrections made:**

1. Removed Alpha Vantage / market data from scope
2. Collapsed `categories` table into `keywords TEXT[]` on `alerts`
3. Replaced plugin registry with factory dict pattern
4. Added `event_hash` dedup field to `matched_events` — was missing from initial draft
5. Added `relevance_score FLOAT` to `matched_events` — needed for audit/debug visibility
