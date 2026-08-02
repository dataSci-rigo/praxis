# Praxis — Technical Specification

## 1. Architecture

Single-user, local-first. Two processes sharing one SQLite database via Django ORM:

```
┌─────────────────────┐        ┌──────────────────────────┐
│  Django web server   │        │  Bot process              │
│  manage.py runserver │        │  manage.py runbot         │
│  localhost:8000      │        │  python-telegram-bot      │
│  dashboard/review    │        │  LONG POLLING (no webhook)│
└──────────┬──────────┘        └────────────┬─────────────┘
           │                                 │
           └───────────► SQLite ◄────────────┘
                     (db.sqlite3, WAL mode)
```

- **Stack:** Python 3.12, Django 5.x, python-telegram-bot ≥ 21 (async), Chart.js via CDN for charts, Django templates (no SPA), APScheduler (inside bot process) for ESM pings.
- **Why long polling:** the app runs on a personal machine with no public URL. Polling requires zero network setup.
- **SQLite in WAL mode** (`PRAGMA journal_mode=WAL`) so web and bot processes can read/write concurrently. Both processes are Django management commands so they share settings and ORM.
- **Auth:** Django admin login for the website (localhost only). The bot ignores every Telegram user ID except `TELEGRAM_OWNER_ID` from `.env`.
- **Config via `.env`:** `TELEGRAM_BOT_TOKEN`, `TELEGRAM_OWNER_ID`, `TIME_ZONE` (default `America/Los_Angeles`), `ESM_PINGS_PER_DAY` (default 3), `ESM_WINDOW` (default `09:00-21:00`).

## 2. Django apps

- `goals` — goal hierarchy
- `sessions_log` — practice/flow sessions (named to avoid clashing with django `sessions`)
- `journal` — journal entries, setbacks, mindset language scoring
- `esm` — experience sampling pings and responses
- `assessments` — grit scale and mindset assessment
- `insights` — analytics services + dashboard views
- `bot` — telegram handlers, `runbot` management command
- `library` — book cards (technique summaries)

## 3. Data model

All models get `created_at`/`updated_at`. Timestamps stored UTC, displayed in local TZ.

### goals.Goal
| field | type | notes |
|---|---|---|
| title | CharField(200) | |
| level | choices: TOP, MID, LOW | Duckworth's hierarchy |
| parent | FK self, null | TOP has no parent; LOW must have parent; enforce in `clean()` |
| domain | CharField(50) | e.g. "piano", "career" — free tag |
| description | TextField, blank | the "why", especially for TOP |
| status | choices: ACTIVE, ACHIEVED, DROPPED | dropping low-level goals is healthy (Duckworth); dropping TOP is flagged in UI |
| target_date | DateField, null | |

### sessions_log.Session
| field | type | notes |
|---|---|---|
| kind | choices: DELIBERATE_PRACTICE, FLOW_PERFORMANCE, LEARNING | LEARNING = reading/study, neither DP nor performance |
| goal | FK Goal (LOW or MID) | required |
| started_at / duration_min | DateTime / PositiveInt | |
| — DP-only fields — | | null unless kind=DP |
| stretch_goal | TextField | the specific weakness targeted |
| feedback_received | TextField | what the immediate feedback was |
| refinement | TextField | what to change next rep |
| discomfort | 1–10 | DP *should* trend uncomfortable |
| — Flow-only fields — | | null unless kind=FLOW_PERFORMANCE |
| challenge / skill | 1–10 each | |
| absorption | 1–10 | "lost track of time" |
| enjoyment | 1–10 | |
| had_clear_goal / had_immediate_feedback | bool | flow-conditions checklist |
| notes | TextField, blank | all kinds |

Validation: reject DP fields on flow sessions and vice versa (model `clean()` + bot flow makes this impossible anyway).

