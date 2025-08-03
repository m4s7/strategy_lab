"""Data feed component for streaming tick data to hftbacktest engine."""

import logging
import random
import time
from collections.abc import Iterator
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

import pandas as pd

from .config import MNQConfig

logger = logging.getLogger(__name__)


@dataclass
class TickData:
    """Standardized tick data format for hftbacktest."""

    timestamp: int  # Nanoseconds since epoch
    price: float  # Price level
    qty: float  # Quantity/volume
    side: int  # 1=Buy, -1=Sell, 0=Unknown
    order_id: int = 0  # Order ID (optional)

    def to_hftbacktest_format(self) -> tuple[int, float, float, int, int]:
        """Convert to hftbacktest expected tuple format."""
        return (self.timestamp, self.price, self.qty, self.side, self.order_id)


@dataclass
class FeedStats:
    """Statistics for data feed performance monitoring."""

    start_time: float = 0.0
    end_time: float | None = None
    ticks_processed: int = 0
    l1_ticks: int = 0
    l2_ticks: int = 0
    bytes_processed: int = 0
    processing_errors: int = 0

    @property
    def duration(self) -> float:
        """Get feed duration in seconds."""
        end = self.end_time or time.time()
        return max(0.0, end - self.start_time)

    @property
    def ticks_per_second(self) -> float:
        """Get processing rate in ticks per second."""
        duration = self.duration
        return self.ticks_processed / duration if duration > 0 else 0.0

    @property
    def mb_per_second(self) -> float:
        """Get data throughput in MB per second."""
        duration = self.duration
        mb_processed = self.bytes_processed / (1024 * 1024)
        return mb_processed / duration if duration > 0 else 0.0


