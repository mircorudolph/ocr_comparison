"""Tests for shared utility helpers."""

from __future__ import annotations

from pathlib import Path

from utils.file_utils import ensure_dir, save_markdown
from utils.metrics import append_metrics, format_metrics_line


def test_ensure_dir_creates_path(tmp_path: Path) -> None:
    """ensure_dir creates nested folders."""
    target = tmp_path / "nested" / "folder"
    ensure_dir(target)
    assert target.exists()
    assert target.is_dir()


def test_save_markdown_writes_content(tmp_path: Path) -> None:
    """save_markdown writes UTF-8 markdown text."""
    target = tmp_path / "provider" / "sample.md"
    save_markdown(target, "# hello")
    assert target.read_text(encoding="utf-8") == "# hello"


def test_append_metrics_appends_lines(tmp_path: Path) -> None:
    """append_metrics appends one line at a time."""
    metrics_file = tmp_path / "output" / "metrics.txt"
    append_metrics(metrics_file, "line-one")
    append_metrics(metrics_file, "line-two")
    assert metrics_file.read_text(encoding="utf-8") == "line-one\nline-two\n"


def test_format_metrics_line_contains_expected_fields() -> None:
    """format_metrics_line renders normalized key/value text."""
    line = format_metrics_line(
        "invoice.pdf",
        {
            "provider": "mistral",
            "duration_sec": 1.234,
            "tokens": 50,
            "estimated_cost": 0.02,
            "model": "mistral-ocr-latest",
        },
    )
    assert "provider=mistral" in line
    assert "pdf=invoice.pdf" in line
    assert "time=1.234s" in line
    assert "tokens=50" in line
    assert "cost=0.02" in line
    assert "model=mistral-ocr-latest" in line

