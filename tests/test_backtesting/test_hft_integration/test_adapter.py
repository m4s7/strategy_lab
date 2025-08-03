"""Tests for HftBacktestAdapter class."""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.strategy_lab.backtesting.hft_integration.adapter import (
    BacktestResults,
    HftBacktestAdapter,
    create_simple_strategy_adapter,
    example_mean_reversion_strategy,
    run_simple_backtest,
)
from src.strategy_lab.backtesting.hft_integration.config import create_testing_config
from src.strategy_lab.backtesting.hft_integration.data_feed import TickData
from src.strategy_lab.backtesting.hft_integration.event_processor import OrderSide


class TestBacktestResults:
    """Test BacktestResults class functionality."""

    def test_backtest_results_creation(self):
        """Test basic results creation."""
        results = BacktestResults(
            start_time=100.0,
            end_time=105.0,
            total_trades=10,
            total_volume=50,
            gross_pnl=100.0,
            net_pnl=90.0,
            total_commission=10.0,
            max_drawdown=25.0,
            sharpe_ratio=1.5,
            win_rate=60.0,
            avg_trade_duration=2.5,
            feed_stats={},
            event_stats={},
            positions={},
        )

        assert results.start_time == 100.0
        assert results.end_time == 105.0
        assert results.total_trades == 10
        assert results.net_pnl == 90.0

    def test_duration_seconds(self):
        """Test duration calculation."""
        results = BacktestResults(
            start_time=100.0,
            end_time=105.0,
            total_trades=0,
            total_volume=0,
            gross_pnl=0.0,
            net_pnl=0.0,
            total_commission=0.0,
            max_drawdown=0.0,
            sharpe_ratio=0.0,
            win_rate=0.0,
            avg_trade_duration=0.0,
            feed_stats={},
            event_stats={},
            positions={},
        )

        assert results.duration_seconds == 5.0

    def test_return_percent(self):
        """Test return percentage calculation."""
        results = BacktestResults(
            start_time=100.0,
            end_time=105.0,
            total_trades=0,
            total_volume=0,
            gross_pnl=0.0,
            net_pnl=5000.0,  # $5000 profit
            total_commission=0.0,
            max_drawdown=0.0,
            sharpe_ratio=0.0,
            win_rate=0.0,
            avg_trade_duration=0.0,
            feed_stats={},
            event_stats={},
            positions={},
        )

        # Default initial capital is $50,000, so $5,000 profit = 10%
        assert results.return_percent == 10.0


