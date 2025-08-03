"""Tests for HftDataFeed class."""

import time
from unittest.mock import patch

import pandas as pd

from src.strategy_lab.backtesting.hft_integration.config import create_testing_config
from src.strategy_lab.backtesting.hft_integration.data_feed import (
    FeedStats,
    HftDataFeed,
    MockDataFeed,
    TickData,
    benchmark_feed_performance,
    create_optimized_feed,
)


class TestTickData:
    """Test TickData class functionality."""

    def test_tick_data_creation(self):
        """Test basic tick data creation."""
        tick = TickData(
            timestamp=1609459200000000000, price=13000.25, qty=5.0, side=1, order_id=123
        )

        assert tick.timestamp == 1609459200000000000
        assert tick.price == 13000.25
        assert tick.qty == 5.0
        assert tick.side == 1
        assert tick.order_id == 123

    def test_to_hftbacktest_format(self):
        """Test conversion to hftbacktest tuple format."""
        tick = TickData(
            timestamp=1609459200000000000, price=13000.25, qty=5.0, side=1, order_id=123
        )

        hft_format = tick.to_hftbacktest_format()
        expected = (1609459200000000000, 13000.25, 5.0, 1, 123)

        assert hft_format == expected
        assert isinstance(hft_format, tuple)
        assert len(hft_format) == 5


class TestFeedStats:
    """Test FeedStats class functionality."""

    def test_feed_stats_creation(self):
        """Test basic feed stats creation."""
        stats = FeedStats()

        assert stats.ticks_processed == 0
        assert stats.l1_ticks == 0
        assert stats.l2_ticks == 0
        assert stats.processing_errors == 0
        assert stats.end_time is None

    def test_duration_calculation(self):
        """Test duration calculation."""
        stats = FeedStats()
        stats.start_time = 100.0
        stats.end_time = 105.0

        assert stats.duration == 5.0

    def test_duration_without_end_time(self):
        """Test duration calculation without end time."""
        stats = FeedStats()
        stats.start_time = time.time() - 5.0

        # Duration should be approximately 5 seconds
        assert 4.9 <= stats.duration <= 5.1

    def test_ticks_per_second(self):
        """Test ticks per second calculation."""
        stats = FeedStats()
        stats.start_time = 100.0
        stats.end_time = 105.0
        stats.ticks_processed = 1000

        assert stats.ticks_per_second == 200.0

    def test_mb_per_second(self):
        """Test MB per second calculation."""
        stats = FeedStats()
        stats.start_time = 100.0
        stats.end_time = 102.0  # 2 seconds
        stats.bytes_processed = 2 * 1024 * 1024  # 2 MB

        assert stats.mb_per_second == 1.0


