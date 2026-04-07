"""
File parsers package.

Each parser is a callable that accepts a file path (Path) and returns
extracted plain text (str).  Returning an empty string means "no content".
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable

from .text import parse_text
from .markup import parse_html, parse_xml
from .data import parse_json, parse_yaml, parse_csv, parse_tsv
from .pdf import parse_pdf
from .docx import parse_docx
from .xlsx import parse_xlsx
from .sqlite_db import parse_sqlite
from .sql import parse_sql
from .code import parse_code

logger = logging.getLogger(__name__)

# Mapping from lowercase extension → parser function
PARSER_MAP: dict[str, Callable[[Path], str]] = {
    # Plain text
    ".txt": parse_text,
    ".md": parse_text,
    ".markdown": parse_text,
    ".log": parse_text,
    ".rst": parse_text,
    # Data / config
    ".json": parse_json,
    ".yaml": parse_yaml,
    ".yml": parse_yaml,
    ".csv": parse_csv,
    ".tsv": parse_tsv,
    # Markup
    ".xml": parse_xml,
    ".html": parse_html,
    ".htm": parse_html,
    # Documents
    ".pdf": parse_pdf,
    ".docx": parse_docx,
    # Spreadsheets
    ".xlsx": parse_xlsx,
    ".xlsm": parse_xlsx,
    # Databases / SQL
    ".sqlite": parse_sqlite,
    ".sqlite3": parse_sqlite,
    ".db": parse_sqlite,
    ".sql": parse_sql,
    # Source code
    ".py": parse_code,
    ".js": parse_code,
    ".ts": parse_code,
    ".jsx": parse_code,
    ".tsx": parse_code,
    ".css": parse_code,
    ".scss": parse_code,
    ".sass": parse_code,
    ".sh": parse_code,
    ".bash": parse_code,
    ".zsh": parse_code,
    ".go": parse_code,
    ".java": parse_code,
    ".c": parse_code,
    ".cpp": parse_code,
    ".h": parse_code,
    ".hpp": parse_code,
    ".cs": parse_code,
    ".rb": parse_code,
    ".php": parse_code,
    ".swift": parse_code,
    ".kt": parse_code,
    ".rs": parse_code,
    ".r": parse_code,
    ".lua": parse_code,
    ".toml": parse_code,
    ".ini": parse_code,
    ".cfg": parse_code,
    ".conf": parse_code,
    ".env": parse_code,
}


def get_parser(path: Path) -> Callable[[Path], str] | None:
    """Return the appropriate parser for *path*, or None if unsupported."""
    return PARSER_MAP.get(path.suffix.lower())


def parse_file(path: Path) -> str:
    """
    Parse *path* and return its text content.

    Returns an empty string if no parser is available or if parsing fails.
    """
    parser = get_parser(path)
    if parser is None:
        return ""
    try:
        return parser(path) or ""
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to parse %s: %s", path, exc)
        return ""
