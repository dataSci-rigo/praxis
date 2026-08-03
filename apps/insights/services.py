"""Pure analytics functions over querysets — no view/template logic here.
See docs/SPECIFICATION.md section 6 for the precise definitions each function
implements. Every function accepts an optional `as_of` so tests are deterministic."""

import statistics
from datetime import date, datetime, timedelta

from django.utils import timezone

from apps.assessments.models import Assessment
from apps.esm.models import PingResponse
from apps.goals.models import Goal
from apps.journal.models import Entry
from apps.sessions_log.models import Session

FLOW = "flow"
ANXIETY = "anxiety"
BOREDOM = "boredom"
APATHY = "apathy"


def _local_date(dt: datetime) -> date:
    return timezone.localtime(dt).date()


def _week_start(d: date) -> date:
    """Monday of the week containing d."""
    return d - timedelta(days=d.weekday())


def week_range(as_of: datetime | None = None, num_weeks: int = 12) -> list[tuple[date, date]]:
    """`num_weeks` (week_start, week_end) pairs, Mon-Sun local, oldest first,
    ending with the week containing `as_of`."""
    as_of = as_of or timezone.now()
    current_week_start = _week_start(_local_date(as_of))
    return [
        (
            current_week_start - timedelta(weeks=num_weeks - 1 - i),
            current_week_start - timedelta(weeks=num_weeks - 1 - i) + timedelta(days=6),
        )
        for i in range(num_weeks)
    ]


def _classify_quadrant(
    challenge: float, skill: float, mean_challenge: float, mean_skill: float
) -> str:
    if challenge > mean_challenge and skill > mean_skill:
        return FLOW
    if challenge > mean_challenge:
        return ANXIETY
    if skill > mean_skill:
        return BOREDOM
    return APATHY


def flow_map_points(as_of: datetime | None = None, window_days: int = 60) -> dict:
    """Scatter of ESM responses + flow sessions, centered on the trailing
    `window_days`-mean challenge/skill (personal baseline, not absolute 5s)."""
    as_of = as_of or timezone.now()
    start = as_of - timedelta(days=window_days)

    points = [
        {
            "source": "esm",
            "activity": r.activity,
            "challenge": r.challenge,
            "skill": r.skill,
            "occurred_at": r.ping.scheduled_for,
        }
        for r in PingResponse.objects.filter(
            ping__scheduled_for__gte=start, ping__scheduled_for__lte=as_of
        ).select_related("ping")
    ] + [
        {
            "source": "session",
            "activity": s.goal.title,
            "challenge": s.challenge,
            "skill": s.skill,
            "occurred_at": s.started_at,
        }
        for s in Session.objects.filter(
            kind=Session.FLOW_PERFORMANCE, started_at__gte=start, started_at__lte=as_of
        ).select_related("goal")
    ]

    if not points:
        return {"baseline_challenge": None, "baseline_skill": None, "points": []}

    mean_challenge = statistics.fmean(p["challenge"] for p in points)
    mean_skill = statistics.fmean(p["skill"] for p in points)
    for p in points:
        p["quadrant"] = _classify_quadrant(p["challenge"], p["skill"], mean_challenge, mean_skill)

    return {"baseline_challenge": mean_challenge, "baseline_skill": mean_skill, "points": points}


def flow_activity_ranking(
    as_of: datetime | None = None, window_days: int = 60, min_points: int = 3
) -> list[dict]:
    """Activities ranked by % of their points landing in the Flow quadrant."""
    points = flow_map_points(as_of=as_of, window_days=window_days)["points"]
    by_activity: dict[str, list[str]] = {}
    for p in points:
        by_activity.setdefault(p["activity"], []).append(p["quadrant"])

    ranking = [
        {
            "activity": activity,
            "n": len(quadrants),
            "flow_pct": quadrants.count(FLOW) / len(quadrants) * 100,
        }
        for activity, quadrants in by_activity.items()
        if len(quadrants) >= min_points
    ]
    return sorted(ranking, key=lambda r: r["flow_pct"], reverse=True)


def weekly_dp_flow_series(as_of: datetime | None = None, num_weeks: int = 12) -> list[dict]:
    """Per week: dp_minutes, ESM flow_rate (None if no ESM responses that week),
    and flow_episodes (flow sessions with absorption >= 7)."""
    as_of = as_of or timezone.now()
    weeks = week_range(as_of=as_of, num_weeks=num_weeks)
    window_days = num_weeks * 7 + 7  # pad so the oldest week is fully covered

    esm_points = [
        p
        for p in flow_map_points(as_of=as_of, window_days=window_days)["points"]
        if p["source"] == "esm"
    ]
    dp_sessions = list(
        Session.objects.filter(
            kind=Session.DELIBERATE_PRACTICE, started_at__gte=as_of - timedelta(days=window_days)
        )
    )
    flow_sessions = list(
        Session.objects.filter(
            kind=Session.FLOW_PERFORMANCE, started_at__gte=as_of - timedelta(days=window_days)
        )
    )

    series = []
    for week_start, week_end in weeks:
        dp_minutes = sum(
            s.duration_min
            for s in dp_sessions
            if week_start <= _local_date(s.started_at) <= week_end
        )
        week_esm = [
            p for p in esm_points if week_start <= _local_date(p["occurred_at"]) <= week_end
        ]
        flow_rate = (
            (sum(1 for p in week_esm if p["quadrant"] == FLOW) / len(week_esm))
            if week_esm
            else None
        )
        flow_episodes = sum(
            1
            for s in flow_sessions
            if week_start <= _local_date(s.started_at) <= week_end
            and s.absorption is not None
            and s.absorption >= 7
        )
        series.append(
            {
                "week_start": week_start,
                "dp_minutes": dp_minutes,
                "flow_rate": flow_rate,
                "flow_episodes": flow_episodes,
            }
        )
    return series


