"""Enhanced strategy protocol for L1+L2 strategies."""

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

from .protocol import StrategyMetadata


class OrderSide(Enum):
    """Order side enumeration."""

    BUY = 1
    SELL = -1


class OrderType(Enum):
    """Order type enumeration."""

    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


@dataclass
class OrderRequest:
    """Order request for strategy signals."""

    side: OrderSide
    size: int
    order_type: OrderType = OrderType.MARKET
    price: Optional[Decimal] = None
    stop_price: Optional[Decimal] = None
    time_in_force: str = "GTC"  # Good Till Cancelled
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class Position:
    """Position information."""

    size: int = 0
    avg_price: Optional[Decimal] = None
    unrealized_pnl: Decimal = Decimal("0")
    realized_pnl: Decimal = Decimal("0")

    @property
    def is_flat(self) -> bool:
        return self.size == 0

    @property
    def is_long(self) -> bool:
        return self.size > 0

    @property
    def is_short(self) -> bool:
        return self.size < 0


@dataclass
class StrategyContext:
    """Context provided to strategy on each tick."""

    position: Position
    current_time: int  # Nanosecond timestamp
    market_state: str = "open"
    daily_pnl: Decimal = Decimal("0")
    total_trades: int = 0


# Re-export from base protocol
__all__ = [
    "OrderSide",
    "OrderType",
    "OrderRequest",
    "Position",
    "StrategyContext",
    "StrategyMetadata",
]
