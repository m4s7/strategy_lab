"""Tests for performance analysis components."""

from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import pytest

from strategy_lab.analysis import (
    PerformanceAnalyzer,
    PerformanceMetrics,
    PerformanceReport,
)
from strategy_lab.analysis.performance.metrics import MetricsCalculator


class TestMetricsCalculator:
    """Test MetricsCalculator class."""

    @pytest.fixture
    def sample_equity_curve(self):
        """Create sample equity curve."""
        dates = pd.date_range("2024-01-01", periods=252, freq="D")
        # Simulate growth with some volatility
        np.random.seed(42)
        returns = np.random.normal(0.0005, 0.01, 252)
        values = 10000 * (1 + returns).cumprod()
        return pd.Series(values, index=dates)

    @pytest.fixture
    def sample_trades(self):
        """Create sample trade data."""
        trades = []
        np.random.seed(42)

        for i in range(50):
            pnl = np.random.normal(20, 100)
            trades.append(
                {
                    "entry_time": datetime(2024, 1, 1) + timedelta(days=i * 5),
                    "exit_time": datetime(2024, 1, 1) + timedelta(days=i * 5 + 2),
                    "pnl": pnl,
                    "holding_time": 48,  # hours
                    "position_size": 100,
                }
            )

        return pd.DataFrame(trades)

    def test_calculate_metrics(self, sample_equity_curve, sample_trades):
        """Test comprehensive metrics calculation."""
        calculator = MetricsCalculator()

        metrics = calculator.calculate_metrics(sample_equity_curve, sample_trades)

        assert isinstance(metrics, PerformanceMetrics)

        # Check basic metrics
        assert metrics.total_return > -1  # Not total loss
        assert 0 <= metrics.win_rate <= 1
        assert metrics.total_trades == len(sample_trades)

        # Check risk metrics
        assert metrics.volatility > 0
        assert metrics.max_drawdown >= 0
        assert metrics.var_95 < 0  # Should be negative

        # Check trade stats
        assert metrics.winning_trades + metrics.losing_trades <= metrics.total_trades
        assert metrics.avg_holding_time == 48

    def test_calculate_rolling_metrics(self, sample_equity_curve):
        """Test rolling metrics calculation."""
        calculator = MetricsCalculator()

        rolling = calculator.calculate_rolling_metrics(
            sample_equity_curve, window=60, min_periods=30
        )

        assert isinstance(rolling, pd.DataFrame)
        assert "return" in rolling.columns
        assert "volatility" in rolling.columns
        assert "sharpe_ratio" in rolling.columns
        assert "max_drawdown" in rolling.columns

        # Check that we have data after min_periods
        assert rolling.dropna().shape[0] > 0

    def test_empty_trades(self, sample_equity_curve):
        """Test metrics calculation with no trades."""
        calculator = MetricsCalculator()
        empty_trades = pd.DataFrame()

        metrics = calculator.calculate_metrics(sample_equity_curve, empty_trades)

        assert metrics.total_trades == 0
        assert metrics.win_rate == 0
        assert metrics.profit_factor == np.inf


class TestPerformanceAnalyzer:
    """Test PerformanceAnalyzer class."""

    @pytest.fixture
    def analyzer(self):
        """Create performance analyzer."""
        return PerformanceAnalyzer()

    @pytest.fixture
    def sample_data(self):
        """Create sample data for analysis."""
        # Create equity curve
        dates = pd.date_range("2024-01-01", periods=100, freq="D")
        np.random.seed(42)
        returns = np.random.normal(0.001, 0.02, 100)
        equity = 10000 * (1 + returns).cumprod()
        equity_curve = pd.Series(equity, index=dates)

        # Create trades
        trades = []
        for i in range(20):
            pnl = np.random.normal(50, 200)
            trades.append(
                {
                    "entry_time": dates[i * 5],
                    "exit_time": dates[i * 5 + 2],
                    "entry_price": 100,
                    "exit_price": 100 + pnl / 100,
                    "pnl": pnl,
                    "holding_time": 48,
                    "position_size": 100,
                    "direction": "long" if pnl > 0 else "short",
                }
            )

        trades_df = pd.DataFrame(trades)

        return {"equity_curve": equity_curve, "trades": trades_df}

    def test_analyze(self, analyzer, sample_data):
        """Test comprehensive analysis."""
        report = analyzer.analyze(
            equity_curve=sample_data["equity_curve"], trades=sample_data["trades"]
        )

        assert isinstance(report, PerformanceReport)
        assert report.metrics is not None
        assert report.risk_metrics is not None
        assert report.drawdown_analysis is not None
        assert report.trade_statistics is not None

        # Check report summary
        summary = report.get_summary()
        assert "performance" in summary
        assert "risk" in summary
        assert "trading" in summary

    def test_compare_strategies(self, analyzer, sample_data):
        """Test strategy comparison."""
        # Create two strategies
        strategies = {
            "Strategy A": sample_data,
            "Strategy B": sample_data,  # Same data for simplicity
        }

        reports = analyzer.compare_strategies(strategies)

        assert len(reports) == 2
        assert "Strategy A" in reports
        assert "Strategy B" in reports

        for name, report in reports.items():
            assert isinstance(report, PerformanceReport)

    def test_generate_executive_summary(self, analyzer, sample_data):
        """Test executive summary generation."""
        report = analyzer.analyze(
            equity_curve=sample_data["equity_curve"], trades=sample_data["trades"]
        )

        summary = analyzer.generate_executive_summary(report)

        assert "overview" in summary
        assert "risk_profile" in summary
        assert "trading_performance" in summary
        assert "strengths" in summary
        assert "weaknesses" in summary
        assert "recommendations" in summary


