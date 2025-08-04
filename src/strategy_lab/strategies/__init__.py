"""Strategy Lab Trading Strategies.

This module provides the core strategy framework for implementing
high-frequency trading strategies on futures markets.
"""

from .base.pluggable_strategy import PluggableStrategy
from .base.position_manager import PositionManager
from .base.signal_generator import SignalGenerator
from .base.strategy import StrategyBase
from .examples.moving_average_crossover import MovingAverageCrossoverStrategy

# Import example strategies to trigger registration
from .examples.simple_ma_strategy import SimpleMAStrategy
from .factory import factory
from .protocol import StrategyMetadata, StrategyProtocol
from .registry import register_strategy, registry

# Import implementation strategies
try:
    from .implementations.bid_ask_bounce import BidAskBounceStrategy
except ImportError:
    pass

try:
    from .implementations.order_book_imbalance import OrderBookImbalanceStrategy
except ImportError:
    pass

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
    # Example strategies
    "SimpleMAStrategy",
    "MovingAverageCrossoverStrategy",
]
