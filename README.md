# OCR Comparison

Minimal benchmark harness to compare PDF -> Markdown extraction across providers using a shared contract and common output format.

## What it does

- Reads PDFs from `sample_pdfs/`
- Runs one or more providers (Mistral first)
- Saves markdown outputs under `output/runs/<run_id>/<provider>/`
- Writes run metrics to `output/runs/<run_id>/metrics.txt`
- Appends benchmark lines to `output/metrics.txt` across all runs

## Install

### UV (recommended)

From project root:

```bash
uv init
uv add mistralai
uv add requests
uv add python-dotenv
uv add --dev pytest
```

If you want to add more providers later, install their SDKs similarly with `uv add ...`.

## Environment variables

Copy `.env.example` to `.env` and set values:

- `MISTRAL_API_KEY`: Required for Mistral OCR.
- `MISTRAL_OCR_MODEL`: Optional, defaults to `mistral-ocr-latest`.
- `MISTRAL_USD_PER_1000_PAGES`: Optional price config for Mistral cost estimation. Default: `2`.
- `LANDING_AI_API_KEY`: Required for Landing AI ADE Parse.
- `LANDING_AI_PARSE_URL`: Optional endpoint override. Default: `https://api.va.landing.ai/v1/ade/parse`.
- `LANDING_AI_MODEL`: Optional ADE Parse model override.
- `LANDING_AI_SPLIT`: Optional split mode (`page`).
- `LANDING_AI_CREDIT_TO_USD`: Optional conversion ratio for estimated cost.
- `LOG_LEVEL`: Optional logging level (`INFO` by default).

The app auto-loads `.env` from project root when you run `python -m main`.

## Run locally

Place PDF files in `sample_pdfs/`, then run:

```bash
python -m main --providers mistral --input-dir sample_pdfs --output-dir output
```

Run only one PDF from that folder:

```bash
python -m main --providers mistral --input-dir sample_pdfs --input-file invoice.pdf
```

Run with Landing AI:

```bash
python -m main --providers landing_ai --input-dir sample_pdfs --output-dir output
```

Multiple providers:

```bash
python -m main --providers mistral,landing_ai,openai,gemini,marker
```

## Output layout

```text
output/
  runs/
    <run_id>/
      mistral/
        <pdf_name>.md
      landing_ai/
        <pdf_name>.md
      openai/
      gemini/
      marker/
      metrics.txt
  metrics.txt
```

`metrics.txt` is append-only and line-based, for example:

```text
run=20260211_141500 provider=mistral pdf=invoice.pdf time=2.300s pages=4 tokens=1234 credits=n/a cost=0.008 model=mistral-ocr-latest
run=20260211_141500 provider=landing_ai pdf=invoice.pdf time=1.842s pages=4 tokens=n/a credits=7.5 cost=0.075 model=default
```

## Run tests

```bash
pytest
```

## Docker

Build image:

```bash
docker build -t ocr-comparison .
```

Run container:

```bash
docker run -it --rm --env-file .env -v "$(pwd)/sample_pdfs:/app/sample_pdfs" -v "$(pwd)/output:/app/output" ocr-comparison
```
