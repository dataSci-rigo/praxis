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
from apps.bot.decorators import owner_only
from apps.bot.handlers.common import cancel
from apps.bot.keyboards import rating_keyboard, yes_no_keyboard
from apps.bot.services import save_esm_response
from apps.esm.models import Ping

ACTIVITY, CHALLENGE, SKILL, ABSORPTION, MOOD, WISH_ELSE, AUTOTELIC = range(7)


@owner_only
async def esm_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    ping_id = int(query.data.split(":")[1])
    ping = await db(Ping.objects.get, pk=ping_id)
    if ping.status != Ping.SENT:
        await query.edit_message_text("This ping already expired or was answered.")
        return ConversationHandler.END
    context.user_data.clear()
    context.user_data["esm_ping_id"] = ping_id
    await query.edit_message_text("📍 What are you doing right now?")
    return ACTIVITY


@owner_only
async def esm_activity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["esm_activity"] = update.message.text
    await update.message.reply_text("Challenge (1–10)?", reply_markup=rating_keyboard("ch"))
    return CHALLENGE


@owner_only
async def esm_challenge(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["esm_challenge"] = int(query.data.split(":")[1])
    await query.edit_message_text("Skill (1–10)?")
    await query.message.reply_text("Skill:", reply_markup=rating_keyboard("sk"))
    return SKILL


@owner_only
async def esm_skill(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["esm_skill"] = int(query.data.split(":")[1])
    await query.edit_message_text("Absorption — how lost in it are you (1–10)?")
    await query.message.reply_text("Absorption:", reply_markup=rating_keyboard("ab"))
    return ABSORPTION


@owner_only
async def esm_absorption(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["esm_absorption"] = int(query.data.split(":")[1])
    await query.edit_message_text("Mood (1–10)?")
    await query.message.reply_text("Mood:", reply_markup=rating_keyboard("mo"))
    return MOOD


@owner_only
async def esm_mood(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["esm_mood"] = int(query.data.split(":")[1])
    await query.edit_message_text("Would you rather be doing something else?")
    await query.message.reply_text("Wish you were elsewhere?", reply_markup=yes_no_keyboard("wish"))
    return WISH_ELSE


@owner_only
async def esm_wish_else(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["esm_wish_doing_else"] = query.data.endswith("yes")
    await query.edit_message_text("Would you do this for its own sake — autotelic?")
    await query.message.reply_text("Autotelic?", reply_markup=yes_no_keyboard("autotelic"))
    return AUTOTELIC


@owner_only
async def esm_autotelic(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    autotelic = query.data.endswith("yes")
    data = context.user_data
    await db(
        save_esm_response,
        ping_id=data["esm_ping_id"],
        activity=data["esm_activity"],
        challenge=data["esm_challenge"],
        skill=data["esm_skill"],
        absorption=data["esm_absorption"],
        mood=data["esm_mood"],
        wish_doing_else=data["esm_wish_doing_else"],
        autotelic=autotelic,
    )
    await query.edit_message_text("✅ Logged. Thanks!")
    context.user_data.clear()
    return ConversationHandler.END


esm_conversation = ConversationHandler(
    entry_points=[CallbackQueryHandler(esm_start, pattern=r"^esm:\d+$")],
    states={
        ACTIVITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, esm_activity)],
        CHALLENGE: [CallbackQueryHandler(esm_challenge, pattern=r"^ch:\d+$")],
        SKILL: [CallbackQueryHandler(esm_skill, pattern=r"^sk:\d+$")],
        ABSORPTION: [CallbackQueryHandler(esm_absorption, pattern=r"^ab:\d+$")],
        MOOD: [CallbackQueryHandler(esm_mood, pattern=r"^mo:\d+$")],
        WISH_ELSE: [CallbackQueryHandler(esm_wish_else, pattern=r"^wish:(yes|no)$")],
        AUTOTELIC: [CallbackQueryHandler(esm_autotelic, pattern=r"^autotelic:(yes|no)$")],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)
