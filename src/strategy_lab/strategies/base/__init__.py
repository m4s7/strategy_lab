"""Base strategy components for Strategy Lab.

This module provides the core building blocks for implementing trading strategies:

- StrategyBase: Abstract base class that all strategies must inherit from
- SignalGenerator: Utilities for generating trading signals based on technical analysis
- PositionManager: Position tracking and risk management functionality
"""

from .position_manager import PositionInfo, PositionManager, PositionSide, RiskLimits
from .signal_generator import (
    MarketMicrostructure,
    Signal,
    SignalGenerator,
    SignalType,
    TechnicalIndicators,
)
from .strategy import (
    MarketState,
    StrategyBase,
    StrategyConfig,
    StrategyMetrics,
    StrategyState,
)

__all__ = [
    # Strategy base class
    "StrategyBase",
    "StrategyConfig",
    "StrategyMetrics",
    "StrategyState",
    "MarketState",
    # Signal generation
    "SignalGenerator",
    "Signal",
    "SignalType",
    "TechnicalIndicators",
    "MarketMicrostructure",
    # Position management
    "PositionManager",
    "PositionInfo",
    "PositionSide",
    "RiskLimits",
]
