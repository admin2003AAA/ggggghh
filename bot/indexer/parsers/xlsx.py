"""Parser for .xlsx / .xlsm files using openpyxl."""

from pathlib import Path


def parse_xlsx(path: Path) -> str:
    """Extract all cell values from every sheet in a workbook."""
    try:
        import openpyxl  # type: ignore

        wb = openpyxl.load_workbook(str(path), read_only=True, data_only=True)
        parts: list[str] = []
        for sheet in wb.worksheets:
            parts.append(f"[Sheet: {sheet.title}]")
            for row in sheet.iter_rows(values_only=True):
                cells = [str(c) for c in row if c is not None and str(c).strip()]
                if cells:
                    parts.append(" | ".join(cells))
        wb.close()
        return "\n".join(parts)
    except Exception:  # noqa: BLE001
        return ""
