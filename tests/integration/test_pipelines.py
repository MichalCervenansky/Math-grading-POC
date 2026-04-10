from unittest.mock import MagicMock, patch

import pytest

from src.models import GradingResult, TaskComponentScore, TaskGradingResult, TriageResult


def _readable_triage():
    return TriageResult(is_readable=True, reason="Citatelne")


def _unreadable_triage():
    return TriageResult(is_readable=False, reason="Necitatelne")


def _grading_result(task_total=999, total=999, max_possible=999):
    """Create a GradingResult with deliberately wrong totals for recalculation testing."""
    return GradingResult(
        tasks=[
            TaskGradingResult(
                task_name="Uloha 4",
                total_score=task_total,
                max_possible_score=5.0,
                component_scores=[
                    TaskComponentScore(
                        component_name="C1",
                        max_points=1.0,
                        awarded_points=1.0,
                        note="ok",
                    ),
                    TaskComponentScore(
                        component_name="C2",
                        max_points=1.0,
                        awarded_points=0.5,
                        note="chyba",
                    ),
                ],
                mistakes=[],
                recognized_data="data",
                verification_notes="notes",
            ),
            TaskGradingResult(
                task_name="Uloha 5",
                total_score=task_total,
                max_possible_score=5.0,
                component_scores=[
                    TaskComponentScore(
                        component_name="C1",
                        max_points=1.0,
                        awarded_points=1.0,
                        note="ok",
                    ),
                    TaskComponentScore(
                        component_name="C2",
                        max_points=1.0,
                        awarded_points=1.0,
                        note="ok",
                    ),
                ],
                mistakes=[],
                recognized_data="data",
                verification_notes="notes",
            ),
        ],
        total_score=total,
        max_possible_score=max_possible,
        feedback_summary="Feedback.",
    )


@pytest.fixture
def pipeline_mocks():
    """Patch all external dependencies of pipelines.grade_exam."""
    with (
        patch("src.pipelines.get_api_key", return_value="fake-key") as mock_key,
        patch("src.pipelines.gemini_client") as mock_gc,
        patch("src.pipelines.pdf_processor") as mock_pdf,
        patch("src.pipelines.create_retry_decorator") as mock_retry,
    ):
        mock_retry.return_value = lambda fn: fn  # passthrough decorator
        mock_pdf.upload_pdf.return_value = MagicMock(name="files/test")
        mock_pdf.upload_pdf_from_bytes.return_value = MagicMock(name="files/test")
        yield {
            "get_api_key": mock_key,
            "gemini_client": mock_gc,
            "pdf_processor": mock_pdf,
            "create_retry_decorator": mock_retry,
        }


class TestGradeExamFullFlow:
    def test_readable_document(self, pipeline_mocks):
        from src.pipelines import grade_exam

        triage = _readable_triage()
        grading = _grading_result()

        mock_gc = pipeline_mocks["gemini_client"]
        mock_gc.generate_structured.side_effect = [triage, grading]

        result_triage, result_grading = grade_exam(pdf_path="/fake/test.pdf")

        assert result_triage.is_readable is True
        assert result_grading is not None
        assert mock_gc.generate_structured.call_count == 2

    def test_unreadable_stops_early(self, pipeline_mocks):
        from src.pipelines import grade_exam

        mock_gc = pipeline_mocks["gemini_client"]
        mock_gc.generate_structured.return_value = _unreadable_triage()

        triage, result = grade_exam(pdf_path="/fake/test.pdf")

        assert triage.is_readable is False
        assert result is None
        assert mock_gc.generate_structured.call_count == 1


