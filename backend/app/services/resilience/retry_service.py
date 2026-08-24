import asyncio
import functools
import random
import time
from typing import Any, Callable, Optional, Tuple, Type, Union

from app.core.logging import get_logger

logger = get_logger("app.services.resilience.retry")


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 0.5,
    backoff_factor: float = 2.0,
    max_delay: float = 10.0,
    jitter: bool = True,
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,),
):
    """Decorator offering exponential backoff retry with jitter for both synchronous and asynchronous functions."""

    def decorator(func: Callable):
        if asyncio.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                delay = initial_delay
                last_exception: Optional[Exception] = None

                for attempt in range(1, max_retries + 1):
                    try:
                        return await func(*args, **kwargs)
                    except retryable_exceptions as e:
                        last_exception = e
                        if attempt == max_retries:
                            logger.error(f"[Async Retry] Function '{func.__name__}' failed after {max_retries} attempts: {e}")
                            raise

                        sleep_time = min(delay * (backoff_factor ** (attempt - 1)), max_delay)
                        if jitter:
                            sleep_time = sleep_time * (0.5 + random.random())

                        logger.warning(
                            f"[Async Retry] Function '{func.__name__}' failed attempt {attempt}/{max_retries} with {type(e).__name__}: {e}. Retrying in {sleep_time:.2f}s..."
                        )
                        await asyncio.sleep(sleep_time)

                if last_exception:
                    raise last_exception

            return async_wrapper
        else:

            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                delay = initial_delay
                last_exception: Optional[Exception] = None

                for attempt in range(1, max_retries + 1):
                    try:
                        return func(*args, **kwargs)
                    except retryable_exceptions as e:
                        last_exception = e
                        if attempt == max_retries:
                            logger.error(f"[Sync Retry] Function '{func.__name__}' failed after {max_retries} attempts: {e}")
                            raise

                        sleep_time = min(delay * (backoff_factor ** (attempt - 1)), max_delay)
                        if jitter:
                            sleep_time = sleep_time * (0.5 + random.random())

                        logger.warning(
                            f"[Sync Retry] Function '{func.__name__}' failed attempt {attempt}/{max_retries} with {type(e).__name__}: {e}. Retrying in {sleep_time:.2f}s..."
                        )
                        time.sleep(sleep_time)

                if last_exception:
                    raise last_exception

            return sync_wrapper

    return decorator
