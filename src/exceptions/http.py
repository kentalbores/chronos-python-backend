import logging

from fastapi import Request
from fastapi.responses import JSONResponse
from httpx import HTTPStatusError

logger = logging.getLogger(__name__)


async def http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Custom exception handler for HTTP errors.
    Logs the HTTP error and returns a JSON response with the error details.
    """
    if isinstance(exc, HTTPStatusError):
        logger.error(f"HTTP error on {request.url}: {exc.response.reason_phrase}")
        return JSONResponse(
            status_code=exc.response.status_code,
            content={"detail": exc.response.reason_phrase},
        )

    return JSONResponse(status_code=500, content={"detail": "Unhandled exception"})
