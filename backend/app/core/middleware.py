import uuid
import time
import logging
from typing import Callable
from fastapi import Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from .config import settings

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request/response logging with request ID tracking."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Log incoming request
        start_time = time.time()
        logger.info(
            f"Request started - ID: {request_id} | "
            f"Method: {request.method} | Path: {request.url.path}"
        )

        # Process request
        try:
            response = await call_next(request)

            # Log successful response
            process_time = time.time() - start_time
            logger.info(
                f"Request completed - ID: {request_id} | "
                f"Status: {response.status_code} | "
                f"Duration: {process_time:.4f}s"
            )

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            return response

        except Exception as exc:
            # Log error
            process_time = time.time() - start_time
            logger.error(
                f"Request failed - ID: {request_id} | "
                f"Error: {str(exc)} | "
                f"Duration: {process_time:.4f}s"
            )
            raise


def add_cors_middleware(app):
    """Add CORS middleware to the FastAPI app."""
    # Force CORS origins to include all necessary localhost ports
    cors_origins = [
        "http://localhost:3000",
        "http://localhost:3456",
        "http://localhost:3457",
        "https://lab.m4s8.dev",
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
