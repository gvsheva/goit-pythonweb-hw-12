"""Rate limiting utilities using slowapi."""
from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)


def rate_limit_exceeded_handler(request: Request, exc: Exception):
    """Return a JSON 429 response when a rate limit is exceeded.

    Args:
        request: Incoming FastAPI request.
        exc: Raised RateLimitExceeded exception.

    Returns:
        JSONResponse with HTTP 429 and a short error message.
    """
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded"},
    )
