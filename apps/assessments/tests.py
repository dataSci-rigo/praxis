from django.test import TestCase

from apps.assessments.scoring import score_grit, score_mindset


class GritScoringTests(TestCase):
    def test_reverse_scoring_flips_even_items(self):
        # Odd items rated 5 (kept as-is), even items rated 1 but flagged
        # reverse-scored -> 6-1=5, so a "grittier" respondent nets a high score
        # despite a low raw rating on those items.
        values = {1: 5, 2: 1, 3: 5, 4: 1, 5: 5, 6: 1, 7: 5, 8: 1, 9: 5, 10: 1}
        reverse_map = {2: True, 4: True, 6: True, 8: True, 10: True}

        total, subscale = score_grit(values, reverse_map)
        self.assertEqual(total, 5.0)
        self.assertEqual(subscale["passion"], 5.0)
        self.assertEqual(subscale["perseverance"], 5.0)

    def test_without_reverse_scoring_low_raw_even_items_drag_score_down(self):
        values = {1: 5, 2: 1, 3: 5, 4: 1, 5: 5, 6: 1, 7: 5, 8: 1, 9: 5, 10: 1}
        total, subscale = score_grit(values, reverse_map={})
        self.assertEqual(total, 3.0)
        self.assertEqual(subscale["passion"], 5.0)
        self.assertEqual(subscale["perseverance"], 1.0)

    def test_odd_items_are_passion_even_are_perseverance(self):
        values = {n: 3 for n in range(1, 11)}
        total, subscale = score_grit(values, reverse_map={})
        self.assertEqual(total, 3.0)
        self.assertEqual(subscale["passion"], 3.0)
        self.assertEqual(subscale["perseverance"], 3.0)


class MindsetScoringTests(TestCase):
    def test_reverse_scoring_fixed_mindset_items(self):
        # Items 2 and 4 are "agreement with a fixed-mindset statement" — low
        # raw agreement (1) should reverse-score to a high growth contribution.
        values = {1: 6, 2: 1, 3: 6, 4: 1}
        reverse_map = {2: True, 4: True}
        score, subscale = score_mindset(values, reverse_map)
        self.assertEqual(score, 100.0)
        self.assertEqual(subscale, {})

    def test_without_reverse_scoring(self):
        values = {1: 6, 2: 1, 3: 6, 4: 1}
        score, _ = score_mindset(values, reverse_map={})
        self.assertEqual(score, 50.0)

    def test_midpoint_scores_fifty(self):
        values = {1: 3, 2: 4}  # mean 3.5 is the scale midpoint on 1-6
        score, _ = score_mindset(values, reverse_map={})
        self.assertEqual(score, 50.0)
