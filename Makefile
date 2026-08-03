.PHONY: setup web bot test lint seed unseed backup freeze

setup:
	uv sync
	[ -f .env ] || cp .env.example .env
	uv run python manage.py migrate
	@echo "Now edit .env with your TELEGRAM_BOT_TOKEN / TELEGRAM_OWNER_ID."

web:
	uv run python manage.py runserver

bot:
	uv run python manage.py runbot

test:
	uv run pytest

lint:
	uv run ruff check .
	uv run ruff format --check .

seed:
	uv run python manage.py seed

unseed:
	uv run python manage.py unseed

backup:
	mkdir -p backups
	cp db.sqlite3 backups/db-$$(date +%Y%m%d-%H%M%S).sqlite3

freeze:
	uv export --no-dev --no-hashes -o requirements.txt
