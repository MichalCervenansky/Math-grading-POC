from pathlib import Path
from unittest.mock import patch

from src.prompts import (
    DEFAULT_RUBRIC_TEXT,
    GRADING_USER_PROMPT,
    TRIAGE_SYSTEM_PROMPT,
    TRIAGE_USER_PROMPT,
    _load_default_rubric,
    build_grading_system_prompt,
)


class TestPromptConstants:
    def test_triage_system_prompt_nonempty(self):
        assert isinstance(TRIAGE_SYSTEM_PROMPT, str)
        assert len(TRIAGE_SYSTEM_PROMPT) > 0

    def test_triage_user_prompt_nonempty(self):
        assert isinstance(TRIAGE_USER_PROMPT, str)
        assert len(TRIAGE_USER_PROMPT) > 0

    def test_grading_user_prompt_nonempty(self):
        assert isinstance(GRADING_USER_PROMPT, str)
        assert len(GRADING_USER_PROMPT) > 0

    def test_default_rubric_text_loaded(self):
        assert isinstance(DEFAULT_RUBRIC_TEXT, str)
        assert len(DEFAULT_RUBRIC_TEXT) > 0

    def test_prompts_mention_slovak(self):
        assert "Slovak" in TRIAGE_SYSTEM_PROMPT
        assert "Slovak" in GRADING_USER_PROMPT


class TestLoadDefaultRubric:
    def test_returns_empty_on_missing_file(self):
        with patch("src.prompts.DEFAULT_RUBRIC_PATH", Path("/nonexistent/file.txt")):
            result = _load_default_rubric()
        assert result == ""


class TestBuildGradingSystemPrompt:
    def test_with_custom_rubric(self):
        result = build_grading_system_prompt("Custom rubric content")
        assert "Custom rubric content" in result
        assert "=== GRADING RUBRIC ===" in result
        assert "=== END OF RUBRIC ===" in result

    def test_with_default_rubric(self):
        result = build_grading_system_prompt(None)
        assert DEFAULT_RUBRIC_TEXT in result

    def test_contains_instructions(self):
        result = build_grading_system_prompt("test rubric")
        assert "IMPORTANT INSTRUCTIONS" in result
        assert "Slovak" in result

    def test_structure(self):
        result = build_grading_system_prompt("my rubric")
        rubric_start = result.index("=== GRADING RUBRIC ===")
        rubric_end = result.index("=== END OF RUBRIC ===")
        assert rubric_start < rubric_end
        assert "my rubric" in result[rubric_start:rubric_end]
