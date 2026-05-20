"""
Background scheduler.

Runs an infinite loop; every POLL_INTERVAL_SECONDS seconds it:
  1. Loads all watches from the DB
  2. Checks availability for each
  3. Sends a Telegram notification for any library that just became available

Note: this simple implementation does NOT deduplicate notifications between
runs. If you want to alert only once (until the item goes unavailable again),
add a `last_notified_at` column or a small in-memory set.
"""

import asyncio
import logging

from telegram import Bot

from config import POLL_INTERVAL_SECONDS
from db import init_db, get_all_watches
from scrapers.library import check_availability

logger = logging.getLogger(__name__)


async def run_scheduler(bot: Bot) -> None:
    """Entry point — call as an asyncio task from bot.py."""
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

        available_libs = [lib for lib, ok in results.items() if ok]
        if available_libs:
            await _notify(bot, watch, available_libs)


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
    except Exception:
        logger.exception("Failed to notify chat %d for watch #%d", watch["chat_id"], watch["id"])
