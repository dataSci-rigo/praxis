from telegram import Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from apps.bot.asyncdb import db
from apps.bot.confirmations import confirmation_text
from apps.bot.decorators import owner_only
from apps.bot.handlers.common import cancel
from apps.bot.keyboards import CANCEL_CALLBACK, goal_choices, goal_keyboard
from apps.bot.services import create_learning_session
from apps.goals.models import Goal
from django.utils import timezone

GOAL, DURATION, NOTES = range(3)


@owner_only
async def learn_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    goals = await db(goal_choices, (Goal.MID, Goal.LOW))
    if not goals:
        await update.message.reply_text("No goals yet — add one with /goal first.")
        return ConversationHandler.END
    await update.message.reply_text("Learning session — pick a goal:", reply_markup=goal_keyboard(goals))
    return GOAL


@owner_only
async def learn_goal_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.data == CANCEL_CALLBACK:
        await query.edit_message_text("Cancelled.")
        return ConversationHandler.END
    context.user_data["learn_goal_id"] = int(query.data.split(":")[1])
    await query.edit_message_text("How many minutes?")
    return DURATION


@owner_only
async def learn_duration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message.text.isdigit():
        await update.message.reply_text("Send a number of minutes, please.")
        return DURATION
    context.user_data["learn_duration_min"] = int(update.message.text)
    await update.message.reply_text("Any notes?")
    return NOTES


@owner_only
async def learn_notes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    data = context.user_data
    await db(
        create_learning_session,
        goal_id=data["learn_goal_id"],
        started_at=timezone.now() - timezone.timedelta(minutes=data["learn_duration_min"]),
        duration_min=data["learn_duration_min"],
        notes=update.message.text,
    )
    text = await db(confirmation_text, "✅ Learning session logged.")
    await update.message.reply_text(text)
    context.user_data.clear()
    return ConversationHandler.END


learn_conversation = ConversationHandler(
    entry_points=[CommandHandler("learn", learn_entry)],
    states={
        GOAL: [CallbackQueryHandler(learn_goal_chosen, pattern=r"^(goal:\d+|cancel)$")],
        DURATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, learn_duration)],
        NOTES: [MessageHandler(filters.TEXT & ~filters.COMMAND, learn_notes)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)
