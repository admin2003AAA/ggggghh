"""Parser for plain .sql files."""

from pathlib import Path


def parse_sql(path: Path) -> str:
    """Read a SQL file as plain text."""
    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return ""