class TestPerformanceReport:
    """Test PerformanceReport class."""

    @pytest.fixture
    def sample_report(self):
        """Create sample performance report."""
        # This would normally come from the analyzer
        # Using minimal data for testing
        from strategy_lab.analysis.risk import RiskMetrics
        from strategy_lab.analysis.risk.drawdown import DrawdownAnalysis
        from strategy_lab.analysis.trade.statistics import TradeStatistics, TradeSummary

        metrics = PerformanceMetrics(
            total_return=0.25,
            annualized_return=0.30,
            profit_factor=2.0,
            win_rate=0.6,
            expectancy=50,
            volatility=0.15,
            sharpe_ratio=1.5,
            sortino_ratio=2.0,
            calmar_ratio=2.5,
            max_drawdown=0.12,
            var_95=-0.02,
            cvar_95=-0.03,
            downside_deviation=0.10,
            tail_ratio=1.5,
            skewness=0.5,
            kurtosis=3.0,
            total_trades=100,
            winning_trades=60,
            losing_trades=40,
            avg_win=100,
            avg_loss=50,
            win_loss_ratio=2.0,
            avg_trade=40,
            avg_holding_time=24,
            recovery_factor=2.0,
            profit_consistency=0.7,
            trade_frequency=0.4,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31),
            trading_days=252,
        )

        risk_metrics = RiskMetrics(
            volatility=0.15,
            downside_deviation=0.10,
            var_95=-0.02,
            var_99=-0.03,
            cvar_95=-0.03,
            cvar_99=-0.04,
            skewness=0.5,
            kurtosis=3.0,
            max_drawdown_duration=30,
            risk_of_ruin=0.05,
            tail_ratio=1.5,
            concentration_risk=0.2,
            correlation_risk=0.1,
            beta=0.8,
        )

        # Minimal drawdown analysis
        drawdown_analysis = DrawdownAnalysis(
            max_drawdown=0.12,
            max_drawdown_duration=30,
            avg_drawdown=0.06,
            avg_recovery_time=15,
            drawdown_periods=[],
            underwater_curve=pd.Series(),
            recovery_factor=2.0,
            worst_periods=[],
            current_drawdown=None,
            time_underwater_pct=0.3,
        )

        # Minimal trade statistics
        trade_stats = TradeStatistics(
            summary=TradeSummary(
                total_trades=100,
                winning_trades=60,
                losing_trades=40,
                breakeven_trades=0,
                win_rate=0.6,
                total_pnl=4000,
                avg_pnl=40,
                avg_win=100,
                avg_loss=50,
                max_win=500,
                max_loss=200,
                win_loss_ratio=2.0,
                profit_factor=2.0,
                expectancy=40,
                avg_holding_time=24,
                avg_win_time=20,
                avg_loss_time=30,
            ),
            pnl_distribution={},
            time_analysis={},
            streak_analysis={},
            entry_exit_analysis={},
            sizing_analysis={},
        )

        return PerformanceReport(
            metrics=metrics,
            risk_metrics=risk_metrics,
            drawdown_analysis=drawdown_analysis,
            trade_statistics=trade_stats,
            rolling_metrics=pd.DataFrame(),
            equity_curve=pd.Series(),
            trades=pd.DataFrame(),
        )

    def test_to_dict(self, sample_report):
        """Test report dictionary conversion."""
        report_dict = sample_report.to_dict()

        assert isinstance(report_dict, dict)
        assert "metrics" in report_dict
        assert "risk_metrics" in report_dict
        assert "drawdown_analysis" in report_dict
        assert "trade_statistics" in report_dict
        assert "summary" in report_dict

    def test_generate_text_report(self, sample_report):
        """Test text report generation."""
        text_report = sample_report.generate_text_report()

        assert isinstance(text_report, str)
        assert "PERFORMANCE ANALYSIS REPORT" in text_report
        assert "Total Return:" in text_report
        assert "Sharpe Ratio:" in text_report
        assert "Win Rate:" in text_report

    def test_save_to_file(self, sample_report, tmp_path):
        """Test saving report to file."""
        # Test JSON
        json_path = tmp_path / "report.json"
        sample_report.save_to_file(json_path, format="json")
        assert json_path.exists()

        # Test CSV
        csv_path = tmp_path / "report.csv"
        sample_report.save_to_file(csv_path, format="csv")
        assert csv_path.exists()

        # Test HTML
        html_path = tmp_path / "report.html"
        sample_report.save_to_file(html_path, format="html")
        assert html_path.exists()
