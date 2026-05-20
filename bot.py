"""
Library availability bot - main entry point.
Starts the Telegram bot and the background polling scheduler.
"""

import asyncio
import logging
from telegram.ext import Application, CommandHandler, CallbackQueryHandler

from config import BOT_TOKEN
from handlers.add import handle_add, handle_library_selection
from handlers.delete import handle_delete, handle_delete_selection
from handlers.check_now import handle_check_now
from scheduler import run_scheduler

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Command handlers
    app.add_handler(CommandHandler("add", handle_add))
    app.add_handler(CommandHandler("delete", handle_delete))
    app.add_handler(CommandHandler("check_now", handle_check_now))

    # Inline keyboard callback handlers
    app.add_handler(CallbackQueryHandler(handle_library_selection, pattern=r"^lib_select:"))
    app.add_handler(CallbackQueryHandler(handle_library_selection, pattern=r"^lib_confirm:"))
    app.add_handler(CallbackQueryHandler(handle_delete_selection, pattern=r"^del_confirm:"))

    # Start background scheduler as a concurrent task
    asyncio.create_task(run_scheduler(app.bot))

    logger.info("Bot started")
    await app.run_polling()


if __name__ == "__main__":
    asyncio.run(main())
