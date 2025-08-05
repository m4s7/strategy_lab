"""L1+L2 Data Synchronizer implementation."""

import heapq
import logging
import time
from collections.abc import Iterator
from dataclasses import dataclass
from decimal import Decimal

import pandas as pd

from strategy_lab.data.processing.order_book import OrderBook

from .models import PriceLevel, SyncStats, UnifiedMarketSnapshot

logger = logging.getLogger(__name__)


@dataclass
class TickEvent:
    """Wrapper for tick events with timestamp ordering."""

    timestamp: int
    tick_type: str  # 'L1' or 'L2'
    data: pd.Series

    def __lt__(self, other):
        """Priority queue ordering by timestamp."""
        return self.timestamp < other.timestamp


class L1L2DataSynchronizer:
    """Synchronizes Level 1 and Level 2 tick data streams."""

    def __init__(
        self,
        sync_window_ns: int = 1_000_000,  # 1ms sync window
        buffer_size: int = 10_000,
        max_depth_levels: int = 10,
        enable_stats: bool = True,
    ):
        """
        Initialize the synchronizer.

        Args:
            sync_window_ns: Time window in nanoseconds for synchronization
            buffer_size: Maximum buffer size for pending ticks
            max_depth_levels: Maximum order book depth levels to maintain
            enable_stats: Whether to collect performance statistics
        """
        self.sync_window_ns = sync_window_ns
        self.buffer_size = buffer_size
        self.max_depth_levels = max_depth_levels
        self.enable_stats = enable_stats

        # State management
        self.order_book = OrderBook(max_depth=max_depth_levels)
        self.last_l1_state = {}
        self.tick_buffer: list[TickEvent] = []
        self.stats = SyncStats() if enable_stats else None

        # Performance monitoring
        self._last_sync_time = 0

    def synchronize(
        self,
        l1_data: pd.DataFrame,
        l2_data: pd.DataFrame,
        start_time: int | None = None,
        end_time: int | None = None,
    ) -> Iterator[UnifiedMarketSnapshot]:
        """
        Synchronize L1 and L2 data streams.

        Args:
            l1_data: Level 1 tick data DataFrame
            l2_data: Level 2 tick data DataFrame
            start_time: Start timestamp (nanoseconds)
            end_time: End timestamp (nanoseconds)

        Yields:
            UnifiedMarketSnapshot objects
        """
        # Reset state
        self._reset_state()

        # Filter data by time range if specified
        if start_time:
            l1_data = l1_data[l1_data["timestamp"] >= start_time]
            l2_data = l2_data[l2_data["timestamp"] >= start_time]
        if end_time:
            l1_data = l1_data[l1_data["timestamp"] <= end_time]
            l2_data = l2_data[l2_data["timestamp"] <= end_time]

        # Create iterators
        l1_iter = iter(l1_data.itertuples(index=False))
        l2_iter = iter(l2_data.itertuples(index=False))

        # Initialize with first ticks
        l1_tick = self._get_next_tick(l1_iter, "L1")
        l2_tick = self._get_next_tick(l2_iter, "L2")

        # Main synchronization loop
        while l1_tick or l2_tick:
            # Add available ticks to buffer
            if l1_tick:
                heapq.heappush(self.tick_buffer, l1_tick)
                l1_tick = self._get_next_tick(l1_iter, "L1")

            if l2_tick:
                heapq.heappush(self.tick_buffer, l2_tick)
                l2_tick = self._get_next_tick(l2_iter, "L2")

            # Process buffer when we have enough data or at end
            if len(self.tick_buffer) >= 100 or (not l1_tick and not l2_tick):
                yield from self._process_buffer()

        # Final buffer processing
        yield from self._process_buffer(final=True)

        if self.stats:
            logger.info(
                f"Synchronization complete: {self.stats.total_snapshots} snapshots, "
                f"avg lag {self.stats.avg_sync_lag_us:.1f}μs"
            )

    def _get_next_tick(self, iterator: Iterator, tick_type: str) -> TickEvent | None:
        """Get next tick from iterator."""
        try:
            tick = next(iterator)
            if self.stats:
                if tick_type == "L1":
                    self.stats.total_l1_ticks += 1
                else:
                    self.stats.total_l2_ticks += 1
            return TickEvent(timestamp=tick.timestamp, tick_type=tick_type, data=tick)
        except StopIteration:
            return None

    def _process_buffer(self, final: bool = False) -> Iterator[UnifiedMarketSnapshot]:
        """Process buffered ticks and generate snapshots."""
        if not self.tick_buffer:
            return

        # Process ticks in timestamp order
        while self.tick_buffer:
            tick = heapq.heappop(self.tick_buffer)

            # Update state based on tick type
            if tick.tick_type == "L1":
                self._update_l1_state(tick.data)
            else:
                self._update_l2_state(tick.data)

            # Check if we should generate a snapshot
            if self._should_generate_snapshot(tick.timestamp, final):
                snapshot = self._create_snapshot(tick.timestamp)
                if snapshot:
                    yield snapshot

                    if self.stats:
                        self.stats.total_snapshots += 1
                        # Track sync lag
                        lag = time.time_ns() - tick.timestamp
                        self.stats.sync_lag_ns.append(lag)

    def _update_l1_state(self, tick):
        """Update Level 1 state from tick."""
        mdt = tick.mdt

        # mdt: 0=Ask, 1=Bid, 2=Last
        if mdt == 2:
            self.last_l1_state["last_price"] = Decimal(str(tick.price))
            self.last_l1_state["last_volume"] = int(tick.volume)

        # Best Bid
        elif mdt == 1:
            self.last_l1_state["bid_price"] = Decimal(str(tick.price))
            self.last_l1_state["bid_volume"] = int(tick.volume)

        # Best Ask
        elif mdt == 0:
            self.last_l1_state["ask_price"] = Decimal(str(tick.price))
            self.last_l1_state["ask_volume"] = int(tick.volume)

    def _update_l2_state(self, tick):
        """Update Level 2 state (order book) from tick."""
        try:
            # Use the OrderBook's process_operation method
            success = self.order_book.process_operation(
                timestamp=int(tick.timestamp),
                mdt=int(tick.mdt),
                price=float(tick.price),
                volume=int(tick.volume),
                operation=int(getattr(tick, "operation", 0)),
                depth=getattr(tick, "depth", None),
                market_maker=getattr(tick, "market_maker", None),
            )

            if not success and self.stats:
                self.stats.data_gaps_count += 1

        except Exception as e:
            logger.warning(f"Error updating L2 state: {e}")
            if self.stats:
                self.stats.data_gaps_count += 1

    def _should_generate_snapshot(self, timestamp: int, final: bool) -> bool:
        """Determine if we should generate a snapshot."""
        if final:
            return True

        # Generate snapshot every sync window
        if timestamp - self._last_sync_time >= self.sync_window_ns:
            self._last_sync_time = timestamp
            return True

        return False

    def _create_snapshot(self, timestamp: int) -> UnifiedMarketSnapshot | None:
        """Create unified market snapshot from current state."""
        try:
            # Get order book snapshot
            book_snapshot = self.order_book.get_snapshot(timestamp)

            # Convert OrderBookLevel objects to PriceLevel objects
            bid_levels = [
                PriceLevel(
                    price=level.price,
                    volume=level.volume,
                    order_count=level.order_count,
                )
                for level in book_snapshot.bid_levels[: self.max_depth_levels]
            ]

            ask_levels = [
                PriceLevel(
                    price=level.price,
                    volume=level.volume,
                    order_count=level.order_count,
                )
                for level in book_snapshot.ask_levels[: self.max_depth_levels]
            ]

            # Create snapshot
            return UnifiedMarketSnapshot(
                timestamp=timestamp,
                last_trade_price=self.last_l1_state.get("last_price"),
                last_trade_volume=self.last_l1_state.get("last_volume"),
                bid_price=self.last_l1_state.get("bid_price"),
                ask_price=self.last_l1_state.get("ask_price"),
                bid_volume=self.last_l1_state.get("bid_volume"),
                ask_volume=self.last_l1_state.get("ask_volume"),
                bid_levels=bid_levels,
                ask_levels=ask_levels,
            )

        except Exception as e:
            logger.error(f"Error creating snapshot: {e}")
            return None

    def _reset_state(self):
        """Reset internal state."""
        self.order_book = OrderBook(max_depth=self.max_depth_levels)
        self.last_l1_state.clear()
        self.tick_buffer.clear()
        self._last_sync_time = 0

        if self.stats:
            self.stats = SyncStats()

    def get_stats(self) -> SyncStats | None:
        """Get synchronization statistics."""
        return self.stats