class TestScoreRecalculation:
    def test_recalculates_total_score(self, pipeline_mocks):
        from src.pipelines import grade_exam

        mock_gc = pipeline_mocks["gemini_client"]
        mock_gc.generate_structured.side_effect = [_readable_triage(), _grading_result()]

        _, result = grade_exam(pdf_path="/fake/test.pdf")

        # Task 1: 1.0 + 0.5 = 1.5, Task 2: 1.0 + 1.0 = 2.0
        assert result.tasks[0].total_score == pytest.approx(1.5)
        assert result.tasks[1].total_score == pytest.approx(2.0)
        assert result.total_score == pytest.approx(3.5)

    def test_recalculates_max_possible(self, pipeline_mocks):
        from src.pipelines import grade_exam

        mock_gc = pipeline_mocks["gemini_client"]
        mock_gc.generate_structured.side_effect = [_readable_triage(), _grading_result()]

        _, result = grade_exam(pdf_path="/fake/test.pdf")

        # Both tasks have max 5.0 each
        assert result.max_possible_score == pytest.approx(10.0)


class TestPdfInputModes:
    def test_pdf_path_calls_upload_pdf(self, pipeline_mocks):
        from src.pipelines import grade_exam

        mock_gc = pipeline_mocks["gemini_client"]
        mock_gc.generate_structured.side_effect = [_readable_triage(), _grading_result()]

        grade_exam(pdf_path="/fake/test.pdf")
        pipeline_mocks["pdf_processor"].upload_pdf.assert_called_once_with("/fake/test.pdf")

    def test_pdf_bytes_calls_upload_from_bytes(self, pipeline_mocks):
        from src.pipelines import grade_exam

        mock_gc = pipeline_mocks["gemini_client"]
        mock_gc.generate_structured.side_effect = [_readable_triage(), _grading_result()]

        grade_exam(pdf_bytes=(b"data", "file.pdf"))
        pipeline_mocks["pdf_processor"].upload_pdf_from_bytes.assert_called_once_with(
            b"data", "file.pdf"
        )

    def test_neither_raises_value_error(self, pipeline_mocks):
        from src.pipelines import grade_exam

        with pytest.raises(ValueError, match="pdf_path alebo pdf_bytes"):
            grade_exam()


class TestCleanup:
    def test_cleanup_called_on_success(self, pipeline_mocks):
        from src.pipelines import grade_exam

        mock_gc = pipeline_mocks["gemini_client"]
        mock_gc.generate_structured.side_effect = [_readable_triage(), _grading_result()]

        grade_exam(pdf_path="/fake/test.pdf")
        pipeline_mocks["pdf_processor"].cleanup_file.assert_called_once()

    def test_cleanup_called_on_error(self, pipeline_mocks):
        from src.pipelines import grade_exam

        mock_gc = pipeline_mocks["gemini_client"]
        mock_gc.generate_structured.side_effect = [
            _readable_triage(),
            RuntimeError("API failed"),
        ]

        with pytest.raises(RuntimeError):
            grade_exam(pdf_path="/fake/test.pdf")

        pipeline_mocks["pdf_processor"].cleanup_file.assert_called_once()


class TestCallbacks:
    def test_on_progress_called(self, pipeline_mocks):
        from src.pipelines import grade_exam

        mock_gc = pipeline_mocks["gemini_client"]
        mock_gc.generate_structured.side_effect = [_readable_triage(), _grading_result()]
        progress = MagicMock()

        grade_exam(pdf_path="/fake/test.pdf", on_progress=progress)

        assert progress.call_count >= 3  # upload, triage, grading, cleanup

    def test_on_status_passed_to_retry(self, pipeline_mocks):
        from src.pipelines import grade_exam

        mock_gc = pipeline_mocks["gemini_client"]
        mock_gc.generate_structured.side_effect = [_readable_triage(), _grading_result()]
        status_cb = MagicMock()

        grade_exam(pdf_path="/fake/test.pdf", on_status=status_cb)

        pipeline_mocks["create_retry_decorator"].assert_called_once_with(on_retry=status_cb)

    def test_api_key_override(self, pipeline_mocks):
        from src.pipelines import grade_exam

        mock_gc = pipeline_mocks["gemini_client"]
        mock_gc.generate_structured.side_effect = [_readable_triage(), _grading_result()]

        grade_exam(pdf_path="/fake/test.pdf", api_key="custom-key")

        pipeline_mocks["get_api_key"].assert_called_once_with("custom-key")
