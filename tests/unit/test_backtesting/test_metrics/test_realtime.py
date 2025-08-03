"""Tests for real-time metrics aggregation."""

from decimal import Decimal
from unittest.mock import Mock

import pandas as pd
import pytest

from strategy_lab.backtesting.metrics.realtime import MetricsAggregator, RealtimeMetrics


class TestRealtimeMetrics:
    """Test RealtimeMetrics class functionality."""

    def test_initialization(self):
        """Test metrics initialization."""
        metrics = RealtimeMetrics(
            starting_equity=Decimal("100000"),
            current_equity=Decimal("100000"),
            peak_equity=Decimal("100000"),
        )

        assert metrics.starting_equity == Decimal("100000")
        assert metrics.current_equity == Decimal("100000")
        assert metrics.peak_equity == Decimal("100000")
        assert metrics.current_drawdown == Decimal("0")
        assert len(metrics.open_trades) == 0
        assert len(metrics.completed_trades) == 0


class TestMetricsAggregator:
    """Test MetricsAggregator functionality."""

    def test_initialization(self):
        """Test aggregator initialization."""
        aggregator = MetricsAggregator(
            starting_equity=Decimal("50000"), update_frequency=50
        )

        assert aggregator.metrics.starting_equity == Decimal("50000")
        assert aggregator.metrics.current_equity == Decimal("50000")
        assert aggregator.metrics.update_frequency == 50

    def test_open_trade(self):
        """Test opening a trade."""
        aggregator = MetricsAggregator()

        aggregator.open_trade(
            trade_id=1,
            entry_price=Decimal("100.00"),
            quantity=10,
            entry_time=pd.Timestamp("2024-01-01 10:00:00"),
            side="BUY",
        )

        assert 1 in aggregator.metrics.open_trades
        trade = aggregator.metrics.open_trades[1]
        assert trade.entry_price == Decimal("100.00")
        assert trade.quantity == 10
        assert trade.side == "BUY"

    def test_close_trade_not_found(self):
        """Test closing a non-existent trade."""
        aggregator = MetricsAggregator()

        result = aggregator.close_trade(
            trade_id=999,
            exit_price=Decimal("105.00"),
            exit_time=pd.Timestamp("2024-01-01 11:00:00"),
        )

        assert result is None

    def test_close_winning_trade(self):
        """Test closing a winning trade."""
        aggregator = MetricsAggregator(starting_equity=Decimal("100000"))

        # Open trade
        aggregator.open_trade(
            trade_id=1,
            entry_price=Decimal("100.00"),
            quantity=10,
            entry_time=pd.Timestamp("2024-01-01 10:00:00"),
            side="BUY",
        )

        # Close with profit
        trade = aggregator.close_trade(
            trade_id=1,
            exit_price=Decimal("105.00"),
            exit_time=pd.Timestamp("2024-01-01 11:00:00"),
            commission=Decimal("2.00"),
        )

        assert trade is not None
        assert trade.pnl == Decimal("48.00")  # (105-100)*10 - 2
        assert aggregator.metrics.current_equity == Decimal("100048.00")
        assert len(aggregator.metrics.completed_trades) == 1
        assert 1 not in aggregator.metrics.open_trades

    def test_close_losing_trade(self):
        """Test closing a losing trade."""
        aggregator = MetricsAggregator(starting_equity=Decimal("100000"))

        # Open trade
        aggregator.open_trade(
            trade_id=1,
            entry_price=Decimal("100.00"),
            quantity=10,
            entry_time=pd.Timestamp("2024-01-01 10:00:00"),
            side="BUY",
        )

        # Close with loss
        trade = aggregator.close_trade(
            trade_id=1,
            exit_price=Decimal("95.00"),
            exit_time=pd.Timestamp("2024-01-01 11:00:00"),
            commission=Decimal("2.00"),
        )

        assert trade.pnl == Decimal("-52.00")  # (95-100)*10 - 2
        assert aggregator.metrics.current_equity == Decimal("99948.00")

    def test_drawdown_tracking(self):
        """Test drawdown calculation during trading."""
        aggregator = MetricsAggregator(starting_equity=Decimal("100000"))

        # First trade - profit
        aggregator.open_trade(
            1, Decimal("100.00"), 10, pd.Timestamp("2024-01-01"), "BUY"
        )
        aggregator.close_trade(1, Decimal("110.00"), pd.Timestamp("2024-01-01"))

        assert aggregator.metrics.current_equity == Decimal("100100.00")
        assert aggregator.metrics.peak_equity == Decimal("100100.00")
        assert aggregator.metrics.current_drawdown == Decimal("0")

        # Second trade - loss
        aggregator.open_trade(
            2, Decimal("110.00"), 10, pd.Timestamp("2024-01-02"), "BUY"
        )
        aggregator.close_trade(2, Decimal("105.00"), pd.Timestamp("2024-01-02"))

        assert aggregator.metrics.current_equity == Decimal("100050.00")
        assert aggregator.metrics.peak_equity == Decimal("100100.00")
        # Drawdown: (100100 - 100050) / 100100 = 0.0004995...
        assert (
            pytest.approx(float(aggregator.metrics.current_drawdown), rel=1e-3)
            == 0.0004995
        )

    def test_quick_update(self):
        """Test quick metric updates."""
        aggregator = MetricsAggregator(update_frequency=100)

        # Open and close a trade
        aggregator.open_trade(
            1, Decimal("100.00"), 10, pd.Timestamp("2024-01-01"), "BUY"
        )
        aggregator.close_trade(1, Decimal("105.00"), pd.Timestamp("2024-01-01"))

        # Should do quick update (not full recalculation)
        assert aggregator.metrics.trades_since_update == 1
        assert aggregator.metrics.performance.total_trades == 1
        assert aggregator.metrics.performance.winning_trades == 1
        assert aggregator.metrics.trade_stats.win_rate == Decimal("100.0")

    def test_full_update_trigger(self):
        """Test triggering full metrics update."""
        aggregator = MetricsAggregator(update_frequency=2)

        # First trade - quick update
        aggregator.open_trade(
            1, Decimal("100.00"), 10, pd.Timestamp("2024-01-01"), "BUY"
        )
        aggregator.close_trade(1, Decimal("105.00"), pd.Timestamp("2024-01-01"))
        assert aggregator.metrics.trades_since_update == 1

        # Second trade - should trigger full update
        aggregator.open_trade(
            2, Decimal("105.00"), 10, pd.Timestamp("2024-01-02"), "BUY"
        )
        aggregator.close_trade(2, Decimal("110.00"), pd.Timestamp("2024-01-02"))
        assert aggregator.metrics.trades_since_update == 0  # Reset after full update

    def test_callbacks(self):
        """Test callback functionality."""
        # Create mocks for callbacks
        on_trade_complete = Mock()
        on_equity_update = Mock()
        on_metrics_update = Mock()

        aggregator = MetricsAggregator(update_frequency=1)
        aggregator.metrics.on_trade_complete = on_trade_complete
        aggregator.metrics.on_equity_update = on_equity_update
        aggregator.metrics.on_metrics_update = on_metrics_update

        # Open and close trade
        aggregator.open_trade(
            1, Decimal("100.00"), 10, pd.Timestamp("2024-01-01"), "BUY"
        )
        trade = aggregator.close_trade(1, Decimal("105.00"), pd.Timestamp("2024-01-01"))

        # Verify callbacks were called
        on_trade_complete.assert_called_once_with(trade)
        on_equity_update.assert_called_once()
        on_metrics_update.assert_called_once()

    def test_get_summary(self):
        """Test getting metrics summary."""
        aggregator = MetricsAggregator(starting_equity=Decimal("100000"))

        # Execute some trades
        aggregator.open_trade(
            1, Decimal("100.00"), 10, pd.Timestamp("2024-01-01"), "BUY"
        )
        aggregator.close_trade(1, Decimal("105.00"), pd.Timestamp("2024-01-01"))

        aggregator.open_trade(
            2, Decimal("105.00"), 10, pd.Timestamp("2024-01-02"), "BUY"
        )
        aggregator.close_trade(2, Decimal("103.00"), pd.Timestamp("2024-01-02"))

        summary = aggregator.get_summary()

        assert "total_pnl" in summary
        assert "total_trades" in summary
        assert "win_rate" in summary
        assert "profit_factor" in summary
        assert "max_drawdown" in summary
        assert "sharpe_ratio" in summary
        assert "current_equity" in summary
        assert "open_trades" in summary

        assert summary["total_trades"] == 2
        assert summary["win_rate"] == 50.0  # 1 win, 1 loss

    def test_reset(self):
        """Test resetting metrics."""
        aggregator = MetricsAggregator(starting_equity=Decimal("100000"))

        # Execute a trade
        aggregator.open_trade(
            1, Decimal("100.00"), 10, pd.Timestamp("2024-01-01"), "BUY"
        )
        aggregator.close_trade(1, Decimal("105.00"), pd.Timestamp("2024-01-01"))

        # Verify state changed
        assert aggregator.metrics.current_equity != Decimal("100000")
        assert len(aggregator.metrics.completed_trades) > 0

        # Reset
        aggregator.reset()

        # Verify reset to initial state
        assert aggregator.metrics.current_equity == Decimal("100000")
        assert len(aggregator.metrics.completed_trades) == 0
        assert len(aggregator.metrics.open_trades) == 0

    def test_multiple_open_trades(self):
        """Test handling multiple open trades."""
        aggregator = MetricsAggregator()

        # Open multiple trades
        aggregator.open_trade(
            1, Decimal("100.00"), 10, pd.Timestamp("2024-01-01"), "BUY"
        )
        aggregator.open_trade(
            2, Decimal("101.00"), 5, pd.Timestamp("2024-01-01"), "SELL"
        )
        aggregator.open_trade(
            3, Decimal("102.00"), 15, pd.Timestamp("2024-01-01"), "BUY"
        )

        assert len(aggregator.metrics.open_trades) == 3

        # Close in different order
        aggregator.close_trade(2, Decimal("100.00"), pd.Timestamp("2024-01-02"))
        assert len(aggregator.metrics.open_trades) == 2

        aggregator.close_trade(1, Decimal("105.00"), pd.Timestamp("2024-01-02"))
        assert len(aggregator.metrics.open_trades) == 1

        aggregator.close_trade(3, Decimal("104.00"), pd.Timestamp("2024-01-02"))
        assert len(aggregator.metrics.open_trades) == 0
        assert len(aggregator.metrics.completed_trades) == 3
