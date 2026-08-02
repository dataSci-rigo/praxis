from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.goals.models import Goal


class GoalHierarchyTests(TestCase):
    def test_top_level_forbids_parent(self):
        top = Goal.objects.create(title="Piano mastery", level=Goal.TOP, domain="piano")
        bogus = Goal(title="Bad", level=Goal.TOP, domain="piano", parent=top)
        with self.assertRaises(ValidationError):
            bogus.full_clean()

    def test_low_level_requires_parent(self):
        low = Goal(title="Practice scales", level=Goal.LOW, domain="piano")
        with self.assertRaises(ValidationError):
            low.full_clean()

    def test_mid_parent_must_be_top(self):
        top = Goal.objects.create(title="Piano mastery", level=Goal.TOP, domain="piano")
        mid = Goal.objects.create(title="Technique", level=Goal.MID, domain="piano", parent=top)
        bad_low = Goal(title="Scales", level=Goal.LOW, domain="piano", parent=top)
        with self.assertRaises(ValidationError):
            bad_low.full_clean()

        low = Goal(title="Scales", level=Goal.LOW, domain="piano", parent=mid)
        low.full_clean()  # should not raise

    def test_full_valid_tree(self):
        top = Goal.objects.create(title="Piano mastery", level=Goal.TOP, domain="piano")
        mid = Goal.objects.create(title="Technique", level=Goal.MID, domain="piano", parent=top)
        low = Goal.objects.create(title="Scales", level=Goal.LOW, domain="piano", parent=mid)
        self.assertEqual(low.parent, mid)
        self.assertEqual(mid.parent, top)
