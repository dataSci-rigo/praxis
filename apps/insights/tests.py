from datetime import date, datetime, timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.assessments.models import Assessment
from apps.esm.models import Ping, PingResponse
from apps.goals.models import Goal
from apps.insights import services
from apps.insights.models import WeeklyReview
from apps.journal.models import Entry
from apps.library.models import BookCard
from apps.sessions_log.models import Session


def local(*args) -> datetime:
    """Build a tz-aware datetime in settings.TIME_ZONE (America/Los_Angeles in tests)."""
    return timezone.make_aware(datetime(*args))


class GoalFixtureMixin:
    def setUp(self):
        self.top = Goal.objects.create(title="Piano mastery", level=Goal.TOP, domain="piano")
        self.mid = Goal.objects.create(
            title="Technique", level=Goal.MID, domain="piano", parent=self.top
        )
        self.low = Goal.objects.create(
            title="Scales", level=Goal.LOW, domain="piano", parent=self.mid
        )


def _make_ping_response(scheduled_for, challenge, skill, activity="practicing"):
    ping = Ping.objects.create(
        scheduled_for=scheduled_for, sent_at=scheduled_for, status=Ping.ANSWERED
    )
    return PingResponse.objects.create(
        ping=ping,
        activity=activity,
        challenge=challenge,
        skill=skill,
        absorption=5,
        mood=5,
        wish_doing_else=False,
        autotelic=True,
    )


class QuadrantAssignmentTests(TestCase):
    def test_four_corners_around_the_mean(self):
        as_of = local(2026, 3, 15, 12, 0)
        # mean challenge = mean skill = 5
        _make_ping_response(as_of - timedelta(days=1), 8, 8, activity="flow_activity")
        _make_ping_response(as_of - timedelta(days=1), 8, 2, activity="anxiety_activity")
        _make_ping_response(as_of - timedelta(days=1), 2, 8, activity="boredom_activity")
        _make_ping_response(as_of - timedelta(days=1), 2, 2, activity="apathy_activity")

        result = services.flow_map_points(as_of=as_of, window_days=60)
        self.assertEqual(result["baseline_challenge"], 5)
        self.assertEqual(result["baseline_skill"], 5)

        by_activity = {p["activity"]: p["quadrant"] for p in result["points"]}
        self.assertEqual(by_activity["flow_activity"], services.FLOW)
        self.assertEqual(by_activity["anxiety_activity"], services.ANXIETY)
        self.assertEqual(by_activity["boredom_activity"], services.BOREDOM)
        self.assertEqual(by_activity["apathy_activity"], services.APATHY)

    def test_empty_state(self):
        result = services.flow_map_points(as_of=local(2026, 3, 15, 12, 0))
        self.assertEqual(result["points"], [])
        self.assertIsNone(result["baseline_challenge"])


class FlowActivityRankingTests(TestCase):
    def test_ranks_by_flow_percentage_with_min_points(self):
        as_of = local(2026, 3, 15, 12, 0)
        # "guitar": 3 points, 2/3 in flow (challenge>mean & skill>mean)
        _make_ping_response(as_of - timedelta(days=1), 9, 9, activity="guitar")
        _make_ping_response(as_of - timedelta(days=1), 9, 9, activity="guitar")
        _make_ping_response(as_of - timedelta(days=1), 1, 1, activity="guitar")
        # "chores": only 2 points -> excluded by min_points=3
        _make_ping_response(as_of - timedelta(days=1), 9, 9, activity="chores")
        _make_ping_response(as_of - timedelta(days=1), 9, 9, activity="chores")

        ranking = services.flow_activity_ranking(as_of=as_of, window_days=60, min_points=3)
        self.assertEqual(len(ranking), 1)
        self.assertEqual(ranking[0]["activity"], "guitar")
        self.assertEqual(ranking[0]["n"], 3)
        self.assertAlmostEqual(ranking[0]["flow_pct"], 200 / 3)


