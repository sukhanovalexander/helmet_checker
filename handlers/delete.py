"""
/delete command — lets a user remove an existing watch.

Flow:
  1. Bot lists the user's current watches as an inline keyboard
  2. User taps one → confirmation prompt
  3. User confirms → row deleted from DB
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from db import get_watches_for_chat, delete_watch


async def handle_delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    watches = get_watches_for_chat(chat_id)

    if not watches:
        await update.message.reply_text("You have no active watches. Use /add to create one.")
        return

    buttons = []
    for w in watches:
        label = f"#{w['id']} — {_short_url(w['url'])} ({', '.join(w['libraries'])})"
        buttons.append([InlineKeyboardButton(label, callback_data=f"del_confirm:{w['id']}")])

    await update.message.reply_text(
        "Which watch do you want to remove?",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


async def handle_delete_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id

    watch_id = int(query.data[len("del_confirm:"):])
    removed = delete_watch(watch_id, chat_id)

    if removed:
        await query.edit_message_text(f"🗑️ Watch #{watch_id} removed.")
    else:
        await query.edit_message_text("Watch not found (already deleted?).")


def _short_url(url: str, max_len: int = 40) -> str:
    return url if len(url) <= max_len else url[:max_len] + "…"
