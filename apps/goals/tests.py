from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.goals import services
from apps.goals.models import Goal
from apps.sessions_log.models import Session


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


class GoalTreeServiceTests(TestCase):
    def setUp(self):
        self.top = Goal.objects.create(title="Piano mastery", level=Goal.TOP, domain="piano")
        self.mid = Goal.objects.create(
            title="Technique", level=Goal.MID, domain="piano", parent=self.top
        )
        self.low = Goal.objects.create(
            title="Scales", level=Goal.LOW, domain="piano", parent=self.mid
        )

    def test_effort_rolls_up_from_descendants(self):
        Session.objects.create(
            kind=Session.LEARNING,
            goal=self.low,
            started_at=timezone.now(),
            duration_min=20,
            notes="x",
        )
        Session.objects.create(
            kind=Session.LEARNING,
            goal=self.mid,
            started_at=timezone.now(),
            duration_min=5,
            notes="x",
        )
        domains = services.build_goal_tree()
        self.assertEqual(len(domains), 1)
        top_node = domains[0]["tops"][0]
        self.assertEqual(top_node["effort_minutes"], 25)
        mid_node = top_node["children"][0]
        self.assertEqual(mid_node["effort_minutes"], 25)
        low_node = mid_node["children"][0]
        self.assertEqual(low_node["effort_minutes"], 20)

    def test_orphan_sessions_flags_dropped_and_achieved_goals(self):
        Session.objects.create(
            kind=Session.LEARNING,
            goal=self.low,
            started_at=timezone.now(),
            duration_min=20,
            notes="x",
        )
        self.assertEqual(list(services.orphan_sessions()), [])

        self.low.status = Goal.DROPPED
        self.low.save()
        orphans = list(services.orphan_sessions())
        self.assertEqual(len(orphans), 1)
        self.assertEqual(orphans[0].goal, self.low)


class GoalViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="owner", password="pw")
        self.top = Goal.objects.create(title="Piano mastery", level=Goal.TOP, domain="piano")
        self.mid = Goal.objects.create(
            title="Technique", level=Goal.MID, domain="piano", parent=self.top
        )

    def test_tree_requires_login(self):
        response = self.client.get(reverse("goal-tree"))
        self.assertEqual(response.status_code, 302)

    def test_tree_renders_for_logged_in_user(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("goal-tree"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Piano mastery")

    def test_add_low_goal(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("goal-add"),
            {
                "title": "Sight-reading",
                "level": Goal.LOW,
                "parent": self.mid.id,
                "domain": "piano",
                "description": "",
                "status": Goal.ACTIVE,
                "target_date": "",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Goal.objects.filter(title="Sight-reading", parent=self.mid).exists())

    def test_add_low_goal_without_parent_rejected(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("goal-add"),
            {
                "title": "Sight-reading",
                "level": Goal.LOW,
                "domain": "piano",
                "description": "",
                "status": Goal.ACTIVE,
                "target_date": "",
            },
        )
        self.assertEqual(response.status_code, 200)  # re-rendered with form errors
        self.assertFalse(Goal.objects.filter(title="Sight-reading").exists())
