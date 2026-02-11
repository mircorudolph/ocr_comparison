"""Marker OCR provider placeholder implementation."""

from __future__ import annotations

def pdf_to_markdown(pdf_path: str) -> tuple[str, dict[str, object]]:
    """Return a clear placeholder until Marker extraction is implemented."""
    _ = pdf_path
    raise NotImplementedError(
        "Marker provider is not implemented yet. "
        "Start with `--providers mistral` and add Marker next."
    )