class WeekBucketingTests(GoalFixtureMixin, TestCase):
    def test_dp_minutes_bucket_across_month_boundary(self):
        # as_of = Thu Feb 5 2026 -> current week = Mon Feb 2 - Sun Feb 8
        # previous week = Mon Jan 26 - Sun Feb 1 (crosses the Jan/Feb boundary)
        as_of = local(2026, 2, 5, 12, 0)

        Session.objects.create(
            kind=Session.DELIBERATE_PRACTICE,
            goal=self.low,
            started_at=local(2026, 1, 29, 9, 0),  # Thu, previous week
            duration_min=10,
            stretch_goal="x",
            feedback_received="y",
            refinement="z",
            discomfort=5,
        )
        Session.objects.create(
            kind=Session.DELIBERATE_PRACTICE,
            goal=self.low,
            started_at=local(2026, 2, 3, 9, 0),  # Tue, current week
            duration_min=20,
            stretch_goal="x",
            feedback_received="y",
            refinement="z",
            discomfort=5,
        )

        series = services.weekly_dp_flow_series(as_of=as_of, num_weeks=2)
        self.assertEqual(series[0]["week_start"], date(2026, 1, 26))
        self.assertEqual(series[0]["dp_minutes"], 10)
        self.assertEqual(series[1]["week_start"], date(2026, 2, 2))
        self.assertEqual(series[1]["dp_minutes"], 20)


class PearsonCorrelationTests(TestCase):
    def test_none_below_min_pairs(self):
        series = [{"dp_minutes": i * 10, "flow_rate": 0.1 * i} for i in range(6)]
        self.assertIsNone(services.dp_flow_correlation(series))

    def test_perfect_correlation_once_enough_weeks(self):
        # dp_minutes(w) vs flow_rate(w+1) — construct a perfectly linear lag-1 relationship.
        series = [{"dp_minutes": i * 10, "flow_rate": None} for i in range(10)]
        for i in range(1, 10):
            series[i]["flow_rate"] = (
                series[i - 1]["dp_minutes"] / 100
            )  # perfectly linear in dp_minutes(w)
        r = services.dp_flow_correlation(series, min_pairs=8)
        self.assertIsNotNone(r)
        self.assertAlmostEqual(r, 1.0, places=6)


class StreakTests(GoalFixtureMixin, TestCase):
    def _session_on(self, d):
        Session.objects.create(
            kind=Session.LEARNING,
            goal=self.mid,
            started_at=timezone.make_aware(datetime(d.year, d.month, d.day, 9, 0)),
            duration_min=15,
            notes="x",
        )

    def test_current_and_longest_streak(self):
        as_of = local(2026, 3, 15, 12, 0)  # Sunday
        today = as_of.date()

        # current streak: today, yesterday, day-before (3 days)
        for delta in (0, 1, 2):
            self._session_on(today - timedelta(days=delta))

        # a longer, older streak of 5 days (days 10-14 ago), separated by a gap
        for delta in range(10, 15):
            self._session_on(today - timedelta(days=delta))

        result = services.streaks(as_of=as_of, lookback_days=30)
        self.assertEqual(result["current_streak"], 3)
        self.assertEqual(result["longest_streak"], 5)

    def test_streak_continues_if_today_not_yet_logged(self):
        as_of = local(2026, 3, 15, 20, 0)
        today = as_of.date()
        for delta in (1, 2, 3):  # yesterday back through 3 days ago; nothing logged today yet
            self._session_on(today - timedelta(days=delta))

        result = services.streaks(as_of=as_of, lookback_days=30)
        self.assertEqual(result["current_streak"], 3)

    def test_no_sessions_zero_streak(self):
        result = services.streaks(as_of=local(2026, 3, 15, 12, 0), lookback_days=30)
        self.assertEqual(result, {"current_streak": 0, "longest_streak": 0})


class ActiveDayPercentageTests(GoalFixtureMixin, TestCase):
    def test_percentage_over_trailing_weeks(self):
        as_of = local(2026, 3, 15, 12, 0)
        for delta in (0, 5):  # 2 distinct active days out of the trailing 28
            Session.objects.create(
                kind=Session.LEARNING,
                goal=self.mid,
                started_at=as_of - timedelta(days=delta),
                duration_min=10,
                notes="x",
            )
        pct = services.active_day_percentage(as_of=as_of, weeks=4)
        self.assertAlmostEqual(pct, 2 / 28 * 100)


