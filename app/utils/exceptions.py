class ApplicationError(RuntimeError):
    """Base class for recoverable application errors."""


class ConfigurationError(ApplicationError):
    """Raised when configuration is missing or invalid."""


class ApiRequestError(ApplicationError):
    """Raised when an outbound request fails before a valid response is received."""


class ApiResponseError(ApplicationError):
    """Raised when a remote API responds with invalid or unexpected data."""


class ApiProtocolError(ApiResponseError):
    """Raised when a remote API shape no longer matches the expected contract."""


class RateLimitError(ApiResponseError):
    """Raised when a remote API throttles the current request."""


class CaptchaError(ApiResponseError):
    """Raised when captcha task creation or polling fails."""


class RetryableOperationError(ApplicationError):
    """Raised to signal that an operation should be retried."""

