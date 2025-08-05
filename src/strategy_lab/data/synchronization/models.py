"""Data models for L1+L2 synchronization."""

from dataclasses import dataclass
from decimal import Decimal

import numpy as np


@dataclass
class PriceLevel:
    """Represents a single price level in the order book."""

    price: Decimal
    volume: int
    order_count: int = 1

    def __repr__(self) -> str:
        return (
            f"PriceLevel(price={self.price}, volume={self.volume}, "
            f"orders={self.order_count})"
        )


@dataclass
class UnifiedMarketSnapshot:
    """Unified market state combining L1 and L2 data at a specific timestamp."""

    # Timestamp
    timestamp: int  # Nanosecond precision

    # Level 1 Data
    last_trade_price: Decimal | None = None
    last_trade_volume: int | None = None
    bid_price: Decimal | None = None
    ask_price: Decimal | None = None
    bid_volume: int | None = None
    ask_volume: int | None = None

    # Level 2 Data
    bid_levels: list[PriceLevel] = None
    ask_levels: list[PriceLevel] = None

    # Derived Metrics (computed properties)
    @property
    def spread(self) -> Decimal | None:
        """Calculate bid-ask spread."""
        if self.bid_price and self.ask_price:
            return self.ask_price - self.bid_price
        return None

    @property
    def mid_price(self) -> Decimal | None:
        """Calculate mid price."""
        if self.bid_price and self.ask_price:
            return (self.bid_price + self.ask_price) / 2
        return None

    @property
    def total_bid_depth(self) -> int:
        """Calculate total bid side depth."""
        if self.bid_levels:
            return sum(level.volume for level in self.bid_levels)
        return 0

    @property
    def total_ask_depth(self) -> int:
        """Calculate total ask side depth."""
        if self.ask_levels:
            return sum(level.volume for level in self.ask_levels)
        return 0

    @property
    def imbalance_ratio(self) -> float:
        """Calculate order book imbalance ratio (-1 to 1)."""
        total_bid = self.total_bid_depth
        total_ask = self.total_ask_depth

        if total_bid + total_ask == 0:
            return 0.0

        return (total_bid - total_ask) / (total_bid + total_ask)

    def __post_init__(self):
        """Initialize empty lists if None."""
        if self.bid_levels is None:
            self.bid_levels = []
        if self.ask_levels is None:
            self.ask_levels = []


@dataclass
class SyncStats:
    """Statistics for synchronization performance monitoring."""

    total_l1_ticks: int = 0
    total_l2_ticks: int = 0
    total_snapshots: int = 0
    sync_lag_ns: list[int] = None
    processing_time_us: list[float] = None
    buffer_overflow_count: int = 0
    data_gaps_count: int = 0

    def __post_init__(self):
        """Initialize lists if None."""
        if self.sync_lag_ns is None:
            self.sync_lag_ns = []
        if self.processing_time_us is None:
            self.processing_time_us = []

    @property
    def avg_sync_lag_us(self) -> float:
        """Average synchronization lag in microseconds."""
        if self.sync_lag_ns:
            return np.mean(self.sync_lag_ns) / 1000
        return 0.0

    @property
    def avg_processing_time_us(self) -> float:
        """Average processing time in microseconds."""
        if self.processing_time_us:
            return np.mean(self.processing_time_us)
        return 0.0

    @property
    def max_sync_lag_us(self) -> float:
        """Maximum synchronization lag in microseconds."""
        if self.sync_lag_ns:
            return max(self.sync_lag_ns) / 1000
        return 0.0
