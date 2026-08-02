"""
Crude wordlist heuristic for Dweck's fixed- vs growth-mindset language.
Counts case-insensitive phrase matches; not NLP, not context-aware — see
docs/SPECIFICATION.md section 3 for documented limitations.
"""

import json
from functools import lru_cache
from pathlib import Path

WORDLIST_PATH = Path(__file__).parent / "mindset_wordlists.json"


@lru_cache(maxsize=1)
def _wordlists() -> dict[str, list[str]]:
    return json.loads(WORDLIST_PATH.read_text())


def score_text(text: str) -> tuple[int, int]:
    """Return (fixed_score, growth_score) — counts of matching phrases in text."""
    lists = _wordlists()
    lowered = text.lower()
    fixed_score = sum(lowered.count(phrase) for phrase in lists["fixed"])
    growth_score = sum(lowered.count(phrase) for phrase in lists["growth"])
    return fixed_score, growth_score
