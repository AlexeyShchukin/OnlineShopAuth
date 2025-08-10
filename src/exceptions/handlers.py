from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import ORJSONResponse
from fastapi import Request, status, Response
from sqlalchemy.exc import SQLAlchemyError

from src.exceptions.service_exceptions import (
    ServiceException,
    InvalidPasswordException,
    TokenNotFoundException,
    TokenAlreadyUsedException
)
from src.loggers.loggers import logger
from src.utils.cookie_utils import delete_old_refresh_token_from_cookie


async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError
) -> ORJSONResponse:
    err = exc.errors()[0]
    field = err["loc"][-1]
    message = err["msg"]
    body = exc.body

    logger.error(
        """Request: %s %s 
        Validation error: [field: %s]
        [message: %s]
        [body: %s]""",
        request.method,
        request.url,
        field,
        message,
        body
    )

    return ORJSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({
            "error": "Validation error",
            "details": [
                {
                    "field": err["loc"][-1],
                    "message": err["msg"]
                }
                for err in exc.errors()
            ],
            "body": exc.body
        })
    )


async def handle_db_error(request: Request, exc: SQLAlchemyError) -> ORJSONResponse:
    logger.error(
        "Database error during request %s %s: %s",
        request.method,
        request.url,
        str(exc),
        exc_info=exc
    )
    return ORJSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": type(exc).__name__,
            "message": "A database error occurred. Please try again later."
        }
    )


async def handle_unexpected_error(request: Request, exc: Exception) -> ORJSONResponse:
    logger.error(
        "Unexpected error occurred during request %s %s: %s",
        request.method,
        request.url,
        str(exc),
        exc_info=exc
    )
    return ORJSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": type(exc).__name__,
            "message": "Internal server error. Please try again later."
        }
    )


async def service_exception_handler(
        request: Request,
        exc: ServiceException
):
    logger.error(
        "ServiceException handled during request %s %s: %s",
        request.method,
        request.url,
        str(exc),
        exc_info=exc
    )

    content = {"detail": exc.message}
    headers = {}
    if isinstance(exc, InvalidPasswordException):
        headers["WWW-Authenticate"] = "Bearer"
        content["remaining_attempts"] = exc.remaining_attempts

    return ORJSONResponse(
        status_code=exc.status_code,
        content=content,
        headers=headers
    )
