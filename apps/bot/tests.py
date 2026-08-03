from unittest.mock import AsyncMock, MagicMock

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from apps.bot import services
from apps.bot.decorators import owner_only
from apps.goals.models import Goal
from apps.journal.models import Entry
from apps.sessions_log.models import Session


class GoalFixtureMixin:
    def setUp(self):
        self.top = Goal.objects.create(title="Piano mastery", level=Goal.TOP, domain="piano")
        self.mid = Goal.objects.create(
            title="Technique", level=Goal.MID, domain="piano", parent=self.top
        )
        self.low = Goal.objects.create(
            title="Scales", level=Goal.LOW, domain="piano", parent=self.mid
        )


class DPServiceTests(GoalFixtureMixin, TestCase):
    def test_creates_dp_session(self):
        session = services.create_dp_session(
            goal_id=self.low.id,
            started_at=timezone.now(),
            duration_min=30,
            stretch_goal="left hand runs",
            feedback_received="rushed at bar 12",
            refinement="slow down",
            discomfort=7,
        )
        self.assertEqual(session.kind, Session.DELIBERATE_PRACTICE)
        self.assertEqual(Session.objects.count(), 1)


class FlowServiceTests(GoalFixtureMixin, TestCase):
    def test_creates_flow_session(self):
        session = services.create_flow_session(
            goal_id=self.mid.id,
            started_at=timezone.now(),
            duration_min=45,
            challenge=7,
            skill=6,
            absorption=8,
            enjoyment=9,
            had_clear_goal=True,
            had_immediate_feedback=True,
        )
        self.assertEqual(session.kind, Session.FLOW_PERFORMANCE)


class LearningServiceTests(GoalFixtureMixin, TestCase):
    def test_creates_learning_session(self):
        session = services.create_learning_session(
            goal_id=self.low.id, started_at=timezone.now(), duration_min=20, notes="read chapter 3"
        )
        self.assertEqual(session.kind, Session.LEARNING)


class SetbackServiceTests(GoalFixtureMixin, TestCase):
    def test_requires_reframe(self):
        with self.assertRaises(ValidationError):
            services.create_setback(body="Missed the cue", reframe="", goal_id=self.low.id)

    def test_creates_setback_with_reframe(self):
        entry = services.create_setback(
            body="Missed the cue", reframe="Not rehearsed enough yet", goal_id=self.low.id
        )
        self.assertEqual(entry.kind, Entry.SETBACK)


class JournalServiceTests(TestCase):
    def test_creates_journal_entry(self):
        entry = services.create_journal_entry(body="Practiced for 30 minutes.")
        self.assertEqual(entry.kind, Entry.JOURNAL)
        self.assertIsNone(entry.goal_id)


class GoalServiceTests(GoalFixtureMixin, TestCase):
    def test_add_low_goal_inherits_domain(self):
        low = services.add_low_goal(parent_id=self.mid.id, title="Sight-reading")
        self.assertEqual(low.level, Goal.LOW)
        self.assertEqual(low.domain, self.mid.domain)
        self.assertEqual(low.parent, self.mid)

    def test_goal_tree_text_includes_all_levels(self):
        services.add_low_goal(parent_id=self.mid.id, title="Sight-reading")
        text = services.goal_tree_text()
        self.assertIn("Piano mastery", text)
        self.assertIn("Technique", text)
        self.assertIn("Scales", text)
        self.assertIn("Sight-reading", text)

    def test_goal_tree_text_empty(self):
        Goal.objects.all().delete()
        self.assertIn("No goals yet", services.goal_tree_text())


class StatsServiceTests(GoalFixtureMixin, TestCase):
    def test_this_week_stats_counts_sessions(self):
        services.create_dp_session(
            goal_id=self.low.id,
            started_at=timezone.now(),
            duration_min=25,
            stretch_goal="x",
            feedback_received="y",
            refinement="z",
            discomfort=5,
        )
        services.create_flow_session(
            goal_id=self.mid.id,
            started_at=timezone.now(),
            duration_min=40,
            challenge=7,
            skill=6,
            absorption=8,
            enjoyment=9,
            had_clear_goal=True,
            had_immediate_feedback=True,
        )
        stats = services.this_week_stats()
        self.assertEqual(stats["dp_minutes"], 25)
        self.assertEqual(stats["flow_episodes"], 1)


class OwnerOnlyDecoratorTests(TestCase):
    def test_blocks_non_owner(self):
        handler = AsyncMock(return_value="handled")
        guarded = owner_only(handler)

        update = MagicMock()
        update.effective_user.id = 99999999  # not settings.TELEGRAM_OWNER_ID
        context = MagicMock()

        import asyncio

        result = asyncio.run(guarded(update, context))
        handler.assert_not_called()
        self.assertIsNotNone(result)  # ConversationHandler.END

    def test_allows_owner(self):
        from django.conf import settings

        handler = AsyncMock(return_value="handled")
        guarded = owner_only(handler)

        update = MagicMock()
        update.effective_user.id = settings.TELEGRAM_OWNER_ID
        context = MagicMock()

        import asyncio

        result = asyncio.run(guarded(update, context))
        handler.assert_called_once()
        self.assertEqual(result, "handled")
