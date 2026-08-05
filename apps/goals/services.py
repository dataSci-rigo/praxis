"""Pure tree-building logic for the /goals/ page — no view/template logic here."""

from collections import defaultdict

from apps.goals.models import Goal
from apps.sessions_log.models import Session


def _own_minutes(goals: list[Goal]) -> dict[int, int]:
    totals: dict[int, int] = defaultdict(int)
    for s in Session.objects.filter(goal__in=goals).values("goal_id", "duration_min"):
        totals[s["goal_id"]] += s["duration_min"]
    return totals


def build_goal_tree() -> list[dict]:
    """Domains, each a list of TOP nodes with nested children, effort_minutes
    rolled up from all descendants (own sessions + every child's total)."""
    goals = list(Goal.objects.select_related("parent"))
    own_minutes = _own_minutes(goals)
    children_map: dict[int, list[Goal]] = defaultdict(list)
    for g in goals:
        if g.parent_id:
            children_map[g.parent_id].append(g)
    for kids in children_map.values():
        kids.sort(key=lambda g: g.title)

    def node(g: Goal) -> dict:
        children = [node(c) for c in children_map[g.id]]
        effort = own_minutes.get(g.id, 0) + sum(c["effort_minutes"] for c in children)
        return {"goal": g, "children": children, "effort_minutes": effort}

    tops = sorted((g for g in goals if g.level == Goal.TOP), key=lambda g: (g.domain, g.title))

    domains: dict[str, list[dict]] = defaultdict(list)
    for top in tops:
        domains[top.domain].append(node(top))
    return [{"domain": domain, "tops": tops} for domain, tops in sorted(domains.items())]


def orphan_sessions():
    """Sessions logged against a goal that's since been dropped or achieved —
    a smell per docs/SPECIFICATION.md section 5."""
    return Session.objects.filter(goal__status__in=[Goal.DROPPED, Goal.ACHIEVED]).select_related(
        "goal"
    )
