import asyncio
from telegram import Update
from telegram.ext import ContextTypes

from db import get_watches_for_chat
from scrapers.library import check_availability


async def handle_check_now(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    watches = get_watches_for_chat(chat_id)

    if not watches:
        await update.message.reply_text("You have no active watches. Use /add to create one.")
        return

    await update.message.reply_text("Checking now... ")

    lines = []
    for w in watches:
        try:
            results = await asyncio.to_thread(check_availability, w["url"], w["libraries"])
        except Exception as e:
            lines.append(f"Watch #{w['id']}: error - {e}")
            continue

        for lib, info in results.items():
            if info["available"]:
                lines.append(f"[AVAILABLE] Watch #{w['id']} - {lib}")
            else:
                due = f", due {info['due_date']}" if info["due_date"] else ""
                lines.append(f"[unavailable{due}] Watch #{w['id']} - {lib}")

    await update.message.reply_text("\n".join(lines) or "No results.")
