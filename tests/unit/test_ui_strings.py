import inspect

from src import ui_strings


class TestUiStrings:
    def test_all_strings_nonempty(self):
        for name, value in inspect.getmembers(ui_strings):
            if name.startswith("_"):
                continue
            if isinstance(value, str):
                assert len(value) > 0, f"{name} is empty"

    def test_error_grading_failed_is_template(self):
        assert "{detail}" in ui_strings.ERROR_GRADING_FAILED

    def test_progress_rate_limit_is_template(self):
        assert "{seconds" in ui_strings.PROGRESS_RATE_LIMIT

    def test_upload_types_contains_pdf(self):
        assert isinstance(ui_strings.UPLOAD_TYPES, list)
        assert "pdf" in ui_strings.UPLOAD_TYPES
