from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from apps.bot.asyncdb import db
from apps.bot.confirmations import random_card_text
from apps.bot.decorators import owner_only


@owner_only
async def card(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = await db(random_card_text)
    await update.message.reply_text(text)


card_handler = CommandHandler("card", card)
