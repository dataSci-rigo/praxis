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
```

## Bot commands

`/dp` deliberate practice · `/flow` flow/performance · `/learn` learning session ·
`/setback` setback + growth reframe · `/journal` free-text entry · `/goal` list the goal
tree / add a LOW goal (deeper editing on the website) · `/card` a random book-technique
card · `/stats` this week's numbers · `/cancel` cancel whatever's in progress.
