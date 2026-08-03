"""Confirmation copy with a spaced-repetition book-card append.

~1 in 4 save confirmations get a random low-times_shown BookCard tacked on,
per docs/SPECIFICATION.md sections 3/4 (library app).
"""

import random

from apps.library.models import BookCard

CARD_CHANCE = 0.25


def _draw_card() -> BookCard | None:
    card = BookCard.objects.order_by("times_shown", "?").first()
    if card is not None:
        BookCard.objects.filter(pk=card.pk).update(times_shown=card.times_shown + 1)
    return card


def confirmation_text(base: str) -> str:
    """Sync — call via apps.bot.asyncdb.db()."""
    if random.random() >= CARD_CHANCE:
        return base
    card = _draw_card()
    if card is None:
        return base
    return f"{base}\n\n📖 [{card.book}] {card.title}\n{card.body}"


def random_card_text() -> str:
    """Sync — call via apps.bot.asyncdb.db(). Used by /card, always returns a card."""
    card = _draw_card()
    if card is None:
        return "No book cards yet."
    return f"📖 [{card.book}] {card.title}\n{card.body}"
