"""Tests for performance metrics calculations."""

from decimal import Decimal

import pandas as pd
import pytest

from strategy_lab.backtesting.metrics.performance import (
    PerformanceMetrics,
    Trade,
    calculate_cumulative_returns,
    calculate_pnl,
    calculate_returns,
)


class TestTrade:
    """Test Trade class functionality."""

    def test_trade_pnl_calculation_buy(self):
        """Test P&L calculation for buy trades."""
        trade = Trade(
            entry_price=Decimal("100.00"),
            exit_price=Decimal("105.00"),
            quantity=10,
            entry_time=pd.Timestamp("2024-01-01 10:00:00"),
            exit_time=pd.Timestamp("2024-01-01 11:00:00"),
            side="BUY",
            commission=Decimal("2.00"),
        )

        expected_pnl = (Decimal("105.00") - Decimal("100.00")) * 10 - Decimal("2.00")
        assert trade.pnl == expected_pnl
        assert trade.pnl == Decimal("48.00")

    def test_trade_pnl_calculation_sell(self):
        """Test P&L calculation for sell trades."""
        trade = Trade(
            entry_price=Decimal("100.00"),
            exit_price=Decimal("95.00"),
            quantity=10,
            entry_time=pd.Timestamp("2024-01-01 10:00:00"),
            exit_time=pd.Timestamp("2024-01-01 11:00:00"),
            side="SELL",
            commission=Decimal("2.00"),
        )

        expected_pnl = (Decimal("100.00") - Decimal("95.00")) * 10 - Decimal("2.00")
        assert trade.pnl == expected_pnl
        assert trade.pnl == Decimal("48.00")

    def test_trade_duration(self):
        """Test trade duration calculation."""
        trade = Trade(
            entry_price=Decimal("100.00"),
            exit_price=Decimal("105.00"),
            quantity=10,
            entry_time=pd.Timestamp("2024-01-01 10:00:00"),
            exit_time=pd.Timestamp("2024-01-01 11:30:00"),
            side="BUY",
        )

        assert trade.duration == pd.Timedelta(hours=1, minutes=30)


class TestPerformanceMetrics:
    """Test PerformanceMetrics class functionality."""

    def test_empty_metrics_initialization(self):
        """Test metrics initialization with default values."""
        metrics = PerformanceMetrics()

        assert metrics.total_pnl == Decimal("0")
        assert metrics.gross_profit == Decimal("0")
        assert metrics.gross_loss == Decimal("0")
        assert metrics.total_trades == 0
        assert metrics.win_rate == Decimal("0")
        assert metrics.profit_factor == Decimal("0")

    def test_profit_factor_calculation(self):
        """Test profit factor calculation."""
        metrics = PerformanceMetrics(
            gross_profit=Decimal("1000.00"), gross_loss=Decimal("500.00")
        )

        assert metrics.profit_factor == Decimal("2.0")

    def test_profit_factor_zero_loss(self):
        """Test profit factor with zero loss."""
        metrics = PerformanceMetrics(
            gross_profit=Decimal("1000.00"), gross_loss=Decimal("0")
        )

        assert metrics.profit_factor == Decimal("inf")

    def test_win_rate_calculation(self):
        """Test win rate calculation."""
        metrics = PerformanceMetrics(total_trades=10, winning_trades=6)

        assert metrics.win_rate == Decimal("60.0")

    def test_expectancy_calculation(self):
        """Test expectancy calculation."""
        metrics = PerformanceMetrics(total_pnl=Decimal("500.00"), total_trades=10)

        assert metrics.expectancy == Decimal("50.00")


