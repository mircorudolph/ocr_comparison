"""Landing AI ADE Parse provider implementation."""

from __future__ import annotations

import os
import time
from pathlib import Path


def _to_float(value: object) -> float | None:
    """Convert a value to float when possible."""
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def pdf_to_markdown(pdf_path: str) -> tuple[str, dict[str, object]]:
    """Convert a PDF to markdown using Landing AI ADE Parse API."""
    start = time.perf_counter()
    pdf = Path(pdf_path)
    api_key = os.getenv("LANDING_AI_API_KEY", "").strip()
    parse_url = os.getenv("LANDING_AI_PARSE_URL", "https://api.va.landing.ai/v1/ade/parse").strip()
    model = os.getenv("LANDING_AI_MODEL", "").strip()
    split = os.getenv("LANDING_AI_SPLIT", "").strip()
    credit_to_usd = _to_float(os.getenv("LANDING_AI_CREDIT_TO_USD"))

    if not api_key:
        raise RuntimeError("Missing LANDING_AI_API_KEY environment variable.")
    if not pdf.exists() or not pdf.is_file():
        raise FileNotFoundError(f"PDF not found: {pdf}")

    try:
        import requests
    except ImportError as error:
        raise RuntimeError(
            "Missing dependency 'requests'. Install it with: uv add requests"
        ) from error

    headers = {"Authorization": f"Bearer {api_key}"}
    data: dict[str, str] = {}
    if model:
        data["model"] = model
    if split:
        data["split"] = split

    with pdf.open("rb") as handle:
        response = requests.post(
            parse_url,
            headers=headers,
            data=data or None,
            files={"document": (pdf.name, handle, "application/pdf")},
            timeout=180,
        )

    if response.status_code not in (200, 206):
        raise RuntimeError(
            f"Landing AI parse failed with status {response.status_code}: {response.text}"
        )

    payload = response.json()
    markdown = str(payload.get("markdown", "")).strip()
    metadata = payload.get("metadata", {}) if isinstance(payload, dict) else {}

    duration_sec = time.perf_counter() - start
    metrics: dict[str, object] = {
        "provider": "landing_ai",
        "model": model or metadata.get("version") or "default",
        "duration_sec": round(duration_sec, 3),
    }
    page_count = metadata.get("page_count") if isinstance(metadata, dict) else None
    if page_count is not None:
        metrics["pages"] = page_count

    duration_ms = metadata.get("duration_ms") if isinstance(metadata, dict) else None
    duration_ms_float = _to_float(duration_ms)
    if duration_ms_float is not None:
        metrics["api_duration_sec"] = round(duration_ms_float / 1000, 3)

    credit_usage = metadata.get("credit_usage") if isinstance(metadata, dict) else None
    credit_usage_float = _to_float(credit_usage)
    if credit_usage_float is not None:
        metrics["credits"] = credit_usage_float
        if credit_to_usd is not None:
            metrics["estimated_cost"] = round(credit_usage_float * credit_to_usd, 6)

    return markdown, metrics

