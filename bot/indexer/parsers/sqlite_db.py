"""Parser for SQLite database files."""

from __future__ import annotations

import sqlite3
from pathlib import Path


def parse_sqlite(path: Path) -> str:
    """
    Extract schema and a sample of data from a SQLite database.

    For each table we emit:
    - The CREATE statement (schema)
    - Up to 100 rows of data as tab-separated values
    """
    parts: list[str] = []
    try:
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row

        # List tables
        tables = [
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            ).fetchall()
        ]

        for table in tables:
            # Schema
            schema_row = conn.execute(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
                (table,),
            ).fetchone()
            if schema_row and schema_row[0]:
                parts.append(schema_row[0])

            # Sample rows
            try:
                rows = conn.execute(
                    f"SELECT * FROM \"{table}\" LIMIT 100"  # noqa: S608
                ).fetchall()
                for row in rows:
                    parts.append("\t".join(str(v) for v in row if v is not None))
            except sqlite3.Error:
                pass

        conn.close()
    except Exception:  # noqa: BLE001
        pass
    return "\n".join(parts)
