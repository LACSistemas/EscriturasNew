"""Tests for error handling and retry logic."""
import pytest
import asyncio
from utils.error_handler import async_retry, MaxRetriesExceededError, RetryableError


class TestAsyncRetry:
    """Tests for async_retry decorator."""

    @pytest.mark.asyncio
    async def test_retry_success_on_first_attempt(self):
        """Test that function succeeds on first attempt."""
        call_count = 0

        @async_retry(max_attempts=3, delay=0.1)
        async def succeeds_immediately():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await succeeds_immediately()
        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retry_success_after_failures(self):
        """Test that function retries and eventually succeeds."""
        call_count = 0

        @async_retry(max_attempts=3, delay=0.1)
        async def succeeds_on_third_attempt():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise RetryableError("Temporary failure")
            return "success"

        result = await succeeds_on_third_attempt()
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_retry_max_attempts_exceeded(self):
        """Test that MaxRetriesExceededError is raised after max attempts."""
        call_count = 0

        @async_retry(max_attempts=3, delay=0.1)
        async def always_fails():
            nonlocal call_count
            call_count += 1
            raise RetryableError("Permanent failure")

        with pytest.raises(MaxRetriesExceededError):
            await always_fails()

        assert call_count == 3

    @pytest.mark.asyncio
    async def test_retry_with_exponential_backoff(self):
        """Test that retry delays increase exponentially."""
        delays = []
        start_time = asyncio.get_event_loop().time()

        @async_retry(max_attempts=3, delay=0.1, backoff=2.0)
        async def fails_twice():
            current_time = asyncio.get_event_loop().time()
            if delays:
                delays.append(current_time - delays[-1])
            else:
                delays.append(current_time - start_time)

            if len(delays) < 3:
                raise RetryableError("Temporary failure")
            return "success"

        await fails_twice()

        # First delay ~0, Second delay ~0.1s, Third delay ~0.2s
        assert len(delays) == 3
        # Allow some tolerance for timing
        assert delays[1] >= 0.09  # ~0.1s with backoff
        assert delays[2] >= 0.18  # ~0.2s with backoff


class TestValidators:
    """Tests for validators module."""

    def test_cpf_validation(self):
        """Test CPF validation."""
        from utils.validators import validate_cpf

        # Valid CPF
        is_valid, formatted = validate_cpf("52998224725")
        assert is_valid is True
        assert formatted == "529.982.247-25"

        # Invalid CPF (all same digits)
        is_valid, formatted = validate_cpf("111.111.111-11")
        assert is_valid is False
        assert formatted is None

    def test_cnpj_validation(self):
        """Test CNPJ validation."""
        from utils.validators import validate_cnpj

        # Valid CNPJ
        is_valid, formatted = validate_cnpj("11222333000181")
        assert is_valid is True
        assert formatted == "11.222.333/0001-81"

        # Invalid CNPJ (all same digits)
        is_valid, formatted = validate_cnpj("00000000000000")
        assert is_valid is False
        assert formatted is None

    def test_date_validation(self):
        """Test date validation."""
        from utils.validators import validate_date

        # Valid date (Brazilian format)
        is_valid, formatted = validate_date("31/12/2023")
        assert is_valid is True
        assert formatted == "2023-12-31"

        # Valid date (ISO format)
        is_valid, formatted = validate_date("2023-12-31")
        assert is_valid is True
        assert formatted == "2023-12-31"

        # Invalid date
        is_valid, formatted = validate_date("invalid-date")
        assert is_valid is False
        assert formatted is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
