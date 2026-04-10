import logging
import tempfile
import time
from pathlib import Path

import google.generativeai as genai

logger = logging.getLogger(__name__)


def upload_pdf(file_path: str, display_name: str | None = None) -> genai.types.File:
    uploaded = genai.upload_file(
        path=file_path,
        display_name=display_name or Path(file_path).name,
    )

    while uploaded.state.name == "PROCESSING":
        time.sleep(2)
        uploaded = genai.get_file(uploaded.name)

    if uploaded.state.name != "ACTIVE":
        raise RuntimeError(f"Subor nedosiahol stav ACTIVE: {uploaded.state.name}")

    return uploaded


def upload_pdf_from_bytes(data: bytes, filename: str) -> genai.types.File:
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(data)
        tmp_path = tmp.name

    try:
        return upload_pdf(tmp_path, display_name=filename)
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def cleanup_file(file_ref: genai.types.File) -> None:
    try:
        genai.delete_file(file_ref.name)
    except Exception:
        logger.debug("Failed to delete file %s", file_ref.name, exc_info=True)
