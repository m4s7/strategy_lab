"""Tests for order book reconstruction engine."""

import tempfile
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from strategy_lab.data.processing.order_book import (
    OrderBook,
    OrderBookAnalytics,
    OrderBookLevel,
    OrderBookReconstructor,
    OrderBookSnapshot,
)


class TestOrderBookLevel:
    """Test OrderBookLevel class."""

    def test_initialization(self):
        """Test level initialization."""
        level = OrderBookLevel(price=100.50, volume=1000)
        assert level.price == Decimal("100.50")
        assert level.volume == 1000
        assert level.order_count == 0
        assert level.market_maker is None

    def test_price_conversion(self):
        """Test price conversion to Decimal."""
        level = OrderBookLevel(price=100.5, volume=1000)
        assert isinstance(level.price, Decimal)
        assert level.price == Decimal("100.5")


class TestOrderBookSnapshot:
    """Test OrderBookSnapshot class."""

    def test_empty_snapshot(self):
        """Test empty snapshot properties."""
        snapshot = OrderBookSnapshot(timestamp=1609459200000000000)
        assert snapshot.best_bid is None
        assert snapshot.best_ask is None
        assert snapshot.spread is None
        assert snapshot.mid_price is None

    def test_snapshot_with_levels(self):
        """Test snapshot with bid/ask levels."""
        bid_level = OrderBookLevel(price=Decimal("100.00"), volume=1000)
        ask_level = OrderBookLevel(price=Decimal("100.25"), volume=500)

        snapshot = OrderBookSnapshot(
            timestamp=1609459200000000000,
            bid_levels=[bid_level],
            ask_levels=[ask_level],
        )

        assert snapshot.best_bid == bid_level
        assert snapshot.best_ask == ask_level
        assert snapshot.spread == Decimal("0.25")
        assert snapshot.mid_price == Decimal("100.125")


class TestOrderBookAnalytics:
    """Test OrderBookAnalytics class."""

    def test_calculate_imbalance_balanced(self):
        """Test imbalance calculation with balanced book."""
        imbalance = OrderBookAnalytics.calculate_imbalance(1000, 1000)
        assert imbalance == 0.0

    def test_calculate_imbalance_bid_heavy(self):
        """Test imbalance calculation with bid-heavy book."""
        imbalance = OrderBookAnalytics.calculate_imbalance(1500, 500)
        assert imbalance == 0.5

    def test_calculate_imbalance_ask_heavy(self):
        """Test imbalance calculation with ask-heavy book."""
        imbalance = OrderBookAnalytics.calculate_imbalance(300, 700)
        assert imbalance == -0.4

    def test_calculate_imbalance_empty_book(self):
        """Test imbalance calculation with empty book."""
        imbalance = OrderBookAnalytics.calculate_imbalance(0, 0)
        assert imbalance == 0.0

    def test_calculate_depth_weighted_price(self):
        """Test depth-weighted price calculation."""
        levels = [
            OrderBookLevel(price=Decimal("100.00"), volume=1000),
            OrderBookLevel(price=Decimal("99.75"), volume=500),
            OrderBookLevel(price=Decimal("99.50"), volume=250),
        ]

        vwap = OrderBookAnalytics.calculate_depth_weighted_price(levels, depth=3)
        expected = (
            Decimal("100.00") * 1000 + Decimal("99.75") * 500 + Decimal("99.50") * 250
        ) / 1750
        assert abs(vwap - expected) < Decimal("0.001")

    def test_calculate_depth_weighted_price_empty(self):
        """Test depth-weighted price with empty levels."""
        result = OrderBookAnalytics.calculate_depth_weighted_price([], depth=5)
        assert result is None

    def test_calculate_book_pressure(self):
        """Test book pressure calculation."""
        bid_levels = [
            OrderBookLevel(price=Decimal("100.00"), volume=1000),
            OrderBookLevel(price=Decimal("99.75"), volume=500),
        ]
        ask_levels = [
            OrderBookLevel(price=Decimal("100.25"), volume=300),
            OrderBookLevel(price=Decimal("100.50"), volume=200),
        ]

        snapshot = OrderBookSnapshot(
            timestamp=1609459200000000000, bid_levels=bid_levels, ask_levels=ask_levels
        )

        pressure = OrderBookAnalytics.calculate_book_pressure(snapshot, depth=2)

        assert pressure["bid_volume"] == 1500
        assert pressure["ask_volume"] == 500
        assert pressure["total_volume"] == 2000
        assert pressure["imbalance"] == 0.5
        assert pressure["bid_ratio"] == 0.75


