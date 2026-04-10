from unittest.mock import MagicMock, patch

import pytest
from google.api_core.exceptions import ResourceExhausted

from src.rate_limiter import create_retry_decorator


@patch("src.rate_limiter.time.sleep")
class TestCreateRetryDecorator:
    def test_returns_callable(self, mock_sleep):
        dec = create_retry_decorator()
        assert callable(dec)

    def test_no_retry_on_success(self, mock_sleep):
        dec = create_retry_decorator(max_attempts=3, min_wait=0.01, max_wait=0.02)
        call_count = 0

        @dec
        def succeed():
            nonlocal call_count
            call_count += 1
            return "ok"

        result = succeed()
        assert result == "ok"
        assert call_count == 1

    def test_retries_on_resource_exhausted(self, mock_sleep):
        dec = create_retry_decorator(max_attempts=3, min_wait=0.01, max_wait=0.02)
        call_count = 0

        @dec
        def fail_once():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ResourceExhausted("rate limited")
            return "ok"

        result = fail_once()
        assert result == "ok"
        assert call_count == 2

    def test_gives_up_after_max_attempts(self, mock_sleep):
        dec = create_retry_decorator(max_attempts=2, min_wait=0.01, max_wait=0.02)

        @dec
        def always_fail():
            raise ResourceExhausted("rate limited")

        with pytest.raises(ResourceExhausted):
            always_fail()

    def test_does_not_retry_on_other_exceptions(self, mock_sleep):
        dec = create_retry_decorator(max_attempts=3, min_wait=0.01, max_wait=0.02)
        call_count = 0

        @dec
        def raise_value_error():
            nonlocal call_count
            call_count += 1
            raise ValueError("bad input")

        with pytest.raises(ValueError):
            raise_value_error()
        assert call_count == 1

    def test_on_retry_callback_called(self, mock_sleep):
        callback = MagicMock()
        # Use min_wait >= 1 so int(seconds) > 0 and the countdown loop fires
        dec = create_retry_decorator(max_attempts=3, min_wait=1, max_wait=2, on_retry=callback)
        call_count = 0

        @dec
        def fail_once():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ResourceExhausted("rate limited")
            return "ok"

        fail_once()
        assert callback.call_count > 0
        # Each call should have (str_message, float_remaining)
        for c in callback.call_args_list:
            args = c[0]
            assert isinstance(args[0], str)
            assert isinstance(args[1], float)

    def test_decorator_with_none_callback(self, mock_sleep):
        dec = create_retry_decorator(max_attempts=3, min_wait=0.01, max_wait=0.02, on_retry=None)
        call_count = 0

        @dec
        def fail_once():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ResourceExhausted("rate limited")
            return "ok"

        result = fail_once()
        assert result == "ok"
