"""Pure ESM time-drawing logic — no Telegram/APScheduler/Django here, so it's
directly unit-testable. See docs/SPECIFICATION.md section 4 ("ESM scheduling")."""

import random
from datetime import time


def draw_esm_times(
    window: str, n: int, min_spacing_min: int = 90, rng: random.Random | None = None
) -> list[time]:
    """Draw `n` random times within `window` ("HH:MM-HH:MM"), each at least
    `min_spacing_min` apart, sorted ascending. Falls back to evenly-spaced times
    if the window is too narrow for random draws to satisfy the spacing
    constraint within a bounded number of attempts."""
    if n <= 0:
        return []

    rng = rng or random.Random()
    start_str, end_str = window.split("-")
    start_h, start_m = (int(p) for p in start_str.split(":"))
    end_h, end_m = (int(p) for p in end_str.split(":"))
    start_total = start_h * 60 + start_m
    end_total = end_h * 60 + end_m
    span = end_total - start_total
    if span <= 0:
        raise ValueError(f"ESM_WINDOW end must be after start, got {window!r}")

    for _ in range(500):
        candidates = sorted(rng.randint(start_total, end_total) for _ in range(n))
        if all(b - a >= min_spacing_min for a, b in zip(candidates, candidates[1:])):
            return [time(hour=t // 60, minute=t % 60) for t in candidates]

    # Window too narrow for the spacing constraint — fall back to even spacing
    # so we always return exactly n times rather than looping forever.
    step = span / (n - 1) if n > 1 else 0
    evenly = [min(round(start_total + i * step), end_total) for i in range(n)]
    return [time(hour=t // 60, minute=t % 60) for t in evenly]
