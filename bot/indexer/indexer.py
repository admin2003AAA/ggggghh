"""
Core file indexer: walks the data directory, parses files, and stores
results in the FTS5 SQLite index.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from pathlib import Path

from bot.config import config
from bot.database import IndexDatabase
from bot.indexer.parsers import PARSER_MAP, parse_file

logger = logging.getLogger(__name__)


@dataclass
class IndexStats:
    """Summary of an indexing run."""

    added: int = 0
    updated: int = 0
    skipped: int = 0
    failed: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def total_processed(self) -> int:
        return self.added + self.updated

    def __str__(self) -> str:
        lines = [
            f"✅ Added:   {self.added}",
            f"🔄 Updated: {self.updated}",
            f"⏭ Skipped: {self.skipped}",
        ]
        if self.failed:
            lines.append(f"❌ Failed:  {self.failed}")
        return "\n".join(lines)


class FileIndexer:
    """
    Walks *data_dir* and indexes every supported file into *db*.

    Designed to be called both synchronously (during startup) and
    asynchronously (from a Telegram command handler).
    """

    def __init__(self, db: IndexDatabase, data_dir: Path | None = None) -> None:
        self.db = db
        self.data_dir = (data_dir or config.DATA_DIR).resolve()

    # ── Public API ────────────────────────────────────────────────────────

    async def reindex_async(self, *, full: bool = False) -> IndexStats:
        """
        Async wrapper so the indexer can be called from a Telegram handler
        without blocking the event loop.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._reindex, full)

    def reindex(self, *, full: bool = False) -> IndexStats:
        """Synchronous index run (used at startup)."""
        return self._reindex(full)

    # ── Internal ──────────────────────────────────────────────────────────

    def _reindex(self, full: bool) -> IndexStats:
        stats = IndexStats()

        if not self.data_dir.exists():
            logger.warning("Data directory does not exist: %s", self.data_dir)
            self.data_dir.mkdir(parents=True, exist_ok=True)
            logger.info("Created data directory: %s", self.data_dir)
            return stats

        if full:
            logger.info("Full re-index: clearing existing index …")
            self.db.clear_all()

        already_indexed = self.db.get_indexed_paths() if not full else set()

        for file_path in self._iter_supported_files():
            try:
                self._index_file(file_path, already_indexed, stats)
            except Exception as exc:  # noqa: BLE001
                stats.failed += 1
                stats.errors.append(f"{file_path.name}: {exc}")
                logger.error("Error indexing %s: %s", file_path, exc)

        logger.info(
            "Indexing complete — added=%d updated=%d skipped=%d failed=%d",
            stats.added,
            stats.updated,
            stats.skipped,
            stats.failed,
        )
        return stats

    def _index_file(
        self, file_path: Path, already_indexed: set[str], stats: IndexStats
    ) -> None:
        path_str = str(file_path)
        size = file_path.stat().st_size

        # Skip files that are too large
        if size > config.MAX_FILE_SIZE_BYTES:
            stats.skipped += 1
            logger.debug("Skipping oversized file: %s (%d bytes)", file_path.name, size)
            return

        content = parse_file(file_path)
        if not content.strip():
            stats.skipped += 1
            return

        self.db.upsert_file(
            path=path_str,
            ext=file_path.suffix.lower(),
            size_bytes=size,
            content=content,
        )

        if path_str in already_indexed:
            stats.updated += 1
        else:
            stats.added += 1

    def _iter_supported_files(self):
        """Yield every supported file under data_dir (recursive)."""
        supported_exts = set(PARSER_MAP.keys())
        for file_path in sorted(self.data_dir.rglob("*")):
            if not file_path.is_file():
                continue
            if file_path.suffix.lower() not in supported_exts:
                continue
            # Skip hidden files/directories
            if any(part.startswith(".") for part in file_path.parts):
                continue
            yield file_path
