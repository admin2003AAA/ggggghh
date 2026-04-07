"""
Configuration loader for the Telegram bot.
Reads settings from environment variables or a .env file.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Central configuration object populated from environment variables."""

    # ── Telegram ──────────────────────────────────────────────────────────
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")

    _raw_allowed = os.getenv("ALLOWED_USERS", "")
    ALLOWED_USERS: set[int] = (
        {int(uid.strip()) for uid in _raw_allowed.split(",") if uid.strip()}
        if _raw_allowed.strip()
        else set()
    )

    # ── Paths ─────────────────────────────────────────────────────────────
    DATA_DIR: Path = Path(os.getenv("DATA_DIR", "./data")).resolve()
    INDEX_DB_PATH: Path = Path(os.getenv("INDEX_DB_PATH", "./index.db")).resolve()

    # ── Indexing ──────────────────────────────────────────────────────────
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
    MAX_FILE_SIZE_BYTES: int = MAX_FILE_SIZE_MB * 1024 * 1024

    # ── Bot ───────────────────────────────────────────────────────────────
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()
    MAX_SEARCH_RESULTS: int = int(os.getenv("MAX_SEARCH_RESULTS", "10"))

    @classmethod
    def validate(cls) -> None:
        """Raise ValueError if required settings are missing."""
        if not cls.BOT_TOKEN:
            raise ValueError(
                "BOT_TOKEN is not set. Copy .env.example to .env and fill in your token."
            )


config = Config()
