"""Strategy Lab Trading Strategies.

This module provides the core strategy framework for implementing
high-frequency trading strategies on futures markets.
"""

from .base.pluggable_strategy import PluggableStrategy
from .base.position_manager import PositionManager
from .base.signal_generator import SignalGenerator
from .base.strategy import StrategyBase
from .factory import factory
from .protocol import StrategyMetadata, StrategyProtocol
from .registry import register_strategy, registry

__all__ = [
    # Base classes
    "StrategyBase",
    "PluggableStrategy",
    "PositionManager",
    "SignalGenerator",
    # Protocol and metadata
    "StrategyProtocol",
    "StrategyMetadata",
    # Registry and factory
    "registry",
    "register_strategy",
    "factory",
]
