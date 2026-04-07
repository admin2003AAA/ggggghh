"""Parser for plain-text files (txt, md, log, rst, …)."""

from pathlib import Path


def parse_text(path: Path) -> str:
    """Read a text file and return its content, trying common encodings."""
    for encoding in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
        try:
            return path.read_text(encoding=encoding)
        except (UnicodeDecodeError, LookupError):
            continue
    return ""
