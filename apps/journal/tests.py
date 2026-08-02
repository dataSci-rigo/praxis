from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.journal.mindset_lang import score_text
from apps.journal.models import Entry


class MindsetLanguageHeuristicTests(TestCase):
    def test_fixed_language_scores_fixed(self):
        # matches "i'm just not", "not a math person", "i can't"
        fixed, growth = score_text("I'm just not a math person, I can't do this.")
        self.assertEqual(fixed, 3)
        self.assertEqual(growth, 0)

    def test_growth_language_scores_growth(self):
        # matches "yet", "next time", "try a different", "strategy"
        fixed, growth = score_text(
            "I haven't mastered it yet — next time I'll try a different strategy."
        )
        self.assertEqual(fixed, 0)
        self.assertEqual(growth, 4)

    def test_neutral_text_scores_zero(self):
        fixed, growth = score_text("Practiced piano for thirty minutes this evening.")
        self.assertEqual(fixed, 0)
        self.assertEqual(growth, 1)  # "practice" is a growth marker

    def test_case_insensitive(self):
        fixed, _ = score_text("I CAN'T do this, NO TALENT for it.")
        self.assertEqual(fixed, 2)


class EntryModelTests(TestCase):
    def test_save_computes_scores(self):
        entry = Entry.objects.create(kind=Entry.JOURNAL, body="I can't do this, no talent.")
        self.assertEqual(entry.fixed_score, 2)
        self.assertEqual(entry.growth_score, 0)

    def test_setback_requires_reframe(self):
        entry = Entry(kind=Entry.SETBACK, body="Missed the recital cue.")
        with self.assertRaises(ValidationError):
            entry.full_clean()

    def test_setback_with_reframe_is_valid(self):
        entry = Entry(
            kind=Entry.SETBACK,
            body="Missed the recital cue.",
            reframe="I hadn't rehearsed the transition enough yet.",
        )
        entry.full_clean()  # should not raise
