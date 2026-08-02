from django.core.management.base import BaseCommand

from apps.assessments.models import Assessment
from apps.esm.models import Ping
from apps.goals.models import Goal
from apps.journal.models import Entry
from apps.sessions_log.models import Session


class Command(BaseCommand):
    help = "Remove all demo data loaded by `make seed`."

    def handle(self, *args, **options):
        counts = {
            "sessions": Session.objects.filter(is_demo=True).delete()[0],
            "journal entries": Entry.objects.filter(is_demo=True).delete()[0],
            "pings (+ responses)": Ping.objects.filter(is_demo=True).delete()[0],
            "assessments (+ item responses)": Assessment.objects.filter(is_demo=True).delete()[0],
            # Goals last — Sessions/Entries FK to Goal with CASCADE/SET_NULL.
            "goals": Goal.objects.filter(is_demo=True).delete()[0],
        }
        for label, count in counts.items():
            self.stdout.write(f"  removed {count} {label} row(s)")
        self.stdout.write(self.style.SUCCESS("Demo data removed."))
