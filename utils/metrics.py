"""Timing and metrics logging helpers."""

from __future__ import annotations

import time
from pathlib import Path

from utils.file_utils import ensure_dir


def timer() -> float:
    """Return a high-resolution timestamp."""
    return time.perf_counter()


def format_metrics_line(pdf_name: str, metrics: dict[str, object]) -> str:
    """Format one metrics dict as an append-only single-line record."""
    provider = str(metrics.get("provider", "unknown"))
    duration = metrics.get("duration_sec")
    duration_value = f"{float(duration):.3f}s" if duration is not None else "n/a"
    tokens = metrics.get("tokens", "n/a")
    cost = metrics.get("estimated_cost", "n/a")
    model = metrics.get("model")

    line = (
        f"provider={provider} pdf={pdf_name} "
        f"time={duration_value} tokens={tokens} cost={cost}"
    )
    if model:
        line += f" model={model}"
    return line


def append_metrics(path: Path, line: str) -> None:
    """Append a metrics line to the metrics text file."""
    ensure_dir(path.parent)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"{line}\n")

