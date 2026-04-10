import pytest
from pydantic import ValidationError

from src.models import (
    GradingResult,
    MistakeDetail,
    TaskComponentScore,
    TaskGradingResult,
    TriageResult,
)


class TestTriageResult:
    def test_valid(self):
        t = TriageResult(is_readable=True, reason="ok")
        assert t.is_readable is True
        assert t.reason == "ok"

    def test_missing_reason_raises(self):
        with pytest.raises(ValidationError):
            TriageResult(is_readable=True)

    def test_missing_is_readable_raises(self):
        with pytest.raises(ValidationError):
            TriageResult(reason="ok")


class TestTaskComponentScore:
    def test_valid(self):
        c = TaskComponentScore(
            component_name="Test", max_points=1.0, awarded_points=0.5, note="ok"
        )
        assert c.component_name == "Test"
        assert c.max_points == 1.0
        assert c.awarded_points == 0.5

    def test_negative_points_allowed(self):
        c = TaskComponentScore(component_name="Test", max_points=1.0, awarded_points=-0.5, note="")
        assert c.awarded_points == -0.5


class TestMistakeDetail:
    def test_valid(self):
        m = MistakeDetail(
            question_number_or_topic="Q1",
            student_answer="42",
            correct_answer="43",
            correction="Off by one",
            points_deducted=1.0,
        )
        assert m.points_deducted == 1.0

    def test_missing_field_raises(self):
        with pytest.raises(ValidationError):
            MistakeDetail(
                question_number_or_topic="Q1",
                student_answer="42",
            )


class TestTaskGradingResult:
    def test_valid(self):
        t = TaskGradingResult(
            task_name="Task 1",
            total_score=4.0,
            max_possible_score=5.0,
            component_scores=[
                TaskComponentScore(
                    component_name="C1", max_points=5.0, awarded_points=4.0, note=""
                )
            ],
            mistakes=[],
            recognized_data="data",
            verification_notes="notes",
        )
        assert t.task_name == "Task 1"
        assert len(t.component_scores) == 1
        assert len(t.mistakes) == 0

    def test_empty_lists_valid(self):
        t = TaskGradingResult(
            task_name="T",
            total_score=0,
            max_possible_score=0,
            component_scores=[],
            mistakes=[],
            recognized_data="",
            verification_notes="",
        )
        assert t.component_scores == []
        assert t.mistakes == []


class TestGradingResult:
    def test_valid(self, sample_grading_result):
        assert isinstance(sample_grading_result, GradingResult)
        assert len(sample_grading_result.tasks) == 1

    def test_json_roundtrip(self, sample_grading_result):
        json_str = sample_grading_result.model_dump_json()
        restored = GradingResult.model_validate_json(json_str)
        assert restored.total_score == sample_grading_result.total_score
        assert len(restored.tasks) == len(sample_grading_result.tasks)
        assert (
            restored.tasks[0].component_scores[0].component_name
            == sample_grading_result.tasks[0].component_scores[0].component_name
        )

    def test_from_dict(self):
        data = {
            "tasks": [
                {
                    "task_name": "T1",
                    "total_score": 3.0,
                    "max_possible_score": 5.0,
                    "component_scores": [
                        {
                            "component_name": "C",
                            "max_points": 5.0,
                            "awarded_points": 3.0,
                            "note": "",
                        }
                    ],
                    "mistakes": [],
                    "recognized_data": "d",
                    "verification_notes": "v",
                }
            ],
            "total_score": 3.0,
            "max_possible_score": 5.0,
            "feedback_summary": "ok",
        }
        result = GradingResult.model_validate(data)
        assert result.total_score == 3.0
        assert result.tasks[0].task_name == "T1"
