import json
import re
from collections.abc import Callable

import google.generativeai as genai
from pydantic import BaseModel

from src.config import GEMINI_MODEL_NAME, GENERATION_TEMPERATURE


def _build_example(schema: type[BaseModel]) -> dict:
    """Build a concrete example dict from a Pydantic model for prompting."""
    example = {}
    for name, field in schema.model_fields.items():
        ann = field.annotation
        origin = getattr(ann, "__origin__", None)
        args = getattr(ann, "__args__", ())

        if ann is str:
            example[name] = "..."
        elif ann is int:
            example[name] = 0
        elif ann is float:
            example[name] = 0.0
        elif ann is bool:
            example[name] = True
        elif origin is list and args:
            inner = args[0]
            if isinstance(inner, type) and issubclass(inner, BaseModel):
                example[name] = [_build_example(inner)]
            else:
                example[name] = []
        elif isinstance(ann, type) and issubclass(ann, BaseModel):
            example[name] = _build_example(ann)
        else:
            example[name] = "..."
    return example


def initialize(api_key: str) -> None:
    genai.configure(api_key=api_key)


def _extract_json(text: str) -> str:
    match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        return match.group(1)
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return match.group(0)
    return text


def generate_structured(
    contents: list,
    system_instruction: str,
    response_schema: type[BaseModel],
    retry_decorator: Callable | None = None,
) -> BaseModel:
    example = _build_example(response_schema)
    system_instruction = (
        system_instruction
        + "\n\n# RESPONSE FORMAT\n"
        + "Your response MUST be EXCLUSIVELY a single JSON object. "
        + "No other text before or after the JSON.\n"
        + "The JSON must have EXACTLY these keys and value types (example):\n"
        + "```json\n"
        + json.dumps(example, indent=2, ensure_ascii=False)
        + "\n```\n"
        + "Fill in actual values instead of the example values. All keys are REQUIRED.\n"
        + "Remember: all text values (feedback_summary, note, correction, "
        + "recognized_data, verification_notes) must be in Slovak."
    )

    model = genai.GenerativeModel(
        model_name=GEMINI_MODEL_NAME,
        system_instruction=system_instruction,
        generation_config=genai.GenerationConfig(
            temperature=GENERATION_TEMPERATURE,
        ),
    )

    def _call():
        response = model.generate_content(contents)
        text = _extract_json(response.text)
        return response_schema.model_validate_json(text)

    if retry_decorator:
        _call = retry_decorator(_call)

    return _call()
