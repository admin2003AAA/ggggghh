"""
Telegram command handlers: /start, /help, /reindex, /search.
"""

from __future__ import annotations

import logging

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from bot.config import config
from bot.database import IndexDatabase
from bot.indexer.indexer import FileIndexer

logger = logging.getLogger(__name__)

# ── Access control ────────────────────────────────────────────────────────────


def _is_allowed(user_id: int) -> bool:
    """Return True if the user is allowed to use the bot."""
    if not config.ALLOWED_USERS:
        return True  # open access
    return user_id in config.ALLOWED_USERS


async def _check_access(update: Update) -> bool:
    """Send an error and return False if the user is not allowed."""
    assert update.effective_user and update.message
    if not _is_allowed(update.effective_user.id):
        await update.message.reply_text("⛔ You are not authorised to use this bot.")
        return False
    return True


# ── /start ────────────────────────────────────────────────────────────────────


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _check_access(update):
        return
    assert update.message
    text = (
        "👋 *Welcome to the File Indexer Bot!*\n\n"
        "I index files in the `data/` directory and let you search their contents "
        "using fast full-text search.\n\n"
        "Type /help to see available commands."
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


# ── /help ─────────────────────────────────────────────────────────────────────


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _check_access(update):
        return
    assert update.message
    text = (
        "📖 *Available Commands*\n\n"
        "• /start — Welcome message\n"
        "• /help — Show this help\n"
        "• /reindex — Re-scan the `data/` directory and update the index\n"
        "• /search `<query>` — Search indexed files\n\n"
        "*Supported file types:*\n"
        "`txt md log rst json yaml yml csv tsv xml html htm`\n"
        "`pdf docx xlsx xlsm sqlite sqlite3 db sql`\n"
        "`py js ts jsx tsx css scss sass sh go java c cpp`\n"
        "`cs rb php swift kt rs r lua toml ini cfg conf`\n\n"
        "*Example:* `/search project requirements`"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


# ── /reindex ──────────────────────────────────────────────────────────────────


async def cmd_reindex(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _check_access(update):
        return
    assert update.message and context.bot_data

    db: IndexDatabase = context.bot_data["db"]
    indexer: FileIndexer = context.bot_data["indexer"]

    status_msg = await update.message.reply_text(
        "🔄 Re-indexing files … please wait."
    )

    try:
        stats = await indexer.reindex_async(full=True)
        db_stats = db.get_stats()

        text = (
            "✅ *Re-indexing complete!*\n\n"
            f"{stats}\n\n"
            f"📊 *Index stats:*\n"
            f"  Files indexed: `{db_stats.get('total_files', 0)}`\n"
            f"  Extensions:    `{db_stats.get('unique_extensions', 0)}`\n"
            f"  Last indexed:  `{db_stats.get('last_indexed', 'never')}`"
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Re-index failed")
        text = f"❌ Re-indexing failed: {exc}"

    await status_msg.edit_text(text, parse_mode=ParseMode.MARKDOWN)


# ── /search ───────────────────────────────────────────────────────────────────


async def cmd_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _check_access(update):
        return
    assert update.message and context.bot_data

    query = " ".join(context.args or []).strip() if context.args else ""
    if not query:
        await update.message.reply_text(
            "ℹ️ Usage: `/search <your query>`\nExample: `/search project requirements`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    db: IndexDatabase = context.bot_data["db"]

    try:
        results = db.search(query, limit=config.MAX_SEARCH_RESULTS)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Search failed for query: %s", query)
        await update.message.reply_text(f"❌ Search error: {exc}")
        return

    if not results:
        await update.message.reply_text(
            f"🔍 No results found for *{_esc(query)}*.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    lines = [f"🔍 *Results for* `{_esc(query)}` *({len(results)} found):*\n"]
    for i, row in enumerate(results, start=1):
        size_kb = row["size_bytes"] / 1024
        snippet = row.get("snippet", "").replace("\n", " ")
        lines.append(
            f"*{i}.* `{_esc(row['path'])}`\n"
            f"   📄 Ext: `{row['ext']}` | Size: `{size_kb:.1f} KB`\n"
            f"   _{_esc(snippet)}_\n"
        )

    # Telegram message limit is 4096 chars; chunk if needed
    message = "\n".join(lines)
    if len(message) > 4000:
        message = message[:4000] + "\n…_(truncated)_"

    await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)


# ── Helper ────────────────────────────────────────────────────────────────────


def _esc(text: str) -> str:
    """Escape Markdown special characters for MarkdownV1 (legacy mode)."""
    for ch in ("*", "_", "`", "["):
        text = text.replace(ch, f"\\{ch}")
    return text
