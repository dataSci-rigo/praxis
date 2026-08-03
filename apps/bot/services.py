"""Pure, synchronous save logic for bot conversations — unit-tested directly,
without any Telegram mocking. Handlers call these via apps.bot.asyncdb.db()."""

from datetime import datetime

from django.utils import timezone

from apps.goals.models import Goal
from apps.journal.models import Entry
from apps.sessions_log.models import Session


def create_dp_session(
    *,
    goal_id: int,
    started_at: datetime,
    duration_min: int,
    stretch_goal: str,
    feedback_received: str,
    refinement: str,
    discomfort: int,
) -> Session:
    session = Session(
        kind=Session.DELIBERATE_PRACTICE,
        goal_id=goal_id,
        started_at=started_at,
        duration_min=duration_min,
        stretch_goal=stretch_goal,
        feedback_received=feedback_received,
        refinement=refinement,
        discomfort=discomfort,
    )
    session.full_clean()
    session.save()
    return session


def create_flow_session(
    *,
    goal_id: int,
    started_at: datetime,
    duration_min: int,
    challenge: int,
    skill: int,
    absorption: int,
    enjoyment: int,
    had_clear_goal: bool,
    had_immediate_feedback: bool,
) -> Session:
    session = Session(
        kind=Session.FLOW_PERFORMANCE,
        goal_id=goal_id,
        started_at=started_at,
        duration_min=duration_min,
        challenge=challenge,
        skill=skill,
        absorption=absorption,
        enjoyment=enjoyment,
        had_clear_goal=had_clear_goal,
        had_immediate_feedback=had_immediate_feedback,
    )
    session.full_clean()
    session.save()
    return session


def create_learning_session(
    *, goal_id: int, started_at: datetime, duration_min: int, notes: str
) -> Session:
    session = Session(
        kind=Session.LEARNING,
        goal_id=goal_id,
        started_at=started_at,
        duration_min=duration_min,
        notes=notes,
    )
    session.full_clean()
    session.save()
    return session


def create_setback(*, body: str, reframe: str, goal_id: int | None = None) -> Entry:
    entry = Entry(kind=Entry.SETBACK, body=body, reframe=reframe, goal_id=goal_id)
    entry.full_clean()
    entry.save()
    return entry


def create_journal_entry(*, body: str, goal_id: int | None = None) -> Entry:
    entry = Entry(kind=Entry.JOURNAL, body=body, goal_id=goal_id)
    entry.full_clean()
    entry.save()
    return entry


def add_low_goal(*, parent_id: int, title: str) -> Goal:
    parent = Goal.objects.get(pk=parent_id)
    goal = Goal(title=title, level=Goal.LOW, domain=parent.domain, parent=parent)
    goal.full_clean()
    goal.save()
    return goal


def goal_tree_text() -> str:
    """Render the full active goal tree, grouped by domain, as plain text."""
    tops = Goal.objects.filter(level=Goal.TOP).order_by("domain", "title")
    if not tops:
        return "No goals yet — add one from the website or /goal."

    lines: list[str] = []
    for top in tops:
        status_tag = "" if top.status == Goal.ACTIVE else f" [{top.status}]"
        lines.append(f"🎯 {top.title}{status_tag}  ({top.domain})")
        for mid in top.children.order_by("title"):
            mid_tag = "" if mid.status == Goal.ACTIVE else f" [{mid.status}]"
            lines.append(f"  ├─ {mid.title}{mid_tag}")
            for low in mid.children.order_by("title"):
                low_tag = "" if low.status == Goal.ACTIVE else f" [{low.status}]"
                lines.append(f"  │   ├─ {low.title}{low_tag}")
    return "\n".join(lines)


def this_week_stats() -> dict:
    """Basic numbers for /stats — full analytics land in Phase 2."""
    now = timezone.localtime()
    week_start = (now - timezone.timedelta(days=now.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    week_sessions = Session.objects.filter(started_at__gte=week_start)
    dp_minutes = sum(s.duration_min for s in week_sessions.filter(kind=Session.DELIBERATE_PRACTICE))
    flow_episodes = week_sessions.filter(kind=Session.FLOW_PERFORMANCE).count()
    return {"dp_minutes": dp_minutes, "flow_episodes": flow_episodes}
