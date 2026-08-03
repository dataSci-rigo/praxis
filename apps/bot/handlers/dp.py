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
from apps.bot.keyboards import CANCEL_CALLBACK, goal_choices, goal_keyboard, rating_keyboard
from apps.bot.services import create_dp_session
from apps.goals.models import Goal
from django.utils import timezone

GOAL, STRETCH, DURATION, FEEDBACK, REFINEMENT, DISCOMFORT = range(6)


@owner_only
async def dp_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    goals = await db(goal_choices, (Goal.LOW,))
    if not goals:
        await update.message.reply_text("No LOW goals yet — add one with /goal first.")
        return ConversationHandler.END
    await update.message.reply_text(
        "Deliberate practice — pick a goal:", reply_markup=goal_keyboard(goals)
    )
    return GOAL


@owner_only
async def dp_goal_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.data == CANCEL_CALLBACK:
        await query.edit_message_text("Cancelled.")
        return ConversationHandler.END
    context.user_data["dp_goal_id"] = int(query.data.split(":")[1])
    await query.edit_message_text("What's the stretch goal — the ONE weakness this session targets?")
    return STRETCH


@owner_only
async def dp_stretch_goal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["dp_stretch_goal"] = update.message.text
    context.user_data["dp_started_at"] = timezone.now()
    await update.message.reply_text(
        "Practicing now — send /done when you finish, or send the number of minutes "
        "to log this session retroactively."
    )
    return DURATION


@owner_only
async def dp_done_live(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    started_at = context.user_data["dp_started_at"]
    elapsed = max(1, int((timezone.now() - started_at).total_seconds() // 60))
    context.user_data["dp_started_at"] = started_at
    context.user_data["dp_duration_min"] = elapsed
    await update.message.reply_text("What feedback did you get?")
    return FEEDBACK


@owner_only
async def dp_duration_retroactive(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    minutes = int(update.message.text)
    context.user_data["dp_started_at"] = timezone.now() - timezone.timedelta(minutes=minutes)
    context.user_data["dp_duration_min"] = minutes
    await update.message.reply_text("What feedback did you get?")
    return FEEDBACK


@owner_only
async def dp_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["dp_feedback_received"] = update.message.text
    await update.message.reply_text("What will you refine next rep?")
    return REFINEMENT


@owner_only
async def dp_refinement(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["dp_refinement"] = update.message.text
    await update.message.reply_text(
        "Discomfort level (1 = comfortable repetition, 10 = maximally uncomfortable):",
        reply_markup=rating_keyboard("disc"),
    )
    return DISCOMFORT


@owner_only
async def dp_discomfort(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    discomfort = int(query.data.split(":")[1])
    data = context.user_data
    await db(
        create_dp_session,
        goal_id=data["dp_goal_id"],
        started_at=data["dp_started_at"],
        duration_min=data["dp_duration_min"],
        stretch_goal=data["dp_stretch_goal"],
        feedback_received=data["dp_feedback_received"],
        refinement=data["dp_refinement"],
        discomfort=discomfort,
    )
    text = await db(confirmation_text, f"✅ Deliberate practice logged ({data['dp_duration_min']} min).")
    await query.edit_message_text(text)
    context.user_data.clear()
    return ConversationHandler.END


dp_conversation = ConversationHandler(
    entry_points=[CommandHandler("dp", dp_entry)],
    states={
        GOAL: [CallbackQueryHandler(dp_goal_chosen, pattern=r"^(goal:\d+|cancel)$")],
        STRETCH: [MessageHandler(filters.TEXT & ~filters.COMMAND, dp_stretch_goal)],
        DURATION: [
            CommandHandler("done", dp_done_live),
            MessageHandler(filters.Regex(r"^\d+$"), dp_duration_retroactive),
        ],
        FEEDBACK: [MessageHandler(filters.TEXT & ~filters.COMMAND, dp_feedback)],
        REFINEMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, dp_refinement)],
        DISCOMFORT: [CallbackQueryHandler(dp_discomfort, pattern=r"^disc:\d+$")],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)
