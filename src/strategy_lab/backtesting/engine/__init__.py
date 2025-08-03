"""Backtest execution engine for running and managing strategy backtests.

This module provides:
- Backtest configuration and validation
- Date range processing and contract handling
- Results storage and retrieval
- Progress monitoring and reporting
- Parallel execution support
- Resource monitoring and throttling
"""

from .backtest_engine import BacktestEngine, BacktestStatus
from .config import BacktestConfig, ConfigTemplate, ExecutionConfig, StrategyConfig
from .execution import BacktestExecutor, ExecutionContext
from .portfolio import Portfolio, Position
from .results import BacktestResult, TradeRecord, load_results, save_results

__all__ = [
    # Engine
    "BacktestEngine",
    "BacktestStatus",
    # Configuration
    "BacktestConfig",
    "StrategyConfig",
    "ExecutionConfig",
    "ConfigTemplate",
    # Execution
    "BacktestExecutor",
    "ExecutionContext",
    # Portfolio
    "Portfolio",
    "Position",
    # Results
    "BacktestResult",
    "TradeRecord",
    "save_results",
    "load_results",
]
