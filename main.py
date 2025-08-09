from uvicorn import run
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError

from src.api.endpoints import router
from src.api.middleware.middleware import LoggingMiddleware, configure_cors
from src.core.lifespan import lifespan
from src.exceptions.handlers import (
    validation_exception_handler,
    handle_db_error,
    handle_unexpected_error,
    service_exception_handler
)
from src.exceptions.service_exceptions import ServiceException

app = FastAPI(lifespan=lifespan, redirect_slashes=False)

app.include_router(router, prefix="/api/v1")

app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, handle_db_error)
app.add_exception_handler(ServiceException, service_exception_handler)
app.add_exception_handler(Exception, handle_unexpected_error)
app.add_middleware(LoggingMiddleware)
configure_cors(app)

if __name__ == "__main__":
    run(
        "main:app",
        host="127.0.0.1",
        port=8000
    )