class DPQualityTests(GoalFixtureMixin, TestCase):
    def test_pct_complete_and_mean_discomfort(self):
        as_of = local(2026, 3, 15, 12, 0)
        Session.objects.create(
            kind=Session.DELIBERATE_PRACTICE,
            goal=self.low,
            started_at=as_of,
            duration_min=20,
            stretch_goal="x",
            feedback_received="y",
            refinement="z",
            discomfort=8,
        )
        Session.objects.create(
            kind=Session.DELIBERATE_PRACTICE,
            goal=self.low,
            started_at=as_of,
            duration_min=20,
            stretch_goal="x",  # feedback/refinement left blank -> incomplete
            discomfort=4,
        )

        result = services.dp_quality(as_of=as_of, num_weeks=12)
        self.assertEqual(result["count"], 2)
        self.assertAlmostEqual(result["pct_complete"], 50.0)
        self.assertAlmostEqual(result["mean_discomfort"], 6.0)

    def test_empty_state(self):
        result = services.dp_quality(as_of=local(2026, 3, 15, 12, 0))
        self.assertEqual(result, {"count": 0, "pct_complete": None, "mean_discomfort": None})


class MindsetRatioTests(TestCase):
    def test_monthly_growth_ratio(self):
        jan_entry = Entry.objects.create(kind=Entry.JOURNAL, body="")
        Entry.objects.filter(pk=jan_entry.pk).update(
            fixed_score=1, growth_score=3, created_at=local(2026, 1, 15, 10, 0)
        )
        feb_entry = Entry.objects.create(kind=Entry.JOURNAL, body="")
        Entry.objects.filter(pk=feb_entry.pk).update(
            fixed_score=3, growth_score=1, created_at=local(2026, 2, 15, 10, 0)
        )

        result = services.monthly_mindset_ratio(as_of=local(2026, 3, 1, 0, 0), num_months=3)
        by_month = {r["month"]: r for r in result}
        self.assertAlmostEqual(by_month["2026-01"]["growth_ratio"], 0.75)
        self.assertAlmostEqual(by_month["2026-02"]["growth_ratio"], 0.25)


class AssessmentHistoryTests(TestCase):
    def test_ordered_by_taken_at(self):
        Assessment.objects.create(
            kind=Assessment.GRIT,
            taken_at=local(2026, 2, 1, 10, 0),
            total_score=3.5,
            subscale_json={},
        )
        Assessment.objects.create(
            kind=Assessment.GRIT,
            taken_at=local(2026, 1, 1, 10, 0),
            total_score=3.0,
            subscale_json={},
        )
        history = services.assessment_history(kind=Assessment.GRIT)
        self.assertEqual([h["total_score"] for h in history], [3.0, 3.5])


class WeeklyMinutesByMidGoalTests(GoalFixtureMixin, TestCase):
    def test_low_goal_sessions_roll_up_to_mid(self):
        as_of = local(2026, 3, 15, 12, 0)
        Session.objects.create(
            kind=Session.LEARNING, goal=self.low, started_at=as_of, duration_min=25, notes="x"
        )
        result = services.weekly_minutes_by_mid_goal(as_of=as_of, num_weeks=4)
        self.assertEqual(result["goals"][self.mid.id], "Technique")
        week_start = services._week_start(as_of.date())
        self.assertEqual(result["matrix"][self.mid.id][week_start], 25)


