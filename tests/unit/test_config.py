import pytest

from src.config import (
    DEFAULT_RUBRIC_PATH,
    GEMINI_MODEL_NAME,
    GENERATION_TEMPERATURE,
    RESOURCES_DIR,
    RETRY_MAX_ATTEMPTS,
    RETRY_MAX_WAIT,
    RETRY_MIN_WAIT,
    get_api_key,
)


class TestConstants:
    def test_types(self):
        assert isinstance(GEMINI_MODEL_NAME, str)
        assert isinstance(RETRY_MIN_WAIT, float)
        assert isinstance(RETRY_MAX_WAIT, float)
        assert isinstance(RETRY_MAX_ATTEMPTS, int)
        assert isinstance(GENERATION_TEMPERATURE, float)

    def test_sensible_values(self):
        assert RETRY_MIN_WAIT < RETRY_MAX_WAIT
        assert RETRY_MAX_ATTEMPTS > 0
        assert 0 < GENERATION_TEMPERATURE < 2.0

    def test_default_rubric_path_format(self):
        assert str(DEFAULT_RUBRIC_PATH).endswith(".txt")

    def test_resources_dir_is_path(self):
        from pathlib import Path

        assert isinstance(RESOURCES_DIR, Path)


class TestGetApiKey:
    def test_from_override(self):
        assert get_api_key("test-key") == "test-key"

    def test_from_env(self, monkeypatch):
        monkeypatch.setenv("GEMINI_API_KEY", "env-key")
        assert get_api_key() == "env-key"

    def test_override_takes_precedence(self, monkeypatch):
        monkeypatch.setenv("GEMINI_API_KEY", "env-key")
        assert get_api_key("override-key") == "override-key"

    def test_missing_raises(self, monkeypatch):
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        with pytest.raises(RuntimeError, match="API kluc"):
            get_api_key()
