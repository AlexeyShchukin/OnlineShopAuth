from time import perf_counter

from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from src.loggers.loggers import logger


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = perf_counter()
        logger.info(
            "Request: %s %s",
            request.method,
            request.url
        )
        response = await call_next(request)
        process_time = perf_counter() - start_time
        logger.info(
            "Response: %s (handling %.4f seconds)",
            response.status_code,
            process_time
        )

        return response


def configure_cors(app):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
