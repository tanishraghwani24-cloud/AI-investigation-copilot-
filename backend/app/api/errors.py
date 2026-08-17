"""Central API error response handling."""

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


class ApiError(BaseModel):
    """Stable error object returned by API exception handlers."""

    code: str
    message: str
    details: Any = None


class ApiErrorEnvelope(BaseModel):
    """Top-level error response envelope."""

    error: ApiError


_HTTP_ERROR_CODES: dict[int, str] = {
    400: "BAD_REQUEST",
    404: "NOT_FOUND",
    409: "CONFLICT",
}


def _http_error_code(status_code: int) -> str:
    """Return a stable API error code for a HTTP status code."""
    if status_code in _HTTP_ERROR_CODES:
        return _HTTP_ERROR_CODES[status_code]
    if 400 <= status_code < 500:
        return "CLIENT_ERROR"
    return "SERVER_ERROR"


def _error_response(
    *,
    status_code: int,
    code: str,
    message: str,
    details: Any = None,
) -> JSONResponse:
    """Build the common JSON API error envelope."""
    envelope = ApiErrorEnvelope(
        error=ApiError(
            code=code,
            message=message,
            details=details,
        )
    )
    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder(envelope),
    )


def _validation_details(exc: RequestValidationError) -> list[dict[str, Any]]:
    """Normalize FastAPI/Pydantic validation errors for API consumers."""
    details: list[dict[str, Any]] = []
    for error in exc.errors():
        details.append(
            {
                "loc": list(error.get("loc", ())),
                "msg": error.get("msg", "Invalid input"),
                "type": error.get("type", "validation_error"),
                "ctx": error.get("ctx"),
            }
        )
    return jsonable_encoder(details)


def register_exception_handlers(application: FastAPI) -> None:
    """Register common API exception handlers on the FastAPI app."""

    @application.exception_handler(RequestValidationError)
    async def request_validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        logger.info(
            "Request validation failed for %s %s",
            request.method,
            request.url.path,
        )
        return _error_response(
            status_code=422,
            code="VALIDATION_ERROR",
            message="Request validation failed",
            details=_validation_details(exc),
        )

    @application.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request,
        exc: StarletteHTTPException,
    ) -> JSONResponse:
        if exc.status_code >= 500:
            logger.error(
                "HTTP error for %s %s: %s",
                request.method,
                request.url.path,
                exc.detail,
            )
        message = exc.detail if isinstance(exc.detail, str) else "Request failed"
        details = None if isinstance(exc.detail, str) else exc.detail
        return _error_response(
            status_code=exc.status_code,
            code=_http_error_code(exc.status_code),
            message=message,
            details=details,
        )

    @application.exception_handler(Exception)
    async def unexpected_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        logger.exception(
            "Unhandled API error for %s %s",
            request.method,
            request.url.path,
        )
        return _error_response(
            status_code=500,
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected server error occurred",
            details=None,
        )
