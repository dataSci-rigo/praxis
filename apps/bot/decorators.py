from functools import wraps

from django.conf import settings
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler


def owner_only(handler):
    """Drop any update whose sender isn't TELEGRAM_OWNER_ID. Single guard, applied
    to every handler per docs/SPECIFICATION.md section 4."""

    @wraps(handler)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = update.effective_user
        if user is None or user.id != settings.TELEGRAM_OWNER_ID:
            return ConversationHandler.END
        return await handler(update, context, *args, **kwargs)

    return wrapper
