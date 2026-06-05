# Sonrisa AI Engineer — Task 04: Feature Design & Build

## Project Context

Build a real-time alerting/notification system from a deliberately vague PM brief.
This is a job interview evaluation task — the process and decision-making matter MORE than the code.

**Brief summary:** Users set up keyword/topic alerts → system monitors news/events → sends notifications via email or Slack (extensible to other channels) → admin view to manage.

## Language Rules

- All code, comments, and technical documentation: **English only**
- Communication with the user (Tamas): **Hungarian**

## Key Directories

- `.claude/rules/` — project rules loaded each session (read these first)
- `.claude/commands/` — available slash commands: `/plan`, `/implement`, `/validate`, `/decide`, `/milestone`
- `docs/` — working artifacts: decision-log.md, prompt-history.md, brief-interpretation.md, architecture.md
- `src/` — implementation code

## Critical Rules

1. Do NOT accept AI-generated output without critical validation (`/validate`)
2. Do NOT change architecture without logging a `/decide` entry first
3. Every major step requires a git commit via `/milestone`
4. At least 2-3 AI output rejections must be documented in `docs/decision-log.md`
5. Read `docs/inner_docs/evaluation-focus.md` before every session to stay aligned with what Sonrisa evaluates

## Tech Stack

Python + FastAPI, PostgreSQL + SQLAlchemy, Celery + Redis, RSS (feedparser), SMTP + slack-sdk, google-genai, pytest
See `.claude/rules/tech-stack.md` for full details and rationale.