class TestCalculatePnl:
    """Test calculate_pnl function."""

    def test_empty_trades(self):
        """Test P&L calculation with no trades."""
        metrics = calculate_pnl([])

        assert metrics.total_pnl == Decimal("0")
        assert metrics.total_trades == 0
        assert len(metrics.equity_curve) == 1  # Just starting equity

    def test_single_winning_trade(self):
        """Test P&L calculation with single winning trade."""
        trade = Trade(
            entry_price=Decimal("100.00"),
            exit_price=Decimal("110.00"),
            quantity=10,
            entry_time=pd.Timestamp("2024-01-01 10:00:00"),
            exit_time=pd.Timestamp("2024-01-01 11:00:00"),
            side="BUY",
            commission=Decimal("2.00"),
        )

        metrics = calculate_pnl([trade])

        assert metrics.total_pnl == Decimal("98.00")  # (110-100)*10 - 2
        assert metrics.gross_profit == Decimal("98.00")
        assert metrics.gross_loss == Decimal("0")
        assert metrics.winning_trades == 1
        assert metrics.losing_trades == 0
        assert metrics.total_trades == 1
        assert metrics.avg_win == Decimal("98.00")

    def test_single_losing_trade(self):
        """Test P&L calculation with single losing trade."""
        trade = Trade(
            entry_price=Decimal("100.00"),
            exit_price=Decimal("90.00"),
            quantity=10,
            entry_time=pd.Timestamp("2024-01-01 10:00:00"),
            exit_time=pd.Timestamp("2024-01-01 11:00:00"),
            side="BUY",
            commission=Decimal("2.00"),
        )

        metrics = calculate_pnl([trade])

        assert metrics.total_pnl == Decimal("-102.00")  # (90-100)*10 - 2
        assert metrics.gross_profit == Decimal("0")
        assert metrics.gross_loss == Decimal("102.00")
        assert metrics.winning_trades == 0
        assert metrics.losing_trades == 1
        assert metrics.avg_loss == Decimal("102.00")

    def test_multiple_trades(self):
        """Test P&L calculation with multiple trades."""
        trades = [
            Trade(
                entry_price=Decimal("100.00"),
                exit_price=Decimal("110.00"),
                quantity=10,
                entry_time=pd.Timestamp("2024-01-01 10:00:00"),
                exit_time=pd.Timestamp("2024-01-01 11:00:00"),
                side="BUY",
                commission=Decimal("2.00"),
            ),
            Trade(
                entry_price=Decimal("110.00"),
                exit_price=Decimal("105.00"),
                quantity=10,
                entry_time=pd.Timestamp("2024-01-01 12:00:00"),
                exit_time=pd.Timestamp("2024-01-01 13:00:00"),
                side="BUY",
                commission=Decimal("2.00"),
            ),
            Trade(
                entry_price=Decimal("105.00"),
                exit_price=Decimal("115.00"),
                quantity=5,
                entry_time=pd.Timestamp("2024-01-01 14:00:00"),
                exit_time=pd.Timestamp("2024-01-01 15:00:00"),
                side="BUY",
                commission=Decimal("1.00"),
            ),
        ]

        metrics = calculate_pnl(trades)

        # Trade 1: (110-100)*10 - 2 = 98
        # Trade 2: (105-110)*10 - 2 = -52
        # Trade 3: (115-105)*5 - 1 = 49
        # Total: 98 - 52 + 49 = 95

        assert metrics.total_pnl == Decimal("95.00")
        assert metrics.gross_profit == Decimal("147.00")  # 98 + 49
        assert metrics.gross_loss == Decimal("52.00")
        assert metrics.winning_trades == 2
        assert metrics.losing_trades == 1
        assert metrics.total_trades == 3
        assert metrics.commission_paid == Decimal("5.00")

    def test_daily_pnl_aggregation(self):
        """Test daily P&L aggregation."""
        trades = [
            Trade(
                entry_price=Decimal("100.00"),
                exit_price=Decimal("110.00"),
                quantity=10,
                entry_time=pd.Timestamp("2024-01-01 10:00:00"),
                exit_time=pd.Timestamp("2024-01-01 11:00:00"),
                side="BUY",
            ),
            Trade(
                entry_price=Decimal("110.00"),
                exit_price=Decimal("105.00"),
                quantity=10,
                entry_time=pd.Timestamp("2024-01-01 12:00:00"),
                exit_time=pd.Timestamp("2024-01-01 13:00:00"),
                side="BUY",
            ),
            Trade(
                entry_price=Decimal("105.00"),
                exit_price=Decimal("115.00"),
                quantity=5,
                entry_time=pd.Timestamp("2024-01-02 10:00:00"),
                exit_time=pd.Timestamp("2024-01-02 11:00:00"),
                side="BUY",
            ),
        ]

        metrics = calculate_pnl(trades)

        # Day 1: 100 - 50 = 50
        # Day 2: 50
        assert pd.Timestamp("2024-01-01").date() in metrics.daily_pnl
        assert pd.Timestamp("2024-01-02").date() in metrics.daily_pnl
        assert metrics.daily_pnl[pd.Timestamp("2024-01-01").date()] == Decimal("50.00")
        assert metrics.daily_pnl[pd.Timestamp("2024-01-02").date()] == Decimal("50.00")

    def test_equity_curve_generation(self):
        """Test equity curve generation."""
        trades = [
            Trade(
                entry_price=Decimal("100.00"),
                exit_price=Decimal("110.00"),
                quantity=10,
                entry_time=pd.Timestamp("2024-01-01 10:00:00"),
                exit_time=pd.Timestamp("2024-01-01 11:00:00"),
                side="BUY",
            ),
            Trade(
                entry_price=Decimal("110.00"),
                exit_price=Decimal("105.00"),
                quantity=10,
                entry_time=pd.Timestamp("2024-01-01 12:00:00"),
                exit_time=pd.Timestamp("2024-01-01 13:00:00"),
                side="BUY",
            ),
        ]

        metrics = calculate_pnl(trades)

        assert len(metrics.equity_curve) == 3  # Start + 2 trades
        assert metrics.equity_curve[0] == Decimal("0")  # Starting equity
        assert metrics.equity_curve[1] == Decimal("100.00")  # After first trade
        assert metrics.equity_curve[2] == Decimal("50.00")  # After second trade