class TestOrderBook:
    """Test OrderBook class."""

    def test_initialization(self):
        """Test order book initialization."""
        book = OrderBook(max_depth=5)
        assert book.max_depth == 5
        assert book.get_best_bid() is None
        assert book.get_best_ask() is None
        assert book._operation_count == 0

    def test_reset(self):
        """Test order book reset."""
        book = OrderBook()

        # Add some operations
        book.process_operation(
            timestamp=1609459200000000000,
            mdt=OrderBook.MDT_BID,
            price=100.0,
            volume=1000,
            operation=OrderBook.OP_ADD,
        )

        assert book.get_best_bid() is not None

        # Reset and verify empty state
        book.reset()
        assert book.get_best_bid() is None
        assert book._operation_count == 0

    def test_add_bid_operation(self):
        """Test adding bid orders."""
        book = OrderBook()

        # Add bid order
        success = book.process_operation(
            timestamp=1609459200000000000,
            mdt=OrderBook.MDT_BID,
            price=100.0,
            volume=1000,
            operation=OrderBook.OP_ADD,
        )

        assert success
        best_bid = book.get_best_bid()
        assert best_bid is not None
        assert best_bid.price == Decimal("100.0")
        assert best_bid.volume == 1000

    def test_add_ask_operation(self):
        """Test adding ask orders."""
        book = OrderBook()

        # Add ask order
        success = book.process_operation(
            timestamp=1609459200000000000,
            mdt=OrderBook.MDT_ASK,
            price=100.25,
            volume=500,
            operation=OrderBook.OP_ADD,
        )

        assert success
        best_ask = book.get_best_ask()
        assert best_ask is not None
        assert best_ask.price == Decimal("100.25")
        assert best_ask.volume == 500

    def test_update_operation(self):
        """Test updating existing orders."""
        book = OrderBook()

        # Add initial order
        book.process_operation(
            timestamp=1609459200000000000,
            mdt=OrderBook.MDT_BID,
            price=100.0,
            volume=1000,
            operation=OrderBook.OP_ADD,
        )

        # Update volume
        success = book.process_operation(
            timestamp=1609459200000000001,
            mdt=OrderBook.MDT_BID,
            price=100.0,
            volume=1500,
            operation=OrderBook.OP_UPDATE,
        )

        assert success
        best_bid = book.get_best_bid()
        assert best_bid.volume == 1500

    def test_remove_operation(self):
        """Test removing orders."""
        book = OrderBook()

        # Add order
        book.process_operation(
            timestamp=1609459200000000000,
            mdt=OrderBook.MDT_BID,
            price=100.0,
            volume=1000,
            operation=OrderBook.OP_ADD,
        )

        assert book.get_best_bid() is not None

        # Remove order
        success = book.process_operation(
            timestamp=1609459200000000001,
            mdt=OrderBook.MDT_BID,
            price=100.0,
            volume=0,
            operation=OrderBook.OP_REMOVE,
        )

        assert success
        assert book.get_best_bid() is None

    def test_update_to_zero_volume(self):
        """Test updating order to zero volume (should remove)."""
        book = OrderBook()

        # Add order
        book.process_operation(
            timestamp=1609459200000000000,
            mdt=OrderBook.MDT_BID,
            price=100.0,
            volume=1000,
            operation=OrderBook.OP_ADD,
        )

        # Update to zero volume
        success = book.process_operation(
            timestamp=1609459200000000001,
            mdt=OrderBook.MDT_BID,
            price=100.0,
            volume=0,
            operation=OrderBook.OP_UPDATE,
        )

        assert success
        assert book.get_best_bid() is None

    def test_multiple_bid_levels(self):
        """Test multiple bid levels ordering."""
        book = OrderBook()

        # Add bids in random order
        prices = [100.0, 99.75, 100.25, 99.50]
        for i, price in enumerate(prices):
            book.process_operation(
                timestamp=1609459200000000000 + i,
                mdt=OrderBook.MDT_BID,
                price=price,
                volume=1000,
                operation=OrderBook.OP_ADD,
            )

        # Check best bid is highest price
        best_bid = book.get_best_bid()
        assert best_bid.price == Decimal("100.25")

        # Check ordering
        snapshot = book.get_snapshot()
        bid_prices = [level.price for level in snapshot.bid_levels]
        assert bid_prices == [
            Decimal("100.25"),
            Decimal("100.0"),
            Decimal("99.75"),
            Decimal("99.50"),
        ]

    def test_multiple_ask_levels(self):
        """Test multiple ask levels ordering."""
        book = OrderBook()

        # Add asks in random order
        prices = [100.50, 100.25, 101.0, 100.75]
        for i, price in enumerate(prices):
            book.process_operation(
                timestamp=1609459200000000000 + i,
                mdt=OrderBook.MDT_ASK,
                price=price,
                volume=500,
                operation=OrderBook.OP_ADD,
            )

        # Check best ask is lowest price
        best_ask = book.get_best_ask()
        assert best_ask.price == Decimal("100.25")

        # Check ordering
        snapshot = book.get_snapshot()
        ask_prices = [level.price for level in snapshot.ask_levels]
        assert ask_prices == [
            Decimal("100.25"),
            Decimal("100.50"),
            Decimal("100.75"),
            Decimal("101.0"),
        ]

    def test_max_depth_limiting(self):
        """Test maximum depth limiting."""
        book = OrderBook(max_depth=3)

        # Add more bid levels than max depth
        for i in range(5):
            price = 100.0 - i * 0.25
            book.process_operation(
                timestamp=1609459200000000000 + i,
                mdt=OrderBook.MDT_BID,
                price=price,
                volume=1000,
                operation=OrderBook.OP_ADD,
            )

        snapshot = book.get_snapshot()
        assert len(snapshot.bid_levels) == 3

        # Check we kept the best levels
        bid_prices = [level.price for level in snapshot.bid_levels]
        assert bid_prices == [Decimal("100.0"), Decimal("99.75"), Decimal("99.50")]

    def test_spread_calculation(self):
        """Test bid-ask spread calculation."""
        book = OrderBook()

        # Add bid and ask
        book.process_operation(
            timestamp=1609459200000000000,
            mdt=OrderBook.MDT_BID,
            price=100.0,
            volume=1000,
            operation=OrderBook.OP_ADD,
        )

        book.process_operation(
            timestamp=1609459200000000001,
            mdt=OrderBook.MDT_ASK,
            price=100.25,
            volume=500,
            operation=OrderBook.OP_ADD,
        )

        spread = book.get_spread()
        assert spread == Decimal("0.25")

        mid_price = book.get_mid_price()
        assert mid_price == Decimal("100.125")

    def test_invalid_operations(self):
        """Test handling of invalid operations."""
        book = OrderBook()

        # Invalid MDT
        success = book.process_operation(
            timestamp=1609459200000000000,
            mdt=99,  # Invalid
            price=100.0,
            volume=1000,
            operation=OrderBook.OP_ADD,
        )
        assert not success
        assert book._invalid_operations == 1

        # Invalid price
        success = book.process_operation(
            timestamp=1609459200000000001,
            mdt=OrderBook.MDT_BID,
            price=-100.0,  # Invalid
            volume=1000,
            operation=OrderBook.OP_ADD,
        )
        assert not success
        assert book._invalid_operations == 2

        # Invalid operation type
        success = book.process_operation(
            timestamp=1609459200000000002,
            mdt=OrderBook.MDT_BID,
            price=100.0,
            volume=1000,
            operation=99,  # Invalid
        )
        assert not success
        assert book._invalid_operations == 3

    def test_out_of_sequence_timestamps(self):
        """Test handling of out-of-sequence timestamps."""
        book = OrderBook()

        with patch("strategy_lab.data.processing.order_book.logger") as mock_logger:
            # Add operations with decreasing timestamps
            book.process_operation(
                timestamp=1609459200000000002,
                mdt=OrderBook.MDT_BID,
                price=100.0,
                volume=1000,
                operation=OrderBook.OP_ADD,
            )

            book.process_operation(
                timestamp=1609459200000000001,  # Earlier timestamp
                mdt=OrderBook.MDT_ASK,
                price=100.25,
                volume=500,
                operation=OrderBook.OP_ADD,
            )

            # Should log warning but still process
            mock_logger.warning.assert_called_once()
            assert "Out-of-sequence" in mock_logger.warning.call_args[0][0]

    def test_process_dataframe(self):
        """Test processing DataFrame of operations."""
        book = OrderBook()

        # Create test DataFrame
        df = pd.DataFrame(
            {
                "timestamp": [
                    1609459200000000000,
                    1609459200000000001,
                    1609459200000000002,
                ],
                "mdt": [OrderBook.MDT_BID, OrderBook.MDT_ASK, OrderBook.MDT_BID],
                "price": [100.0, 100.25, 99.75],
                "volume": [1000, 500, 750],
                "operation": [OrderBook.OP_ADD, OrderBook.OP_ADD, OrderBook.OP_ADD],
            }
        )

        processed_count = book.process_dataframe(df)
        assert processed_count == 3

        # Verify state
        assert book.get_best_bid().price == Decimal("100.0")
        assert book.get_best_ask().price == Decimal("100.25")

        snapshot = book.get_snapshot()
        assert len(snapshot.bid_levels) == 2
        assert len(snapshot.ask_levels) == 1

    def test_book_validation(self):
        """Test order book validation."""
        book = OrderBook()

        # Empty book should be valid
        assert book.is_valid_book()

        # Add normal orders
        book.process_operation(
            timestamp=1609459200000000000,
            mdt=OrderBook.MDT_BID,
            price=100.0,
            volume=1000,
            operation=OrderBook.OP_ADD,
        )

        book.process_operation(
            timestamp=1609459200000000001,
            mdt=OrderBook.MDT_ASK,
            price=100.25,
            volume=500,
            operation=OrderBook.OP_ADD,
        )

        assert book.is_valid_book()

        # Manually create crossed book for testing
        book._bid_levels[Decimal("100.50")] = OrderBookLevel(
            price=Decimal("100.50"), volume=1000
        )
        book._bid_prices.insert(0, Decimal("100.50"))

        assert not book.is_valid_book()

    def test_get_analytics(self):
        """Test comprehensive analytics calculation."""
        book = OrderBook()

        # Add multiple levels
        bid_prices = [100.0, 99.75, 99.50]
        ask_prices = [100.25, 100.50, 100.75]

        for i, price in enumerate(bid_prices):
            book.process_operation(
                timestamp=1609459200000000000 + i,
                mdt=OrderBook.MDT_BID,
                price=price,
                volume=1000 * (i + 1),
                operation=OrderBook.OP_ADD,
            )

        for i, price in enumerate(ask_prices):
            book.process_operation(
                timestamp=1609459200000000000 + i + 3,
                mdt=OrderBook.MDT_ASK,
                price=price,
                volume=500 * (i + 1),
                operation=OrderBook.OP_ADD,
            )

        analytics = book.get_analytics(depth=3)

        # Check basic metrics
        assert analytics["best_bid"] == Decimal("100.0")
        assert analytics["best_ask"] == Decimal("100.25")
        assert analytics["spread"] == Decimal("0.25")
        assert analytics["mid_price"] == Decimal("100.125")
        assert analytics["bid_levels"] == 3
        assert analytics["ask_levels"] == 3

        # Check volume metrics
        total_bid_volume = 1000 + 2000 + 3000  # 6000
        total_ask_volume = 500 + 1000 + 1500  # 3000

        assert analytics["bid_volume"] == total_bid_volume
        assert analytics["ask_volume"] == total_ask_volume
        assert analytics["total_volume"] == total_bid_volume + total_ask_volume

        # Check imbalance
        expected_imbalance = (total_bid_volume - total_ask_volume) / (
            total_bid_volume + total_ask_volume
        )
        assert abs(analytics["imbalance"] - expected_imbalance) < 0.001

        # Check operation counts
        assert analytics["operation_count"] == 6
        assert analytics["invalid_operations"] == 0
        assert analytics["error_rate"] == 0.0

    def test_repr(self):
        """Test string representation."""
        book = OrderBook()

        # Empty book
        repr_str = repr(book)
        assert "bids=0" in repr_str
        assert "asks=0" in repr_str
        assert "best_bid=None" in repr_str
        assert "best_ask=None" in repr_str

        # Add orders
        book.process_operation(
            timestamp=1609459200000000000,
            mdt=OrderBook.MDT_BID,
            price=100.0,
            volume=1000,
            operation=OrderBook.OP_ADD,
        )

        book.process_operation(
            timestamp=1609459200000000001,
            mdt=OrderBook.MDT_ASK,
            price=100.25,
            volume=500,
            operation=OrderBook.OP_ADD,
        )

        repr_str = repr(book)
        assert "bids=1" in repr_str
        assert "asks=1" in repr_str
        assert "best_bid=100.0" in repr_str
        assert "best_ask=100.25" in repr_str


