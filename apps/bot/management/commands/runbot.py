from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from telegram.ext import Application

from apps.bot.handlers import all_handlers


class Command(BaseCommand):
    help = "Run the Praxis Telegram bot (long polling — never a webhook)."

    def handle(self, *args, **options):
        if not settings.TELEGRAM_BOT_TOKEN:
            raise CommandError("Set TELEGRAM_BOT_TOKEN in .env before running `make bot`.")
        if not settings.TELEGRAM_OWNER_ID:
            raise CommandError("Set TELEGRAM_OWNER_ID in .env before running `make bot`.")

        application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
        application.add_handlers(all_handlers)

        self.stdout.write(self.style.SUCCESS("Praxis bot starting (long polling)..."))
        application.run_polling()
