import logging

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


async def validation_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """
    Custom exception handler for RequestValidationError.
    Logs the validation error and returns a JSON response with the error details.
    """
    if type(exc) is RequestValidationError:
        logger.error(f"Validation error on {request.url}:\n{exc.errors()}")
        return JSONResponse(
            status_code=422,
            content={"detail": exc.errors()},
        )

    return JSONResponse(status_code=500, content={"detail": "Unhandled exception"})
