"""Tests for command-line orchestration helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from main import list_pdfs, parse_provider_names


def test_parse_provider_names_valid_values() -> None:
    """parse_provider_names returns normalized provider list."""
    providers = parse_provider_names("mistral, openai")
    assert providers == ["mistral", "openai"]


def test_parse_provider_names_rejects_unknown() -> None:
    """parse_provider_names fails for unsupported providers."""
    with pytest.raises(ValueError):
        parse_provider_names("mistral,unknown")


def test_list_pdfs_only_returns_pdf_files(tmp_path: Path) -> None:
    """list_pdfs ignores non-PDF files."""
    (tmp_path / "a.pdf").write_text("x", encoding="utf-8")
    (tmp_path / "b.PDF").write_text("x", encoding="utf-8")
    (tmp_path / "notes.txt").write_text("x", encoding="utf-8")
    pdfs = list_pdfs(tmp_path)
    assert [path.name for path in pdfs] == ["a.pdf", "b.PDF"]

