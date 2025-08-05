"""Tests for Performance Reporter."""

import json
import tempfile
from decimal import Decimal
from pathlib import Path

import pytest

from strategy_lab.analytics.performance import (
    L1L2PerformanceAnalyzer,
    PerformanceReporter,
)
from strategy_lab.data.synchronization import PriceLevel, UnifiedMarketSnapshot
from strategy_lab.strategies.protocol_enhanced import OrderSide


class TestPerformanceReporter:
    """Test Performance Reporter functionality."""

    @pytest.fixture
    def analyzer_with_data(self):
        """Create analyzer with sample data."""
        analyzer = L1L2PerformanceAnalyzer(initial_capital=Decimal("100000"))

        # Add sample snapshot
        snapshot = UnifiedMarketSnapshot(
            timestamp=1000000000,
            last_trade_price=Decimal("100.50"),
            last_trade_volume=10,
            bid_price=Decimal("100.25"),
            ask_price=Decimal("100.50"),
            bid_levels=[
                PriceLevel(Decimal("100.25"), 50),
                PriceLevel(Decimal("100.00"), 100),
            ],
            ask_levels=[
                PriceLevel(Decimal("100.50"), 30),
                PriceLevel(Decimal("100.75"), 80),
            ],
        )

        # Add signals
        for i in range(5):
            analyzer.record_signal(
                timestamp=1000000000 + i * 1000000000,
                snapshot=snapshot,
                confidence=70 + i * 5,
                imbalance=0.2 + i * 0.05,
                volume=100 + i * 20,
                action_taken=True,
            )

        # Add trades
        analyzer.record_trade(
            timestamp=1000000000,
            side=OrderSide.BUY,
            size=10,
            entry_price=Decimal("100.00"),
            exit_price=Decimal("101.00"),
            commission=Decimal("2.00"),
        )

        analyzer.record_trade(
            timestamp=2000000000,
            side=OrderSide.SELL,
            size=5,
            entry_price=Decimal("102.00"),
            exit_price=Decimal("102.50"),  # Loss: sold at 102, bought back at 102.50
            commission=Decimal("1.00"),
        )

        # Add daily returns for metrics
        analyzer.performance.daily_returns = [0.01, -0.005, 0.002, -0.008, 0.012]

        return analyzer

    @pytest.fixture
    def reporter(self, analyzer_with_data):
        """Create reporter with analyzer."""
        return PerformanceReporter(analyzer_with_data)

    def test_reporter_initialization(self, analyzer_with_data):
        """Test reporter initialization."""
        reporter = PerformanceReporter(analyzer_with_data)

        assert reporter.analyzer == analyzer_with_data
        assert reporter.metrics is not None
        assert "performance" in reporter.metrics
        assert "signal_quality" in reporter.metrics

    def test_generate_text_report(self, reporter):
        """Test text report generation."""
        report = reporter.generate_text_report()

        assert isinstance(report, str)
        assert "L1+L2 STRATEGY PERFORMANCE REPORT" in report
        assert "EXECUTIVE SUMMARY" in report
        assert "Total Return:" in report
        assert "Sharpe Ratio:" in report
        assert "PERFORMANCE METRICS" in report
        assert "SIGNAL QUALITY METRICS" in report
        assert "EXECUTION METRICS" in report
        assert "RISK METRICS" in report

    def test_generate_json_report(self, reporter):
        """Test JSON report generation."""
        json_report = reporter.generate_json_report()

        # Verify it's valid JSON
        data = json.loads(json_report)

        assert "performance" in data
        assert "signal_quality" in data
        assert "execution" in data
        assert "risk" in data
        assert "summary" in data

        # Check some values
        assert data["performance"]["total_trades"] == 2
        assert data["signal_quality"]["total_signals"] == 5

    def test_save_report(self, reporter):
        """Test saving complete report."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            # Save report without plots (faster for testing)
            reporter.save_report(output_dir, include_plots=False)

            # Check files were created
            assert (output_dir / "performance_report.txt").exists()
            assert (output_dir / "performance_metrics.json").exists()
            assert (output_dir / "trade_log.csv").exists()

            # Verify content
            with open(output_dir / "performance_report.txt") as f:
                text_content = f.read()
                assert "EXECUTIVE SUMMARY" in text_content

            with open(output_dir / "performance_metrics.json") as f:
                json_data = json.load(f)
                assert "performance" in json_data

    def test_summary_metrics(self, reporter):
        """Test summary metrics calculation."""
        summary = reporter.metrics["summary"]

        assert "total_return_pct" in summary
        assert "sharpe_ratio" in summary
        assert "max_drawdown_pct" in summary
        assert "win_rate_pct" in summary
        assert "profit_factor" in summary
        assert "total_trades" in summary
        assert "avg_confidence" in summary
        assert "signal_hit_rate_pct" in summary
        assert "fill_rate_pct" in summary
        assert "avg_slippage_ticks" in summary

        # Check values
        assert summary["total_trades"] == 2
        assert summary["win_rate_pct"] == 50.0  # 1 win, 1 loss

    def test_empty_analyzer_report(self):
        """Test report generation with empty analyzer."""
        analyzer = L1L2PerformanceAnalyzer()
        reporter = PerformanceReporter(analyzer)

        # Should not crash
        text_report = reporter.generate_text_report()
        json_report = reporter.generate_json_report()

        assert isinstance(text_report, str)
        assert isinstance(json_report, str)

        # Check default values
        data = json.loads(json_report)
        assert data["performance"]["total_trades"] == 0
        assert data["signal_quality"]["total_signals"] == 0