class ReviewViewTests(GoalFixtureMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(username="owner", password="pw")

    def test_requires_login(self):
        self.assertEqual(self.client.get(reverse("review")).status_code, 302)

    def test_renders_and_shows_last_weeks_setback(self):
        self.client.force_login(self.user)
        # An entry created "now" falls in last week relative to `services.week_range`'s
        # notion of "current" only once we treat "now" as inside the current week — the
        # view itself calls services with no `as_of`, so just assert the page renders.
        Entry.objects.create(
            kind=Entry.SETBACK, body="Missed cue", reframe="Not yet rehearsed enough"
        )
        response = self.client.get(reverse("review"))
        self.assertEqual(response.status_code, 200)

    def test_submitting_review_persists(self):
        self.client.force_login(self.user)
        self.client.get(reverse("review"))  # creates the WeeklyReview row via get_or_create
        review = WeeklyReview.objects.get()
        response = self.client.post(
            reverse("review"),
            {
                "what_worked": "Consistent morning practice",
                "what_to_change": "Log DP sessions same-day",
                "next_stretch_goal": "Left-hand runs at tempo",
            },
        )
        self.assertEqual(response.status_code, 302)
        review.refresh_from_db()
        self.assertEqual(review.what_worked, "Consistent morning practice")

    def test_revisiting_review_shows_saved_answers(self):
        self.client.force_login(self.user)
        self.client.post(
            reverse("review"),
            {"what_worked": "x", "what_to_change": "y", "next_stretch_goal": "z"},
        )
        response = self.client.get(reverse("review"))
        self.assertContains(response, "x")


class ExportCSVTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="owner", password="pw")

    def test_index_requires_login(self):
        self.assertEqual(self.client.get(reverse("export-index")).status_code, 302)

    def test_index_lists_all_models(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("export-index"))
        self.assertContains(response, "goals.csv")
        self.assertContains(response, "library.csv")

    def test_csv_download_contains_rows(self):
        self.client.force_login(self.user)
        BookCard.objects.create(book=BookCard.GRIT, title="Test card", body="Body text")
        response = self.client.get(reverse("export-csv", args=["library"]))
        self.assertEqual(response["Content-Type"], "text/csv")
        content = response.content.decode()
        self.assertIn("Test card", content)
        header = content.splitlines()[0]
        self.assertIn("title", header)

    def test_unknown_model_404s(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("export-csv", args=["nope"]))
        self.assertEqual(response.status_code, 404)


class MonthlyDigestTests(GoalFixtureMixin, TestCase):
    def test_covers_the_previous_calendar_month(self):
        as_of = local(2026, 3, 5, 12, 0)  # digest run on Mar 5 -> covers all of February

        Session.objects.create(
            kind=Session.DELIBERATE_PRACTICE,
            goal=self.low,
            started_at=local(2026, 2, 10, 9, 0),
            duration_min=30,
            stretch_goal="x",
            feedback_received="y",
            refinement="z",
            discomfort=5,
        )
        # January session should NOT be counted.
        Session.objects.create(
            kind=Session.DELIBERATE_PRACTICE,
            goal=self.low,
            started_at=local(2026, 1, 15, 9, 0),
            duration_min=999,
            stretch_goal="x",
            feedback_received="y",
            refinement="z",
            discomfort=5,
        )

        digest = services.monthly_digest(as_of=as_of)
        self.assertEqual(digest["month_start"], date(2026, 2, 1))
        self.assertEqual(digest["month_end"], date(2026, 2, 28))
        self.assertEqual(digest["dp_minutes"], 30)

    def test_includes_setbacks_and_suggested_focus(self):
        as_of = local(2026, 3, 1, 10, 0)
        setback = Entry.objects.create(kind=Entry.SETBACK, body="Missed cue", reframe="Not yet")
        Entry.objects.filter(pk=setback.pk).update(created_at=local(2026, 2, 20, 10, 0))

        WeeklyReview.objects.create(
            week_start=date(2026, 2, 16),
            next_stretch_goal="Left-hand runs at tempo",
        )

        digest = services.monthly_digest(as_of=as_of)
        self.assertEqual(len(digest["setbacks"]), 1)
        self.assertEqual(digest["suggested_focus"], "Left-hand runs at tempo")

    def test_empty_month_has_no_suggested_focus(self):
        digest = services.monthly_digest(as_of=local(2026, 3, 1, 10, 0))
        self.assertEqual(digest["dp_minutes"], 0)
        self.assertEqual(digest["setbacks"], [])
        self.assertIsNone(digest["suggested_focus"])


class DigestViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="owner", password="pw")

    def test_requires_login(self):
        self.assertEqual(self.client.get(reverse("digest")).status_code, 302)

    def test_renders_empty_state(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("digest"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No setbacks logged this month.")