class TestHftDataFeed:
    """Test HftDataFeed class functionality."""

    def test_data_feed_creation(self):
        """Test basic data feed creation."""
        config = create_testing_config()
        feed = HftDataFeed(config)

        assert feed.config == config
        assert isinstance(feed.stats, FeedStats)
        assert feed._current_timestamp == 0
        assert feed._buffer_size == 10000

    def test_validate_tick_data_valid(self):
        """Test validation of valid tick data."""
        config = create_testing_config()
        feed = HftDataFeed(config)

        tick = TickData(timestamp=1609459200000000000, price=13000.25, qty=5.0, side=1)

        assert feed.validate_tick_data(tick) is True
        assert feed._current_timestamp == tick.timestamp

    def test_validate_tick_data_invalid_timestamp(self):
        """Test validation with invalid timestamp."""
        config = create_testing_config()
        feed = HftDataFeed(config)

        tick = TickData(timestamp=0, price=13000.25, qty=5.0, side=1)

        assert feed.validate_tick_data(tick) is False

    def test_validate_tick_data_invalid_price(self):
        """Test validation with invalid price."""
        config = create_testing_config()
        feed = HftDataFeed(config)

        tick = TickData(timestamp=1609459200000000000, price=0, qty=5.0, side=1)

        assert feed.validate_tick_data(tick) is False

    def test_validate_tick_data_invalid_quantity(self):
        """Test validation with invalid quantity."""
        config = create_testing_config()
        feed = HftDataFeed(config)

        tick = TickData(timestamp=1609459200000000000, price=13000.25, qty=-1.0, side=1)

        assert feed.validate_tick_data(tick) is False

    def test_validate_tick_data_invalid_side(self):
        """Test validation with invalid side."""
        config = create_testing_config()
        feed = HftDataFeed(config)

        tick = TickData(timestamp=1609459200000000000, price=13000.25, qty=5.0, side=2)

        assert feed.validate_tick_data(tick) is False

    def test_validate_tick_data_out_of_order(self):
        """Test validation with out-of-order timestamps."""
        config = create_testing_config()
        feed = HftDataFeed(config)

        # First tick
        tick1 = TickData(timestamp=1609459200000000000, price=13000.25, qty=5.0, side=1)
        assert feed.validate_tick_data(tick1) is True

        # Second tick with earlier timestamp
        tick2 = TickData(
            timestamp=1609459100000000000, price=13000.50, qty=3.0, side=-1
        )
        assert feed.validate_tick_data(tick2) is True  # Valid but warns

        # Current timestamp should be the later one
        assert feed._current_timestamp == tick1.timestamp

    def test_process_l1_data_empty(self):
        """Test processing empty L1 data."""
        config = create_testing_config()
        feed = HftDataFeed(config)

        empty_df = pd.DataFrame()
        ticks = list(feed.process_l1_data(empty_df))

        assert len(ticks) == 0

    def test_process_l1_data_valid(self):
        """Test processing valid L1 data."""
        config = create_testing_config()
        feed = HftDataFeed(config)

        # Create test L1 data
        l1_data = pd.DataFrame(
            {
                "timestamp": [1609459200000000000, 1609459200001000000],
                "price": [13000.25, 13000.50],
                "qty": [5.0, 3.0],
                "side": [1, -1],
                "order_id": [1, 2],
            }
        )

        ticks = list(feed.process_l1_data(l1_data))

        assert len(ticks) == 2
        assert feed.stats.l1_ticks == 2
        assert feed.stats.ticks_processed == 2

        # Check first tick
        assert ticks[0].timestamp == 1609459200000000000
        assert ticks[0].price == 13000.25
        assert ticks[0].qty == 5.0
        assert ticks[0].side == 1

    def test_process_l1_data_with_errors(self):
        """Test processing L1 data with errors."""
        config = create_testing_config()
        feed = HftDataFeed(config)

        # Create test data with invalid values
        l1_data = pd.DataFrame(
            {
                "timestamp": [1609459200000000000, 0],  # Second timestamp invalid
                "price": [13000.25, 13000.50],
                "qty": [5.0, 3.0],
                "side": [1, -1],
            }
        )

        ticks = list(feed.process_l1_data(l1_data))

        assert len(ticks) == 1  # Only one valid tick
        assert feed.stats.processing_errors == 1

    def test_process_l2_data_disabled(self):
        """Test processing L2 data when disabled."""
        config = create_testing_config()
        config.enable_level2 = False
        feed = HftDataFeed(config)

        l2_data = pd.DataFrame(
            {
                "timestamp": [1609459200000000000],
                "price": [13000.25],
                "qty": [5.0],
                "side": [1],
            }
        )

        ticks = list(feed.process_l2_data(l2_data))
        assert len(ticks) == 0

    def test_merge_l1_l2_streams(self):
        """Test merging L1 and L2 data streams."""
        config = create_testing_config()
        feed = HftDataFeed(config)

        # Create test data with mixed timestamps
        l1_data = pd.DataFrame(
            {
                "timestamp": [1609459200000000000, 1609459200002000000],
                "price": [13000.25, 13000.75],
                "qty": [5.0, 2.0],
                "side": [1, 1],
            }
        )

        l2_data = pd.DataFrame(
            {
                "timestamp": [1609459200001000000, 1609459200003000000],
                "price": [13000.50, 13001.00],
                "qty": [3.0, 4.0],
                "side": [-1, -1],
            }
        )

        ticks = list(feed.merge_l1_l2_streams(l1_data, l2_data))

        assert len(ticks) == 4

        # Check that ticks are sorted by timestamp
        timestamps = [tick.timestamp for tick in ticks]
        assert timestamps == sorted(timestamps)

    def test_apply_price_tick_size(self):
        """Test price tick size application."""
        config = create_testing_config()
        feed = HftDataFeed(config)

        # Test rounding for different price levels
        # At $13,000 level, tick size is $1.00
        rounded_price = feed.apply_price_tick_size(13000.13)
        assert rounded_price == 13000.0  # Rounded down to nearest $1.00

        rounded_price = feed.apply_price_tick_size(13000.6)
        assert rounded_price == 13001.0  # Rounded up to nearest $1.00

        # Test lower price level with $0.25 tick size
        rounded_price = feed.apply_price_tick_size(400.13)
        assert rounded_price == 400.25  # Rounded up to nearest $0.25

        rounded_price = feed.apply_price_tick_size(400.37)
        assert rounded_price == 400.25  # Rounded down to nearest $0.25

    def test_simulate_latency_disabled(self):
        """Test latency simulation when disabled."""
        config = create_testing_config()
        config.latency_simulation = False
        feed = HftDataFeed(config)

        tick = TickData(timestamp=1609459200000000000, price=13000.25, qty=5.0, side=1)
        result_tick = feed.simulate_latency(tick)

        assert result_tick.timestamp == tick.timestamp  # No change

    def test_simulate_latency_enabled(self):
        """Test latency simulation when enabled."""
        config = create_testing_config()
        config.latency_simulation = True
        config.min_latency_ns = 1000
        config.max_latency_ns = 2000
        feed = HftDataFeed(config)

        tick = TickData(timestamp=1609459200000000000, price=13000.25, qty=5.0, side=1)

        with patch("random.randint", return_value=1500):
            result_tick = feed.simulate_latency(tick)

        assert result_tick.timestamp == tick.timestamp + 1500
        assert result_tick.price == tick.price
        assert result_tick.qty == tick.qty
        assert result_tick.side == tick.side

    def test_create_data_stream(self):
        """Test creating unified data stream."""
        config = create_testing_config()
        feed = HftDataFeed(config)

        # Create test data chunk
        data_chunk = {
            "l1_data": pd.DataFrame(
                {
                    "timestamp": [1609459200000000000],
                    "price": [13000.25],
                    "qty": [5.0],
                    "side": [1],
                }
            ),
            "l2_data": pd.DataFrame(
                {
                    "timestamp": [1609459200001000000],
                    "price": [13000.50],
                    "qty": [3.0],
                    "side": [-1],
                }
            ),
        }

        ticks = list(feed.create_data_stream(data_chunk))

        assert len(ticks) == 2
        assert feed.stats.bytes_processed > 0

    def test_set_buffer_size(self):
        """Test setting buffer size."""
        config = create_testing_config()
        feed = HftDataFeed(config)

        feed.set_buffer_size(50000)
        assert feed._buffer_size == 50000

        # Test minimum buffer size
        feed.set_buffer_size(500)
        assert feed._buffer_size == 1000  # Minimum enforced

    def test_reset_stats(self):
        """Test resetting feed statistics."""
        config = create_testing_config()
        feed = HftDataFeed(config)

        # Set some stats
        feed.stats.ticks_processed = 100
        feed.stats.processing_errors = 5
        feed._current_timestamp = 1609459200000000000

        feed.reset_stats()

        assert feed.stats.ticks_processed == 0
        assert feed.stats.processing_errors == 0
        assert feed._current_timestamp == 0


