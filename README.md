# Praxis

Personal practice system implementing *Mindset* (Dweck), *Flow* (Csikszentmihalyi), and
*Grit* (Duckworth). Telegram bot for capture, Django website for review and analytics.
See `docs/PROJECT_PLAN.md` and `docs/SPECIFICATION.md` for the why/what; `CLAUDE.md` for
build conventions.

## Setup

```bash
make setup   # uv sync, copy .env.example -> .env, migrate
```

Then fill in `.env`:

```
DJANGO_SECRET_KEY=<anything random>
TELEGRAM_BOT_TOKEN=<see below>
TELEGRAM_OWNER_ID=<your numeric Telegram user id>
```

### Creating the bot with @BotFather

1. Open a chat with [@BotFather](https://t.me/BotFather) on Telegram.
2. Send `/newbot`, follow the prompts (name, then a unique `_bot`-suffixed username).
3. BotFather replies with an HTTP API token — that's `TELEGRAM_BOT_TOKEN`.
4. To find your own numeric Telegram user id for `TELEGRAM_OWNER_ID`, message
   [@userinfobot](https://t.me/userinfobot) (or any similar "what's my id" bot) and copy
   the id it returns. The bot ignores every update from any other user id.

### Running

```bash
make web    # Django site at localhost:8000 (admin at /admin/ — create a superuser first)
make bot    # long-polling bot process (needs TELEGRAM_BOT_TOKEN + TELEGRAM_OWNER_ID)
```

Runs the same way locally (for development) or on the VM as `app-praxis-web` /
`app-praxis-bot` systemd services — no Docker, no webhook, just two long-running
processes. Locally, run both at once in two terminals or under any simple supervisor.

```bash
uv run python manage.py createsuperuser
```

### Entering Grit Scale / Mindset Assessment items

Item text isn't shipped in this repo (copyright — see `CLAUDE.md`). Before `/grit` or
`/mindset` will work, log into `/admin/` and add the items yourself under
**Assessments → Scale items**:

- **Grit Scale**: all 10 items, numbered 1–10, sourced from Angela Duckworth's published
  scale (angeladuckworth.com/grit-scale, or the appendix of *Grit*). Mark the
  reverse-scored items (check the source — roughly half of them).
- **Mindset Assessment**: however many items you're using from Carol Dweck's published
  assessment, numbered from 1. Mark agreement-with-a-fixed-mindset-statement items as
  reverse-scored.

`/grit` and `/mindset` refuse with instructions (rather than crashing) if the items
aren't fully entered yet.

## Demo data

```bash
make seed     # ~6 weeks of demo "piano" domain data, flagged is_demo
make unseed   # removes it all
```

## Everyday commands

```bash
make test    # pytest
make lint    # ruff check + format --check
make backup  # copy db.sqlite3 -> backups/db-<timestamp>.sqlite3
make freeze  # regenerate requirements.txt from pyproject.toml (VM deploy uses pip, not uv)
```

### Backup / restore

`make backup` copies `db.sqlite3` into `backups/` with a timestamp — safe to run anytime,
including via cron. To restore, stop both processes and copy a backup back over the live
database:

```bash
cp backups/db-20260801-120000.sqlite3 db.sqlite3
```

## Website pages

`/` dashboard · `/insights/` full analytics · `/goals/` goal tree · `/sessions/` session
list/edit · `/journal/` journal entries · `/library/` book cards · `/review/` guided
weekly review · `/digest/` monthly digest · `/export/` CSV export · `/admin/` Django admin
(scale items, raw data, anything not yet covered by a page above).

## Bot commands

`/dp` deliberate practice · `/flow` flow/performance · `/learn` learning session ·
`/setback` setback + growth reframe · `/journal` free-text entry · `/goal` list the goal
tree / add a LOW goal (deeper editing on the website) · `/grit` Grit Scale · `/mindset`
Mindset Assessment · `/card` a random book-technique card · `/stats` this week's numbers ·
`/cancel` cancel whatever's in progress.

ESM (experience-sampling) pings arrive on their own a few times a day within
`ESM_WINDOW`, each with an "Answer" button. The bot also sends a monthly reminder and
digest on the 1st.
