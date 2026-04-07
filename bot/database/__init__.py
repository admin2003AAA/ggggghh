"""
SQLite FTS5-based index database for full-text search.
"""

import logging
import sqlite3
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# DDL ─────────────────────────────────────────────────────────────────────────

_CREATE_FILES_TABLE = """
CREATE TABLE IF NOT EXISTS files (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    path        TEXT    UNIQUE NOT NULL,
    ext         TEXT    NOT NULL,
    size_bytes  INTEGER NOT NULL DEFAULT 0,
    indexed_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);
"""

_CREATE_FTS_TABLE = """
CREATE VIRTUAL TABLE IF NOT EXISTS fts_index
USING fts5(
    path        UNINDEXED,
    filename    ,
    content     ,
    tokenize    = 'unicode61'
);
"""

_CREATE_UPDATED_TRIGGER = """
CREATE TRIGGER IF NOT EXISTS trg_files_after_update
AFTER UPDATE ON files
BEGIN
    UPDATE files SET indexed_at = datetime('now') WHERE id = NEW.id;
END;
"""


class IndexDatabase:
    """Manages the SQLite index with FTS5 full-text search."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._conn: sqlite3.Connection | None = None

    # ── Lifecycle ─────────────────────────────────────────────────────────

    def connect(self) -> None:
        """Open (or create) the database and initialise schema."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.execute("PRAGMA synchronous=NORMAL;")
        self._init_schema()
        logger.info("Database connected: %s", self.db_path)

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    def _init_schema(self) -> None:
        assert self._conn
        with self._conn:
            self._conn.execute(_CREATE_FILES_TABLE)
            self._conn.execute(_CREATE_FTS_TABLE)
            self._conn.execute(_CREATE_UPDATED_TRIGGER)

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            raise RuntimeError("Database is not connected. Call connect() first.")
        return self._conn

    # ── Write operations ──────────────────────────────────────────────────

    def upsert_file(self, path: str, ext: str, size_bytes: int, content: str) -> None:
        """Insert or update a file record and its FTS content."""
        with self.conn:
            # Upsert into the metadata table
            self.conn.execute(
                """
                INSERT INTO files (path, ext, size_bytes, indexed_at)
                VALUES (?, ?, ?, datetime('now'))
                ON CONFLICT(path) DO UPDATE SET
                    ext        = excluded.ext,
                    size_bytes = excluded.size_bytes,
                    indexed_at = datetime('now')
                """,
                (path, ext, size_bytes),
            )
            # Remove old FTS entry (if any) then insert fresh
            self.conn.execute("DELETE FROM fts_index WHERE path = ?", (path,))
            filename = Path(path).name
            self.conn.execute(
                "INSERT INTO fts_index (path, filename, content) VALUES (?, ?, ?)",
                (path, filename, content),
            )

    def remove_file(self, path: str) -> None:
        """Remove a file record and its FTS content."""
        with self.conn:
            self.conn.execute("DELETE FROM files WHERE path = ?", (path,))
            self.conn.execute("DELETE FROM fts_index WHERE path = ?", (path,))

    def clear_all(self) -> None:
        """Remove every record (used before a full re-index)."""
        with self.conn:
            self.conn.execute("DELETE FROM files")
            self.conn.execute("DELETE FROM fts_index")

    # ── Read operations ───────────────────────────────────────────────────

    def search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """Full-text search using FTS5 MATCH syntax."""
        # Escape user input so that special FTS5 chars don't raise errors
        safe_query = self._escape_fts_query(query)
        rows = self.conn.execute(
            """
            SELECT
                f.path,
                f.ext,
                f.size_bytes,
                f.indexed_at,
                snippet(fts_index, 2, '<b>', '</b>', '…', 20) AS snippet
            FROM fts_index
            JOIN files f ON fts_index.path = f.path
            WHERE fts_index MATCH ?
            ORDER BY rank
            LIMIT ?
            """,
            (safe_query, limit),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_stats(self) -> dict[str, Any]:
        """Return basic statistics about the index."""
        row = self.conn.execute(
            """
            SELECT
                COUNT(*)                                AS total_files,
                COUNT(DISTINCT ext)                     AS unique_extensions,
                COALESCE(SUM(size_bytes), 0)            AS total_bytes,
                COALESCE(MAX(indexed_at), 'never')      AS last_indexed
            FROM files
            """
        ).fetchone()
        return dict(row) if row else {}

    def get_indexed_paths(self) -> set[str]:
        """Return all paths currently in the index."""
        rows = self.conn.execute("SELECT path FROM files").fetchall()
        return {r["path"] for r in rows}

    # ── Helpers ───────────────────────────────────────────────────────────

    @staticmethod
    def _escape_fts_query(query: str) -> str:
        """Wrap each token in double quotes to prevent FTS5 syntax errors."""
        tokens = query.strip().split()
        escaped = " ".join('"' + t.replace('"', '') + '"' for t in tokens if t)
        return escaped or '""'
