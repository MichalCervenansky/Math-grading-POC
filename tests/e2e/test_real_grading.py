from pathlib import Path

import pytest

from src.models import GradingResult, TriageResult
from src.pipelines import grade_exam

pytestmark = pytest.mark.e2e

MAT4_PATH = Path(__file__).parent.parent.parent / "test_examples" / "mat4.pdf"

EXPECTED_TOTAL = 4.5


@pytest.fixture(scope="module")
def grading_results():
    """Run grading once via real Gemini API. Shared across structural tests."""
    assert MAT4_PATH.exists(), f"Test PDF not found: {MAT4_PATH}"
    triage, result = grade_exam(pdf_path=str(MAT4_PATH))
    return triage, result


class TestMat4Structure:
    """Structural assertions that don't depend on exact score values."""

    def test_document_is_readable(self, grading_results):
        triage, _ = grading_results
        assert isinstance(triage, TriageResult)
        assert triage.is_readable is True

    def test_grading_result_not_none(self, grading_results):
        _, result = grading_results
        assert result is not None
        assert isinstance(result, GradingResult)

    def test_has_tasks(self, grading_results):
        _, result = grading_results
        assert len(result.tasks) >= 1

    def test_max_possible_score_is_reasonable(self, grading_results):
        _, result = grading_results
        assert result.max_possible_score > 0
        assert result.max_possible_score <= 10.0

    def test_score_recalculation_integrity(self, grading_results):
        _, result = grading_results
        expected_total = sum(t.total_score for t in result.tasks)
        assert result.total_score == pytest.approx(expected_total, abs=0.01)

        for task in result.tasks:
            expected_task_total = sum(c.awarded_points for c in task.component_scores)
            assert task.total_score == pytest.approx(expected_task_total, abs=0.01)

    def test_feedback_summary_nonempty(self, grading_results):
        _, result = grading_results
        assert result.feedback_summary

    def test_each_task_has_component_scores(self, grading_results):
        _, result = grading_results
        for task in result.tasks:
            assert len(task.component_scores) > 0

    def test_awarded_points_within_bounds(self, grading_results):
        _, result = grading_results
        for task in result.tasks:
            assert task.total_score >= 0
            assert task.total_score <= task.max_possible_score
            for comp in task.component_scores:
                assert comp.awarded_points >= 0
                assert comp.awarded_points <= comp.max_points


@pytest.mark.flaky(reruns=3)
def test_mat4_total_score_is_4_5():
    """Exact score assertion. Reruns on failure because LLM output may vary."""
    assert MAT4_PATH.exists(), f"Test PDF not found: {MAT4_PATH}"
    triage, result = grade_exam(pdf_path=str(MAT4_PATH))
    assert triage.is_readable is True
    assert result is not None
    assert result.total_score == EXPECTED_TOTAL, (
        f"Expected total_score={EXPECTED_TOTAL}, got {result.total_score}"
    )
