from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from httpx import HTTPStatusError

from src.exceptions.http import http_exception_handler
from src.exceptions.validation import validation_exception_handler


def add_exception_handlers(app: FastAPI) -> None:
    """
    Add custom exception handlers to the FastAPI app.

    Args:
        app (FastAPI): The FastAPI application instance.
    """
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(HTTPStatusError, http_exception_handler)
