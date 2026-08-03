from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters

from apps.bot.asyncdb import db
from apps.bot.confirmations import confirmation_text
from apps.bot.decorators import owner_only
from apps.bot.handlers.common import cancel
from apps.bot.services import create_setback

BODY, REFRAME = range(2)


@owner_only
async def setback_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text("What happened?")
    return BODY


@owner_only
async def setback_body(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["setback_body"] = update.message.text
    await update.message.reply_text(
        "Growth reframe — what does this tell you? What's the 'not yet' version?"
    )
    return REFRAME


@owner_only
async def setback_reframe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reframe = update.message.text
    body = context.user_data["setback_body"]
    await db(create_setback, body=body, reframe=reframe)
    text = await db(confirmation_text, f"✅ Setback logged. Your reframe:\n\n{reframe}")
    await update.message.reply_text(text)
    context.user_data.clear()
    return ConversationHandler.END


setback_conversation = ConversationHandler(
    entry_points=[CommandHandler("setback", setback_entry)],
    states={
        BODY: [MessageHandler(filters.TEXT & ~filters.COMMAND, setback_body)],
        REFRAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, setback_reframe)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)