class TestCalculateReturns:
    """Test returns calculation functions."""

    def test_empty_equity_curve(self):
        """Test returns calculation with empty equity curve."""
        returns = calculate_returns([], [])
        assert len(returns) == 0

    def test_single_value_equity_curve(self):
        """Test returns calculation with single value."""
        returns = calculate_returns([Decimal("100000")], [pd.Timestamp("2024-01-01")])
        assert len(returns) == 0

    def test_daily_returns_calculation(self):
        """Test daily returns calculation."""
        equity_curve = [
            Decimal("100000"),
            Decimal("101000"),
            Decimal("99000"),
            Decimal("102000"),
        ]
        timestamps = [
            pd.Timestamp("2024-01-01 10:00:00"),
            pd.Timestamp("2024-01-01 15:00:00"),
            pd.Timestamp("2024-01-02 10:00:00"),
            pd.Timestamp("2024-01-03 10:00:00"),
        ]

        returns = calculate_returns(equity_curve, timestamps, period="D")

        assert len(returns) == 2  # 3 days - 1
        # Day 1 to Day 2: (99000 - 101000) / 101000 = -0.0198019...
        assert pytest.approx(returns.iloc[0], rel=1e-3) == -0.01980198
        # Day 2 to Day 3: (102000 - 99000) / 99000 = 0.030303...
        assert pytest.approx(returns.iloc[1], rel=1e-3) == 0.030303

    def test_cumulative_returns(self):
        """Test cumulative returns calculation."""
        returns = pd.Series([0.01, -0.02, 0.03, -0.01])
        cum_returns = calculate_cumulative_returns(returns)

        assert len(cum_returns) == 4
        assert pytest.approx(cum_returns.iloc[0]) == 0.01
        assert pytest.approx(cum_returns.iloc[1]) == -0.0102
        assert pytest.approx(cum_returns.iloc[2], rel=1e-3) == 0.019494
        assert pytest.approx(cum_returns.iloc[3], rel=1e-3) == 0.009299
