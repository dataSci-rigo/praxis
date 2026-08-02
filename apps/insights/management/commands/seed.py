import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.assessments.models import Assessment, ItemResponse
from apps.esm.models import Ping, PingResponse
from apps.goals.models import Goal
from apps.journal.models import Entry
from apps.sessions_log.models import Session

WEEKS = 6
DAYS = WEEKS * 7

DP_ACTIVITIES = ["Scales & arpeggios", "Sight-reading"]
FIXED_SENTENCES = [
    "I'm just not a fast sight-reader, I can't keep up with the metronome.",
    "No talent for this piece — I've always been bad at trills.",
    "I give up on the left-hand runs, that's just who I am.",
]
GROWTH_SENTENCES = [
    "Not there yet on the trill, but slowing down is helping — I learned a lot today.",
    "Next time I'll try a different fingering and practice the transition more.",
    "Getting better at sight-reading — figure out the rhythm first, then the notes.",
]
NEUTRAL_SENTENCES = [
    "Practiced for forty minutes after work, felt pretty ordinary.",
    "Worked through the middle section again, nothing remarkable.",
]
ESM_ACTIVITIES = [
    "practicing scales",
    "sight-reading a new piece",
    "rehearsing the Nocturne",
    "reading music theory",
    "browsing sheet music",
    "planning next week's practice",
]


