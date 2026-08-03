from telegram.ext import CommandHandler

from apps.bot.handlers.card import card_handler
from apps.bot.handlers.common import start, stats
from apps.bot.handlers.dp import dp_conversation
from apps.bot.handlers.flow import flow_conversation
from apps.bot.handlers.goal import goal_conversation
from apps.bot.handlers.journal import journal_conversation
from apps.bot.handlers.learn import learn_conversation
from apps.bot.handlers.setback import setback_conversation

all_handlers = [
    CommandHandler("start", start),
    CommandHandler("stats", stats),
    dp_conversation,
    flow_conversation,
    learn_conversation,
    setback_conversation,
    journal_conversation,
    goal_conversation,
    card_handler,
]