### journal.Entry
| field | type | notes |
|---|---|---|
| kind | choices: JOURNAL, SETBACK | |
| body | TextField | raw entry / raw reaction to setback |
| reframe | TextField, blank | required by bot flow when kind=SETBACK |
| goal | FK Goal, null | |
| fixed_score / growth_score | int | computed on save by wordlist heuristic |

**Mindset language heuristic** (`journal/mindset_lang.py`): two configurable wordlists in a JSON fixture. Fixed markers include phrases like "i'm just not", "i can't", "no talent", "not a X person", "always been bad". Growth markers: "yet", "strategy", "next time", "learned", "improve", "practice". Score = count of case-insensitive matches per entry. Crude on purpose; document limitations in the UI tooltip.

### esm.Ping / esm.PingResponse
Ping: `scheduled_for`, `sent_at`, `status` (PENDING/SENT/ANSWERED/EXPIRED — expire after 45 min).
PingResponse: FK ping, `activity` (short text), `challenge` 1–10, `skill` 1–10, `absorption` 1–10, `mood` 1–10, `wish_doing_else` bool, `autotelic` bool ("would you do this for its own sake?").

### assessments.Assessment / assessments.ItemResponse
Assessment: `kind` (GRIT/MINDSET), `taken_at`, `total_score` float, `subscale_json`.
ItemResponse: FK, `item_number`, `value` 1–5 (grit) or 1–6 (mindset).

**Grit Scale mechanics:** 10 items answered 1–5; half are reverse-scored; total = mean of all 10 (max 5.0); odd items → passion subscale, even → perseverance subscale (verify pairing against the source when implementing). **Item text is not stored in this repo** — the owner enters the items once via admin from Duckworth's published scale (angeladuckworth.com/grit-scale or the book's appendix). `ScaleItem` model: `kind`, `number`, `text`, `reverse_scored`.
**Mindset assessment mechanics:** same pattern; owner enters items from Dweck's published assessment; agreement with fixed-mindset statements is reverse-scored; output a 0–100 growth orientation score.

### library.BookCard
`book` (MINDSET/FLOW/GRIT), `title`, `body` (owner-written paraphrase of a technique), `times_shown`. Bot appends a random low-`times_shown` card to ~1 in 4 confirmations.

## 4. Telegram bot

Framework: python-telegram-bot `ConversationHandler`s; inline keyboards for 1–10 ratings and goal picking (buttons, minimal typing). Every conversation ≤ 60 seconds, cancelable with /cancel.

| command | flow |
|---|---|
| /dp | pick goal (buttons, LOW goals of active domains) → "What's the stretch goal — the ONE weakness this session targets?" → after: bot sends a follow-up prompt when you send /done or after `duration`: feedback? refinement? discomfort 1–10 → save. Alt: log retroactively in one pass. |
| /flow | pick goal → duration → challenge/skill/absorption/enjoyment via button rows → clear goal? immediate feedback? → save |
| /learn | pick goal → duration → notes → save (LEARNING session) |
| /setback | "What happened?" → body saved → **immediately**: "Growth reframe — what does this tell you? What's the 'not yet' version?" → reframe required → confirmation echoes the reframe back |
| /journal | free text → saved, language-scored silently |
| /goal | mini-CRUD: list tree, add LOW goal under a picked MID (deeper editing → website) |
| /grit, /mindset | walk the assessment items with 1–5 / 1–6 buttons; refuse if items not yet entered in admin, with instructions |
| /stats | text summary: this week's DP minutes, flow episodes, streak, top flow activity |
| /card | send a random BookCard |
| ESM ping (bot-initiated) | "📍 What are you doing right now?" → activity text → challenge, skill, absorption, mood buttons → autotelic yes/no. Expires after 45 min. |

**ESM scheduling:** at startup and daily at 00:05, APScheduler draws `ESM_PINGS_PER_DAY` random times uniformly in `ESM_WINDOW` with ≥ 90 min spacing, creates PENDING Pings, schedules jobs. Missed (machine off) → EXPIRED, never back-filled.

Security: a middleware-style check drops any update whose `from.id != TELEGRAM_OWNER_ID`.

