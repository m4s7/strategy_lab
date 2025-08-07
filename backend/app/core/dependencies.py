from typing import Generator
from fastapi import Depends, HTTPException, Request
from .config import settings


async def get_current_request_id(request: Request) -> str:
    """Get the current request ID from request state."""
    return getattr(request.state, "request_id", "unknown")


def get_settings():
    """Dependency to get application settings."""
    return settings


# Database dependency
async def get_db():
    """Database dependency that provides async session."""
    from ..database.connection import get_db_session

    async for session in get_db_session():
        yield session


# Health check dependencies
class HealthCheckDependencies:
    """Dependencies for health check endpoints."""

    @staticmethod
    def get_system_info() -> dict:
        """Get system information for health checks."""
        return {
            "app_name": settings.app_name,
            "version": settings.version,
            "environment": settings.environment,
            "debug": settings.debug,
        }
