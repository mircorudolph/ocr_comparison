"""Filesystem utilities used by the OCR comparison harness."""

from __future__ import annotations

from pathlib import Path


def ensure_dir(path: Path) -> None:
    """Create a directory (and parents) when it does not exist."""
    path.mkdir(parents=True, exist_ok=True)


def save_markdown(path: Path, content: str) -> None:
    """Write markdown content to a UTF-8 file."""
    ensure_dir(path.parent)
    path.write_text(content, encoding="utf-8")

