# Math Grading POC

Automated grading of scanned handwritten math exams using the Gemma 4 model via the Google Gemini API.
Uploads student exam PDFs, assesses legibility, and grades them against a configurable rubric.
All grading output and UI text is in Slovak.

## Features

- **Two-step pipeline** -- Triage (legibility check) followed by rubric-based grading
- **Streamlit web UI** -- multi-file upload, real-time progress with rate-limit countdown, color-coded score cards
- **CLI** -- single-file grading with ANSI-colored terminal output
- **Configurable rubric** -- default rubric included; custom rubrics via file upload or CLI flag
- **Rate limiting** -- automatic retry with exponential backoff and countdown display for free-tier API limits
- **Score validation** -- server-side recalculation of component scores for consistency

## Requirements

- Python 3.13+
- Google Gemini API key ([get one here](https://aistudio.google.com/apikey))

## Installation

```bash
git clone https://github.com/MichalCervenansky/Math-grading-POC.git
cd Math-grading-POC

python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the project root:

```
GEMINI_API_KEY=your_api_key_here
```

To change the model, edit `GEMINI_MODEL_NAME` in `src/config.py`. The default model is `gemma-4-31b-it`.

## Usage

### Streamlit Web UI

```bash
streamlit run app.py
```

Upload one or more PDF files, optionally provide a custom rubric in the sidebar, and click **Spustit hodnotenie** to start grading.

### Command-Line Interface

```bash
# Grade with default rubric
python cli.py --file path/to/exam.pdf

# Grade with custom rubric
python cli.py --file path/to/exam.pdf --rubric path/to/rubric.txt

# Provide API key directly
python cli.py --file path/to/exam.pdf --api-key YOUR_KEY
```

## Project Structure

```
app.py                  Streamlit web UI (multi-file upload, threading)
cli.py                  CLI with ANSI-colored output
src/
  config.py             Model name, retry params, API key loading
  models.py             Pydantic schemas (TriageResult, GradingResult, ...)
  prompts.py            LLM system/user prompts (Slovak) + rubric loading
  gemini_client.py      Gemini API calls + JSON extraction fallback
  rate_limiter.py       Tenacity retry with countdown callback
  pdf_processor.py      PDF upload/cleanup via Gemini File API
  pipelines.py          Orchestrates triage -> grading flow
  ui_strings.py         All Slovak UI text constants
tests/
  unit/                 Fast unit tests (no external dependencies)
  integration/          Integration tests (mocked external services)
  e2e/                  End-to-end tests (requires real API key)
resources/              Default grading rubric and sample PDFs
```

## Grading Pipeline

1. **Upload** -- PDF sent to Gemini File API, polling until `ACTIVE`
2. **Triage** -- Gemma 4 assesses document legibility (handwriting clarity, scan quality)
3. **Grading** -- if readable, Gemma 4 grades against the rubric in three phases:
   - *Recognition* -- transcribe student's work exactly as written
   - *Verification* -- independently compute correct answers and compare
   - *Scoring* -- assign points per rubric components
4. **Validation** -- component scores are recalculated server-side for consistency
5. **Cleanup** -- uploaded file is deleted from Gemini File API

## Testing

```bash
# Run unit and integration tests
python -m pytest tests/unit tests/integration -v

# Run all tests including e2e (requires GEMINI_API_KEY in .env)
python -m pytest -v
```

## Development

```bash
# Install dev tools
pip install ruff pre-commit

# Set up pre-commit hooks
pre-commit install

# Lint and format
ruff check .
ruff format .
```

## License

This project is a proof of concept for educational purposes.
