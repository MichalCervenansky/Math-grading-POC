import logging
import time
from collections.abc import Callable

from src import gemini_client, pdf_processor
from src.config import get_api_key
from src.models import GradingResult, TriageResult
from src.prompts import (
    GRADING_USER_PROMPT,
    TRIAGE_SYSTEM_PROMPT,
    TRIAGE_USER_PROMPT,
    build_grading_system_prompt,
)
from src.rate_limiter import StatusCallback, create_retry_decorator

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[str], None]


def grade_exam(
    pdf_path: str | None = None,
    pdf_bytes: tuple[bytes, str] | None = None,
    rubric_text: str | None = None,
    api_key: str | None = None,
    on_status: StatusCallback | None = None,
    on_progress: ProgressCallback | None = None,
) -> tuple[TriageResult, GradingResult | None]:
    t_start = time.monotonic()
    key = get_api_key(api_key)
    gemini_client.initialize(key)

    retry_dec = create_retry_decorator(on_retry=on_status)

    def _progress(msg: str) -> None:
        if on_progress:
            on_progress(msg)

    _progress("Nahravam PDF na server... (krok 1/3)")

    t0 = time.monotonic()
    if pdf_path:
        file_ref = pdf_processor.upload_pdf(pdf_path)
    elif pdf_bytes:
        data, filename = pdf_bytes
        file_ref = pdf_processor.upload_pdf_from_bytes(data, filename)
    else:
        raise ValueError("Musite zadat pdf_path alebo pdf_bytes")
    logger.info("PDF upload took %.1fs", time.monotonic() - t0)

    try:
        # Step A: Triage
        _progress("Kontrolujem citatelnost dokumentu... (krok 2/3)")
        t0 = time.monotonic()
        triage = gemini_client.generate_structured(
            contents=[file_ref, TRIAGE_USER_PROMPT],
            system_instruction=TRIAGE_SYSTEM_PROMPT,
            response_schema=TriageResult,
            retry_decorator=retry_dec,
        )
        logger.info("Triage API call took %.1fs", time.monotonic() - t0)

        if not triage.is_readable:
            return triage, None

        # Step B: Grading
        _progress("Hodnotim riesenie... (krok 3/3)")
        t0 = time.monotonic()
        grading_prompt = build_grading_system_prompt(rubric_text)
        result = gemini_client.generate_structured(
            contents=[file_ref, GRADING_USER_PROMPT],
            system_instruction=grading_prompt,
            response_schema=GradingResult,
            retry_decorator=retry_dec,
        )
        logger.info("Grading API call took %.1fs", time.monotonic() - t0)

        # Validate score sums
        for task in result.tasks:
            task.total_score = sum(c.awarded_points for c in task.component_scores)
        result.total_score = sum(t.total_score for t in result.tasks)
        result.max_possible_score = sum(t.max_possible_score for t in result.tasks)

        logger.info("Total pipeline took %.1fs", time.monotonic() - t_start)
        return triage, result

    finally:
        _progress("Cistim docasne subory...")
        pdf_processor.cleanup_file(file_ref)
