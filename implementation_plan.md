# PDF → Markdown Comparison Project (Minimal Benchmark Harness)

## Goal

Build a small experiment harness that:

- runs the same PDFs through multiple PDF → Markdown tools
- saves Markdown outputs per provider
- logs simple comparable metrics (time, tokens, cost if available)
- is easy to extend when new APIs or tools appear

This project is intentionally **simple and not over-engineered**.

---

## Project Structure

```
OCR_comparison/
  main.py
  pyproject.toml
  .env

  sample_pdfs/
    invoice.pdf
    report.pdf
    scan.pdf

  output/

  app/
    mistral/
      extract.py
    openai/
      extract.py
    gemini/
      extract.py
    marker/
      extract.py

  utils/
    file_utils.py
    metrics.py
```

Each provider exposes **one function only**.

---

## Provider Contract

Every provider module must implement:

```python
def pdf_to_markdown(pdf_path: str) -> tuple[str, dict]:
```

Return values:

```
markdown, metrics
```

Example metrics:

```python
{
  "provider": "mistral",
  "model": "mistral-ocr-3",
  "duration_sec": 2.31,
  "tokens": 1234,
  "estimated_cost": 0.02
}
```

Fields are optional. Include what the API provides.

---

## Output Structure

After running `main.py`, the output folder looks like:

```
output/
  mistral/
    invoice.md
    report.md
    scan.md

  openai/
    invoice.md
    report.md
    scan.md

  gemini/
    ...

  marker/
    ...

  metrics.txt
```

This allows:

- visual inspection of Markdown
- simple performance comparison
- easy reruns

---

## main.py Flow

The main script:

1. loads PDFs from `sample_pdfs/`
2. loops through providers
3. runs extraction
4. saves Markdown output
5. logs metrics

Conceptual structure:

```python
PROVIDERS = [
    ("mistral", mistral_extract),
    ("openai", openai_extract),
    ("gemini", gemini_extract),
    ("marker", marker_extract),
]
```

Execution pattern:

```
for each pdf:
    for each provider:
        run extraction
        save markdown
        log metrics
```

---

## Metrics Logging

Use one file:

```
output/metrics.txt
```

Example:

```
provider=mistral pdf=invoice.pdf time=2.3s tokens=1234 cost=0.02
provider=openai pdf=invoice.pdf time=4.8s tokens=2200 cost=0.05
provider=marker pdf=invoice.pdf time=0.9s
```

Keep this simple and append-only.

---

## Utilities

### utils/file_utils.py

Helpers:

```python
def ensure_dir(path)
def save_markdown(path, content)
```

---

### utils/metrics.py

Simple timer utility:

```python
import time

def timer():
    return time.time()
```

---

## Example Provider Implementation

Example: `app/mistral/extract.py`

```python
import time

def pdf_to_markdown(pdf_path: str):
    start = time.time()

    # Call API here
    markdown = "example markdown output"

    duration = time.time() - start

    metrics = {
        "provider": "mistral",
        "duration_sec": duration,
    }

    return markdown, metrics
```

All providers follow the same pattern.

---

## Why This Design Works

This setup provides:

- direct visual comparison of outputs
- comparable timing across tools
- minimal code complexity
- easy provider additions
- no abstraction overhead

You can always evolve this later into a larger benchmarking system if needed.

---

## Recommended First Step

Start with:

- Marker (local baseline)
- Mistral OCR API

Test on:

- digital PDF
- scanned PDF
- table-heavy PDF

Then add OpenAI and Gemini providers.
