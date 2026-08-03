from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters

from apps.bot.asyncdb import db
from apps.bot.confirmations import confirmation_text
from apps.bot.decorators import owner_only
from apps.bot.handlers.common import cancel
from apps.bot.services import create_journal_entry

BODY = 0


@owner_only
async def journal_entry_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("What's on your mind?")
    return BODY


@owner_only
async def journal_body(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await db(create_journal_entry, body=update.message.text)
    text = await db(confirmation_text, "✅ Journal entry saved.")
    await update.message.reply_text(text)
    return ConversationHandler.END


journal_conversation = ConversationHandler(
    entry_points=[CommandHandler("journal", journal_entry_start)],
    states={BODY: [MessageHandler(filters.TEXT & ~filters.COMMAND, journal_body)]},
    fallbacks=[CommandHandler("cancel", cancel)],
)