class Command(BaseCommand):
    help = "Load ~6 weeks of demo data (piano domain), flagged is_demo=True."

    def handle(self, *args, **options):
        if Goal.objects.filter(is_demo=True).exists():
            self.stdout.write(
                self.style.WARNING("Demo data already present — run `make unseed` first.")
            )
            return

        rng = random.Random(42)
        now = timezone.now()

        top = Goal.objects.create(
            title="Become a strong intermediate pianist",
            level=Goal.TOP,
            domain="piano",
            description="The ultimate concern behind all the piano practice.",
            is_demo=True,
        )
        technique = Goal.objects.create(
            title="Technique", level=Goal.MID, domain="piano", parent=top, is_demo=True
        )
        repertoire = Goal.objects.create(
            title="Repertoire", level=Goal.MID, domain="piano", parent=top, is_demo=True
        )
        scales = Goal.objects.create(
            title="Scales & arpeggios",
            level=Goal.LOW,
            domain="piano",
            parent=technique,
            is_demo=True,
        )
        sight_reading = Goal.objects.create(
            title="Sight-reading", level=Goal.LOW, domain="piano", parent=technique, is_demo=True
        )
        nocturne = Goal.objects.create(
            title="Chopin Nocturne Op. 9 No. 2",
            level=Goal.LOW,
            domain="piano",
            parent=repertoire,
            is_demo=True,
        )
        low_goals = [scales, sight_reading, nocturne]

        self._seed_sessions(rng, now, low_goals, technique, repertoire)
        self._seed_esm(rng, now)
        self._seed_journal(rng, now, low_goals)
        self._seed_assessments(now)

        self.stdout.write(self.style.SUCCESS("Seeded ~6 weeks of demo data (piano domain)."))

    def _seed_sessions(self, rng, now, low_goals, technique, repertoire):
        # Deliberate practice — discomfort trends down as reps accumulate, per Ericsson.
        for i in range(15):
            day_offset = DAYS - int(i * DAYS / 15) - rng.randint(0, 2)
            started_at = now - timedelta(days=day_offset, hours=rng.randint(0, 12))
            goal = rng.choice(low_goals)
            discomfort = max(2, 8 - i // 3)
            Session.objects.create(
                kind=Session.DELIBERATE_PRACTICE,
                goal=goal,
                started_at=started_at,
                duration_min=rng.randint(15, 40),
                stretch_goal=f"Clean up the tricky passage in {goal.title}",
                feedback_received="Metronome exposed where I rushed.",
                refinement="Slow it down 20% and rebuild speed gradually.",
                discomfort=discomfort,
                is_demo=True,
            )

        # Flow / performance — spread across all four challenge/skill quadrants.
        quadrants = [(8, 7), (8, 3), (3, 8), (2, 2)]
        for i in range(16):
            day_offset = DAYS - int(i * DAYS / 16) - rng.randint(0, 2)
            started_at = now - timedelta(days=day_offset, hours=rng.randint(0, 12))
            challenge, skill = quadrants[i % len(quadrants)]
            goal = rng.choice([technique, repertoire, *low_goals])
            Session.objects.create(
                kind=Session.FLOW_PERFORMANCE,
                goal=goal,
                started_at=started_at,
                duration_min=rng.randint(20, 50),
                challenge=challenge + rng.randint(-1, 1),
                skill=skill + rng.randint(-1, 1),
                absorption=rng.randint(5, 10)
                if (challenge, skill) == (8, 7)
                else rng.randint(2, 7),
                enjoyment=rng.randint(5, 10),
                had_clear_goal=rng.random() > 0.2,
                had_immediate_feedback=rng.random() > 0.3,
                is_demo=True,
            )

        # Learning sessions.
        for i in range(5):
            day_offset = DAYS - int(i * DAYS / 5) - rng.randint(0, 3)
            started_at = now - timedelta(days=day_offset, hours=rng.randint(0, 12))
            Session.objects.create(
                kind=Session.LEARNING,
                goal=rng.choice([technique, repertoire]),
                started_at=started_at,
                duration_min=rng.randint(15, 30),
                notes="Read a chapter on phrasing and pedal technique.",
                is_demo=True,
            )

    def _seed_esm(self, rng, now):
        for day in range(DAYS):
            for _ in range(rng.choice([1, 2, 2, 3])):
                scheduled_for = now - timedelta(
                    days=day, hours=rng.randint(0, 11), minutes=rng.randint(0, 59)
                )
                ping = Ping.objects.create(
                    scheduled_for=scheduled_for,
                    sent_at=scheduled_for,
                    status=Ping.ANSWERED,
                    is_demo=True,
                )
                challenge, skill = rng.choice([(8, 7), (7, 8), (8, 2), (2, 8), (2, 2), (5, 5)])
                PingResponse.objects.create(
                    ping=ping,
                    activity=rng.choice(ESM_ACTIVITIES),
                    challenge=challenge,
                    skill=skill,
                    absorption=rng.randint(3, 10),
                    mood=rng.randint(3, 10),
                    wish_doing_else=rng.random() < 0.25,
                    autotelic=rng.random() < 0.5,
                )

    def _seed_journal(self, rng, now, low_goals):
        for i in range(20):
            day_offset = DAYS - int(i * DAYS / 20) - rng.randint(0, 2)
            created = now - timedelta(days=day_offset, hours=rng.randint(0, 12))
            is_setback = i % 5 == 0
            if is_setback:
                body = rng.choice(FIXED_SENTENCES)
                entry = Entry.objects.create(
                    kind=Entry.SETBACK,
                    body=body,
                    reframe=rng.choice(GROWTH_SENTENCES),
                    goal=rng.choice(low_goals),
                    is_demo=True,
                )
            else:
                body = rng.choice(FIXED_SENTENCES + GROWTH_SENTENCES + NEUTRAL_SENTENCES)
                entry = Entry.objects.create(
                    kind=Entry.JOURNAL, body=body, goal=rng.choice(low_goals), is_demo=True
                )
            Entry.objects.filter(pk=entry.pk).update(created_at=created)

    def _seed_assessments(self, now):
        for weeks_ago, passion, perseverance in [(6, 3.4, 3.6), (2, 3.8, 4.0)]:
            taken_at = now - timedelta(weeks=weeks_ago)
            total = round((passion + perseverance) / 2, 2)
            assessment = Assessment.objects.create(
                kind=Assessment.GRIT,
                taken_at=taken_at,
                total_score=total,
                subscale_json={"passion": passion, "perseverance": perseverance},
                is_demo=True,
            )
            values = [round(passion)] * 5 + [
                round(perseverance)
            ] * 5  # odd items -> passion, even -> perseverance
            ItemResponse.objects.bulk_create(
                ItemResponse(assessment=assessment, item_number=n, value=v)
                for n, v in enumerate(values, start=1)
            )
