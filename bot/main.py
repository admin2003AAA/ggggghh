"""
Entry point for the Telegram File Indexer Bot.

Usage:
    python -m bot.main
or simply:
    python main.py
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

# Ensure project root is on sys.path when run directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from telegram import BotCommand
from telegram.ext import Application, CommandHandler

from bot.config import config
from bot.database import IndexDatabase
from bot.handlers.commands import cmd_help, cmd_reindex, cmd_search, cmd_start
from bot.indexer.indexer import FileIndexer


def _setup_logging() -> None:
    logging.basicConfig(
        format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        level=getattr(logging, config.LOG_LEVEL, logging.INFO),
    )
    # Reduce noise from third-party libraries
    for noisy in ("httpx", "httpcore", "telegram"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


async def _post_init(application: Application) -> None:
    """Called once the bot is initialised — set up DB, indexer, and commands."""
    db: IndexDatabase = application.bot_data["db"]
    db.connect()

    indexer: FileIndexer = application.bot_data["indexer"]
    logging.getLogger(__name__).info("Running initial index scan …")
    stats = indexer.reindex(full=False)
    logging.getLogger(__name__).info("Initial scan done: %s", stats)

    await application.bot.set_my_commands(
        [
            BotCommand("start", "Welcome message"),
            BotCommand("help", "Show available commands"),
            BotCommand("reindex", "Re-scan and update the file index"),
            BotCommand("search", "Search indexed files"),
        ]
    )


async def _post_shutdown(application: Application) -> None:
    """Gracefully close the database connection."""
    db: IndexDatabase = application.bot_data.get("db")
    if db:
        db.close()


def main() -> None:
    _setup_logging()
    logger = logging.getLogger(__name__)

    try:
        config.validate()
    except ValueError as exc:
        logger.critical(str(exc))
        sys.exit(1)

    db = IndexDatabase(config.INDEX_DB_PATH)
    indexer = FileIndexer(db, config.DATA_DIR)

    app = (
        Application.builder()
        .token(config.BOT_TOKEN)
        .post_init(_post_init)
        .post_shutdown(_post_shutdown)
        .build()
    )

    # Share db and indexer via bot_data so handlers can access them
    app.bot_data["db"] = db
    app.bot_data["indexer"] = indexer

    # Register command handlers
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("reindex", cmd_reindex))
    app.add_handler(CommandHandler("search", cmd_search))

    logger.info("Bot is starting — polling for updates …")
    app.run_polling(allowed_updates=["message"])


if __name__ == "__main__":
    main()
