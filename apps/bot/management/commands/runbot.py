from datetime import time as dtime
from zoneinfo import ZoneInfo

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from telegram.ext import Application

from apps.bot.handlers import all_handlers
from apps.bot.scheduler import (
    monthly_assessment_reminder,
    monthly_digest_message,
    schedule_todays_pings,
)


class Command(BaseCommand):
    help = "Run the Praxis Telegram bot (long polling — never a webhook)."

    def handle(self, *args, **options):
        if not settings.TELEGRAM_BOT_TOKEN:
            raise CommandError("Set TELEGRAM_BOT_TOKEN in .env before running `make bot`.")
        if not settings.TELEGRAM_OWNER_ID:
            raise CommandError("Set TELEGRAM_OWNER_ID in .env before running `make bot`.")

        application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
        application.add_handlers(all_handlers)

        tz = ZoneInfo(settings.TIME_ZONE)
        job_queue = application.job_queue
        job_queue.run_once(schedule_todays_pings, when=1, name="schedule_esm_startup")
        job_queue.run_daily(
            schedule_todays_pings, time=dtime(0, 5, tzinfo=tz), name="schedule_esm_daily"
        )
        job_queue.run_monthly(
            monthly_assessment_reminder,
            when=dtime(10, 0, tzinfo=tz),
            day=1,
            name="monthly_assessment_reminder",
        )
        job_queue.run_monthly(
            monthly_digest_message,
            when=dtime(9, 0, tzinfo=tz),
            day=1,
            name="monthly_digest_message",
        )

        self.stdout.write(self.style.SUCCESS("Praxis bot starting (long polling)..."))
        application.run_polling()
