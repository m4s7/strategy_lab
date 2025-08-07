import logging
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from .core.config import settings
from .core.middleware import LoggingMiddleware, add_cors_middleware
from .api.router import api_router
from .websocket.routes import websocket_router, http_router
from .models.base import ErrorResponse


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.
    """
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.version}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"Server will run on {settings.host}:{settings.port}")

    # Test database connection
    try:
        from .database.connection import test_db_connection

        db_connected = await test_db_connection()
        if db_connected:
            logger.info("Database connection: OK")
        else:
            logger.warning("Database connection: FAILED")
    except Exception as e:
        logger.error(f"Database connection error: {e}")

    # Start dashboard updater
    try:
        from .websocket.dashboard import dashboard_updater

        await dashboard_updater.start()
        logger.info("Dashboard updater started")
    except Exception as e:
        logger.error(f"Failed to start dashboard updater: {e}")

    yield

    # Shutdown
    logger.info(f"Shutting down {settings.app_name}")

    # Stop dashboard updater
    try:
        from .websocket.dashboard import dashboard_updater

        await dashboard_updater.stop()
        logger.info("Dashboard updater stopped")
    except Exception as e:
        logger.error(f"Error stopping dashboard updater: {e}")

    # Close database connections
    try:
        from .database.connection import close_db_connections

        await close_db_connections()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="High-performance futures trading backtesting and optimization platform API",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    debug=settings.debug,
    lifespan=lifespan,
)

# Add middleware
app.add_middleware(LoggingMiddleware)
add_cors_middleware(app)

# Add trusted host middleware in production
if not settings.debug:
    app.add_middleware(
        TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1", settings.host]
    )

# Include API router
app.include_router(api_router)

# Include WebSocket router
app.include_router(websocket_router)

# Include WebSocket HTTP endpoints
app.include_router(http_router, prefix="/api/v1")


# Global exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Global HTTP exception handler."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.__class__.__name__,
            message=str(exc.detail),
            timestamp=datetime.utcnow(),
            request_id=getattr(request.state, "request_id", "unknown"),
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="InternalServerError",
            message="An internal server error occurred",
            detail=str(exc) if settings.debug else None,
            timestamp=datetime.utcnow(),
            request_id=getattr(request.state, "request_id", "unknown"),
        ).model_dump(),
    )


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint providing basic API information."""
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.version,
        "docs": "/docs",
        "health": "/api/v1/health",
        "timestamp": datetime.utcnow(),
    }


# Health check endpoint (also available at root level for load balancers)
@app.get("/health")
async def root_health():
    """Simple health check for load balancers."""
    return {"status": "healthy", "timestamp": datetime.utcnow()}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level,
    )
