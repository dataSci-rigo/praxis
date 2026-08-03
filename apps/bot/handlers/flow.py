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
from apps.bot.keyboards import (
    CANCEL_CALLBACK,
    goal_choices,
    goal_keyboard,
    rating_keyboard,
    yes_no_keyboard,
)
from apps.bot.services import create_flow_session
from apps.goals.models import Goal
from django.utils import timezone

GOAL, DURATION, CHALLENGE, SKILL, ABSORPTION, ENJOYMENT, CLEAR_GOAL, IMMEDIATE_FEEDBACK = range(8)


@owner_only
async def flow_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    goals = await db(goal_choices, (Goal.MID, Goal.LOW))
    if not goals:
        await update.message.reply_text("No goals yet — add one with /goal first.")
        return ConversationHandler.END
    await update.message.reply_text(
        "Flow / performance — pick a goal:", reply_markup=goal_keyboard(goals)
    )
    return GOAL


@owner_only
async def flow_goal_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.data == CANCEL_CALLBACK:
        await query.edit_message_text("Cancelled.")
        return ConversationHandler.END
    context.user_data["flow_goal_id"] = int(query.data.split(":")[1])
    await query.edit_message_text("How many minutes (just finished, or roughly how long)?")
    return DURATION


@owner_only
async def flow_duration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message.text.isdigit():
        await update.message.reply_text("Send a number of minutes, please.")
        return DURATION
    context.user_data["flow_duration_min"] = int(update.message.text)
    await update.message.reply_text("Challenge level (1–10)?", reply_markup=rating_keyboard("ch"))
    return CHALLENGE


@owner_only
async def flow_challenge(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["flow_challenge"] = int(query.data.split(":")[1])
    await query.edit_message_text("Skill level (1–10)?")
    await query.message.reply_text("Skill:", reply_markup=rating_keyboard("sk"))
    return SKILL


@owner_only
async def flow_skill(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["flow_skill"] = int(query.data.split(":")[1])
    await query.edit_message_text("Absorption — how lost in it were you (1–10)?")
    await query.message.reply_text("Absorption:", reply_markup=rating_keyboard("ab"))
    return ABSORPTION


@owner_only
async def flow_absorption(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["flow_absorption"] = int(query.data.split(":")[1])
    await query.edit_message_text("Enjoyment (1–10)?")
    await query.message.reply_text("Enjoyment:", reply_markup=rating_keyboard("en"))
    return ENJOYMENT


@owner_only
async def flow_enjoyment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["flow_enjoyment"] = int(query.data.split(":")[1])
    await query.edit_message_text("Did you have a clear goal?")
    await query.message.reply_text("Clear goal?", reply_markup=yes_no_keyboard("clear"))
    return CLEAR_GOAL


@owner_only
async def flow_clear_goal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["flow_had_clear_goal"] = query.data.endswith("yes")
    await query.edit_message_text("Did you get immediate feedback?")
    await query.message.reply_text("Immediate feedback?", reply_markup=yes_no_keyboard("feedback"))
    return IMMEDIATE_FEEDBACK


@owner_only
async def flow_immediate_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    data = context.user_data
    had_immediate_feedback = query.data.endswith("yes")
    await db(
        create_flow_session,
        goal_id=data["flow_goal_id"],
        started_at=timezone.now() - timezone.timedelta(minutes=data["flow_duration_min"]),
        duration_min=data["flow_duration_min"],
        challenge=data["flow_challenge"],
        skill=data["flow_skill"],
        absorption=data["flow_absorption"],
        enjoyment=data["flow_enjoyment"],
        had_clear_goal=data["flow_had_clear_goal"],
        had_immediate_feedback=had_immediate_feedback,
    )
    text = await db(confirmation_text, "✅ Flow session logged.")
    await query.edit_message_text(text)
    context.user_data.clear()
    return ConversationHandler.END


flow_conversation = ConversationHandler(
    entry_points=[CommandHandler("flow", flow_entry)],
    states={
        GOAL: [CallbackQueryHandler(flow_goal_chosen, pattern=r"^(goal:\d+|cancel)$")],
        DURATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, flow_duration)],
        CHALLENGE: [CallbackQueryHandler(flow_challenge, pattern=r"^ch:\d+$")],
        SKILL: [CallbackQueryHandler(flow_skill, pattern=r"^sk:\d+$")],
        ABSORPTION: [CallbackQueryHandler(flow_absorption, pattern=r"^ab:\d+$")],
        ENJOYMENT: [CallbackQueryHandler(flow_enjoyment, pattern=r"^en:\d+$")],
        CLEAR_GOAL: [CallbackQueryHandler(flow_clear_goal, pattern=r"^clear:(yes|no)$")],
        IMMEDIATE_FEEDBACK: [
            CallbackQueryHandler(flow_immediate_feedback, pattern=r"^feedback:(yes|no)$")
        ],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)
