# CLAUDE.md — Praxis

Personal single-user system implementing practices from *Mindset* (Dweck), *Flow* (Csikszentmihalyi), and *Grit* (Duckworth). Telegram bot for capture, Django website for review and analytics. Local machine only.

Authoritative documents: `docs/PROJECT_PLAN.md` (why, phases) and `docs/SPECIFICATION.md` (what, exactly). **When this file, the spec, and your instincts disagree: the spec wins.** If the spec is ambiguous, ask before implementing.

## Core domain rule (do not violate)

Deliberate practice and flow are **distinct concepts** per Duckworth: DP = effortful preparation targeting weaknesses; flow = absorbed performance. Never merge their session types, fields, or metrics. The DP→flow weekly correlation is the flagship analytic and depends on this separation.

## Stack

- Python 3.12, Django 5.x, SQLite (WAL mode), python-telegram-bot ≥ 21 (async, **long polling — never webhooks**), APScheduler in the bot process, Django templates + Chart.js CDN, Pico.css. No SPA, no JS build step, no Docker.
- Dependency management: `uv` with `pyproject.toml` (fall back to pip + requirements.txt only if uv unavailable).

## Commands

```bash
make setup      # create venv, install deps, migrate, prompt for .env values
make web        # manage.py runserver
make bot        # manage.py runbot   (long-polling bot + APScheduler)
make test       # pytest
make lint       # ruff check . && ruff format --check .
make seed       # load demo fixtures (flagged as demo)
make unseed     # remove demo data
make backup     # copy db.sqlite3 to backups/ with date suffix
```

## Layout

```
praxis/settings.py            # reads .env via environs/django-environ
apps/goals, sessions_log, journal, esm, assessments, insights, bot, library
docs/PROJECT_PLAN.md, docs/SPECIFICATION.md, docs/BUILD_TASKS.md
```

## Conventions

- All timestamps stored UTC; `TIME_ZONE` from `.env` (default `America/Los_Angeles`) for display and week boundaries (weeks are Mon–Sun local).
- Analytics = pure, unit-tested functions in `apps/insights/services.py` taking querysets/dataframes-of-dicts; views only orchestrate. No analytics math in templates or views.
- Model validation in `clean()` (goal hierarchy rules; session kind/field exclusivity).
- Bot: every handler drops updates where `from.id != settings.TELEGRAM_OWNER_ID` (single decorator). Conversations use inline keyboards for ratings and goal picks; every conversation supports /cancel; target ≤ 60s to complete.
- Ruff for lint+format. Type hints on services and bot handlers. Keep functions small; no premature abstraction.
- Tests: pytest + pytest-django. Known-answer fixture tests for every analytics function and for grit reverse-scoring. Write tests in the same task as the feature, not deferred.
- **Never commit `.env` or `db.sqlite3`** (gitignore them). `.env.example` documents all vars.
- Copyright: do NOT embed the Grit Scale or Dweck assessment item text in code or fixtures. Store items in the `ScaleItem` model; the owner enters text via admin from the published sources. Book quotes: paraphrase only in BookCards seed examples.

## Workflow for build tasks

Work through `docs/BUILD_TASKS.md` phase by phase. For each task: read the relevant spec section first, plan briefly, implement, run `make test` and `make lint`, then stop and summarize what changed and how to manually verify. Do not start the next phase without being asked. Commit at the end of each task with a message like `phase1: telegram /dp conversation`.

## Gotchas

- SQLite + two processes: enable WAL mode in a connection signal; keep transactions short in bot handlers.
- python-telegram-bot v21 is asyncio-based; Django ORM calls from handlers must use `sync_to_async` (or `asgiref`) — wrap them consistently in a small helper.
- APScheduler lives inside the `runbot` process only. Web process never schedules jobs.
- ESM pings missed while the machine is off are marked EXPIRED, never back-filled.
- The `sessions_log` app is deliberately not named `sessions` (clashes with `django.contrib.sessions`).
