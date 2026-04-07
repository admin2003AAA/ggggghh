"""Parser for source code files (py, js, ts, css, …)."""

from pathlib import Path


def parse_code(path: Path) -> str:
    """Read a source-code file as plain text, trying common encodings."""
    for encoding in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
        try:
            return path.read_text(encoding=encoding)
        except (UnicodeDecodeError, LookupError):
            continue
    return ""
