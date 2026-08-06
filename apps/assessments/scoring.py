"""Pure scoring functions for the Grit Scale and Mindset Assessment.
See docs/SPECIFICATION.md section 3 for the mechanics each implements."""

import statistics

GRIT_SCALE_MAX = 5
MINDSET_SCALE_MAX = 6


def _reverse(value: int, scale_max: int) -> int:
    return scale_max + 1 - value


def score_grit(item_values: dict[int, int], reverse_map: dict[int, bool]) -> tuple[float, dict]:
    """item_values: {item_number: raw 1-5 rating}. Odd items -> passion subscale,
    even items -> perseverance (Duckworth's pairing). Total = mean of all 10,
    max 5.0, after reverse-scoring the items flagged in `reverse_map`."""
    scored = {
        n: _reverse(v, GRIT_SCALE_MAX) if reverse_map.get(n) else v for n, v in item_values.items()
    }
    total = statistics.fmean(scored.values())
    passion = statistics.fmean(v for n, v in scored.items() if n % 2 == 1)
    perseverance = statistics.fmean(v for n, v in scored.items() if n % 2 == 0)
    return round(total, 2), {"passion": round(passion, 2), "perseverance": round(perseverance, 2)}


def score_mindset(item_values: dict[int, int], reverse_map: dict[int, bool]) -> tuple[float, dict]:
    """item_values: {item_number: raw 1-6 rating}. Items in `reverse_map` are
    agreement-with-fixed-mindset statements, reverse-scored so higher always
    means more growth-oriented. Output: 0-100 growth orientation score."""
    scored = {
        n: _reverse(v, MINDSET_SCALE_MAX) if reverse_map.get(n) else v
        for n, v in item_values.items()
    }
    mean = statistics.fmean(scored.values())
    growth_score = (mean - 1) / (MINDSET_SCALE_MAX - 1) * 100
    return round(growth_score, 1), {}
