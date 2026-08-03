from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from apps.goals.models import Goal

CANCEL_CALLBACK = "cancel"


def goal_choices(levels: tuple[str, ...] = (Goal.LOW,)) -> list[Goal]:
    """Sync helper — call via apps.bot.asyncdb.db(). Active-domain goals only
    (i.e. not under a DROPPED/ACHIEVED ancestor chain isn't tracked; we just
    filter the goal's own status)."""
    return list(Goal.objects.filter(level__in=levels, status=Goal.ACTIVE).select_related("parent"))


def goal_keyboard(goals: list[Goal]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(f"{g.title} ({g.domain})", callback_data=f"goal:{g.id}")]
        for g in goals
    ]
    rows.append([InlineKeyboardButton("Cancel", callback_data=CANCEL_CALLBACK)])
    return InlineKeyboardMarkup(rows)


def rating_keyboard(prefix: str, low: int = 1, high: int = 10, per_row: int = 5) -> InlineKeyboardMarkup:
    numbers = list(range(low, high + 1))
    rows = [
        [
            InlineKeyboardButton(str(n), callback_data=f"{prefix}:{n}")
            for n in numbers[i : i + per_row]
        ]
        for i in range(0, len(numbers), per_row)
    ]
    return InlineKeyboardMarkup(rows)


def yes_no_keyboard(prefix: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Yes", callback_data=f"{prefix}:yes"),
                InlineKeyboardButton("No", callback_data=f"{prefix}:no"),
            ]
        ]
    )