def dp_flow_correlation(series: list[dict], min_pairs: int = 8) -> float | None:
    """Pearson r between dp_minutes(w) and flow_rate(w+1) — the flagship analytic.
    None until there are at least `min_pairs` weeks with a following week's flow_rate."""
    pairs = [
        (series[i]["dp_minutes"], series[i + 1]["flow_rate"])
        for i in range(len(series) - 1)
        if series[i + 1]["flow_rate"] is not None
    ]
    if len(pairs) < min_pairs:
        return None
    xs, ys = zip(*pairs, strict=True)
    if len(set(xs)) < 2 or len(set(ys)) < 2:
        return None  # statistics.correlation requires variance in both series
    return statistics.correlation(xs, ys)


def _active_dates(as_of: datetime | None = None, lookback_days: int = 120) -> set[date]:
    as_of = as_of or timezone.now()
    start = as_of - timedelta(days=lookback_days)
    return {
        _local_date(s.started_at)
        for s in Session.objects.filter(started_at__gte=start, started_at__lte=as_of)
    }


def streaks(as_of: datetime | None = None, lookback_days: int = 120) -> dict:
    """Current & longest streak of days with >= 1 goal-linked session."""
    as_of = as_of or timezone.now()
    active = _active_dates(as_of, lookback_days)
    today = _local_date(as_of)

    current = 0
    d = today
    while d in active:
        current += 1
        d -= timedelta(days=1)
    if current == 0:
        d = today - timedelta(days=1)
        while d in active:
            current += 1
            d -= timedelta(days=1)

    longest = 0
    if active:
        ordered = sorted(active)
        run = 1
        longest = 1
        for i in range(1, len(ordered)):
            run = run + 1 if ordered[i] == ordered[i - 1] + timedelta(days=1) else 1
            longest = max(longest, run)

    return {"current_streak": current, "longest_streak": longest}


def active_day_percentage(as_of: datetime | None = None, weeks: int = 4) -> float:
    as_of = as_of or timezone.now()
    days = weeks * 7
    return len(_active_dates(as_of, lookback_days=days)) / days * 100


def weekly_minutes_by_mid_goal(as_of: datetime | None = None, num_weeks: int = 12) -> dict:
    """MID-goal weekly-minutes matrix — LOW-goal sessions roll up to their parent MID."""
    as_of = as_of or timezone.now()
    weeks = week_range(as_of=as_of, num_weeks=num_weeks)

    sessions = Session.objects.filter(
        started_at__gte=as_of - timedelta(days=num_weeks * 7 + 7), started_at__lte=as_of
    ).select_related("goal", "goal__parent")

    goal_titles: dict[int, str] = {}
    matrix: dict[int, dict[date, int]] = {}
    for s in sessions:
        mid = s.goal if s.goal.level == Goal.MID else s.goal.parent
        if mid is None:
            continue
        wk = _week_start(_local_date(s.started_at))
        goal_titles[mid.id] = mid.title
        matrix.setdefault(mid.id, {})
        matrix[mid.id][wk] = matrix[mid.id].get(wk, 0) + s.duration_min

    return {"weeks": [w for w, _ in weeks], "goals": goal_titles, "matrix": matrix}


def monthly_mindset_ratio(as_of: datetime | None = None, num_months: int = 6) -> list[dict]:
    """Monthly growth ratio = growth_score / (growth_score + fixed_score) across entries."""
    as_of = as_of or timezone.now()
    start = as_of - timedelta(days=num_months * 31)
    buckets: dict[str, list[int]] = {}
    for e in Entry.objects.filter(created_at__gte=start, created_at__lte=as_of):
        key = timezone.localtime(e.created_at).strftime("%Y-%m")
        bucket = buckets.setdefault(key, [0, 0])
        bucket[0] += e.fixed_score
        bucket[1] += e.growth_score

    result = []
    for key in sorted(buckets):
        fixed, growth = buckets[key]
        total = fixed + growth
        result.append(
            {
                "month": key,
                "growth_ratio": (growth / total) if total else None,
                "fixed": fixed,
                "growth": growth,
            }
        )
    return result


def dp_quality(as_of: datetime | None = None, num_weeks: int = 12) -> dict:
    """% of DP sessions with stretch_goal/feedback/refinement all filled, and
    mean discomfort — drifting toward 1-3 suggests comfortable repetition, not DP."""
    as_of = as_of or timezone.now()
    start = as_of - timedelta(days=num_weeks * 7)
    dp_sessions = list(
        Session.objects.filter(
            kind=Session.DELIBERATE_PRACTICE, started_at__gte=start, started_at__lte=as_of
        )
    )
    if not dp_sessions:
        return {"count": 0, "pct_complete": None, "mean_discomfort": None}

    complete = sum(
        1 for s in dp_sessions if s.stretch_goal and s.feedback_received and s.refinement
    )
    discomforts = [s.discomfort for s in dp_sessions if s.discomfort is not None]
    return {
        "count": len(dp_sessions),
        "pct_complete": complete / len(dp_sessions) * 100,
        "mean_discomfort": statistics.fmean(discomforts) if discomforts else None,
    }


def assessment_history(kind: str = Assessment.GRIT) -> list[dict]:
    return [
        {"taken_at": a.taken_at, "total_score": a.total_score, "subscale": a.subscale_json}
        for a in Assessment.objects.filter(kind=kind).order_by("taken_at")
    ]
