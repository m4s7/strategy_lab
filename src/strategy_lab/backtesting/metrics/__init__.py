"""Performance metrics calculation for backtesting.

This module provides comprehensive performance measurement tools including:
- P&L calculations and trade statistics
- Risk metrics (Sharpe ratio, drawdown, volatility)
- Time-based performance analysis
- Real-time metric updates during backtesting
"""

from .performance import (
    PerformanceMetrics,
    calculate_pnl,
    calculate_returns,
)
from .realtime import (
    MetricsAggregator,
    RealtimeMetrics,
)
from .risk import (
    RiskMetrics,
    calculate_max_drawdown,
    calculate_sharpe_ratio,
    calculate_volatility,
)
from .trade_analysis import (
    TradeStatistics,
    analyze_trades,
    calculate_profit_factor,
    calculate_win_rate,
)

__all__ = [
    # Performance
    "PerformanceMetrics",
    "calculate_pnl",
    "calculate_returns",
    # Risk
    "RiskMetrics",
    "calculate_sharpe_ratio",
    "calculate_max_drawdown",
    "calculate_volatility",
    # Trade Analysis
    "TradeStatistics",
    "analyze_trades",
    "calculate_win_rate",
    "calculate_profit_factor",
    # Real-time
    "RealtimeMetrics",
    "MetricsAggregator",
]
