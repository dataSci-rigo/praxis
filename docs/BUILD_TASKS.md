# BUILD_TASKS.md — Ordered prompts for Claude Code

How to use: open Claude Code in the repo root (with CLAUDE.md, docs/PROJECT_PLAN.md, docs/SPECIFICATION.md already in place). Paste one task prompt at a time. Verify the acceptance criteria yourself before moving on. Ask Claude Code to plan first on the larger tasks (1.2, 2.1, 4.1).

---

## Phase 0 — Foundation

**Task 0.1 — Scaffold**
> Read CLAUDE.md and docs/SPECIFICATION.md sections 1–2. Scaffold the Django project `praxis` with the eight apps listed, pyproject.toml managed by uv, ruff config, pytest-django config, the Makefile targets from CLAUDE.md, .env.example, .gitignore (env, sqlite, backups/), and a settings module reading .env. Enable SQLite WAL mode. Add a smoke test that the settings load and `make test` passes. Initialize git and commit.

✅ `make setup && make test && make lint` all pass; `make web` serves the Django welcome/blank index at localhost:8000.

**Task 0.2 — Data model + admin**
> Implement every model from SPECIFICATION.md section 3 (Goal, Session, journal Entry, Ping, PingResponse, Assessment, ItemResponse, ScaleItem, BookCard) with the validation rules in their `clean()` methods, migrations, and admin registrations with useful list_display/filters. Write model tests covering: goal hierarchy rules (LOW requires parent, TOP forbids parent), session kind/field exclusivity, and journal language scoring on save using the wordlist heuristic in `apps/journal/mindset_lang.py` with a JSON wordlist fixture. Commit.

✅ Can create a full goal tree and one session of each kind in /admin; invalid combos are rejected; tests cover the heuristic with known-answer cases.

**Task 0.3 — Seed data**
> Implement `make seed`/`make unseed` per spec: ~6 weeks of realistic demo data (goal tree for a "piano" domain, DP/flow/learning sessions, ESM responses spread across quadrants, journal entries with both fixed and growth language, two grit assessments) all flagged with a `demo` marker for clean removal. Commit.

✅ After `make seed`, admin shows populated data; `make unseed` removes it all.

---

## Phase 1 — Telegram capture bot

**Task 1.1 — Bot skeleton**
> Read SPECIFICATION.md section 4. Create the `runbot` management command: python-telegram-bot v21 app in long-polling mode, owner-ID guard decorator applied to all handlers, a `sync_to_async` ORM helper, /start (greeting + command list), /cancel, and /stats (text summary per spec, fine if numbers are basic for now). Document in README how to create the bot with @BotFather and fill .env. Commit.

✅ With a real token in .env, `make bot` runs; the bot answers /start for the owner ID and stays silent for any other account.

**Task 1.2 — Capture conversations**
> Implement the /dp, /flow, /learn, /setback, /journal, and /goal conversations exactly per SPECIFICATION.md section 4: inline-keyboard goal pickers and 1–10 button rows, DP's stretch-goal-first flow with feedback/refinement/discomfort at close (support both live and retroactive logging), the setback flow requiring a reframe before saving, /goal limited to listing the tree and adding a LOW goal. Every conversation ≤ 60s and cancelable. Unit-test handler functions with fake updates. Commit.

✅ Each command completes end-to-end on a phone and the records appear correctly in /admin; /cancel works mid-flow everywhere.

**Task 1.3 — Book cards**
> Implement the library app behaviors: /card command, and appending a random low-times_shown BookCard to roughly 1 in 4 save confirmations, incrementing times_shown. Seed 3 example cards written as short original paraphrases (no book quotes). Commit.

✅ /card works; confirmations sometimes include a card.

---

## Phase 2 — Analytics (top priority feature)