class TestOrderBookReconstructor:
    """Test OrderBookReconstructor class."""

    def test_initialization(self):
        """Test reconstructor initialization."""
        reconstructor = OrderBookReconstructor(max_depth=5)
        assert reconstructor.max_depth == 5
        assert isinstance(reconstructor.order_book, OrderBook)

    def test_reconstruct_from_file(self):
        """Test reconstructing from file."""
        # Create test data
        test_data = pd.DataFrame(
            {
                "level": ["2", "2", "2", "2"],
                "timestamp": [
                    1609459200000000000,
                    1609459200000000001,
                    1609459200000000002,
                    1609459200000000003,
                ],
                "mdt": [
                    OrderBook.MDT_BID,
                    OrderBook.MDT_ASK,
                    OrderBook.MDT_BID,
                    OrderBook.MDT_ASK,
                ],
                "price": [100.0, 100.25, 99.75, 100.50],
                "volume": [1000, 500, 750, 250],
                "operation": [
                    OrderBook.OP_ADD,
                    OrderBook.OP_ADD,
                    OrderBook.OP_ADD,
                    OrderBook.OP_ADD,
                ],
            }
        )

        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tmp_file:
            test_data.to_parquet(tmp_file.name)

            reconstructor = OrderBookReconstructor()
            snapshot = reconstructor.reconstruct_from_file(tmp_file.name)

            # Verify reconstruction
            assert snapshot.best_bid.price == Decimal("100.0")
            assert snapshot.best_ask.price == Decimal("100.25")
            assert len(snapshot.bid_levels) == 2
            assert len(snapshot.ask_levels) == 2

            # Clean up
            Path(tmp_file.name).unlink()

    def test_reconstruct_with_timestamp_filter(self):
        """Test reconstructing up to specific timestamp."""
        # Create test data
        test_data = pd.DataFrame(
            {
                "level": ["2", "2", "2", "2"],
                "timestamp": [
                    1609459200000000000,
                    1609459200000000001,
                    1609459200000000002,
                    1609459200000000003,
                ],
                "mdt": [
                    OrderBook.MDT_BID,
                    OrderBook.MDT_ASK,
                    OrderBook.MDT_BID,
                    OrderBook.MDT_ASK,
                ],
                "price": [100.0, 100.25, 99.75, 100.50],
                "volume": [1000, 500, 750, 250],
                "operation": [
                    OrderBook.OP_ADD,
                    OrderBook.OP_ADD,
                    OrderBook.OP_ADD,
                    OrderBook.OP_ADD,
                ],
            }
        )

        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tmp_file:
            test_data.to_parquet(tmp_file.name)

            reconstructor = OrderBookReconstructor()
            # Only process first two operations
            target_timestamp = 1609459200000000001
            snapshot = reconstructor.reconstruct_from_file(
                tmp_file.name, target_timestamp
            )

            # Should only have one bid and one ask
            assert len(snapshot.bid_levels) == 1
            assert len(snapshot.ask_levels) == 1
            assert snapshot.best_bid.price == Decimal("100.0")
            assert snapshot.best_ask.price == Decimal("100.25")

            # Clean up
            Path(tmp_file.name).unlink()

    def test_reconstruct_time_series(self):
        """Test time series reconstruction."""
        # Create test data over 3 seconds
        test_data = pd.DataFrame(
            {
                "level": ["2"] * 6,
                "timestamp": [
                    1609459200000000000,  # t=0
                    1609459200500000000,  # t=0.5s
                    1609459201000000000,  # t=1s
                    1609459201500000000,  # t=1.5s
                    1609459202000000000,  # t=2s
                    1609459202500000000,  # t=2.5s
                ],
                "mdt": [
                    OrderBook.MDT_BID,
                    OrderBook.MDT_ASK,
                    OrderBook.MDT_BID,
                    OrderBook.MDT_ASK,
                    OrderBook.MDT_BID,
                    OrderBook.MDT_ASK,
                ],
                "price": [100.0, 100.25, 99.75, 100.50, 99.50, 100.75],
                "volume": [1000, 500, 750, 250, 500, 300],
                "operation": [OrderBook.OP_ADD] * 6,
            }
        )

        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tmp_file:
            test_data.to_parquet(tmp_file.name)

            reconstructor = OrderBookReconstructor()
            snapshots = reconstructor.reconstruct_time_series(
                tmp_file.name,
                start_time=1609459200000000000,
                end_time=1609459202000000000,
                interval_ns=1_000_000_000,  # 1 second
            )

            # Should have 3 snapshots (t=0, t=1, t=2)
            assert len(snapshots) == 3

            # Check progression
            assert len(snapshots[0].bid_levels) == 1  # Only first bid
            assert len(snapshots[1].bid_levels) == 2  # Two bids by t=1
            assert len(snapshots[2].bid_levels) == 3  # Three bids by t=2

            # Clean up
            Path(tmp_file.name).unlink()


