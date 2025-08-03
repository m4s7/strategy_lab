"""Tests for trade analysis and statistics."""

from decimal import Decimal

import pandas as pd

from strategy_lab.backtesting.metrics.performance import Trade
from strategy_lab.backtesting.metrics.trade_analysis import (
    TradeStatistics,
    analyze_trade_distribution,
    analyze_trades,
    calculate_profit_factor,
    calculate_win_rate,
    find_best_worst_periods,
)


def create_sample_trades():
    """Create sample trades for testing."""
    return [
        Trade(
            entry_price=Decimal("100.00"),
            exit_price=Decimal("105.00"),
            quantity=10,
            entry_time=pd.Timestamp("2024-01-01 09:00:00"),
            exit_time=pd.Timestamp("2024-01-01 10:00:00"),
            side="BUY",
        ),
        Trade(
            entry_price=Decimal("105.00"),
            exit_price=Decimal("103.00"),
            quantity=10,
            entry_time=pd.Timestamp("2024-01-01 11:00:00"),
            exit_time=pd.Timestamp("2024-01-01 12:00:00"),
            side="BUY",
        ),
        Trade(
            entry_price=Decimal("103.00"),
            exit_price=Decimal("107.00"),
            quantity=5,
            entry_time=pd.Timestamp("2024-01-02 09:00:00"),
            exit_time=pd.Timestamp("2024-01-02 10:30:00"),
            side="BUY",
        ),
        Trade(
            entry_price=Decimal("107.00"),
            exit_price=Decimal("107.00"),
            quantity=10,
            entry_time=pd.Timestamp("2024-01-02 14:00:00"),
            exit_time=pd.Timestamp("2024-01-02 14:30:00"),
            side="BUY",
        ),
    ]


class TestTradeStatistics:
    """Test TradeStatistics class functionality."""

    def test_empty_statistics(self):
        """Test statistics initialization with default values."""
        stats = TradeStatistics()

        assert stats.total_trades == 0
        assert stats.win_rate == Decimal("0")
        assert stats.profit_factor == Decimal("0")
        assert stats.max_consecutive_wins == 0
        assert stats.max_consecutive_losses == 0


class TestAnalyzeTrades:
    """Test analyze_trades function."""

    def test_empty_trades(self):
        """Test analysis with no trades."""
        stats = analyze_trades([])

        assert stats.total_trades == 0
        assert stats.winning_trades == 0
        assert stats.losing_trades == 0

    def test_basic_statistics(self):
        """Test basic trade statistics calculation."""
        trades = create_sample_trades()
        stats = analyze_trades(trades)

        assert stats.total_trades == 4
        assert stats.winning_trades == 2  # Trades 1 and 3
        assert stats.losing_trades == 1  # Trade 2
        assert stats.breakeven_trades == 1  # Trade 4

        # Win rate: 2/4 = 50%
        assert stats.win_rate == Decimal("50.0")

    def test_pnl_statistics(self):
        """Test P&L-related statistics."""
        trades = create_sample_trades()
        stats = analyze_trades(trades)

        # Trade 1: +50, Trade 2: -20, Trade 3: +20, Trade 4: 0
        assert stats.avg_win == Decimal("35.0")  # (50 + 20) / 2
        assert stats.avg_loss == Decimal("20.0")  # 20 / 1
        assert stats.avg_trade == Decimal("12.5")  # 50 / 4

        # Profit factor: 70 / 20 = 3.5
        assert stats.profit_factor == Decimal("3.5")

        # Win/loss ratio: 35 / 20 = 1.75
        assert stats.win_loss_ratio == Decimal("1.75")

    def test_consecutive_trades(self):
        """Test consecutive win/loss tracking."""
        trades = [
            # 3 consecutive wins
            Trade(
                entry_price=Decimal("100"),
                exit_price=Decimal("101"),
                quantity=1,
                entry_time=pd.Timestamp("2024-01-01"),
                exit_time=pd.Timestamp("2024-01-01"),
                side="BUY",
            ),
            Trade(
                entry_price=Decimal("100"),
                exit_price=Decimal("101"),
                quantity=1,
                entry_time=pd.Timestamp("2024-01-02"),
                exit_time=pd.Timestamp("2024-01-02"),
                side="BUY",
            ),
            Trade(
                entry_price=Decimal("100"),
                exit_price=Decimal("101"),
                quantity=1,
                entry_time=pd.Timestamp("2024-01-03"),
                exit_time=pd.Timestamp("2024-01-03"),
                side="BUY",
            ),
            # 2 consecutive losses
            Trade(
                entry_price=Decimal("100"),
                exit_price=Decimal("99"),
                quantity=1,
                entry_time=pd.Timestamp("2024-01-04"),
                exit_time=pd.Timestamp("2024-01-04"),
                side="BUY",
            ),
            Trade(
                entry_price=Decimal("100"),
                exit_price=Decimal("99"),
                quantity=1,
                entry_time=pd.Timestamp("2024-01-05"),
                exit_time=pd.Timestamp("2024-01-05"),
                side="BUY",
            ),
        ]

        stats = analyze_trades(trades)

        assert stats.max_consecutive_wins == 3
        assert stats.max_consecutive_losses == 2
        assert stats.current_streak == -2  # Currently on losing streak

    def test_duration_metrics(self):
        """Test trade duration calculations."""
        trades = create_sample_trades()
        stats = analyze_trades(trades)

        # Average duration should be calculated
        assert stats.avg_trade_duration > pd.Timedelta(0)
        assert stats.avg_winning_duration > pd.Timedelta(0)
        assert stats.avg_losing_duration > pd.Timedelta(0)

    def test_time_based_analysis(self):
        """Test hourly and daily trade analysis."""
        trades = create_sample_trades()
        stats = analyze_trades(trades)

        # Check hourly distribution (based on exit times)
        assert stats.trades_by_hour[10] == 2  # Two trades exit at 10:00 and 10:30
        assert stats.trades_by_hour[12] == 1  # One trade exits at 12:00
        assert stats.trades_by_hour[14] == 1  # One trade exits at 14:30

        # Check daily distribution
        assert stats.trades_by_day["Monday"] == 2  # 2024-01-01 is Monday
        assert stats.trades_by_day["Tuesday"] == 2  # 2024-01-02 is Tuesday

    def test_largest_trades(self):
        """Test tracking of largest win and loss."""
        trades = create_sample_trades()
        stats = analyze_trades(trades)

        assert stats.largest_win == Decimal("50.0")  # First trade
        assert stats.largest_loss == Decimal("20.0")  # Second trade


