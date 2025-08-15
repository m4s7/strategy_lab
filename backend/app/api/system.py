from typing import Dict, Any
import psutil
import time
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from ..database.connection import get_db_session as get_db
from ..database.models import Backtest, BacktestStatus

router = APIRouter()

_system_start_time = time.time()


@router.get("/status")
async def get_system_status() -> Dict[str, Any]:
    """Get current system status including resources and health checks."""

    # Get system resource usage
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    return {
        "cpu": round(cpu_percent, 1),
        "memory": {
            "used_percent": round(memory.percent, 1),
            "available_gb": round(memory.available / (1024**3), 2),
            "total_gb": round(memory.total / (1024**3), 2),
        },
        "disk": {
            "used_percent": round((disk.used / disk.total) * 100, 1),
            "free_gb": round(disk.free / (1024**3), 2),
            "total_gb": round(disk.total / (1024**3), 2),
        },
        "database": "healthy",  # Will be updated with actual health check
        "websocket": "connected",
        "uptime": round(time.time() - _system_start_time, 0),
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)) -> Dict[str, str]:
    """Simple health check endpoint."""
    try:
        # Test database connection
        result = await db.execute(text("SELECT 1"))
        await result.fetchone()

        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }


@router.get("/stats")
async def get_system_stats(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """Get system performance statistics."""

    # Get today's backtest statistics
    from sqlalchemy import func, and_

    today = datetime.now().date()

    # Count backtests by status for today
    backtest_stats = await db.execute(
        text(
            """
        SELECT
            status,
            COUNT(*) as count,
            AVG(CAST((julianday(COALESCE(completed_at, created_at)) - julianday(created_at)) * 86400 AS INTEGER)) as avg_duration
        FROM backtests
        WHERE DATE(created_at) = DATE('now')
        GROUP BY status
        """
        )
    )

    results = backtest_stats.fetchall()

    # Process results
    total_today = sum(row.count for row in results)
    completed_today = sum(
        row.count for row in results if row.status == BacktestStatus.COMPLETED.value
    )
    failed_today = sum(
        row.count for row in results if row.status == BacktestStatus.FAILED.value
    )

    success_rate = (completed_today / total_today * 100) if total_today > 0 else 0

    # Calculate average duration for completed backtests
    avg_duration = 0
    for row in results:
        if row.status == BacktestStatus.COMPLETED.value and row.avg_duration:
            avg_duration = row.avg_duration
            break

    return {
        "today": {
            "backtests_run": total_today,
            "success_rate": round(success_rate, 1),
            "average_duration": round(avg_duration, 1) if avg_duration else 0,
            "completed": completed_today,
            "failed": failed_today,
        },
        "performance": {
            "average_response_time": 150,  # Mock value - would be calculated from metrics
            "uptime": round(time.time() - _system_start_time, 0),
            "requests_per_minute": 25,  # Mock value - would be tracked
        },
        "data": {
            "records_processed": 1234567,  # Mock value - would be tracked
            "processing_speed": 50000,  # Mock value - records per second
            "last_update": datetime.now().isoformat(),
        },
    }
