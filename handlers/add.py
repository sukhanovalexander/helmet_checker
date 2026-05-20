"""
/add command — lets a user start tracking a library item URL.

Flow:
  1. User sends /add <url>
  2. Bot fetches the page, extracts library names
  3. Bot sends an inline keyboard so user can toggle which libraries to watch
  4. User taps "Confirm" → watch is saved to DB
"""

import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from db import add_watch
from scrapers.library import fetch_libraries

logger = logging.getLogger(__name__)

# Temporary in-memory state while user is picking libraries.
# Key: chat_id, Value: {"url": str, "all_libs": [...], "selected": set()}
_pending: dict[int, dict] = {}


async def handle_add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Entry point: /add <url>"""
    chat_id = update.effective_chat.id
    args = context.args

    if not args:
        await update.message.reply_text(
            "Usage: /add <url>\n\nSend me the URL of the library item page."
        )
        return

    url = args[0].strip()
    await update.message.reply_text("Fetching library availability… ⏳")

    try:
        libraries = await asyncio.to_thread(fetch_libraries, url)
    except Exception as e:
        logger.exception("Failed to fetch libraries from %s", url)
        await update.message.reply_text(f"❌ Couldn't load the page:\n{e}")
        return

    if not libraries:
        await update.message.reply_text(
            "⚠️ No library branches found on that page. "
            "Check the URL or the scraper configuration."
        )
        return

    _pending[chat_id] = {"url": url, "all_libs": libraries, "selected": set()}
    await update.message.reply_text(
        "Select the libraries you want to track, then tap *Confirm*.",
        parse_mode="Markdown",
        reply_markup=_build_keyboard(chat_id),
    )


async def handle_library_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles toggle taps and the Confirm button."""
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    data = query.data  # e.g. "lib_select:Helsinki" or "lib_confirm:done"

    if chat_id not in _pending:
        await query.edit_message_text("Session expired. Please /add again.")
        return

    if data.startswith("lib_select:"):
        lib_name = data[len("lib_select:"):]
        state = _pending[chat_id]
        if lib_name in state["selected"]:
            state["selected"].discard(lib_name)
        else:
            state["selected"].add(lib_name)
        await query.edit_message_reply_markup(_build_keyboard(chat_id))

    elif data == "lib_confirm:done":
        state = _pending.pop(chat_id)
        selected = sorted(state["selected"])

        if not selected:
            await query.edit_message_text("No libraries selected. Use /add to try again.")
            return

        watch_id = add_watch(chat_id, state["url"], selected)
        libs_text = "\n• ".join(selected)
        await query.edit_message_text(
            f"✅ Watch #{watch_id} saved!\n\nTracking:\n• {libs_text}\n\n"
            f"I'll notify you as soon as the item becomes available. 📚"
        )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _build_keyboard(chat_id: int) -> InlineKeyboardMarkup:
    state = _pending[chat_id]
    buttons = []
    for lib in state["all_libs"]:
        tick = "✅ " if lib in state["selected"] else ""
        buttons.append(
            [InlineKeyboardButton(f"{tick}{lib}", callback_data=f"lib_select:{lib}")]
        )
    buttons.append([InlineKeyboardButton("Confirm →", callback_data="lib_confirm:done")])
    return InlineKeyboardMarkup(buttons)
