"""Database operations and utilities."""

import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, text
from sqlalchemy.orm import selectinload

from .models import (
    Backtest,
    BacktestResult,
    OptimizationJob,
    UserPreference,
    BacktestStatus,
    BacktestCreate,
    BacktestResultCreate,
)


class BacktestOperations:
    """Database operations for backtests."""

    @staticmethod
    async def create_backtest(
        session: AsyncSession, backtest_data: BacktestCreate
    ) -> Backtest:
        """Create a new backtest."""
        backtest = Backtest(
            id=str(uuid.uuid4()),
            strategy_id=backtest_data.strategy_id,
            config=backtest_data.config,
            status=BacktestStatus.PENDING,
        )
        session.add(backtest)
        await session.commit()
        await session.refresh(backtest)
        return backtest

    @staticmethod
    async def get_backtest(
        session: AsyncSession, backtest_id: str
    ) -> Optional[Backtest]:
        """Get backtest by ID."""
        result = await session.execute(
            select(Backtest).where(Backtest.id == backtest_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_backtests(
        session: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        strategy_id: Optional[str] = None,
        status: Optional[BacktestStatus] = None,
    ) -> List[Backtest]:
        """Get list of backtests with optional filtering."""
        query = select(Backtest).order_by(desc(Backtest.created_at))

        if strategy_id:
            query = query.where(Backtest.strategy_id == strategy_id)
        if status:
            query = query.where(Backtest.status == status)

        query = query.offset(skip).limit(limit)
        result = await session.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def update_backtest_status(
        session: AsyncSession,
        backtest_id: str,
        status: BacktestStatus,
        error_message: Optional[str] = None,
    ) -> Optional[Backtest]:
        """Update backtest status."""
        backtest = await BacktestOperations.get_backtest(session, backtest_id)
        if not backtest:
            return None

        backtest.status = status
        if status == BacktestStatus.RUNNING and not backtest.started_at:
            backtest.started_at = datetime.utcnow()
        elif status in [
            BacktestStatus.COMPLETED,
            BacktestStatus.FAILED,
            BacktestStatus.CANCELLED,
        ]:
            backtest.completed_at = datetime.utcnow()

        if error_message:
            backtest.error_message = error_message

        await session.commit()
        await session.refresh(backtest)
        return backtest


class BacktestResultOperations:
    """Database operations for backtest results."""

    @staticmethod
    async def create_result(
        session: AsyncSession, result_data: BacktestResultCreate
    ) -> BacktestResult:
        """Create a new backtest result."""
        result = BacktestResult(
            id=str(uuid.uuid4()),
            backtest_id=result_data.backtest_id,
            metrics=result_data.metrics,
            trades_count=result_data.trades_count,
        )
        session.add(result)
        await session.commit()
        await session.refresh(result)
        return result

    @staticmethod
    async def get_results_by_backtest(
        session: AsyncSession, backtest_id: str
    ) -> List[BacktestResult]:
        """Get all results for a specific backtest."""
        result = await session.execute(
            select(BacktestResult)
            .where(BacktestResult.backtest_id == backtest_id)
            .order_by(desc(BacktestResult.created_at))
        )
        return list(result.scalars().all())


class DatabaseHealthOperations:
    """Database health and utility operations."""

    @staticmethod
    async def check_connection(session: AsyncSession) -> bool:
        """Check if database connection is working."""
        try:
            await session.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    @staticmethod
    async def get_table_counts(session: AsyncSession) -> dict:
        """Get row counts for all tables."""
        try:
            counts = {}

            # Count backtests
            result = await session.execute(text("SELECT COUNT(*) FROM backtests"))
            counts["backtests"] = result.scalar()

            # Count backtest_results
            result = await session.execute(
                text("SELECT COUNT(*) FROM backtest_results")
            )
            counts["backtest_results"] = result.scalar()

            # Count optimization_jobs
            result = await session.execute(
                text("SELECT COUNT(*) FROM optimization_jobs")
            )
            counts["optimization_jobs"] = result.scalar()

            # Count user_preferences
            result = await session.execute(
                text("SELECT COUNT(*) FROM user_preferences")
            )
            counts["user_preferences"] = result.scalar()

            return counts
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    async def get_recent_activity(session: AsyncSession, limit: int = 10) -> dict:
        """Get recent database activity."""
        try:
            # Recent backtests
            result = await session.execute(
                select(Backtest).order_by(desc(Backtest.created_at)).limit(limit)
            )
            recent_backtests = [
                {
                    "id": bt.id,
                    "strategy_id": bt.strategy_id,
                    "status": bt.status,
                    "created_at": bt.created_at,
                }
                for bt in result.scalars().all()
            ]

            return {
                "recent_backtests": recent_backtests,
                "timestamp": datetime.utcnow(),
            }
        except Exception as e:
            return {"error": str(e)}
