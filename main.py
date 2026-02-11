"""
Brief: Run PDF-to-Markdown extraction across multiple providers and save comparable outputs.

Inputs:
- CLI args:
  - `--input-dir`: Directory containing source PDFs (default: `sample_pdfs`).
  - `--input-file`: Optional single PDF filename inside `--input-dir` (example: `invoice.pdf`).
  - `--output-dir`: Directory where provider folders and `metrics.txt` are written (default: `output`).
  - `--providers`: Comma-separated provider names to run. Supported: `mistral`, `landing_ai`, `openai`, `gemini`, `marker`.
- Files/paths: Input directory is expected to contain `.pdf` files.
- Env vars:
  - `MISTRAL_API_KEY`: API key for Mistral OCR.
  - `MISTRAL_OCR_MODEL`: Optional model name override (default: `mistral-ocr-latest`).
  - `MISTRAL_USD_PER_1000_PAGES`: Optional price config for estimated cost (default: `2`).
  - `LANDING_AI_API_KEY`: API key for Landing AI ADE Parse.
  - `LANDING_AI_PARSE_URL`: Optional endpoint override (default: `https://api.va.landing.ai/v1/ade/parse`).
  - `LANDING_AI_MODEL`: Optional model override for ADE Parse.
  - `LANDING_AI_SPLIT`: Optional split mode (for example: `page`).
  - `LANDING_AI_CREDIT_TO_USD`: Optional conversion ratio to estimate cost from API credit usage.
  - `LOG_LEVEL`: Optional logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`).

Outputs:
- Run-scoped markdown files in `output/runs/<run_id>/<provider>/<pdf_stem>.md`.
- Run-scoped metrics at `output/runs/<run_id>/metrics.txt`.
- Append-only benchmark log at `output/metrics.txt` (all runs).

Usage (from project root):
- python -m main --providers mistral --input-dir sample_pdfs --output-dir output
- python -m main --providers mistral --input-file invoice.pdf
"""

from __future__ import annotations

import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import Callable

from dotenv import load_dotenv

from app.gemini.extract import pdf_to_markdown as gemini_extract
from app.landing_ai.extract import pdf_to_markdown as landing_ai_extract
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
    "landing_ai": landing_ai_extract,
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
        "--input-file",
        default=None,
        help="Optional PDF filename in --input-dir to run only one file (for example: invoice.pdf).",
    )
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Directory for extracted markdown and metrics.",
    )
    parser.add_argument(
        "--providers",
        default="mistral",
        help="Comma-separated providers to run (mistral,landing_ai,openai,gemini,marker).",
    )
    return parser.parse_args()


def list_pdfs(input_dir: Path) -> list[Path]:
    """Return all PDFs in the input directory sorted by filename."""
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory does not exist: {input_dir}")
    return sorted(path for path in input_dir.iterdir() if path.suffix.lower() == ".pdf")


def resolve_pdf_paths(input_dir: Path, input_file: str | None) -> list[Path]:
    """Resolve either all PDFs in a folder or one selected PDF file."""
    if not input_file:
        return list_pdfs(input_dir)

    selected_pdf = input_dir / input_file
    if not selected_pdf.exists() or not selected_pdf.is_file():
        raise FileNotFoundError(f"Input PDF does not exist: {selected_pdf}")
    if selected_pdf.suffix.lower() != ".pdf":
        raise ValueError(f"Input file must be a PDF: {selected_pdf.name}")
    return [selected_pdf]


def parse_provider_names(raw_providers: str) -> list[str]:
    """Validate selected provider names and return normalized provider list."""
    requested = [
        item.strip().lower() for item in raw_providers.split(",") if item.strip()
    ]
    if not requested:
        raise ValueError("No providers were selected. Pass at least one provider.")
    unknown = [name for name in requested if name not in PROVIDERS]
    if unknown:
        raise ValueError(f"Unsupported providers: {', '.join(unknown)}")
    return requested


def create_run_output_dir(output_dir: Path) -> tuple[str, Path]:
    """Create and return a unique run directory id and path."""
    runs_dir = output_dir / "runs"
    ensure_dir(runs_dir)
    base_run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_id = base_run_id
    suffix = 1
    while (runs_dir / run_id).exists():
        run_id = f"{base_run_id}_{suffix:02d}"
        suffix += 1
    run_output_dir = runs_dir / run_id
    ensure_dir(run_output_dir)
    return run_id, run_output_dir


def run_provider_for_pdf(
    run_id: str,
    provider_name: str,
    provider_fn: ProviderFn,
    pdf_path: Path,
    run_output_dir: Path,
    run_metrics_path: Path,
    global_metrics_path: Path,
) -> None:
    """Run one provider for one PDF and persist markdown + metrics."""
    start = timer()
    try:
        markdown, metrics = provider_fn(str(pdf_path))
        provider_output_dir = run_output_dir / provider_name
        ensure_dir(provider_output_dir)
        output_path = provider_output_dir / f"{pdf_path.stem}.md"
        save_markdown(output_path, markdown)

        metrics = dict(metrics)
        metrics.setdefault("run_id", run_id)
        metrics.setdefault("provider", provider_name)
        metrics.setdefault("duration_sec", round(timer() - start, 3))

        line = format_metrics_line(pdf_path.name, metrics)
        append_metrics(run_metrics_path, line)
        append_metrics(global_metrics_path, line)
        logger.info("Completed provider=%s pdf=%s", provider_name, pdf_path.name)
    except Exception as error:
        failed_metrics: dict[str, object] = {
            "run_id": run_id,
            "provider": provider_name,
            "duration_sec": round(timer() - start, 3),
            "error": str(error),
        }
        line = format_metrics_line(pdf_path.name, failed_metrics)
        append_metrics(run_metrics_path, f"{line} error={error}")
        append_metrics(global_metrics_path, f"{line} error={error}")
        logger.exception("Failed provider=%s pdf=%s", provider_name, pdf_path.name)


def main() -> None:
    """Script entrypoint for running the OCR comparison harness."""
    args = parse_args()
    project_root = Path(__file__).parent
    input_dir = project_root / args.input_dir
    output_dir = project_root / args.output_dir
    global_metrics_path = output_dir / "metrics.txt"
    provider_names = parse_provider_names(args.providers)

    ensure_dir(output_dir)
    run_id, run_output_dir = create_run_output_dir(output_dir)
    run_metrics_path = run_output_dir / "metrics.txt"
    pdf_paths = resolve_pdf_paths(input_dir=input_dir, input_file=args.input_file)
    if not pdf_paths:
        logger.warning("No PDF files found in %s", input_dir)
        return

    logger.info(
        "Starting benchmark run_id=%s providers=%s pdf_count=%s",
        run_id,
        ",".join(provider_names),
        len(pdf_paths),
    )
    for pdf_path in pdf_paths:
        for provider_name in provider_names:
            run_provider_for_pdf(
                run_id=run_id,
                provider_name=provider_name,
                provider_fn=PROVIDERS[provider_name],
                pdf_path=pdf_path,
                run_output_dir=run_output_dir,
                run_metrics_path=run_metrics_path,
                global_metrics_path=global_metrics_path,
            )

    logger.info(
        "Finished benchmark run_id=%s. Run metrics: %s. Global metrics: %s",
        run_id,
        run_metrics_path,
        global_metrics_path,
    )


if __name__ == "__main__":
    load_dotenv()
    setup_logger()
    main()
