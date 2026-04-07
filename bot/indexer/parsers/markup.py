"""Parsers for HTML and XML files."""

from pathlib import Path


def parse_html(path: Path) -> str:
    """Extract visible text from an HTML file using BeautifulSoup."""
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return path.read_text(encoding="utf-8", errors="replace")

    raw = path.read_text(encoding="utf-8", errors="replace")
    soup = BeautifulSoup(raw, "lxml")
    # Remove script and style elements
    for tag in soup(["script", "style"]):
        tag.decompose()
    return soup.get_text(separator=" ", strip=True)


def parse_xml(path: Path) -> str:
    """Extract all text nodes from an XML file."""
    try:
        from lxml import etree

        tree = etree.parse(str(path))  # noqa: S320
        return " ".join(tree.getroot().itertext())
    except Exception:  # noqa: BLE001
        # Fallback: read as plain text
        return path.read_text(encoding="utf-8", errors="replace")
