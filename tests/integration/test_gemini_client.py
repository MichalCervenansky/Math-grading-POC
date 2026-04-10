import json
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from src.config import GEMINI_MODEL_NAME
from src.gemini_client import generate_structured, initialize
from src.models import GradingResult, TriageResult


@patch("src.gemini_client.genai")
class TestInitialize:
    def test_calls_configure(self, mock_genai):
        initialize("key123")
        mock_genai.configure.assert_called_once_with(api_key="key123")


@patch("src.gemini_client.genai")
class TestGenerateStructured:
    def _setup_mock(self, mock_genai, response_text):
        mock_response = MagicMock()
        mock_response.text = response_text
        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        return mock_model

    def test_triage_result(self, mock_genai):
        self._setup_mock(mock_genai, '{"is_readable": true, "reason": "ok"}')
        result = generate_structured(
            contents=["test"],
            system_instruction="test prompt",
            response_schema=TriageResult,
        )
        assert isinstance(result, TriageResult)
        assert result.is_readable is True
        assert result.reason == "ok"

    def test_with_code_block(self, mock_genai):
        self._setup_mock(mock_genai, '```json\n{"is_readable": false, "reason": "blur"}\n```')
        result = generate_structured(
            contents=["test"],
            system_instruction="test",
            response_schema=TriageResult,
        )
        assert result.is_readable is False

    def test_grading_result(self, mock_genai):
        grading_json = json.dumps(
            {
                "tasks": [
                    {
                        "task_name": "Task 4",
                        "total_score": 4.0,
                        "max_possible_score": 5.0,
                        "component_scores": [
                            {
                                "component_name": "C1",
                                "max_points": 5.0,
                                "awarded_points": 4.0,
                                "note": "ok",
                            }
                        ],
                        "mistakes": [],
                        "recognized_data": "data",
                        "verification_notes": "notes",
                    }
                ],
                "total_score": 4.0,
                "max_possible_score": 5.0,
                "feedback_summary": "Good",
            }
        )
        self._setup_mock(mock_genai, grading_json)
        result = generate_structured(
            contents=["test"],
            system_instruction="test",
            response_schema=GradingResult,
        )
        assert isinstance(result, GradingResult)
        assert result.total_score == 4.0
        assert len(result.tasks) == 1

    def test_invalid_json_raises(self, mock_genai):
        self._setup_mock(mock_genai, "not json at all {{")
        with pytest.raises((ValidationError, json.JSONDecodeError)):
            generate_structured(
                contents=["test"],
                system_instruction="test",
                response_schema=TriageResult,
            )

    def test_system_instruction_includes_schema(self, mock_genai):
        self._setup_mock(mock_genai, '{"is_readable": true, "reason": "ok"}')
        generate_structured(
            contents=["test"],
            system_instruction="original prompt",
            response_schema=TriageResult,
        )
        call_kwargs = mock_genai.GenerativeModel.call_args
        system_instr = call_kwargs.kwargs.get("system_instruction") or call_kwargs[1].get(
            "system_instruction"
        )
        assert "RESPONSE FORMAT" in system_instr
        assert "is_readable" in system_instr

    def test_uses_correct_model_name(self, mock_genai):
        self._setup_mock(mock_genai, '{"is_readable": true, "reason": "ok"}')
        generate_structured(
            contents=["test"],
            system_instruction="test",
            response_schema=TriageResult,
        )
        call_kwargs = mock_genai.GenerativeModel.call_args
        assert call_kwargs.kwargs.get("model_name") == GEMINI_MODEL_NAME

    def test_with_retry_decorator(self, mock_genai):
        self._setup_mock(mock_genai, '{"is_readable": true, "reason": "ok"}')

        def passthrough_decorator(fn):
            return fn

        result = generate_structured(
            contents=["test"],
            system_instruction="test",
            response_schema=TriageResult,
            retry_decorator=passthrough_decorator,
        )
        assert isinstance(result, TriageResult)
