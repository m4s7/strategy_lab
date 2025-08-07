from datetime import datetime
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from ..core.config import settings
from ..core.dependencies import get_current_request_id, HealthCheckDependencies, get_db
from ..database.operations import DatabaseHealthOperations
from ..models.base import HealthResponse

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/", response_model=HealthResponse)
async def health_check(
    request: Request,
    db: AsyncSession = Depends(get_db),
    request_id: str = Depends(get_current_request_id),
):
    """
    Health check endpoint that returns the current status of the API.

    Returns:
        HealthResponse: Current system status and metadata
    """
    system_info = HealthCheckDependencies.get_system_info()

    # Check database connection
    db_connected = await DatabaseHealthOperations.check_connection(db)
    db_status = "connected" if db_connected else "disconnected"

    return HealthResponse(
        status="healthy" if db_connected else "degraded",
        timestamp=datetime.utcnow(),
        version=settings.version,
        environment=settings.environment,
        app_name=settings.app_name,
        database=db_status,
        system_info={
            "debug_mode": settings.debug,
            "log_level": settings.log_level,
            "request_id": request_id,
            "database_url": settings.database_url.split("///")[-1]
            if "///" in settings.database_url
            else "hidden",
        },
    )


@router.get("/detailed")
async def detailed_health_check(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Detailed health check with extended system information.

    Returns:
        dict: Comprehensive system health information
    """
    # Check database connection and get metrics
    db_connected = await DatabaseHealthOperations.check_connection(db)
    table_counts = await DatabaseHealthOperations.get_table_counts(db)
    recent_activity = await DatabaseHealthOperations.get_recent_activity(db, limit=5)

    # Get WebSocket statistics
    try:
        from ..websocket.connection_manager import connection_manager

        ws_stats = await connection_manager.get_connection_stats()
    except Exception as e:
        ws_stats = {"error": str(e)}

    return {
        "status": "healthy" if db_connected else "degraded",
        "timestamp": datetime.utcnow(),
        "version": settings.version,
        "environment": settings.environment,
        "services": {
            "api": "healthy",
            "database": "connected" if db_connected else "disconnected",
            "websocket": "active",
        },
        "database_metrics": {
            "connection_status": "connected" if db_connected else "disconnected",
            "table_counts": table_counts,
            "recent_activity": recent_activity,
        },
        "websocket_metrics": ws_stats,
        "configuration": {
            "cors_origins": settings.cors_origins,
            "debug": settings.debug,
            "log_level": settings.log_level,
            "database_url": settings.database_url.split("///")[-1]
            if "///" in settings.database_url
            else "hidden",
        },
        "request_info": {
            "request_id": getattr(request.state, "request_id", "unknown"),
            "client_host": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
        },
    }
