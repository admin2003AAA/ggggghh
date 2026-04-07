"""Parser for PDF files using pypdf."""

from pathlib import Path


def parse_pdf(path: Path) -> str:
    """Extract text from all pages of a PDF."""
    try:
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        pages: list[str] = []
        for page in reader.pages:
            text = page.extract_text() or ""
            pages.append(text)
        return "\n".join(pages)
    except Exception:  # noqa: BLE001
        return ""
