"""APScheduler jobs (via PTB's JobQueue) — ESM ping scheduling + the monthly
assessment reminder. Lives only in the `runbot` process; the web process never
schedules jobs. See docs/SPECIFICATION.md section 4."""

from datetime import datetime, timedelta

from django.conf import settings
from django.utils import timezone
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from apps.bot.asyncdb import db
from apps.bot.esm_scheduling import draw_esm_times
from apps.esm.models import Ping
from apps.insights.services import monthly_digest


def _create_todays_pings() -> list[tuple[int, datetime]]:
    """Idempotent: skips the draw if today's pings already exist (covers restarts)."""
    today = timezone.localdate()
    if Ping.objects.filter(scheduled_for__date=today).exists():
        return []

    now = timezone.now()
    created = []
    for t in draw_esm_times(settings.ESM_WINDOW, settings.ESM_PINGS_PER_DAY):
        scheduled_for = timezone.make_aware(datetime.combine(today, t))
        if scheduled_for < now:
            continue
        ping = Ping.objects.create(scheduled_for=scheduled_for, status=Ping.PENDING)
        created.append((ping.id, scheduled_for))
    return created


def _mark_sent(ping_id: int) -> bool:
    updated = Ping.objects.filter(pk=ping_id, status=Ping.PENDING).update(
        status=Ping.SENT, sent_at=timezone.now()
    )
    return updated > 0


def _expire_if_unanswered(ping_id: int) -> None:
    Ping.objects.filter(pk=ping_id, status__in=[Ping.PENDING, Ping.SENT]).update(
        status=Ping.EXPIRED
    )


async def schedule_todays_pings(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Run at startup and daily at 00:05: draw today's ESM times, create PENDING
    Ping rows, and schedule a send + a 45-min expiry job for each."""
    for ping_id, scheduled_for in await db(_create_todays_pings):
        context.job_queue.run_once(
            send_ping_job, when=scheduled_for, data=ping_id, name=f"send_ping_{ping_id}"
        )
        context.job_queue.run_once(
            expire_ping_job,
            when=scheduled_for + timedelta(minutes=45),
            data=ping_id,
            name=f"expire_ping_{ping_id}",
        )


async def send_ping_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    ping_id = context.job.data
    if not await db(_mark_sent, ping_id):
        return  # already handled (e.g. cancelled) — don't send
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("📝 Answer", callback_data=f"esm:{ping_id}")]]
    )
    await context.bot.send_message(
        settings.TELEGRAM_OWNER_ID,
        "📍 ESM ping — what are you doing right now?",
        reply_markup=keyboard,
    )


async def expire_ping_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    await db(_expire_if_unanswered, context.job.data)


async def monthly_assessment_reminder(context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.bot.send_message(
        settings.TELEGRAM_OWNER_ID,
        "🗓 It's the 1st — retake your Grit Scale (/grit) and Mindset Assessment (/mindset)?",
    )


def format_digest_text(digest: dict) -> str:
    lines = [f"📊 {digest['month_start']:%B %Y} digest", ""]
    lines.append(f"Deliberate practice: {digest['dp_minutes']} min")
    lines.append(f"Flow episodes: {digest['flow_episodes']}")

    if digest["best_activities"]:
        lines.append("")
        lines.append("Best flow activities:")
        for row in digest["best_activities"]:
            lines.append(f"  {row['activity']} — {row['flow_pct']:.0f}% flow")

    if digest["setbacks"]:
        lines.append("")
        lines.append(f"{len(digest['setbacks'])} setback reframe(s) to re-read on the website.")

    if digest["suggested_focus"]:
        lines.append("")
        lines.append(f"Suggested focus: {digest['suggested_focus']}")

    return "\n".join(lines)


async def monthly_digest_message(context: ContextTypes.DEFAULT_TYPE) -> None:
    digest = await db(monthly_digest)
    await context.bot.send_message(settings.TELEGRAM_OWNER_ID, format_digest_text(digest))