**Task 2.1 — Analytics services**
> Read SPECIFICATION.md section 6 carefully. Implement analytics 1–6 as pure functions in apps/insights/services.py: flow-map points with personal-baseline quadrant assignment (trailing 60-day means), weekly dp_minutes and flow_rate series with the lag-1 Pearson r gated on ≥ 8 weeks, streaks and active-day percentages, per-MID-goal weekly minutes matrix, monthly mindset language ratio, DP quality metrics, and assessment history. Every function gets known-answer tests built on small hand-computed fixtures — especially quadrant assignment, week bucketing across a month boundary in America/Los_Angeles, streaks, and Pearson r. Commit.

✅ `make test` passes; I can spot-check one week's dp_minutes by hand against seeded data and it matches.

**Task 2.2 — Insights pages + dashboard**
> Build /insights/ and the / dashboard per SPECIFICATION.md sections 5–6 with Chart.js: flow-map scatter colored by quadrant with activity tooltips and the flow-% activity ranking table, the DP-vs-flow dual-series chart with the correlation caption from the spec, streak/consistency panel, heatmap, mindset language trend, DP quality panel, assessment history. Implement every empty state ("need N more days of data"). Style with Pico.css. Commit.

✅ With seed data, all charts render sensibly; with `make unseed`, every panel shows its empty state instead of breaking.

---

## Phase 3 — Web review UI

**Task 3.1 — Goal tree + CRUD**
> Build /goals/ (collapsible tree per domain, add/edit/drop, per-node effort totals, orphan-effort warnings), /sessions/ (filterable list + edit), /journal/ (list; setbacks as raw-vs-reframe pairs; language badge), and /library/ CRUD, per SPECIFICATION.md section 5. Server-rendered forms, login required. Commit.

✅ Full daily workflow possible without /admin.

**Task 3.2 — Weekly review + export**
> Build /review/ as the guided weekly page per spec, storing the three reflection answers (add a small WeeklyReview model), and /export/ with one-click CSV per model. Commit.

✅ Completing a weekly review persists; CSVs open correctly in a spreadsheet.

---

## Phase 4 — ESM + assessments

**Task 4.1 — ESM pings**
> Read SPECIFICATION.md sections 3–4 on ESM. Add APScheduler to the runbot process: daily draw of ESM_PINGS_PER_DAY random times in ESM_WINDOW with ≥ 90-min spacing, Ping records, the ping conversation (activity → challenge/skill/absorption/mood buttons → autotelic), 45-min expiry, EXPIRED for missed. Feed responses into the existing flow-map analytics (they should already flow through if models match spec — verify). Test the time-drawing function. Commit.

✅ Setting ESM_WINDOW to the next few minutes triggers a real ping; answering it adds a point to the flow map; ignoring it expires it.

**Task 4.2 — Assessments via bot**
> Implement /grit and /mindset per spec: refuse with instructions if ScaleItems are missing; otherwise walk items with buttons, apply reverse-scoring, compute totals and subscales, save. Add a monthly reminder (1st of month, 10:00 local) via the scheduler. Build /assessments/ history page if not already covered in 2.2. Known-answer tests for scoring including reverse-scored items. Commit.

✅ After entering items in admin, /grit produces a plausible score; reverse-scoring verified by test.

---

## Phase 5 — Sustainability

**Task 5.1 — Monthly digest + backup**
> Implement the monthly digest (rendered page + text summary sent via bot on the 1st per spec), `make backup`, and a README covering: setup from scratch, BotFather walkthrough, entering scale items, running web+bot (mention how to keep both running, e.g. two terminals or a simple supervisor script), backup/restore. Commit.

✅ Digest renders from seed data; backup file appears in backups/; a stranger could set the project up from the README.

**Task 5.2 — Polish pass**
> Run through the app as a user for each flow in PROJECT_PLAN.md section 4's learning loop and fix friction: confirmation copy, chart labels, mobile-width Telegram messages, dashboard information hierarchy. No new features. Commit.

---

## Stretch (only if asked)

- Optional Claude API pass over journal entries for richer mindset-language analysis (replacing the wordlist score with a rubric-based one; keep the heuristic as fallback).
- iCal export of weekly review reminders.
