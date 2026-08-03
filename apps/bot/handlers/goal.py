from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
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
from apps.bot.keyboards import CANCEL_CALLBACK, goal_choices, goal_keyboard
from apps.bot.services import add_low_goal, goal_tree_text
from apps.goals.models import Goal

MENU, PICK_MID, TITLE = range(3)

ADD_LOW_CALLBACK = "add_low"
DONE_CALLBACK = "done"

_MENU_KEYBOARD = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("+ Add LOW goal", callback_data=ADD_LOW_CALLBACK)],
        [InlineKeyboardButton("Done", callback_data=DONE_CALLBACK)],
    ]
)


@owner_only
async def goal_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    tree = await db(goal_tree_text)
    await update.message.reply_text(tree, reply_markup=_MENU_KEYBOARD)
    return MENU


@owner_only
async def goal_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.data == DONE_CALLBACK:
        await query.edit_message_reply_markup(reply_markup=None)
        return ConversationHandler.END

    mids = await db(goal_choices, (Goal.MID,))
    if not mids:
        await query.edit_message_text("No MID-level goals yet — add one via the website first.")
        return ConversationHandler.END
    await query.edit_message_text(
        "Add a LOW goal under which MID goal?", reply_markup=goal_keyboard(mids)
    )
    return PICK_MID


@owner_only
async def goal_pick_mid(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.data == CANCEL_CALLBACK:
        await query.edit_message_text("Cancelled.")
        return ConversationHandler.END
    context.user_data["goal_parent_id"] = int(query.data.split(":")[1])
    await query.edit_message_text("Title for the new LOW goal?")
    return TITLE


@owner_only
async def goal_title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    parent_id = context.user_data["goal_parent_id"]
    goal = await db(add_low_goal, parent_id=parent_id, title=update.message.text)
    await update.message.reply_text(f"✅ Added LOW goal: {goal.title}")
    context.user_data.clear()
    return ConversationHandler.END


goal_conversation = ConversationHandler(
    entry_points=[CommandHandler("goal", goal_entry)],
    states={
        MENU: [CallbackQueryHandler(goal_menu, pattern=r"^(add_low|done)$")],
        PICK_MID: [CallbackQueryHandler(goal_pick_mid, pattern=r"^(goal:\d+|cancel)$")],
        TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, goal_title)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)