class TestHftBacktestAdapter:
    """Test HftBacktestAdapter class functionality."""

    def test_adapter_creation(self):
        """Test basic adapter creation."""
        config = create_testing_config()
        adapter = HftBacktestAdapter(config)

        assert adapter.config == config
        assert adapter.data_directory == Path("./data/MNQ")
        assert adapter.strategy_callback is None
        assert adapter._is_running is False
        assert adapter._current_timestamp == 0
        assert adapter._current_price == 0.0

    def test_adapter_creation_with_custom_directory(self):
        """Test adapter creation with custom data directory."""
        config = create_testing_config()
        custom_dir = Path("/custom/data/path")
        adapter = HftBacktestAdapter(config, data_directory=custom_dir)

        assert adapter.data_directory == custom_dir

    def test_set_strategy_callback(self):
        """Test setting strategy callback."""
        config = create_testing_config()
        adapter = HftBacktestAdapter(config)

        def dummy_strategy(tick):
            pass

        adapter.set_strategy_callback(dummy_strategy)
        assert adapter.strategy_callback == dummy_strategy

    def test_set_fill_callback(self):
        """Test setting fill callback."""
        config = create_testing_config()
        adapter = HftBacktestAdapter(config)

        def dummy_fill_handler(fill):
            pass

        adapter.set_fill_callback(dummy_fill_handler)
        assert adapter.on_fill_callback == dummy_fill_handler
        assert adapter.event_processor.on_order_filled == dummy_fill_handler

    def test_submit_market_order_when_not_running(self):
        """Test submitting market order when backtest not running."""
        config = create_testing_config()
        adapter = HftBacktestAdapter(config)

        with pytest.raises(RuntimeError, match="Backtest not running"):
            adapter.submit_market_order(OrderSide.BUY, 5)

    def test_submit_market_order_when_running(self):
        """Test submitting market order when backtest is running."""
        config = create_testing_config()
        adapter = HftBacktestAdapter(config)

        # Simulate running state
        adapter._is_running = True
        adapter._current_timestamp = 1609459200000000000
        adapter._current_price = 13000.25

        order_id = adapter.submit_market_order(OrderSide.BUY, 5)

        assert isinstance(order_id, int)
        assert order_id > 0

        # Check that order was processed
        assert len(adapter.event_processor.orders) == 1
        assert len(adapter.event_processor.fills) == 1  # Should be immediately filled

    def test_submit_limit_order_when_running(self):
        """Test submitting limit order when backtest is running."""
        config = create_testing_config()
        adapter = HftBacktestAdapter(config)

        # Simulate running state
        adapter._is_running = True
        adapter._current_timestamp = 1609459200000000000

        order_id = adapter.submit_limit_order(OrderSide.BUY, 5, 13000.25)

        assert isinstance(order_id, int)
        assert order_id > 0

        # Check that order was created (but not filled automatically for limit order)
        assert len(adapter.event_processor.orders) == 1
        order = adapter.event_processor.orders[order_id]
        assert order.price == 13000.25

    def test_cancel_order(self):
        """Test canceling order."""
        config = create_testing_config()
        adapter = HftBacktestAdapter(config)

        # Simulate running state
        adapter._is_running = True
        adapter._current_timestamp = 1609459200000000000

        # Submit limit order
        order_id = adapter.submit_limit_order(OrderSide.BUY, 5, 13000.25)

        # Cancel order
        success = adapter.cancel_order(order_id)

        assert success is True

    def test_get_current_position(self):
        """Test getting current position."""
        config = create_testing_config()
        adapter = HftBacktestAdapter(config)

        position_info = adapter.get_current_position()

        assert "quantity" in position_info
        assert "average_price" in position_info
        assert "market_value" in position_info
        assert "unrealized_pnl" in position_info
        assert "realized_pnl" in position_info
        assert "is_long" in position_info
        assert "is_short" in position_info
        assert "is_flat" in position_info

        # Initially should be flat
        assert position_info["is_flat"] is True

    @patch("src.strategy_lab.backtesting.hft_integration.adapter.DataPipeline")
    def test_run_backtest_without_strategy(self, mock_pipeline):
        """Test running backtest without strategy callback."""
        config = create_testing_config()
        adapter = HftBacktestAdapter(config)

        with pytest.raises(ValueError, match="Strategy callback required"):
            adapter.run_backtest("2021-01-01", "2021-01-02")

    @patch("src.strategy_lab.backtesting.hft_integration.adapter.DataPipeline")
    def test_run_backtest_basic(self, mock_pipeline):
        """Test basic backtest execution."""
        config = create_testing_config()
        adapter = HftBacktestAdapter(config)

        # Mock data pipeline
        mock_instance = mock_pipeline.return_value
        mock_instance.process_date_range.return_value = [
            {
                "l1_data": MockDataFrame(
                    [
                        {
                            "timestamp": 1609459200000000000,
                            "price": 13000.25,
                            "qty": 5.0,
                            "side": 1,
                        }
                    ]
                )
            }
        ]

        # Set strategy callback
        strategy_calls = []

        def test_strategy(tick):
            strategy_calls.append(tick)

        adapter.set_strategy_callback(test_strategy)

        # Run backtest
        results = adapter.run_backtest("2021-01-01", "2021-01-02")

        assert isinstance(results, BacktestResults)
        assert len(strategy_calls) > 0  # Strategy should have been called
        assert adapter._is_running is False  # Should be stopped after completion

    def test_get_live_stats_when_not_running(self):
        """Test getting live stats when not running."""
        config = create_testing_config()
        adapter = HftBacktestAdapter(config)

        stats = adapter.get_live_stats()
        assert stats == {}

    def test_get_live_stats_when_running(self):
        """Test getting live stats when running."""
        config = create_testing_config()
        adapter = HftBacktestAdapter(config)

        # Simulate running state
        adapter._is_running = True
        adapter._current_timestamp = 1609459200000000000
        adapter._current_price = 13000.25

        stats = adapter.get_live_stats()

        assert "current_timestamp" in stats
        assert "current_price" in stats
        assert "current_position" in stats
        assert "open_orders" in stats
        assert "total_fills" in stats
        assert stats["current_timestamp"] == 1609459200000000000
        assert stats["current_price"] == 13000.25

    def test_reset(self):
        """Test resetting adapter state."""
        config = create_testing_config()
        adapter = HftBacktestAdapter(config)

        # Set some state
        adapter._current_timestamp = 1609459200000000000
        adapter._current_price = 13000.25
        adapter._is_running = True

        # Reset
        adapter.reset()

        assert adapter._current_timestamp == 0
        assert adapter._current_price == 0.0
        assert adapter._is_running is False
        assert adapter._backtest_results is None

    def test_export_results_without_results(self):
        """Test exporting results when no results exist."""
        config = create_testing_config()
        adapter = HftBacktestAdapter(config)

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "results.json"

            with pytest.raises(ValueError, match="No results to export"):
                adapter.export_results(output_path)

    def test_export_results_with_results(self):
        """Test exporting results when results exist."""
        config = create_testing_config()
        adapter = HftBacktestAdapter(config)

        # Create mock results
        adapter._backtest_results = BacktestResults(
            start_time=100.0,
            end_time=105.0,
            total_trades=5,
            total_volume=25,
            gross_pnl=50.0,
            net_pnl=45.0,
            total_commission=5.0,
            max_drawdown=10.0,
            sharpe_ratio=1.0,
            win_rate=80.0,
            avg_trade_duration=1.0,
            feed_stats={},
            event_stats={},
            positions={},
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "results.json"

            adapter.export_results(output_path)

            assert output_path.exists()

            # Verify exported data
            with open(output_path) as f:
                data = json.load(f)

            assert "config" in data
            assert "performance" in data
            assert data["performance"]["total_trades"] == 5
            assert data["performance"]["net_pnl"] == 45.0


class TestUtilityFunctions:
    """Test utility functions."""

    def test_create_simple_strategy_adapter_default_config(self):
        """Test creating simple adapter with default config."""
        adapter = create_simple_strategy_adapter()

        assert isinstance(adapter, HftBacktestAdapter)
        assert adapter.config.symbol == "MNQ"
        assert adapter.on_fill_callback is not None

    def test_create_simple_strategy_adapter_custom_config(self):
        """Test creating simple adapter with custom config."""
        config = create_testing_config()
        adapter = create_simple_strategy_adapter(config)

        assert adapter.config == config

    @patch(
        "src.strategy_lab.backtesting.hft_integration.adapter.create_simple_strategy_adapter"
    )
    def test_run_simple_backtest(self, mock_create_adapter):
        """Test running simple backtest."""
        # Mock adapter
        mock_adapter = Mock()
        mock_adapter.run_backtest.return_value = Mock(spec=BacktestResults)
        mock_create_adapter.return_value = mock_adapter

        # Define test strategy
        def test_strategy(tick, adapter):
            pass

        # Run backtest
        results = run_simple_backtest(test_strategy, "2021-01-01", "2021-01-02")

        # Verify adapter was configured correctly
        mock_adapter.set_strategy_callback.assert_called_once()
        mock_adapter.run_backtest.assert_called_once_with("2021-01-01", "2021-01-02")
        assert isinstance(results, Mock)  # Mock BacktestResults

    def test_example_mean_reversion_strategy(self):
        """Test example mean reversion strategy."""
        config = create_testing_config()
        adapter = HftBacktestAdapter(config)

        # Simulate running state
        adapter._is_running = True
        adapter._current_timestamp = 1609459200000000000
        adapter._current_price = 13000.25

        # Create test tick
        tick = TickData(timestamp=1609459200000000000, price=13000.25, qty=5.0, side=1)

        # Mock random to control strategy behavior
        with patch(
            "random.random", return_value=0.0005
        ):  # Low probability to trigger entry
            example_mean_reversion_strategy(tick, adapter)

        # Strategy should have potentially placed an order (depending on random)
        # This is hard to test deterministically due to randomness


# Helper class for mocking DataFrame
class MockDataFrame:
    """Mock DataFrame for testing."""

    def __init__(self, data):
        self.data = data
        self._index = 0

    def empty(self):
        return len(self.data) == 0

    @property
    def empty(self):
        return len(self.data) == 0

    def __len__(self):
        return len(self.data)

    def iterrows(self):
        for i, row in enumerate(self.data):
            yield i, MockRow(row)

    def memory_usage(self, deep=True):
        return MockSeries([100] * (len(self.data[0]) if self.data else 0))


class MockRow:
    """Mock DataFrame row."""

    def __init__(self, data):
        self.data = data

    def __getitem__(self, key):
        return self.data[key]

    def get(self, key, default=None):
        return self.data.get(key, default)


class MockSeries:
    """Mock pandas Series."""

    def __init__(self, data):
        self.data = data

    def sum(self):
        return sum(self.data)