## 5. Website (Django templates)

| route | page |
|---|---|
| / | **Dashboard** — this week vs last: DP minutes, flow episodes, streak, latest reframe, flow-map thumbnail |
| /goals/ | **Goal tree** — collapsible tree per domain; add/edit/drop nodes; orphan-effort warnings (sessions on DROPPED/ACHIEVED goals); per-node effort totals |
| /sessions/ | filterable list (kind, goal, date range); detail/edit |
| /journal/ | entries list; setbacks shown as raw-vs-reframe pairs; language-ratio badge per entry |
| /review/ | **Weekly review** — guided page: last week's numbers, all setback reframes to re-read, orphaned goals, flow-map delta, and 3 owner-answered questions (kept + stored): what worked / what to change / next week's DP stretch goal |
| /insights/ | full analytics (below) |
| /assessments/ | score history charts, passion vs perseverance subscales, link to retake via bot |
| /library/ | BookCard CRUD |
| /export/ | CSV per model, one click |

Design: server-rendered, Chart.js, light CSS (Pico.css or similar). No JS build step.

## 6. Analytics (insights app) — precise definitions

Implement as pure functions in `insights/services.py`, unit-tested, over querysets. Weeks are Mon–Sun local time.

1. **Flow map.** Scatter of ESM responses + flow sessions: x = challenge, y = skill, centered on the **user's trailing 60-day mean** challenge/skill (Csikszentmihalyi's method — quadrants are relative to personal baselines, not absolute 5s). Quadrants: challenge>mean & skill>mean = **Flow**; challenge>mean & skill≤mean = **Anxiety**; skill>mean & challenge≤mean = **Boredom/Control**; both ≤ mean = **Apathy**. Points colored by quadrant, tooltip shows activity. Table: activities ranked by % of their points in Flow quadrant (min 3 points).
2. **DP → Flow relationship (flagship).** Per week w: `dp_minutes(w)` and `flow_rate(w)` = flow-quadrant ESM responses ÷ total ESM responses (plus flow sessions with absorption ≥ 7 counted as episodes, shown separately). Chart both series; once ≥ 8 weeks of data, show Pearson r between `dp_minutes(w)` and `flow_rate(w+1)` with the caption "correlation, not causation — n is tiny; treat as a mirror, not a verdict."
3. **Consistency (grit).** Current & longest streak of days with ≥ 1 goal-linked session; % active days per trailing 4 weeks; per-MID-goal weekly minutes heatmap (passion = *consistency* over time).
4. **Mindset language trend.** Monthly growth ratio = growth_score ÷ (growth + fixed) across entries; line chart; annotate assessment retake dates.
5. **Deliberate practice quality.** % of DP sessions with all three of stretch_goal/feedback/refinement filled; mean discomfort trend (drifting toward 1–3 suggests comfortable repetition, not DP — show Ericsson-based hint).
6. **Assessment history.** Grit total + subscales over time; mindset score over time.
7. **Monthly digest** (Phase 5): rendered page + text digest sent via bot on the 1st: last month's numbers, best flow activities, re-read reframes, suggested focus.

Empty states everywhere: every chart shows "need N more days of data" rather than a blank.

## 7. Testing

pytest + pytest-django. Priorities: analytics services (fixture-based known-answer tests), model validation (goal hierarchy rules, session kind/field rules), mindset language heuristic, grit scoring (reverse-scoring!), bot conversations via python-telegram-bot's test utilities or by unit-testing handler functions with fake updates. Target: analytics and scoring at ~100%; bot happy-paths covered.

## 8. Non-functional

- Runs with `make web` and `make bot` (or two `manage.py` commands). Provide a `make backup` that copies db.sqlite3 to `backups/` with date suffix.
- No internet dependencies at runtime except Telegram API.
- Migrations committed; `make seed` loads demo fixture data so the dashboard is inspectable before real data exists (demo data clearly flagged and deletable via `make unseed`).
