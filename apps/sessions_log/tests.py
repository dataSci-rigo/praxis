from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.goals.models import Goal
from apps.sessions_log.models import Session


class SessionKindExclusivityTests(TestCase):
    def setUp(self):
        top = Goal.objects.create(title="Piano mastery", level=Goal.TOP, domain="piano")
        self.goal = Goal.objects.create(
            title="Technique", level=Goal.MID, domain="piano", parent=top
        )

    def test_valid_dp_session(self):
        session = Session(
            kind=Session.DELIBERATE_PRACTICE,
            goal=self.goal,
            started_at=timezone.now(),
            duration_min=30,
            stretch_goal="left-hand runs",
            feedback_received="stumbled at bar 12",
            refinement="slow it down next time",
            discomfort=7,
        )
        session.full_clean()  # should not raise

    def test_valid_flow_session(self):
        session = Session(
            kind=Session.FLOW_PERFORMANCE,
            goal=self.goal,
            started_at=timezone.now(),
            duration_min=45,
            challenge=7,
            skill=6,
            absorption=9,
            enjoyment=8,
            had_clear_goal=True,
            had_immediate_feedback=True,
        )
        session.full_clean()  # should not raise

    def test_dp_session_rejects_flow_fields(self):
        session = Session(
            kind=Session.DELIBERATE_PRACTICE,
            goal=self.goal,
            started_at=timezone.now(),
            duration_min=30,
            stretch_goal="left-hand runs",
            challenge=7,
        )
        with self.assertRaises(ValidationError):
            session.full_clean()

    def test_flow_session_rejects_dp_fields(self):
        session = Session(
            kind=Session.FLOW_PERFORMANCE,
            goal=self.goal,
            started_at=timezone.now(),
            duration_min=30,
            challenge=7,
            skill=6,
            absorption=9,
            enjoyment=8,
            stretch_goal="should not be here",
        )
        with self.assertRaises(ValidationError):
            session.full_clean()

    def test_session_requires_mid_or_low_goal(self):
        top = Goal.objects.create(title="Career", level=Goal.TOP, domain="career")
        session = Session(
            kind=Session.LEARNING,
            goal=top,
            started_at=timezone.now(),
            duration_min=20,
        )
        with self.assertRaises(ValidationError):
            session.full_clean()


class SessionListViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="owner", password="pw")
        top = Goal.objects.create(title="Piano mastery", level=Goal.TOP, domain="piano")
        self.mid = Goal.objects.create(
            title="Technique", level=Goal.MID, domain="piano", parent=top
        )
        self.other_mid = Goal.objects.create(
            title="Repertoire", level=Goal.MID, domain="piano", parent=top
        )
        Session.objects.create(
            kind=Session.LEARNING,
            goal=self.mid,
            started_at=timezone.now(),
            duration_min=15,
            notes="x",
        )
        Session.objects.create(
            kind=Session.DELIBERATE_PRACTICE,
            goal=self.other_mid,
            started_at=timezone.now(),
            duration_min=30,
            stretch_goal="x",
            feedback_received="y",
            refinement="z",
            discomfort=5,
        )

    def test_list_requires_login(self):
        self.assertEqual(self.client.get(reverse("session-list")).status_code, 302)

    def test_list_shows_all_by_default(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("session-list"))
        self.assertEqual(len(response.context["sessions"]), 2)

    def test_filter_by_kind(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("session-list"), {"kind": Session.LEARNING})
        self.assertEqual(len(response.context["sessions"]), 1)
        self.assertEqual(response.context["sessions"][0].kind, Session.LEARNING)

    def test_filter_by_goal(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("session-list"), {"goal": self.mid.id})
        self.assertEqual(len(response.context["sessions"]), 1)
        self.assertEqual(response.context["sessions"][0].goal_id, self.mid.id)

    def test_edit_persists(self):
        self.client.force_login(self.user)
        session = Session.objects.get(kind=Session.LEARNING)
        response = self.client.post(
            reverse("session-edit", args=[session.pk]),
            {
                "kind": Session.LEARNING,
                "goal": self.mid.id,
                "started_at": "2026-01-01T10:00",
                "duration_min": 45,
                "notes": "updated notes",
            },
        )
        self.assertEqual(response.status_code, 302)
        session.refresh_from_db()
        self.assertEqual(session.duration_min, 45)
        self.assertEqual(session.notes, "updated notes")
