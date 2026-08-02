from django.core.exceptions import ValidationError
from django.test import TestCase
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
