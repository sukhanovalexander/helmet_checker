"""
Background scheduler.

Notification logic:
- When a library becomes available, notify once and record it in notified_libraries.
- Skip subsequent polls for already-notified libraries.
- If a library goes unavailable again, clear it from notified_libraries so it
  can trigger a new notification next time it becomes available.
"""

import asyncio
import logging

from telegram import Bot

from config import POLL_INTERVAL_SECONDS
from db import init_db, get_all_watches, set_notified, clear_notified
from scrapers.library import check_availability

logger = logging.getLogger(__name__)


async def run_scheduler(bot: Bot) -> None:
    init_db()
    logger.info("Scheduler started; polling every %ds", POLL_INTERVAL_SECONDS)

    while True:
        await asyncio.sleep(POLL_INTERVAL_SECONDS)
        await _poll_all(bot)


async def _poll_all(bot: Bot) -> None:
    watches = get_all_watches()
    logger.info("Polling %d watch(es)", len(watches))

    for watch in watches:
        try:
            results = await asyncio.to_thread(
                check_availability, watch["url"], watch["libraries"]
            )
        except Exception:
            logger.exception("Error checking watch #%d (%s)", watch["id"], watch["url"])
            continue

        already_notified = set(watch["notified_libraries"])

        newly_available = [
            lib for lib, info in results.items()
            if info["available"] and lib not in already_notified
        ]
        newly_unavailable = [
            lib for lib, info in results.items()
            if not info["available"] and lib in already_notified
        ]

        # Re-arm: remove from notified if item went unavailable again
        if newly_unavailable:
            updated_notified = already_notified - set(newly_unavailable)
            set_notified(watch["id"], list(updated_notified))

        # Notify and record
        if newly_available:
            await _notify(bot, watch, newly_available)
            set_notified(watch["id"], list(already_notified | set(newly_available)))


async def _notify(bot: Bot, watch: dict, available_libs: list[str]) -> None:
    libs_text = "\n• ".join(available_libs)
    text = (
        f"📗 *Item available!*\n\n"
        f"Watch #{watch['id']} — the following librar{'y' if len(available_libs) == 1 else 'ies'} "
        f"now {'has' if len(available_libs) == 1 else 'have'} it ready:\n\n"
        f"• {libs_text}\n\n"
        f"🔗 {watch['url']}"
    )
    try:
        await bot.send_message(
            chat_id=watch["chat_id"],
            text=text,
            parse_mode="Markdown",
        )
        logger.info("Notified chat %d for watch #%d: %s", watch["chat_id"], watch["id"], available_libs)
    except Exception:
        logger.exception("Failed to notify chat %d for watch #%d", watch["chat_id"], watch["id"])
