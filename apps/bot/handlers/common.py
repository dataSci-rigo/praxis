from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from apps.bot.asyncdb import db
from apps.bot.decorators import owner_only
from apps.bot.services import this_week_stats

COMMANDS_TEXT = (
    "Praxis — capture bot\n\n"
    "/dp — deliberate practice session\n"
    "/flow — flow / performance session\n"
    "/learn — learning session\n"
    "/setback — log a setback + growth reframe\n"
    "/journal — free-text journal entry\n"
    "/goal — list the goal tree / add a LOW goal\n"
    "/card — a random book card\n"
    "/stats — this week's numbers\n"
    "/cancel — cancel whatever you're doing\n"
)


@owner_only
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f"👋 Welcome to Praxis.\n\n{COMMANDS_TEXT}")


@owner_only
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text("Cancelled.")
    return ConversationHandler.END


@owner_only
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    numbers = await db(this_week_stats)
    await update.message.reply_text(
        "This week:\n"
        f"  Deliberate practice: {numbers['dp_minutes']} min\n"
        f"  Flow episodes: {numbers['flow_episodes']}"
    )
