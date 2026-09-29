import logging
from typing import Any, Optional

from bson import ObjectId
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pymongo.errors import DuplicateKeyError, PyMongoError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("thinksync.errors")

# Change to 422 if you prefer FastAPI's default for validation errors.
VALIDATION_STATUS = 400

_CODE_BY_STATUS = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    409: "CONFLICT",
    422: "UNPROCESSABLE_ENTITY",
    500: "INTERNAL_ERROR",
}


# ---------- Custom exceptions ----------
class AppException(Exception):
    status_code = 500
    code = "INTERNAL_ERROR"

    def __init__(self, message: str, details: Any = None):
        self.message = message
        self.details = details
        super().__init__(message)


class BadRequestError(AppException):
    status_code, code = 400, "BAD_REQUEST"


class UnauthorizedError(AppException):
    status_code, code = 401, "UNAUTHORIZED"


class ForbiddenError(AppException):
    status_code, code = 403, "FORBIDDEN"


class NotFoundError(AppException):
    status_code, code = 404, "NOT_FOUND"

    def __init__(self, resource: str, identifier: Any = None):
        msg = f"{resource} not found" if identifier is None else f"{resource} '{identifier}' not found"
        super().__init__(msg)


class ConflictError(AppException):
    status_code, code = 409, "CONFLICT"


# ---------- Helpers ----------
def parse_object_id(value: str, name: str = "id") -> ObjectId:
    """Use in routes/services instead of ObjectId(value) so bad ids give 400, not 500."""
    if not ObjectId.is_valid(value):
        raise BadRequestError(f"Invalid {name}: '{value}'")
    return ObjectId(value)


def _body(request: Request, status: int, message: str, code: Optional[str] = None, details: Any = None):
    payload = {
        "error": {
            "code": code or _CODE_BY_STATUS.get(status, "ERROR"),
            "message": message,
            "path": request.url.path,
            "request_id": getattr(request.state, "request_id", None),
        }
    }
    if details is not None:
        payload["error"]["details"] = details
    return payload


# ---------- Handlers ----------
async def app_exception_handler(request: Request, exc: AppException):
    level = logging.WARNING if exc.status_code < 500 else logging.ERROR
    logger.log(level, "%s %s -> %d %s", request.method, request.url.path, exc.status_code, exc.message)
    return JSONResponse(
        status_code=exc.status_code,
        content=_body(request, exc.status_code, exc.message, exc.code, exc.details),
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    # Covers HTTPException raised by auth dependencies, plus router 404/405.
    logger.warning("%s %s -> %d %s", request.method, request.url.path, exc.status_code, exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content=_body(request, exc.status_code, str(exc.detail)),
        headers=getattr(exc, "headers", None),  # keeps WWW-Authenticate on 401
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    details = [
        {"field": ".".join(str(p) for p in e["loc"] if p != "body"), "message": e["msg"]}
        for e in exc.errors()
    ]
    logger.warning("%s %s -> validation failed: %s", request.method, request.url.path, details)
    return JSONResponse(
        status_code=VALIDATION_STATUS,
        content=_body(request, VALIDATION_STATUS, "Request validation failed", "VALIDATION_ERROR", details),
    )


async def duplicate_key_handler(request: Request, exc: DuplicateKeyError):
    logger.warning("%s %s -> duplicate key: %s", request.method, request.url.path, exc)
    return JSONResponse(status_code=409, content=_body(request, 409, "Resource already exists"))


async def pymongo_handler(request: Request, exc: PyMongoError):
    logger.exception("%s %s -> database error", request.method, request.url.path)
    return JSONResponse(status_code=500, content=_body(request, 500, "A database error occurred"))


async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("%s %s -> unhandled exception", request.method, request.url.path)
    return JSONResponse(status_code=500, content=_body(request, 500, "Internal server error"))


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(DuplicateKeyError, duplicate_key_handler)
    app.add_exception_handler(PyMongoError, pymongo_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)