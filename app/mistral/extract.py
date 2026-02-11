"""Mistral OCR provider implementation."""

from __future__ import annotations

import os
import time
from pathlib import Path
def _extract_pages_markdown(ocr_response: object) -> str:
    """Extract page markdown from a Mistral OCR response object."""
    pages = getattr(ocr_response, "pages", None)
    if not pages:
        return ""
    markdown_pages: list[str] = []
    for page in pages:
        page_markdown = getattr(page, "markdown", "")
        if page_markdown:
            markdown_pages.append(page_markdown.strip())
    return "\n\n".join(markdown_pages).strip()


def _extract_token_count(ocr_response: object) -> int | None:
    """Extract token count when available in response usage data."""
    usage = getattr(ocr_response, "usage_info", None) or getattr(ocr_response, "usage", None)
    if usage is None:
        return None
    if isinstance(usage, dict):
        return usage.get("total_tokens") or usage.get("tokens")
    total_tokens = getattr(usage, "total_tokens", None)
    if total_tokens is not None:
        return int(total_tokens)
    tokens = getattr(usage, "tokens", None)
    return int(tokens) if tokens is not None else None


def pdf_to_markdown(pdf_path: str) -> tuple[str, dict[str, object]]:
    """Convert a PDF to markdown using Mistral OCR API."""
    start = time.perf_counter()
    pdf = Path(pdf_path)
    api_key = os.getenv("MISTRAL_API_KEY", "").strip()
    model = os.getenv("MISTRAL_OCR_MODEL", "mistral-ocr-latest").strip()

    if not api_key:
        raise RuntimeError("Missing MISTRAL_API_KEY environment variable.")
    if not pdf.exists() or not pdf.is_file():
        raise FileNotFoundError(f"PDF not found: {pdf}")

    try:
        from mistralai import Mistral
    except ImportError as error:
        raise RuntimeError(
            "Missing dependency 'mistralai'. Install it with: uv add mistralai"
        ) from error

    client = Mistral(api_key=api_key)
    with pdf.open("rb") as handle:
        uploaded = client.files.upload(
            file={
                "file_name": pdf.name,
                "content": handle,
            },
            purpose="ocr",
        )

    signed_url = client.files.get_signed_url(file_id=uploaded.id)
    ocr_response = client.ocr.process(
        model=model,
        document={
            "type": "document_url",
            "document_url": signed_url.url,
        },
        include_image_base64=False,
    )

    markdown = _extract_pages_markdown(ocr_response)
    duration_sec = time.perf_counter() - start
    tokens = _extract_token_count(ocr_response)

    metrics: dict[str, object] = {
        "provider": "mistral",
        "model": model,
        "duration_sec": round(duration_sec, 3),
    }
    if tokens is not None:
        metrics["tokens"] = tokens

    return markdown, metrics

