from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.pdf_processor import cleanup_file, upload_pdf, upload_pdf_from_bytes


def _make_file_mock(state_name="ACTIVE", name="files/abc123"):
    mock_file = MagicMock()
    mock_file.state.name = state_name
    mock_file.name = name
    return mock_file


@patch("src.pdf_processor.time.sleep")
@patch("src.pdf_processor.genai")
class TestUploadPdf:
    def test_active_immediately(self, mock_genai, mock_sleep):
        active_file = _make_file_mock("ACTIVE")
        mock_genai.upload_file.return_value = active_file

        result = upload_pdf("/tmp/test.pdf")
        assert result == active_file
        mock_genai.get_file.assert_not_called()
        mock_sleep.assert_not_called()

    def test_polls_until_active(self, mock_genai, mock_sleep):
        processing_file = _make_file_mock("PROCESSING")
        active_file = _make_file_mock("ACTIVE")
        mock_genai.upload_file.return_value = processing_file
        mock_genai.get_file.return_value = active_file

        result = upload_pdf("/tmp/test.pdf")
        assert result == active_file
        mock_genai.get_file.assert_called_once()
        mock_sleep.assert_called_once_with(2)

    def test_raises_on_failed_state(self, mock_genai, mock_sleep):
        failed_file = _make_file_mock("FAILED")
        mock_genai.upload_file.return_value = failed_file

        with pytest.raises(RuntimeError, match="nedosiahol stav ACTIVE"):
            upload_pdf("/tmp/test.pdf")

    def test_display_name_default(self, mock_genai, mock_sleep):
        mock_genai.upload_file.return_value = _make_file_mock("ACTIVE")

        upload_pdf("/tmp/exam.pdf")
        mock_genai.upload_file.assert_called_once_with(
            path="/tmp/exam.pdf", display_name="exam.pdf"
        )

    def test_display_name_override(self, mock_genai, mock_sleep):
        mock_genai.upload_file.return_value = _make_file_mock("ACTIVE")

        upload_pdf("/tmp/exam.pdf", display_name="custom.pdf")
        mock_genai.upload_file.assert_called_once_with(
            path="/tmp/exam.pdf", display_name="custom.pdf"
        )


@patch("src.pdf_processor.time.sleep")
@patch("src.pdf_processor.genai")
class TestUploadPdfFromBytes:
    def test_uploads_and_returns(self, mock_genai, mock_sleep):
        mock_genai.upload_file.return_value = _make_file_mock("ACTIVE")

        result = upload_pdf_from_bytes(b"fake pdf data", "test.pdf")
        assert result.name == "files/abc123"
        mock_genai.upload_file.assert_called_once()
        # Verify the display_name was passed through
        _, kwargs = mock_genai.upload_file.call_args
        assert kwargs["display_name"] == "test.pdf"

    def test_cleans_up_temp_file(self, mock_genai, mock_sleep):
        mock_genai.upload_file.return_value = _make_file_mock("ACTIVE")

        captured_paths = []

        def capture_path(**kwargs):
            captured_paths.append(kwargs["path"])
            return _make_file_mock("ACTIVE")

        mock_genai.upload_file.side_effect = capture_path

        upload_pdf_from_bytes(b"data", "test.pdf")
        assert len(captured_paths) == 1
        # Temp file should be cleaned up
        assert not Path(captured_paths[0]).exists()


@patch("src.pdf_processor.genai")
class TestCleanupFile:
    def test_calls_delete(self, mock_genai):
        file_ref = _make_file_mock()
        cleanup_file(file_ref)
        mock_genai.delete_file.assert_called_once_with("files/abc123")

    def test_swallows_exception(self, mock_genai):
        mock_genai.delete_file.side_effect = Exception("API error")
        file_ref = _make_file_mock()
        # Should not raise
        cleanup_file(file_ref)