class TestIntegration:
    """Integration tests for order book system."""

    def test_realistic_book_scenario(self):
        """Test realistic order book scenario."""
        book = OrderBook(max_depth=5)

        # Simulate realistic market scenario
        operations = [
            # Initial book setup
            (1609459200000000000, OrderBook.MDT_BID, 100.00, 1000, OrderBook.OP_ADD),
            (1609459200000000001, OrderBook.MDT_BID, 99.75, 750, OrderBook.OP_ADD),
            (1609459200000000002, OrderBook.MDT_ASK, 100.25, 500, OrderBook.OP_ADD),
            (1609459200000000003, OrderBook.MDT_ASK, 100.50, 300, OrderBook.OP_ADD),
            # Market order consumes best bid
            (1609459200000000004, OrderBook.MDT_BID, 100.00, 0, OrderBook.OP_REMOVE),
            # New best bid
            (1609459200000000005, OrderBook.MDT_BID, 99.90, 800, OrderBook.OP_ADD),
            # Update ask volume
            (1609459200000000006, OrderBook.MDT_ASK, 100.25, 800, OrderBook.OP_UPDATE),
            # Add deeper levels
            (1609459200000000007, OrderBook.MDT_BID, 99.50, 500, OrderBook.OP_ADD),
            (1609459200000000008, OrderBook.MDT_ASK, 100.75, 400, OrderBook.OP_ADD),
        ]

        # Process all operations
        for timestamp, mdt, price, volume, operation in operations:
            success = book.process_operation(timestamp, mdt, price, volume, operation)
            assert success

        # Verify final state
        assert book.is_valid_book()

        best_bid = book.get_best_bid()
        best_ask = book.get_best_ask()

        assert best_bid.price == Decimal("99.90")
        assert best_ask.price == Decimal("100.25")
        assert book.get_spread() == Decimal("0.35")

        # Check analytics
        analytics = book.get_analytics()
        assert analytics["bid_levels"] == 3
        assert analytics["ask_levels"] == 3
        assert analytics["error_rate"] == 0.0

        # Check imbalance (should be slightly bid-heavy)
        assert analytics["imbalance"] > 0

    def test_market_stress_scenario(self):
        """Test order book under market stress."""
        book = OrderBook(max_depth=10)

        # Simulate rapid fire operations
        timestamp = 1609459200000000000

        # Build initial book
        for i in range(10):
            # Bids from 100.00 down to 99.25 (0.25 increment)
            bid_price = 100.00 - i * 0.05
            book.process_operation(
                timestamp + i, OrderBook.MDT_BID, bid_price, 1000, OrderBook.OP_ADD
            )

            # Asks from 100.25 up to 101.50 (0.25 increment)
            ask_price = 100.25 + i * 0.05
            book.process_operation(
                timestamp + i + 10, OrderBook.MDT_ASK, ask_price, 500, OrderBook.OP_ADD
            )

        # Verify deep book
        snapshot = book.get_snapshot()
        assert len(snapshot.bid_levels) == 10
        assert len(snapshot.ask_levels) == 10

        # Market order simulation - consume top 3 levels
        for i in range(3):
            price = 100.00 - i * 0.05
            book.process_operation(
                timestamp + 100 + i, OrderBook.MDT_BID, price, 0, OrderBook.OP_REMOVE
            )

        # Verify book integrity after removals
        assert book.is_valid_book()
        snapshot = book.get_snapshot()
        assert len(snapshot.bid_levels) == 7
        assert snapshot.best_bid.price == Decimal("99.85")  # 4th level becomes best

        # Check analytics are still reasonable
        analytics = book.get_analytics()
        assert analytics["error_rate"] == 0.0
        assert analytics["best_bid"] == Decimal("99.85")
        assert analytics["best_ask"] == Decimal("100.25")

    def test_edge_case_handling(self):
        """Test various edge cases."""
        book = OrderBook()

        # Try to update non-existent level
        success = book.process_operation(
            timestamp=1609459200000000000,
            mdt=OrderBook.MDT_BID,
            price=100.0,
            volume=1000,
            operation=OrderBook.OP_UPDATE,
        )
        # Should succeed by adding instead
        assert success
        assert book.get_best_bid().volume == 1000

        # Try to remove non-existent level
        success = book.process_operation(
            timestamp=1609459200000000001,
            mdt=OrderBook.MDT_BID,
            price=99.0,
            volume=0,
            operation=OrderBook.OP_REMOVE,
        )
        # Should fail gracefully
        assert not success

        # Try to add at existing price level
        success = book.process_operation(
            timestamp=1609459200000000002,
            mdt=OrderBook.MDT_BID,
            price=100.0,
            volume=2000,
            operation=OrderBook.OP_ADD,
        )
        # Should succeed by updating instead
        assert success
        assert book.get_best_bid().volume == 2000

        # Book should still be valid
        assert book.is_valid_book()

    def test_performance_counters(self):
        """Test performance monitoring counters."""
        book = OrderBook()

        # Process valid operations
        for i in range(10):
            book.process_operation(
                timestamp=1609459200000000000 + i,
                mdt=OrderBook.MDT_BID,
                price=100.0 - i * 0.25,
                volume=1000,
                operation=OrderBook.OP_ADD,
            )

        # Process some invalid operations
        book.process_operation(
            1609459200000000000, -1, 100.0, 1000, OrderBook.OP_ADD
        )  # Invalid MDT
        book.process_operation(
            1609459200000000000, OrderBook.MDT_BID, -100.0, 1000, OrderBook.OP_ADD
        )  # Invalid price

        analytics = book.get_analytics()
        assert analytics["operation_count"] == 12
        assert analytics["invalid_operations"] == 2
        assert analytics["error_rate"] == 2.0 / 12.0
