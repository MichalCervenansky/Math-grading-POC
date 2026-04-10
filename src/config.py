import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

GEMINI_MODEL_NAME = "gemma-4-31b-it"
RETRY_MIN_WAIT = 15.0
RETRY_MAX_WAIT = 120.0
RETRY_MAX_ATTEMPTS = 6
GENERATION_TEMPERATURE = 0.1


def get_api_key(override: str | None = None) -> str:
    key = override or os.environ.get("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("API kluc nie je nastaveny. Nastavte GEMINI_API_KEY v .env ")
    return key


RESOURCES_DIR = Path(__file__).parent.parent / "resources"
