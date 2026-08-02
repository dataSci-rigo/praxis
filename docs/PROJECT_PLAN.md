# Praxis — Project Plan

A personal system for practicing the core ideas of *Mindset* (Carol Dweck), *Flow* (Mihaly Csikszentmihalyi), and *Grit* (Angela Duckworth). Capture happens primarily through a Telegram bot; review, editing, and analytics happen on a local Django website. Single user, runs on your own machine.

**Working name:** Praxis (rename freely).

---

## 1. Why this project exists

The three books converge on one claim: sustained, structured effort on self-chosen goals — with the right interpretation of setbacks — is how people get good at things and enjoy the process. But reading the books isn't practicing them. This system turns their practical steps into daily, low-friction behaviors:

- **Dweck** → interpret setbacks as information ("not yet"), praise process over outcome, notice fixed-mindset self-talk and reframe it.
- **Csikszentmihalyi** → engineer the conditions for flow (clear goals, immediate feedback, challenge/skill balance) and measure your actual experience with sampling, not memory.
- **Duckworth** → build a goal hierarchy (one top-level goal, supporting mid-level goals, daily low-level tasks), do deliberate practice with its four requirements, and value consistency over intensity.

## 2. The core design principle: deliberate practice ≠ flow

Duckworth flags this contradiction directly in *Grit* (ch. 7, "Practice"): Ericsson's deliberate practice is effortful, uncomfortable, and focused on weaknesses — the opposite of flow's effortless absorption. Her resolution: **deliberate practice is for preparation; flow is for performance.** Experts suffer in the practice room so they can lose themselves on stage.

This system therefore refuses to merge the two into one "productivity session" concept. It tracks them as distinct session types with distinct fields:

| | Deliberate practice | Flow / performance |
|---|---|---|
| Feels like | Effortful, often frustrating | Effortless, absorbing |
| Focus | A specific weakness (stretch goal) | The whole activity |
| Requires | Full concentration, immediate feedback, repetition with refinement | Challenge/skill balance, clear goals |
| Logged fields | stretch goal, what feedback you got, what you'll refine | challenge, skill, absorption, enjoyment |

The flagship analytic is the relationship between the two: *do weeks with more deliberate practice minutes precede weeks with more flow episodes?* That is the books' promise, tested on your own data.

## 3. What each book contributes to the feature set

### Dweck — Mindset
- **Setback log with forced reframe.** When you log a setback via Telegram, the bot immediately asks for a growth reframe ("What does this tell you? What's the 'not yet' version?"). Both the raw reaction and the reframe are stored.
- **Self-talk language tracking.** Journal entries are scored with a simple wordlist heuristic for fixed-mindset markers ("I'm just not", "I can't", "talent", "natural") vs growth markers ("yet", "strategy", "next time", "learned"). The ratio is charted over months.
- **Mindset self-assessment**, retaken monthly (mechanics in spec; item text sourced from Dweck's published materials).

### Csikszentmihalyi — Flow
- **Experience Sampling Method (ESM), his actual research method.** The bot pings you at random times within waking hours: what are you doing, challenge (1–10), skill (1–10), absorption, mood. Over weeks this maps your personal flow/anxiety/boredom/apathy quadrants and reveals which activities reliably produce flow.
- **Flow conditions checklist** on performance sessions: did you have a clear goal? immediate feedback? Distractions?
- **Autotelic tagging** — mark which activities you'd do for their own sake.

### Duckworth — Grit
- **Goal hierarchy.** A tree per domain: one top-level goal ("ultimate concern"), mid-level goals, low-level daily tasks. Every session and task must link to a node; orphan effort is surfaced as a smell.
- **Deliberate practice protocol.** The `/dp` conversation walks the four Ericsson requirements: stretch goal → focused work → feedback → reflection/refinement. Duckworth's advice to make it a habit (same time, same place) is supported by streak tracking.
- **Grit Scale**, retaken monthly, with passion and perseverance subscales charted separately (her point: passion = consistency of interests over time, not intensity).
- **Consistency analytics.** Days-active percentage and streaks per goal — "grit is living life like a marathon."

## 4. Learning loop (how you'll actually internalize the books)

1. **Capture** on Telegram in under 60 seconds per event (sessions, setbacks, pings, journal).
2. **Review** weekly on the website: read your setback reframes, check the flow map, see orphaned goals.
3. **Measure** monthly: retake Grit Scale and mindset assessment; read the auto-generated monthly digest.
4. **Adjust**: prune the goal tree, raise/lower challenge on activities stuck in boredom/anxiety quadrants, pick next month's deliberate-practice stretch goals.

A small library of "book cards" (short paraphrased summaries of each practical technique, written by you as you re-read) is stored in the app and randomly appended to bot confirmations — spaced repetition of the ideas themselves.

## 5. Build phases

| Phase | Deliverable | Why this order |
|---|---|---|
| 0 | Django project, data model, admin, fixtures | Data model is the analytics foundation |
| 1 | Telegram bot: /dp, /flow, /setback, /journal, /goal (long polling) | No data → no analytics |
| 2 | Analytics dashboard (your #1 priority) | Becomes useful ~2 weeks after Phase 1 |
| 3 | Web review UI: goal tree, session/journal CRUD, weekly review page | Replaces admin for daily use |
| 4 | ESM random pings + monthly assessment reminders | Scheduler on top of a working bot |
| 5 | Monthly digest, CSV export, backups, polish | Long-term sustainability |

Each phase is independently useful; stop anywhere and you still have a working tool.

## 6. Success criteria

- Logging any event via Telegram takes < 60 seconds.
- After 4 weeks: flow map has ≥ 40 data points; ≥ 10 deliberate practice sessions logged.
- After 8 weeks: DP-vs-flow weekly correlation is computable and displayed.
- You can answer, from data: *Which activities put me in flow? Am I practicing deliberately or just repeating? Is my self-talk shifting toward growth language?*

## 7. Out of scope (v1)

Multi-user support, mobile app, cloud deployment, social features, LLM-based journaling analysis (a heuristic wordlist ships first; an optional Claude API pass is a stretch goal), calendar integration.
