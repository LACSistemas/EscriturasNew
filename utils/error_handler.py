"""Error handling and retry logic for OCR and AI services."""
import asyncio
import logging
from typing import Callable, Any, Optional, Type
from functools import wraps

logger = logging.getLogger(__name__)


class RetryableError(Exception):
    """Base class for errors that should trigger a retry."""
    pass


class OCRError(RetryableError):
    """Error during OCR processing."""
    pass


class AIExtractionError(RetryableError):
    """Error during AI data extraction."""
    pass


class MaxRetriesExceededError(Exception):
    """Raised when maximum retry attempts are exceeded."""
    pass


def async_retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """Decorator for async functions with exponential backoff retry logic.

    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries (seconds)
        backoff: Multiplier for delay after each retry (exponential backoff)
        exceptions: Tuple of exception types to catch and retry

    Example:
        @async_retry(max_attempts=3, delay=1.0, backoff=2.0)
        async def my_function():
            # Function that might fail
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            current_delay = delay
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    logger.debug(f"Attempt {attempt}/{max_attempts} for {func.__name__}")
                    result = await func(*args, **kwargs)

                    if attempt > 1:
                        logger.info(f"✅ {func.__name__} succeeded on attempt {attempt}")

                    return result

                except exceptions as e:
                    last_exception = e

                    if attempt == max_attempts:
                        logger.error(
                            f"❌ {func.__name__} failed after {max_attempts} attempts: {str(e)}"
                        )
                        raise MaxRetriesExceededError(
                            f"Failed after {max_attempts} attempts: {str(e)}"
                        ) from e

                    logger.warning(
                        f"⚠️  {func.__name__} attempt {attempt} failed: {str(e)}. "
                        f"Retrying in {current_delay:.1f}s..."
                    )

                    await asyncio.sleep(current_delay)
                    current_delay *= backoff

            # Should never reach here, but just in case
            raise last_exception

        return wrapper
    return decorator


def log_processing_step(step_name: str, data: dict = None):
    """Log a processing step with optional data.

    Args:
        step_name: Name of the processing step
        data: Optional dictionary with data to log
    """
    if data:
        logger.info(f"📋 {step_name}: {data}")
    else:
        logger.info(f"📋 {step_name}")


def log_error(error: Exception, context: str = ""):
    """Log an error with context.

    Args:
        error: The exception that occurred
        context: Optional context description
    """
    if context:
        logger.error(f"❌ Error in {context}: {type(error).__name__} - {str(error)}")
    else:
        logger.error(f"❌ Error: {type(error).__name__} - {str(error)}")


def log_warning(message: str):
    """Log a warning message.

    Args:
        message: Warning message
    """
    logger.warning(f"⚠️  {message}")


def log_success(message: str):
    """Log a success message.

    Args:
        message: Success message
    """
    logger.info(f"✅ {message}")
