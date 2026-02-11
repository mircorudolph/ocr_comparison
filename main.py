"""
Brief: Run PDF-to-Markdown extraction across multiple providers and save comparable outputs.

Inputs:
- CLI args:
  - `--input-dir`: Directory containing source PDFs (default: `sample_pdfs`).
  - `--output-dir`: Directory where provider folders and `metrics.txt` are written (default: `output`).
  - `--providers`: Comma-separated provider names to run. Supported: `mistral`, `openai`, `gemini`, `marker`.
- Files/paths: Input directory is expected to contain `.pdf` files.
- Env vars:
  - `MISTRAL_API_KEY`: API key for Mistral OCR.
  - `MISTRAL_OCR_MODEL`: Optional model name override (default: `mistral-ocr-latest`).
  - `LOG_LEVEL`: Optional logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`).

Outputs:
- Markdown files in `output/<provider>/<pdf_stem>.md`.
- Append-only benchmark log at `output/metrics.txt`.

Usage (from project root):
- python -m main --providers mistral --input-dir sample_pdfs --output-dir output
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Callable

from app.gemini.extract import pdf_to_markdown as gemini_extract
from app.marker.extract import pdf_to_markdown as marker_extract
from app.mistral.extract import pdf_to_markdown as mistral_extract
from app.openai.extract import pdf_to_markdown as openai_extract
from utils.file_utils import ensure_dir, save_markdown
from utils.logging_config import setup_logger
from utils.metrics import append_metrics, format_metrics_line, timer

logger = logging.getLogger(__name__)

ProviderFn = Callable[[str], tuple[str, dict[str, object]]]
PROVIDERS: dict[str, ProviderFn] = {
    "mistral": mistral_extract,
    "openai": openai_extract,
    "gemini": gemini_extract,
    "marker": marker_extract,
}


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Run OCR comparison and write markdown + metrics."
    )
    parser.add_argument(
        "--input-dir",
        default="sample_pdfs",
        help="Directory with input PDF files.",
    )
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Directory for extracted markdown and metrics.",
    )
    parser.add_argument(
        "--providers",
        default="mistral",
        help="Comma-separated providers to run (mistral,openai,gemini,marker).",
    )
    return parser.parse_args()


def list_pdfs(input_dir: Path) -> list[Path]:
    """Return all PDFs in the input directory sorted by filename."""
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory does not exist: {input_dir}")
    return sorted(path for path in input_dir.iterdir() if path.suffix.lower() == ".pdf")


def parse_provider_names(raw_providers: str) -> list[str]:
    """Validate selected provider names and return normalized provider list."""
    requested = [item.strip().lower() for item in raw_providers.split(",") if item.strip()]
    if not requested:
        raise ValueError("No providers were selected. Pass at least one provider.")
    unknown = [name for name in requested if name not in PROVIDERS]
    if unknown:
        raise ValueError(f"Unsupported providers: {', '.join(unknown)}")
    return requested


def run_provider_for_pdf(
    provider_name: str,
    provider_fn: ProviderFn,
    pdf_path: Path,
    output_dir: Path,
    metrics_path: Path,
) -> None:
    """Run one provider for one PDF and persist markdown + metrics."""
    start = timer()
    try:
        markdown, metrics = provider_fn(str(pdf_path))
        provider_output_dir = output_dir / provider_name
        ensure_dir(provider_output_dir)
        output_path = provider_output_dir / f"{pdf_path.stem}.md"
        save_markdown(output_path, markdown)

        metrics = dict(metrics)
        metrics.setdefault("provider", provider_name)
        metrics.setdefault("duration_sec", round(timer() - start, 3))

        line = format_metrics_line(pdf_path.name, metrics)
        append_metrics(metrics_path, line)
        logger.info("Completed provider=%s pdf=%s", provider_name, pdf_path.name)
    except Exception as error:
        failed_metrics: dict[str, object] = {
            "provider": provider_name,
            "duration_sec": round(timer() - start, 3),
            "error": str(error),
        }
        line = format_metrics_line(pdf_path.name, failed_metrics)
        append_metrics(metrics_path, f"{line} error={error}")
        logger.exception("Failed provider=%s pdf=%s", provider_name, pdf_path.name)


def main() -> None:
    """Script entrypoint for running the OCR comparison harness."""
    args = parse_args()
    project_root = Path(__file__).parent
    input_dir = project_root / args.input_dir
    output_dir = project_root / args.output_dir
    metrics_path = output_dir / "metrics.txt"
    provider_names = parse_provider_names(args.providers)

    ensure_dir(output_dir)
    pdf_paths = list_pdfs(input_dir)
    if not pdf_paths:
        logger.warning("No PDF files found in %s", input_dir)
        return

    logger.info(
        "Starting benchmark with providers=%s pdf_count=%s",
        ",".join(provider_names),
        len(pdf_paths),
    )
    for pdf_path in pdf_paths:
        for provider_name in provider_names:
            run_provider_for_pdf(
                provider_name=provider_name,
                provider_fn=PROVIDERS[provider_name],
                pdf_path=pdf_path,
                output_dir=output_dir,
                metrics_path=metrics_path,
            )

    logger.info("Finished benchmark run. Metrics file: %s", metrics_path)


if __name__ == "__main__":
    setup_logger()
    main()

