import time
from typing import Callable, TypeVar

from loguru import logger
T = TypeVar("T")


class RetryExhaustedError(RuntimeError):
    ...

def retry_call(
    operation: Callable[[], T],
    *,
    attempts: int = 3,
    initial_delay: float = 1.0,
    backoff: float = 2.0,
    operation_name: str = "operation",
    retry_exceptions: tuple[type[Exception], ...] = (Exception,),
) -> T:

    delay = initial_delay
    last_error: Exception | None = None

    for attempt in range(1, attempts + 1):
        try:
            return operation()
        except retry_exceptions as exc:
            last_error = exc
            if attempt == attempts:
                break

            logger.warning(
                "{} failed on attempt {}/{}: {}. Retrying in {:.1f}s",
                operation_name,
                attempt,
                attempts,
                exc,
                delay,
            )
            if delay > 0:
                time.sleep(delay)
            delay *= backoff

    raise RetryExhaustedError(
        f"{operation_name} failed after {attempts} attempts"
    ) from last_error