class TestCalculateWinRate:
    """Test calculate_win_rate function."""

    def test_empty_trades(self):
        """Test win rate with no trades."""
        assert calculate_win_rate([]) == Decimal("0")

    def test_all_winning(self):
        """Test win rate with all winning trades."""
        trades = [
            Trade(
                entry_price=Decimal("100"),
                exit_price=Decimal("105"),
                quantity=1,
                entry_time=pd.Timestamp("2024-01-01"),
                exit_time=pd.Timestamp("2024-01-01"),
                side="BUY",
            )
            for _ in range(5)
        ]

        assert calculate_win_rate(trades) == Decimal("100.0")

    def test_mixed_trades(self):
        """Test win rate with mixed trades."""
        trades = create_sample_trades()
        assert calculate_win_rate(trades) == Decimal("50.0")


class TestCalculateProfitFactor:
    """Test calculate_profit_factor function."""

    def test_empty_trades(self):
        """Test profit factor with no trades."""
        assert calculate_profit_factor([]) == Decimal("0")

    def test_no_losses(self):
        """Test profit factor with no losing trades."""
        trades = [
            Trade(
                entry_price=Decimal("100"),
                exit_price=Decimal("105"),
                quantity=1,
                entry_time=pd.Timestamp("2024-01-01"),
                exit_time=pd.Timestamp("2024-01-01"),
                side="BUY",
            )
        ]

        assert calculate_profit_factor(trades) == Decimal("inf")

    def test_normal_profit_factor(self):
        """Test profit factor calculation."""
        trades = create_sample_trades()
        # Gross profit: 70, Gross loss: 20
        assert calculate_profit_factor(trades) == Decimal("3.5")


class TestTradeDistribution:
    """Test trade distribution analysis."""

    def test_empty_distribution(self):
        """Test distribution with no trades."""
        dist = analyze_trade_distribution([])

        assert dist["mean"] == 0.0
        assert dist["median"] == 0.0
        assert dist["std"] == 0.0

    def test_trade_distribution_stats(self):
        """Test distribution statistics calculation."""
        trades = create_sample_trades()
        dist = analyze_trade_distribution(trades)

        # Should have all required statistics
        assert "mean" in dist
        assert "median" in dist
        assert "std" in dist
        assert "skew" in dist
        assert "kurtosis" in dist
        assert "percentile_25" in dist
        assert "percentile_75" in dist

        # Mean should be positive (profitable overall)
        assert dist["mean"] > 0


class TestBestWorstPeriods:
    """Test finding best and worst trading periods."""

    def test_empty_trades(self):
        """Test with no trades."""
        best_period, best_pnl, worst_period, worst_pnl = find_best_worst_periods([])

        assert best_period is None
        assert best_pnl == Decimal("0")
        assert worst_period is None
        assert worst_pnl == Decimal("0")

    def test_daily_periods(self):
        """Test finding best/worst days."""
        trades = create_sample_trades()
        best_day, best_pnl, worst_day, worst_pnl = find_best_worst_periods(
            trades, period="D"
        )

        # Day 1: +50 - 20 = +30
        # Day 2: +20 + 0 = +20
        assert best_pnl == Decimal("30.0")
        assert worst_pnl == Decimal("20.0")

    def test_monthly_periods(self):
        """Test finding best/worst months."""
        # Create trades spanning multiple months
        trades = [
            Trade(
                entry_price=Decimal("100"),
                exit_price=Decimal("110"),
                quantity=10,
                entry_time=pd.Timestamp("2024-01-01"),
                exit_time=pd.Timestamp("2024-01-01"),
                side="BUY",
            ),
            Trade(
                entry_price=Decimal("100"),
                exit_price=Decimal("95"),
                quantity=10,
                entry_time=pd.Timestamp("2024-02-01"),
                exit_time=pd.Timestamp("2024-02-01"),
                side="BUY",
            ),
        ]

        best_month, best_pnl, worst_month, worst_pnl = find_best_worst_periods(
            trades, period="ME"
        )

        assert best_pnl == Decimal("100.0")  # January
        assert worst_pnl == Decimal("-50.0")  # February
