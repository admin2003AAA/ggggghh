"""Parsers for structured data files: JSON, YAML, CSV, TSV."""

from __future__ import annotations

import csv
import json
from pathlib import Path


def parse_json(path: Path) -> str:
    """Flatten JSON into searchable text."""
    raw = path.read_text(encoding="utf-8", errors="replace")
    try:
        data = json.loads(raw)
        return _flatten(data)
    except json.JSONDecodeError:
        return raw


def parse_yaml(path: Path) -> str:
    """Flatten YAML into searchable text."""
    try:
        import yaml  # type: ignore

        raw = path.read_text(encoding="utf-8", errors="replace")
        data = yaml.safe_load(raw)
        return _flatten(data) if data is not None else ""
    except Exception:  # noqa: BLE001
        return path.read_text(encoding="utf-8", errors="replace")


def parse_csv(path: Path) -> str:
    """Join all CSV cells as space-separated text."""
    return _read_delimited(path, delimiter=",")


def parse_tsv(path: Path) -> str:
    """Join all TSV cells as space-separated text."""
    return _read_delimited(path, delimiter="\t")


# ── Helpers ───────────────────────────────────────────────────────────────────


def _read_delimited(path: Path, delimiter: str) -> str:
    tokens: list[str] = []
    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            with path.open(encoding=encoding, newline="") as fh:
                reader = csv.reader(fh, delimiter=delimiter)
                for row in reader:
                    tokens.extend(cell.strip() for cell in row if cell.strip())
            return " ".join(tokens)
        except UnicodeDecodeError:
            tokens.clear()
            continue
    return ""


def _flatten(obj: object, depth: int = 0) -> str:
    """Recursively extract all leaf string values from a JSON/YAML structure."""
    if depth > 20:
        return ""
    if isinstance(obj, dict):
        parts = []
        for k, v in obj.items():
            parts.append(str(k))
            parts.append(_flatten(v, depth + 1))
        return " ".join(parts)
    if isinstance(obj, (list, tuple)):
        return " ".join(_flatten(item, depth + 1) for item in obj)
    return str(obj) if obj is not None else ""