class HftDataFeed:
    """High-performance data feed for streaming tick data to hftbacktest."""

    def __init__(self, config: MNQConfig):
        """Initialize the data feed with MNQ configuration."""
        self.config = config
        self.stats = FeedStats()
        self._current_timestamp = 0
        self._tick_buffer: list[TickData] = []
        self._buffer_size = 10000  # Buffer size for batch processing

        logger.info("Initialized HftDataFeed for %s", config.symbol)

    def validate_tick_data(self, tick: TickData) -> bool:
        """Validate individual tick data."""
        if tick.timestamp <= 0:
            logger.warning("Invalid timestamp: %s", tick.timestamp)
            return False

        if tick.price <= 0:
            logger.warning("Invalid price: %s", tick.price)
            return False

        if tick.qty < 0:
            logger.warning("Invalid quantity: %s", tick.qty)
            return False

        if tick.side not in [-1, 0, 1]:
            logger.warning("Invalid side: %s", tick.side)
            return False

        # Check timestamp ordering
        if tick.timestamp < self._current_timestamp:
            logger.warning(
                "Out-of-order timestamp: %s < %s",
                tick.timestamp,
                self._current_timestamp,
            )
            # Don't reject, but warn

        self._current_timestamp = max(self._current_timestamp, tick.timestamp)
        return True

    def process_l1_data(self, df: pd.DataFrame) -> Iterator[TickData]:
        """Process Level 1 data and yield TickData objects."""
        if df.empty:
            return

        logger.debug("Processing %d L1 ticks", len(df))

        for _, row in df.iterrows():
            try:
                tick = TickData(
                    timestamp=int(row["timestamp"]),
                    price=float(row["price"]),
                    qty=float(row["qty"]),
                    side=int(row["side"]),
                    order_id=int(row.get("order_id", 0)),
                )

                if self.validate_tick_data(tick):
                    self.stats.l1_ticks += 1
                    self.stats.ticks_processed += 1
                    yield tick
                else:
                    self.stats.processing_errors += 1

            except Exception:
                logger.exception("Error processing L1 tick")
                self.stats.processing_errors += 1

    def process_l2_data(self, df: pd.DataFrame) -> Iterator[TickData]:
        """Process Level 2 data and yield TickData objects."""
        if df.empty or not self.config.enable_level2:
            return

        logger.debug("Processing %d L2 ticks", len(df))

        for _, row in df.iterrows():
            try:
                tick = TickData(
                    timestamp=int(row["timestamp"]),
                    price=float(row["price"]),
                    qty=float(row["qty"]),
                    side=int(row["side"]),
                    order_id=int(row.get("order_id", 0)),
                )

                if self.validate_tick_data(tick):
                    self.stats.l2_ticks += 1
                    self.stats.ticks_processed += 1
                    yield tick
                else:
                    self.stats.processing_errors += 1

            except Exception:
                logger.exception("Error processing L2 tick")
                self.stats.processing_errors += 1

    def merge_l1_l2_streams(
        self, l1_data: pd.DataFrame, l2_data: pd.DataFrame
    ) -> Iterator[TickData]:
        """Merge and synchronize L1 and L2 data streams by timestamp."""

        # Combine data and sort by timestamp
        l1_ticks = list(self.process_l1_data(l1_data))
        l2_ticks = list(self.process_l2_data(l2_data))

        all_ticks = l1_ticks + l2_ticks
        all_ticks.sort(key=lambda x: x.timestamp)

        logger.debug(
            "Merged %d L1 + %d L2 = %d total ticks",
            len(l1_ticks),
            len(l2_ticks),
            len(all_ticks),
        )

        yield from all_ticks

    def create_data_stream(self, data_chunk: dict[str, Any]) -> Iterator[TickData]:
        """Create a unified data stream from a data pipeline chunk."""

        l1_data = data_chunk.get("l1_data", pd.DataFrame())
        l2_data = data_chunk.get("l2_data", pd.DataFrame())

        # Calculate data size for stats
        l1_bytes = l1_data.memory_usage(deep=True).sum() if not l1_data.empty else 0
        l2_bytes = l2_data.memory_usage(deep=True).sum() if not l2_data.empty else 0
        self.stats.bytes_processed += l1_bytes + l2_bytes

        # Stream data based on configuration
        if self.config.enable_level1 and self.config.enable_level2:
            # Merge both streams
            yield from self.merge_l1_l2_streams(l1_data, l2_data)
        elif self.config.enable_level1:
            # L1 only
            yield from self.process_l1_data(l1_data)
        elif self.config.enable_level2:
            # L2 only
            yield from self.process_l2_data(l2_data)

    def apply_price_tick_size(self, price: float) -> float:
        """Apply MNQ tick size rounding to price."""

        price_decimal = Decimal(str(price))
        tick_size = self.config.get_tick_size_for_price(price_decimal)

        # Round to nearest tick
        ticks = (price_decimal / tick_size).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        )
        rounded_price = ticks * tick_size

        return float(rounded_price)

    def simulate_latency(self, tick: TickData, base_latency_ns: int = 0) -> TickData:
        """Apply latency simulation to tick data."""
        if not self.config.latency_simulation:
            return tick

        # Add random latency within configured range
        latency_ns = random.randint(
            self.config.min_latency_ns, self.config.max_latency_ns
        )
        latency_ns += base_latency_ns

        # Create new tick with adjusted timestamp
        return TickData(
            timestamp=tick.timestamp + latency_ns,
            price=tick.price,
            qty=tick.qty,
            side=tick.side,
            order_id=tick.order_id,
        )

    def stream_to_hftbacktest(
        self, data_chunks: Iterator[dict[str, Any]]
    ) -> Iterator[tuple[int, float, float, int, int]]:
        """
        Main streaming interface for hftbacktest integration.

        Yields tuples in hftbacktest format: (timestamp, price, qty, side, order_id)
        """
        self.stats.start_time = time.time()

        try:
            for chunk_count, chunk in enumerate(data_chunks, 1):

                # Process chunk and stream ticks
                for tick in self.create_data_stream(chunk):
                    # Apply price rounding
                    tick.price = self.apply_price_tick_size(tick.price)

                    # Apply latency simulation
                    if self.config.latency_simulation:
                        processed_tick = self.simulate_latency(tick)
                    else:
                        processed_tick = tick

                    # Yield in hftbacktest format
                    yield processed_tick.to_hftbacktest_format()

                # Progress reporting
                if chunk_count % 10 == 0:
                    logger.info(
                        "Processed %d chunks, %d ticks, %.0f ticks/sec",
                        chunk_count,
                        self.stats.ticks_processed,
                        self.stats.ticks_per_second,
                    )

        finally:
            self.stats.end_time = time.time()
            self._log_final_stats()

    def _log_final_stats(self):
        """Log final processing statistics."""
        logger.info("Data feed completed:")
        logger.info("  Duration: %.2f seconds", self.stats.duration)
        logger.info("  Ticks processed: %s", f"{self.stats.ticks_processed:,}")
        logger.info("  L1 ticks: %s", f"{self.stats.l1_ticks:,}")
        logger.info("  L2 ticks: %s", f"{self.stats.l2_ticks:,}")
        logger.info(
            "  Processing rate: %.0f ticks/second", self.stats.ticks_per_second
        )
        logger.info("  Data throughput: %.2f MB/second", self.stats.mb_per_second)
        logger.info("  Errors: %d", self.stats.processing_errors)

        if self.stats.processing_errors > 0:
            error_rate = (
                self.stats.processing_errors / max(1, self.stats.ticks_processed) * 100
            )
            logger.warning("  Error rate: %.2f%%", error_rate)

    def get_stats(self) -> FeedStats:
        """Get current feed statistics."""
        return self.stats

    def reset_stats(self):
        """Reset feed statistics."""
        self.stats = FeedStats()
        self._current_timestamp = 0

    def set_buffer_size(self, size: int):
        """Set internal buffer size for batch processing."""
        self._buffer_size = max(1000, size)
        logger.debug("Set buffer size to %d", self._buffer_size)


