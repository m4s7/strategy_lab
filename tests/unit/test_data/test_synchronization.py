"""Tests for L1+L2 data synchronization."""

from decimal import Decimal

import pandas as pd
import pytest

from strategy_lab.data.synchronization import (
    L1L2DataSynchronizer,
    PriceLevel,
    UnifiedMarketSnapshot,
)


class TestUnifiedMarketSnapshot:
    """Test UnifiedMarketSnapshot model."""

    def test_snapshot_creation(self):
        """Test basic snapshot creation."""
        snapshot = UnifiedMarketSnapshot(
            timestamp=1000000000,
            bid_price=Decimal("100.25"),
            ask_price=Decimal("100.50"),
            bid_volume=10,
            ask_volume=15,
        )

        assert snapshot.timestamp == 1000000000
        assert snapshot.spread == Decimal("0.25")
        assert snapshot.mid_price == Decimal("100.375")

    def test_depth_calculations(self):
        """Test order book depth calculations."""
        snapshot = UnifiedMarketSnapshot(
            timestamp=1000000000,
            bid_levels=[
                PriceLevel(Decimal("100.25"), 10),
                PriceLevel(Decimal("100.00"), 20),
                PriceLevel(Decimal("99.75"), 30),
            ],
            ask_levels=[
                PriceLevel(Decimal("100.50"), 15),
                PriceLevel(Decimal("100.75"), 25),
            ],
        )

        assert snapshot.total_bid_depth == 60
        assert snapshot.total_ask_depth == 40
        assert snapshot.imbalance_ratio == 0.2  # (60-40)/(60+40)

    def test_empty_book_handling(self):
        """Test handling of empty order book."""
        snapshot = UnifiedMarketSnapshot(timestamp=1000000000)

        assert snapshot.spread is None
        assert snapshot.mid_price is None
        assert snapshot.total_bid_depth == 0
        assert snapshot.total_ask_depth == 0
        assert snapshot.imbalance_ratio == 0.0


class TestL1L2DataSynchronizer:
    """Test L1L2DataSynchronizer."""

    @pytest.fixture
    def sample_l1_data(self):
        """Create sample L1 data."""
        return pd.DataFrame(
            {
                "timestamp": [1000, 2000, 3000, 4000, 5000],
                "mdt": [1, 0, 2, 1, 0],  # Bid, Ask, Trade, Bid, Ask
                "price": [100.25, 100.50, 100.50, 100.00, 100.75],
                "volume": [10, 15, 5, 20, 25],
            }
        )

    @pytest.fixture
    def sample_l2_data(self):
        """Create sample L2 data."""
        return pd.DataFrame(
            {
                "timestamp": [1500, 2500, 3500, 4500],
                "mdt": [1, 0, 1, 0],  # Bid, Ask, Bid, Ask
                "price": [100.00, 100.75, 99.75, 101.00],
                "volume": [30, 35, 40, 45],
                "operation": [0, 0, 0, 0],  # All adds
                "depth": [1, 1, 2, 2],
            }
        )

    def test_synchronizer_initialization(self):
        """Test synchronizer initialization."""
        sync = L1L2DataSynchronizer(
            sync_window_ns=1_000_000, buffer_size=1000, max_depth_levels=5
        )

        assert sync.sync_window_ns == 1_000_000
        assert sync.buffer_size == 1000
        assert sync.max_depth_levels == 5
        assert sync.stats is not None

    def test_basic_synchronization(self, sample_l1_data, sample_l2_data):
        """Test basic synchronization of L1 and L2 data."""
        sync = L1L2DataSynchronizer(sync_window_ns=2000)

        snapshots = list(sync.synchronize(sample_l1_data, sample_l2_data))

        assert len(snapshots) > 0

        # Check first snapshot
        first = snapshots[0]
        assert isinstance(first, UnifiedMarketSnapshot)
        assert first.timestamp > 0

        # Check that we have both L1 and L2 data
        has_l1 = any(s.bid_price or s.ask_price for s in snapshots)
        has_l2 = any(s.bid_levels or s.ask_levels for s in snapshots)

        assert has_l1, "Should have L1 data"
        assert has_l2, "Should have L2 data"

    def test_timestamp_ordering(self, sample_l1_data, sample_l2_data):
        """Test that snapshots are in timestamp order."""
        sync = L1L2DataSynchronizer()

        snapshots = list(sync.synchronize(sample_l1_data, sample_l2_data))

        timestamps = [s.timestamp for s in snapshots]
        assert timestamps == sorted(timestamps)

    def test_time_range_filtering(self, sample_l1_data, sample_l2_data):
        """Test filtering by time range."""
        sync = L1L2DataSynchronizer()

        # Only get data between 2000 and 4000
        snapshots = list(
            sync.synchronize(
                sample_l1_data, sample_l2_data, start_time=2000, end_time=4000
            )
        )

        for snapshot in snapshots:
            assert 2000 <= snapshot.timestamp <= 4000

    def test_stats_collection(self, sample_l1_data, sample_l2_data):
        """Test statistics collection."""
        # Use small sync window to ensure snapshots are generated
        sync = L1L2DataSynchronizer(enable_stats=True, sync_window_ns=1000)

        list(sync.synchronize(sample_l1_data, sample_l2_data))

        stats = sync.get_stats()
        assert stats is not None
        assert stats.total_l1_ticks == len(sample_l1_data)
        assert stats.total_l2_ticks == len(sample_l2_data)
        assert stats.total_snapshots > 0

    def test_empty_data_handling(self):
        """Test handling of empty data."""
        sync = L1L2DataSynchronizer()

        empty_df = pd.DataFrame()
        snapshots = list(sync.synchronize(empty_df, empty_df))

        assert len(snapshots) == 0

    def test_l1_only_synchronization(self, sample_l1_data):
        """Test synchronization with only L1 data."""
        sync = L1L2DataSynchronizer(sync_window_ns=2000)

        empty_l2 = pd.DataFrame(columns=["timestamp", "mdt", "price", "volume"])
        snapshots = list(sync.synchronize(sample_l1_data, empty_l2))

        assert len(snapshots) > 0
        # Should have L1 data but no L2
        for s in snapshots:
            assert s.bid_levels == []
            assert s.ask_levels == []
