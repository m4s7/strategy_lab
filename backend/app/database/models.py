from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from sqlalchemy import String, Integer, DateTime, Text, JSON, ForeignKey, func
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from pydantic import BaseModel


# Database Base
class Base(AsyncAttrs, DeclarativeBase):
    """Base class for all database models."""
    pass


# Enums
class BacktestStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class OptimizationType(str, Enum):
    GRID = "grid"
    GENETIC = "genetic"
    WALK_FORWARD = "walk_forward"


# Database Models
class Backtest(Base):
    """Backtest database model."""
    __tablename__ = "backtests"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    strategy_id: Mapped[str] = mapped_column(String, nullable=False)
    config: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    status: Mapped[BacktestStatus] = mapped_column(String, nullable=False, default=BacktestStatus.PENDING)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    result_path: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    # Relationships
    results: Mapped[List["BacktestResult"]] = relationship(
        "BacktestResult", 
        back_populates="backtest", 
        cascade="all, delete-orphan"
    )


class BacktestResult(Base):
    """Backtest result database model."""
    __tablename__ = "backtest_results"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    backtest_id: Mapped[str] = mapped_column(
        String, 
        ForeignKey("backtests.id", ondelete="CASCADE"),
        nullable=False
    )
    metrics: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    equity_curve: Mapped[Optional[bytes]] = mapped_column(nullable=True)  # BLOB for compressed data
    trades_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    backtest: Mapped["Backtest"] = relationship("Backtest", back_populates="results")


class OptimizationJob(Base):
    """Optimization job database model."""
    __tablename__ = "optimization_jobs"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    strategy_id: Mapped[str] = mapped_column(String, nullable=False)
    optimization_type: Mapped[OptimizationType] = mapped_column(String, nullable=False)
    config: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    status: Mapped[BacktestStatus] = mapped_column(String, nullable=False, default=BacktestStatus.PENDING)
    best_params: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class UserPreference(Base):
    """User preferences database model."""
    __tablename__ = "user_preferences"
    
    key: Mapped[str] = mapped_column(String, primary_key=True)
    value: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        onupdate=func.now()
    )


# Pydantic schemas for API (matching database models)
class BacktestBase(BaseModel):
    """Base Pydantic model for Backtest."""
    strategy_id: str
    config: Dict[str, Any]


class BacktestCreate(BacktestBase):
    """Pydantic model for creating Backtest."""
    pass


class BacktestResponse(BacktestBase):
    """Pydantic model for Backtest responses."""
    id: str
    status: BacktestStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    result_path: Optional[str] = None
    
    class Config:
        from_attributes = True


class BacktestResultBase(BaseModel):
    """Base Pydantic model for BacktestResult."""
    metrics: Dict[str, Any]
    trades_count: int = 0


class BacktestResultCreate(BacktestResultBase):
    """Pydantic model for creating BacktestResult."""
    backtest_id: str


class BacktestResultResponse(BacktestResultBase):
    """Pydantic model for BacktestResult responses."""
    id: str
    backtest_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True