class MockDataFeed(HftDataFeed):
    """Mock data feed for testing purposes."""

    def __init__(self, config: MNQConfig, tick_count: int = 1000):
        """Initialize mock feed with specified number of ticks."""
        super().__init__(config)
        self.tick_count = tick_count
        self._generate_mock_data()

    def _generate_mock_data(self):
        """Generate synthetic tick data for testing."""

        base_timestamp = 1609459200000000000  # 2021-01-01 00:00:00 UTC
        base_price = 13000.0  # MNQ around $13,000

        self._mock_ticks = []

        for i in range(self.tick_count):
            # Generate realistic tick data
            timestamp = base_timestamp + i * 1_000_000  # 1ms intervals

            # Random walk price
            price_change = random.uniform(-0.5, 0.5)
            price = base_price + price_change
            price = self.apply_price_tick_size(price)  # Apply tick size

            qty = random.randint(1, 10)
            side = random.choice([-1, 1])  # Buy or sell

            tick = TickData(
                timestamp=timestamp, price=price, qty=qty, side=side, order_id=i + 1
            )

            self._mock_ticks.append(tick)

    def stream_mock_data(self) -> Iterator[tuple[int, float, float, int, int]]:
        """Stream mock data in hftbacktest format."""
        self.stats.start_time = time.time()

        for tick in self._mock_ticks:
            self.stats.ticks_processed += 1
            yield tick.to_hftbacktest_format()

        self.stats.end_time = time.time()
        self._log_final_stats()


# Utility functions for data feed management
def create_optimized_feed(
    config: MNQConfig, performance_mode: str = "balanced"
) -> HftDataFeed:
    """Create an optimized data feed based on performance requirements."""

    feed = HftDataFeed(config)

    if performance_mode == "speed":
        # Optimize for maximum speed
        feed.set_buffer_size(50000)
        config.latency_simulation = False
        config.enable_market_impact = False

    elif performance_mode == "accuracy":
        # Optimize for maximum accuracy
        feed.set_buffer_size(1000)
        config.latency_simulation = True
        config.enable_market_impact = True

    elif performance_mode == "balanced":
        # Balanced speed and accuracy
        feed.set_buffer_size(10000)
        config.latency_simulation = True
        config.enable_market_impact = True

    return feed


def benchmark_feed_performance(
    feed: HftDataFeed, test_data_chunks: list[dict[str, Any]]
) -> dict[str, float]:
    """Benchmark data feed performance with test data."""

    feed.reset_stats()
    start_time = time.time()

    # Stream all test data
    tick_count = 0
    for _ in feed.stream_to_hftbacktest(iter(test_data_chunks)):
        tick_count += 1

    end_time = time.time()
    duration = end_time - start_time

    return {
        "duration_seconds": duration,
        "ticks_processed": tick_count,
        "ticks_per_second": tick_count / duration if duration > 0 else 0,
        "mb_per_second": feed.stats.mb_per_second,
        "error_rate": feed.stats.processing_errors / max(1, tick_count) * 100,
    }
