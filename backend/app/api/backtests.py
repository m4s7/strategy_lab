from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_

from ..core.dependencies import get_db
from ..database.operations import BacktestOperations
from ..database.models import (
    BacktestCreate,
    BacktestResponse, 
    BacktestStatus,
    Backtest
)

router = APIRouter(prefix="/backtests", tags=["backtests"])


@router.post("/", response_model=BacktestResponse)
async def create_backtest(
    backtest_data: BacktestCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new backtest."""
    backtest = await BacktestOperations.create_backtest(db, backtest_data)
    return backtest


@router.get("/", response_model=List[BacktestResponse])
async def get_backtests(
    skip: int = 0,
    limit: int = 100,
    strategy_id: str = None,
    status: BacktestStatus = None,
    db: AsyncSession = Depends(get_db)
):
    """Get list of backtests with optional filtering."""
    backtests = await BacktestOperations.get_backtests(
        db, skip=skip, limit=limit, strategy_id=strategy_id, status=status
    )
    return backtests


@router.get("/{backtest_id}", response_model=BacktestResponse)
async def get_backtest(
    backtest_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific backtest by ID."""
    backtest = await BacktestOperations.get_backtest(db, backtest_id)
    if not backtest:
        raise HTTPException(status_code=404, detail="Backtest not found")
    return backtest


@router.patch("/{backtest_id}/status")
async def update_backtest_status(
    backtest_id: str,
    status: BacktestStatus,
    error_message: str = None,
    db: AsyncSession = Depends(get_db)
):
    """Update backtest status."""
    backtest = await BacktestOperations.update_backtest_status(
        db, backtest_id, status, error_message
    )
    if not backtest:
        raise HTTPException(status_code=404, detail="Backtest not found")
    return {"message": f"Backtest status updated to {status}", "backtest": backtest}


@router.get("/recent", response_model=List[BacktestResponse])
async def get_recent_backtests(
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """Get recent backtests for dashboard display."""
    stmt = select(Backtest).order_by(desc(Backtest.created_at)).limit(limit)
    result = await db.execute(stmt)
    backtests = result.scalars().all()
    return backtests


@router.get("/active", response_model=List[BacktestResponse])
async def get_active_backtests(
    db: AsyncSession = Depends(get_db)
):
    """Get currently running backtests."""
    stmt = select(Backtest).where(
        and_(
            Backtest.status.in_([BacktestStatus.RUNNING, BacktestStatus.PENDING])
        )
    ).order_by(desc(Backtest.created_at))
    
    result = await db.execute(stmt)
    backtests = result.scalars().all()
    return backtests