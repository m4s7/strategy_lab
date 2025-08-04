"""Tests for comprehensive performance metrics calculation."""

import tempfile
from decimal import Decimal
from pathlib import Path

import pandas as pd
import pytest

from strategy_lab.backtesting.metrics.comprehensive import (
    ComprehensiveMetrics,
    ComprehensiveMetricsCalculator,
    convert_portfolio_trades_to_performance_trades,
)
from strategy_lab.backtesting.metrics.performance import Trade
from strategy_lab.backtesting.engine.portfolio import Position, PositionSide


class TestComprehensiveMetricsCalculator:
    """Test ComprehensiveMetricsCalculator functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.calculator = ComprehensiveMetricsCalculator(
            risk_free_rate=0.02, periods_per_year=252
        )

    def create_sample_trades(self) -> list[Trade]:
        """Create sample trades for testing."""
        base_time = pd.Timestamp("2024-01-01 09:30:00")
        trades = []

        # Create mix of winning and losing trades
        # Calculate actual P&L: (exit - entry) * quantity - commission
        trade_data = [
            (4000, 4010, "BUY"),  # (4010 - 4000) * 100 - 2 = $998
            (4010, 4005, "BUY"),  # (4005 - 4010) * 100 - 2 = -$502 (loss)
            (4005, 4020, "BUY"),  # (4020 - 4005) * 100 - 2 = $1498
            (4020, 4015, "BUY"),  # (4015 - 4020) * 100 - 2 = -$502 (loss)
            (4015, 4030, "BUY"),  # (4030 - 4015) * 100 - 2 = $1498
        ]

        for i, (entry, exit, side) in enumerate(trade_data):
            trades.append(
                Trade(
                    entry_price=Decimal(str(entry)),
                    exit_price=Decimal(str(exit)),
                    quantity=100,
                    entry_time=base_time
                    + pd.Timedelta(days=i * 10),  # Spread trades over time
                    exit_time=base_time + pd.Timedelta(days=i * 10, hours=1),
                    side=side,
                    commission=Decimal("2.00"),
                )
            )

        return trades

    def create_sample_equity_curve(self) -> tuple[list[Decimal], list[pd.Timestamp]]:
        """Create sample equity curve data."""
        initial_capital = Decimal("100000")
        equity_values = [
            initial_capital,
            initial_capital + Decimal("1000"),  # After first trade
            initial_capital + Decimal("500"),  # After second trade
            initial_capital + Decimal("2000"),  # After third trade
            initial_capital + Decimal("1500"),  # After fourth trade
            initial_capital + Decimal("4500"),  # After fifth trade
        ]

        base_time = pd.Timestamp("2024-01-01 09:30:00")
        timestamps = [base_time + pd.Timedelta(days=i * 10, hours=1) for i in range(6)]

        return equity_values, timestamps

    def test_calculate_all_metrics_empty_data(self):
        """Test metrics calculation with empty data."""
        metrics = self.calculator.calculate_all_metrics(
            trades=[],
            equity_curve=[Decimal("100000")],
            timestamps=[pd.Timestamp.now()],
            initial_capital=Decimal("100000"),
        )

        assert isinstance(metrics, ComprehensiveMetrics)
        assert metrics.total_return == 0.0
        assert metrics.performance.total_trades == 0

    def test_calculate_all_metrics_with_trades(self):
        """Test comprehensive metrics calculation with real trade data."""
        trades = self.create_sample_trades()
        equity_curve, timestamps = self.create_sample_equity_curve()
        initial_capital = Decimal("100000")

        metrics = self.calculator.calculate_all_metrics(
            trades=trades,
            equity_curve=equity_curve,
            timestamps=timestamps,
            initial_capital=initial_capital,
        )

        # Test performance metrics
        assert metrics.performance.total_trades == 5
        assert metrics.performance.winning_trades == 3
        assert metrics.performance.losing_trades == 2
        assert float(metrics.performance.win_rate) == 60.0
        assert metrics.performance.total_pnl > 0

        # Test return calculations
        assert metrics.total_return > 0
        assert metrics.annualized_return > 0

        # Test risk metrics
        assert metrics.risk.max_drawdown >= 0
        assert isinstance(metrics.risk.sharpe_ratio, float)
        assert isinstance(metrics.risk.sortino_ratio, float)

        # Test trade statistics
        assert metrics.trade_stats.total_trades == 5
        assert metrics.trade_stats.max_consecutive_wins >= 0
        assert metrics.trade_stats.max_consecutive_losses >= 0

    def test_total_return_calculation(self):
        """Test total return calculation."""
        equity_curve = [Decimal("100000"), Decimal("110000")]
        initial_capital = Decimal("100000")

        total_return = self.calculator._calculate_total_return(
            equity_curve, initial_capital
        )
        assert total_return == 0.10  # 10% return

    def test_annualized_return_calculation(self):
        """Test annualized return calculation."""
        total_return = 0.10  # 10% total return
        timestamps = [
            pd.Timestamp("2024-01-01"),
            pd.Timestamp("2024-07-01"),  # 6 months
        ]

        annual_return = self.calculator._calculate_annualized_return(
            total_return, timestamps
        )
        assert (
            annual_return > 0.10
        )  # Should be higher than total return due to annualization

    def test_calmar_ratio_calculation(self):
        """Test Calmar ratio calculation."""
        annual_return = 0.15
        max_drawdown = 0.05

        calmar = self.calculator._calculate_calmar_ratio(annual_return, max_drawdown)
        assert (
            abs(calmar - 3.0) < 1e-10
        )  # 15% / 5% = 3.0 (allow for floating point precision)

    def test_recovery_factor_calculation(self):
        """Test recovery factor calculation."""
        total_pnl = 10000.0
        max_drawdown = 2000.0

        recovery_factor = self.calculator._calculate_recovery_factor(
            total_pnl, max_drawdown
        )
        assert recovery_factor == 5.0  # 10000 / 2000 = 5.0

    def test_drawdown_series_calculation(self):
        """Test drawdown series calculation."""
        equity_curve = [
            Decimal("100000"),
            Decimal("110000"),  # New high
            Decimal("105000"),  # 5% drawdown from high
            Decimal("115000"),  # New high
        ]
        timestamps = [
            pd.Timestamp("2024-01-01") + pd.Timedelta(days=i) for i in range(4)
        ]

        drawdown_series = self.calculator._calculate_drawdown_series(
            equity_curve, timestamps
        )

        assert len(drawdown_series) == 4
        assert drawdown_series.iloc[0] == 0.0  # No drawdown at start
        assert drawdown_series.iloc[1] == 0.0  # At new high
        assert drawdown_series.iloc[2] < 0.0  # In drawdown
        assert drawdown_series.iloc[3] == 0.0  # At new high

    def test_rolling_sharpe_calculation(self):
        """Test rolling Sharpe ratio calculation."""
        # Create synthetic daily returns
        returns = pd.Series([0.01, -0.005, 0.015, -0.01, 0.02] * 20)  # 100 days
        returns.index = pd.date_range("2024-01-01", periods=100, freq="D")

        rolling_sharpe = self.calculator._calculate_rolling_sharpe(returns, window=30)

        # Should have values starting from the 30th observation
        # The rolling function fills with zeros for insufficient data, not NaN
        valid_sharpe = rolling_sharpe[rolling_sharpe.index >= returns.index[29]]
        assert len(valid_sharpe) == 71  # 100 - 30 + 1
        assert not valid_sharpe.empty

    def test_best_worst_periods_calculation(self):
        """Test best and worst period identification."""
        trades = self.create_sample_trades()

        best_month, worst_month = self.calculator._find_best_worst_months(trades)
        best_day, worst_day = self.calculator._find_best_worst_days(trades)

        # Should return tuples with timestamp and PnL
        assert isinstance(best_month[0], pd.Timestamp)
        assert isinstance(best_month[1], float)
        assert isinstance(worst_month[0], pd.Timestamp)
        assert isinstance(worst_month[1], float)

        assert isinstance(best_day[0], pd.Timestamp)
        assert isinstance(best_day[1], float)
        assert isinstance(worst_day[0], pd.Timestamp)
        assert isinstance(worst_day[1], float)

    def test_export_detailed_report(self):
        """Test detailed report export functionality."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir)

            trades = self.create_sample_trades()
            equity_curve, timestamps = self.create_sample_equity_curve()

            metrics = self.calculator.calculate_all_metrics(
                trades=trades,
                equity_curve=equity_curve,
                timestamps=timestamps,
                initial_capital=Decimal("100000"),
            )

            config_info = {
                "strategy_name": "TestStrategy",
                "start_date": "2024-01-01",
                "end_date": "2024-01-02",
                "initial_capital": 100000,
            }

            # Export report
            self.calculator.export_detailed_report(metrics, output_path, config_info)

            # Verify files were created
            assert (output_path / "performance_summary.txt").exists()
            assert (output_path / "metrics_summary.json").exists()

            # Verify CSV files if there's data
            if not metrics.daily_returns.empty:
                assert (output_path / "daily_returns.csv").exists()
            if not metrics.drawdown_series.empty:
                assert (output_path / "drawdown_series.csv").exists()

    def test_convert_portfolio_trades_to_performance_trades(self):
        """Test conversion from portfolio trades to performance trades."""

        # Create mock portfolio position
        class MockTrade:
            def __init__(self):
                self.entry_price = Decimal("4000")
                self.exit_price = Decimal("4010")
                self.quantity = 100
                self.entry_time = pd.Timestamp("2024-01-01 09:30:00")
                self.exit_time = pd.Timestamp("2024-01-01 10:00:00")
                self.side = PositionSide.LONG
                self.commission = Decimal("2.00")

        portfolio_trades = [MockTrade()]
        performance_trades = convert_portfolio_trades_to_performance_trades(
            portfolio_trades
        )

        assert len(performance_trades) == 1
        trade = performance_trades[0]
        assert isinstance(trade, Trade)
        assert trade.entry_price == Decimal("4000")
        assert trade.exit_price == Decimal("4010")
        assert trade.side == "BUY"  # LONG converted to BUY

    def test_edge_cases(self):
        """Test edge cases and error handling."""
        # Test with single trade
        single_trade = [
            Trade(
                entry_price=Decimal("4000"),
                exit_price=Decimal("4010"),
                quantity=100,
                entry_time=pd.Timestamp("2024-01-01 09:30:00"),
                exit_time=pd.Timestamp("2024-01-01 10:00:00"),
                side="BUY",
            )
        ]

        equity_curve = [Decimal("100000"), Decimal("101000")]
        timestamps = [
            pd.Timestamp("2024-01-01 09:30:00"),
            pd.Timestamp("2024-01-01 10:00:00"),
        ]

        metrics = self.calculator.calculate_all_metrics(
            trades=single_trade,
            equity_curve=equity_curve,
            timestamps=timestamps,
            initial_capital=Decimal("100000"),
        )

        assert metrics.performance.total_trades == 1
        assert metrics.performance.winning_trades == 1
        assert metrics.performance.losing_trades == 0

    def test_zero_division_handling(self):
        """Test handling of zero division cases."""
        # Test Calmar ratio with zero drawdown
        calmar = self.calculator._calculate_calmar_ratio(0.10, 0.0)
        assert calmar == 0.0

        # Test recovery factor with zero drawdown
        recovery = self.calculator._calculate_recovery_factor(10000.0, 0.0)
        assert recovery == 0.0

    def test_comprehensive_metrics_dataclass(self):
        """Test ComprehensiveMetrics dataclass initialization."""
        metrics = ComprehensiveMetrics()

        # Test default values
        assert metrics.total_return == 0.0
        assert metrics.annualized_return == 0.0
        assert metrics.excess_return == 0.0
        assert metrics.calmar_ratio == 0.0
        assert metrics.recovery_factor == 0.0

        # Test that pandas Series are properly initialized
        assert isinstance(metrics.daily_returns, pd.Series)
        assert isinstance(metrics.monthly_returns, pd.Series)
        assert isinstance(metrics.drawdown_series, pd.Series)
        assert isinstance(metrics.rolling_sharpe_30d, pd.Series)
        assert isinstance(metrics.rolling_sharpe_90d, pd.Series)

    def test_performance_with_all_losing_trades(self):
        """Test metrics calculation with all losing trades."""
        base_time = pd.Timestamp("2024-01-01 09:30:00")
        losing_trades = []

        for i in range(3):
            trade = Trade(
                entry_price=Decimal("4000"),
                exit_price=Decimal("3990"),  # Always losing $10 per share
                quantity=100,
                entry_time=base_time + pd.Timedelta(hours=i),
                exit_time=base_time + pd.Timedelta(hours=i, minutes=30),
                side="BUY",
                commission=Decimal("2.00"),
            )
            losing_trades.append(trade)

        equity_curve = [
            Decimal("100000"),
            Decimal("99000"),
            Decimal("98000"),
            Decimal("97000"),
        ]
        timestamps = [base_time + pd.Timedelta(hours=i, minutes=30) for i in range(4)]

        metrics = self.calculator.calculate_all_metrics(
            trades=losing_trades,
            equity_curve=equity_curve,
            timestamps=timestamps,
            initial_capital=Decimal("100000"),
        )

        assert metrics.performance.total_trades == 3
        assert metrics.performance.winning_trades == 0
        assert metrics.performance.losing_trades == 3
        assert float(metrics.performance.win_rate) == 0.0
        assert metrics.performance.total_pnl < 0
        assert metrics.total_return < 0

    def test_time_series_with_insufficient_data(self):
        """Test time series calculations with insufficient data."""
        # Test with less than 30 days of returns
        returns = pd.Series([0.01, -0.005, 0.015] * 5)  # 15 days
        returns.index = pd.date_range("2024-01-01", periods=15, freq="D")

        rolling_sharpe_30d = self.calculator._calculate_rolling_sharpe(
            returns, window=30
        )
        assert rolling_sharpe_30d.empty

        rolling_sharpe_5d = self.calculator._calculate_rolling_sharpe(returns, window=5)
        assert not rolling_sharpe_5d.dropna().empty
