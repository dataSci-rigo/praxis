import random
from datetime import time
from unittest.mock import AsyncMock, MagicMock

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from apps.assessments.models import Assessment, ScaleItem
from apps.bot import scheduler, services
from apps.bot.decorators import owner_only
from apps.bot.esm_scheduling import draw_esm_times
from apps.esm.models import Ping
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


class DrawESMTimesTests(TestCase):
    def test_returns_n_times_within_window(self):
        times = draw_esm_times("09:00-21:00", 3, min_spacing_min=90, rng=random.Random(1))
        self.assertEqual(len(times), 3)
        for t in times:
            self.assertGreaterEqual(t, time(9, 0))
            self.assertLessEqual(t, time(21, 0))

    def test_respects_minimum_spacing(self):
        times = draw_esm_times("09:00-21:00", 3, min_spacing_min=90, rng=random.Random(42))
        minutes = [t.hour * 60 + t.minute for t in times]
        for a, b in zip(minutes, minutes[1:]):
            self.assertGreaterEqual(b - a, 90)

    def test_sorted_ascending(self):
        times = draw_esm_times("09:00-21:00", 4, min_spacing_min=60, rng=random.Random(7))
        self.assertEqual(times, sorted(times))

    def test_zero_pings_returns_empty(self):
        self.assertEqual(draw_esm_times("09:00-21:00", 0), [])

    def test_falls_back_to_even_spacing_when_window_too_narrow(self):
        # 3 pings needing 90 min spacing each would need a 180 min span; window is only 60 min.
        times = draw_esm_times("09:00-10:00", 3, min_spacing_min=90, rng=random.Random(3))
        self.assertEqual(len(times), 3)
        for t in times:
            self.assertGreaterEqual(t, time(9, 0))
            self.assertLessEqual(t, time(10, 0))

    def test_invalid_window_raises(self):
        with self.assertRaises(ValueError):
            draw_esm_times("21:00-09:00", 3)


class ESMResponseServiceTests(TestCase):
    def setUp(self):
        self.ping = Ping.objects.create(
            scheduled_for=timezone.now(), sent_at=timezone.now(), status=Ping.SENT
        )

    def test_save_esm_response_marks_ping_answered(self):
        response = services.save_esm_response(
            ping_id=self.ping.id,
            activity="practicing scales",
            challenge=7,
            skill=6,
            absorption=8,
            mood=7,
            wish_doing_else=False,
            autotelic=True,
        )
        self.assertEqual(response.ping_id, self.ping.id)
        self.ping.refresh_from_db()
        self.assertEqual(self.ping.status, Ping.ANSWERED)


class AssessmentServiceTests(TestCase):
    def test_scale_items_for_ordered_by_number(self):
        ScaleItem.objects.create(kind=ScaleItem.GRIT, number=2, text="b")
        ScaleItem.objects.create(kind=ScaleItem.GRIT, number=1, text="a")
        items = services.scale_items_for(ScaleItem.GRIT)
        self.assertEqual([i.number for i in items], [1, 2])

    def test_save_assessment_creates_item_responses(self):
        assessment = services.save_assessment(
            kind=Assessment.GRIT,
            total_score=4.2,
            subscale_json={"passion": 4.0, "perseverance": 4.4},
            item_values={1: 4, 2: 5},
        )
        self.assertEqual(assessment.item_responses.count(), 2)
        self.assertEqual(assessment.total_score, 4.2)


class SchedulerTests(TestCase):
    def test_create_todays_pings_is_idempotent(self):
        # An existing Ping for today should stop a second draw from running.
        Ping.objects.create(scheduled_for=timezone.now(), status=Ping.PENDING)
        created = scheduler._create_todays_pings()
        self.assertEqual(created, [])
        self.assertEqual(Ping.objects.count(), 1)

    def test_create_todays_pings_skips_past_times(self):
        with self.settings(ESM_WINDOW="00:00-00:01", ESM_PINGS_PER_DAY=1):
            created = scheduler._create_todays_pings()
        # 00:00-00:01 is almost certainly in the past by the time this test runs.
        self.assertEqual(created, [])
        self.assertEqual(Ping.objects.count(), 0)

    def test_mark_sent_transitions_pending_to_sent(self):
        ping = Ping.objects.create(scheduled_for=timezone.now(), status=Ping.PENDING)
        self.assertTrue(scheduler._mark_sent(ping.id))
        ping.refresh_from_db()
        self.assertEqual(ping.status, Ping.SENT)
        self.assertIsNotNone(ping.sent_at)

    def test_mark_sent_is_a_noop_if_already_handled(self):
        ping = Ping.objects.create(scheduled_for=timezone.now(), status=Ping.ANSWERED)
        self.assertFalse(scheduler._mark_sent(ping.id))
        ping.refresh_from_db()
        self.assertEqual(ping.status, Ping.ANSWERED)

    def test_expire_if_unanswered_expires_sent_and_pending(self):
        sent = Ping.objects.create(scheduled_for=timezone.now(), status=Ping.SENT)
        scheduler._expire_if_unanswered(sent.id)
        sent.refresh_from_db()
        self.assertEqual(sent.status, Ping.EXPIRED)

    def test_expire_if_unanswered_leaves_answered_pings_alone(self):
        answered = Ping.objects.create(scheduled_for=timezone.now(), status=Ping.ANSWERED)
        scheduler._expire_if_unanswered(answered.id)
        answered.refresh_from_db()
        self.assertEqual(answered.status, Ping.ANSWERED)


class DigestTextTests(TestCase):
    def test_formats_all_sections(self):
        from datetime import date

        digest = {
            "month_start": date(2026, 2, 1),
            "dp_minutes": 120,
            "flow_episodes": 3,
            "best_activities": [{"activity": "guitar", "n": 5, "flow_pct": 80.0}],
            "setbacks": [object()],
            "suggested_focus": "Left-hand runs at tempo",
        }
        text = scheduler.format_digest_text(digest)
        self.assertIn("February 2026", text)
        self.assertIn("120 min", text)
        self.assertIn("guitar", text)
        self.assertIn("1 setback reframe(s)", text)
        self.assertIn("Left-hand runs at tempo", text)

    def test_formats_empty_month_without_crashing(self):
        from datetime import date

        digest = {
            "month_start": date(2026, 2, 1),
            "dp_minutes": 0,
            "flow_episodes": 0,
            "best_activities": [],
            "setbacks": [],
            "suggested_focus": None,
        }
        text = scheduler.format_digest_text(digest)
        self.assertIn("0 min", text)