class TestMockDataFeed:
    """Test MockDataFeed class functionality."""

    def test_mock_data_feed_creation(self):
        """Test mock data feed creation."""
        config = create_testing_config()
        mock_feed = MockDataFeed(config, tick_count=100)

        assert mock_feed.tick_count == 100
        assert len(mock_feed._mock_ticks) == 100

    def test_mock_data_generation(self):
        """Test mock data generation."""
        config = create_testing_config()
        mock_feed = MockDataFeed(config, tick_count=10)

        # Check that all ticks are valid
        for tick in mock_feed._mock_ticks:
            assert tick.timestamp > 0
            assert tick.price > 0
            assert tick.qty > 0
            assert tick.side in [-1, 1]
            assert tick.order_id > 0

    def test_stream_mock_data(self):
        """Test streaming mock data."""
        config = create_testing_config()
        mock_feed = MockDataFeed(config, tick_count=5)

        ticks = list(mock_feed.stream_mock_data())

        assert len(ticks) == 5
        assert mock_feed.stats.ticks_processed == 5
        assert mock_feed.stats.end_time is not None


class TestUtilityFunctions:
    """Test utility functions."""

    def test_create_optimized_feed_speed(self):
        """Test creating speed-optimized feed."""
        config = create_testing_config()
        feed = create_optimized_feed(config, performance_mode="speed")

        assert feed._buffer_size == 50000
        assert config.latency_simulation is False
        assert config.enable_market_impact is False

    def test_create_optimized_feed_accuracy(self):
        """Test creating accuracy-optimized feed."""
        config = create_testing_config()
        feed = create_optimized_feed(config, performance_mode="accuracy")

        assert feed._buffer_size == 1000
        assert config.latency_simulation is True
        assert config.enable_market_impact is True

    def test_create_optimized_feed_balanced(self):
        """Test creating balanced feed."""
        config = create_testing_config()
        feed = create_optimized_feed(config, performance_mode="balanced")

        assert feed._buffer_size == 10000
        assert config.latency_simulation is True
        assert config.enable_market_impact is True

    def test_benchmark_feed_performance(self):
        """Test benchmarking feed performance."""
        config = create_testing_config()
        feed = HftDataFeed(config)

        # Create test data chunks
        test_chunks = [
            {
                "l1_data": pd.DataFrame(
                    {
                        "timestamp": [1609459200000000000 + i * 1000000],
                        "price": [13000.25 + i * 0.25],
                        "qty": [5.0],
                        "side": [1],
                    }
                )
            }
            for i in range(10)
        ]

        results = benchmark_feed_performance(feed, test_chunks)

        assert "duration_seconds" in results
        assert "ticks_processed" in results
        assert "ticks_per_second" in results
        assert "mb_per_second" in results
        assert "error_rate" in results

        assert results["ticks_processed"] == 10
        assert results["duration_seconds"] > 0
