from telegram import Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes, ConversationHandler

from apps.assessments.models import ScaleItem
from apps.assessments.scoring import score_grit, score_mindset
from apps.bot.asyncdb import db
from apps.bot.decorators import owner_only
from apps.bot.handlers.common import cancel
from apps.bot.keyboards import rating_keyboard
from apps.bot.services import save_assessment, scale_items_for

ANSWERING = 0

_SCALE_MAX = {ScaleItem.GRIT: 5, ScaleItem.MINDSET: 6}
_MIN_ITEMS = {ScaleItem.GRIT: 10, ScaleItem.MINDSET: 1}
_LABEL = {ScaleItem.GRIT: "Grit Scale", ScaleItem.MINDSET: "Mindset Assessment"}


async def _send_current_item(bot, chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:
    items = context.user_data["assess_items"]
    idx = context.user_data["assess_index"]
    number, text, _reverse = items[idx]
    scale_max = _SCALE_MAX[context.user_data["assess_kind"]]
    await bot.send_message(
        chat_id,
        f"({idx + 1}/{len(items)}) {text}",
        reply_markup=rating_keyboard("assess", 1, scale_max),
    )


async def _assessment_entry(update: Update, context: ContextTypes.DEFAULT_TYPE, kind: str) -> int:
    items = await db(scale_items_for, kind)
    required = _MIN_ITEMS[kind]
    if len(items) < required:
        await update.message.reply_text(
            f"{_LABEL[kind]} isn't set up yet ({len(items)} item(s) entered, need at least "
            f"{required}). Add the items via /admin → Assessments → Scale items, using the "
            f"published source, then try again."
        )
        return ConversationHandler.END

    context.user_data.clear()
    context.user_data["assess_kind"] = kind
    context.user_data["assess_items"] = [(i.number, i.text, i.reverse_scored) for i in items]
    context.user_data["assess_index"] = 0
    context.user_data["assess_responses"] = {}
    await update.message.reply_text(f"{_LABEL[kind]} — {len(items)} items. Let's go.")
    await _send_current_item(context.bot, update.effective_chat.id, context)
    return ANSWERING


@owner_only
async def grit_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await _assessment_entry(update, context, ScaleItem.GRIT)


@owner_only
async def mindset_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await _assessment_entry(update, context, ScaleItem.MINDSET)


@owner_only
async def assess_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    value = int(query.data.split(":")[1])

    items = context.user_data["assess_items"]
    idx = context.user_data["assess_index"]
    number, _text, _reverse = items[idx]
    context.user_data["assess_responses"][number] = value
    context.user_data["assess_index"] += 1

    if context.user_data["assess_index"] >= len(items):
        return await _finish(query, context)

    await _send_current_item(context.bot, query.message.chat_id, context)
    return ANSWERING


async def _finish(query, context: ContextTypes.DEFAULT_TYPE) -> int:
    kind = context.user_data["assess_kind"]
    items = context.user_data["assess_items"]
    responses = context.user_data["assess_responses"]
    reverse_map = {number: reverse for number, _text, reverse in items}

    if kind == ScaleItem.GRIT:
        total, subscale = score_grit(responses, reverse_map)
        summary = (
            f"Grit score: {total}/5.0\n"
            f"Passion: {subscale['passion']}/5.0\n"
            f"Perseverance: {subscale['perseverance']}/5.0"
        )
    else:
        total, subscale = score_mindset(responses, reverse_map)
        summary = f"Growth-mindset score: {total}/100"

    await db(
        save_assessment,
        kind=kind,
        total_score=total,
        subscale_json=subscale,
        item_values=responses,
    )
    await query.message.reply_text(f"✅ Saved.\n\n{summary}")
    context.user_data.clear()
    return ConversationHandler.END


grit_conversation = ConversationHandler(
    entry_points=[CommandHandler("grit", grit_entry)],
    states={ANSWERING: [CallbackQueryHandler(assess_answer, pattern=r"^assess:\d+$")]},
    fallbacks=[CommandHandler("cancel", cancel)],
)

mindset_conversation = ConversationHandler(
    entry_points=[CommandHandler("mindset", mindset_entry)],
    states={ANSWERING: [CallbackQueryHandler(assess_answer, pattern=r"^assess:\d+$")]},
    fallbacks=[CommandHandler("cancel", cancel)],
)
