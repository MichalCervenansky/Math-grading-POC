import time
from collections.abc import Callable

from google.api_core.exceptions import ResourceExhausted
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.config import RETRY_MAX_ATTEMPTS, RETRY_MAX_WAIT, RETRY_MIN_WAIT

StatusCallback = Callable[[str, float], None]


def create_retry_decorator(
    max_attempts: int = RETRY_MAX_ATTEMPTS,
    min_wait: float = RETRY_MIN_WAIT,
    max_wait: float = RETRY_MAX_WAIT,
    on_retry: StatusCallback | None = None,
) -> Callable:
    def _countdown_sleep(seconds):
        remaining = int(seconds)
        frac = seconds - remaining
        # Show initial value immediately
        if on_retry and remaining > 0:
            on_retry(
                f"Gemini API limit dosiahnuty. Cakam {remaining}s...",
                float(remaining),
            )
        while remaining > 0:
            time.sleep(1)
            remaining -= 1
            if on_retry:
                if remaining > 0:
                    on_retry(
                        f"Gemini API limit dosiahnuty. Cakam {remaining}s...",
                        float(remaining),
                    )
                else:
                    on_retry("Opakujem poziadavku...", 0.0)
        if frac > 0:
            time.sleep(frac)

    return retry(
        retry=retry_if_exception_type(ResourceExhausted),
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
        sleep=_countdown_sleep,
        reraise=True,
    )
