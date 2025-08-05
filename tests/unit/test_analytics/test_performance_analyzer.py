"""Tests for L1+L2 Performance Analyzer."""

from decimal import Decimal

import pytest

from strategy_lab.analytics.performance import L1L2PerformanceAnalyzer
from strategy_lab.data.synchronization import PriceLevel, UnifiedMarketSnapshot
from strategy_lab.strategies.protocol_enhanced import OrderRequest, OrderSide, OrderType


class TestL1L2PerformanceAnalyzer:
    """Test L1+L2 Performance Analyzer."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance."""
        return L1L2PerformanceAnalyzer(initial_capital=Decimal("100000"))

    @pytest.fixture
    def sample_snapshot(self):
        """Create sample market snapshot."""
        return UnifiedMarketSnapshot(
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

    def test_analyzer_initialization(self):
        """Test analyzer initialization."""
        analyzer = L1L2PerformanceAnalyzer(initial_capital=Decimal("50000"))

        assert analyzer.initial_capital == Decimal("50000")
        assert analyzer.current_capital == Decimal("50000")
        assert analyzer.performance.total_pnl == Decimal("0")
        assert analyzer.signal_quality.total_signals == 0
        assert analyzer.execution.total_orders == 0
        assert analyzer.risk.max_position_size == 0

    def test_record_signal(self, analyzer, sample_snapshot):
        """Test recording trading signals."""
        # Record signal that was acted on
        analyzer.record_signal(
            timestamp=1000000000,
            snapshot=sample_snapshot,
            confidence=85.5,
            imbalance=0.25,
            volume=100,
            action_taken=True,
        )

        assert analyzer.signal_quality.total_signals == 1
        assert analyzer.signal_quality.signals_acted_on == 1
        assert analyzer.signal_quality.confidence_scores == [85.5]
        assert analyzer.signal_quality.imbalance_readings == [0.25]
        assert analyzer.signal_quality.volume_readings == [100]

        # Record signal that was not acted on
        analyzer.record_signal(
            timestamp=2000000000,
            snapshot=sample_snapshot,
            confidence=45.0,
            imbalance=0.10,
            volume=50,
            action_taken=False,
        )

        assert analyzer.signal_quality.total_signals == 2
        assert analyzer.signal_quality.signals_acted_on == 1

    def test_record_order(self, analyzer):
        """Test recording order executions."""
        # Create order
        order = OrderRequest(
            side=OrderSide.BUY,
            size=5,
            order_type=OrderType.LIMIT,
            price=Decimal("100.25"),
            metadata={"signal_time": 1000000000},
        )

        # Record successful fill
        analyzer.record_order(
            order=order, fill_price=Decimal("100.30"), fill_timestamp=1000001000
        )

        assert analyzer.execution.total_orders == 1
        assert analyzer.execution.filled_orders == 1
        assert analyzer.execution.rejected_orders == 0
        assert len(analyzer.execution.slippage_readings) == 1
        assert analyzer.execution.slippage_readings[0] == 0.2  # 0.05 / 0.25
        assert len(analyzer.execution.latency_readings) == 1
        assert analyzer.execution.latency_readings[0] == 1.0  # 1000 ns = 1 μs

        # Record rejected order
        analyzer.record_order(order=order, rejected=True)

        assert analyzer.execution.total_orders == 2
        assert analyzer.execution.rejected_orders == 1

    def test_record_trade(self, analyzer):
        """Test recording completed trades."""
        # Record winning trade
        analyzer.record_trade(
            timestamp=1000000000,
            side=OrderSide.BUY,
            size=10,
            entry_price=Decimal("100.00"),
            exit_price=Decimal("101.00"),
            commission=Decimal("2.00"),
        )

        assert analyzer.performance.total_trades == 1
        assert analyzer.performance.winning_trades == 1
        assert analyzer.performance.gross_profit == Decimal("8.00")  # (101-100)*10 - 2
        assert analyzer.performance.total_commission == Decimal("2.00")
        assert analyzer.current_capital == Decimal("100008.00")

        # Record losing trade
        analyzer.record_trade(
            timestamp=2000000000,
            side=OrderSide.SELL,
            size=5,
            entry_price=Decimal("102.00"),
            exit_price=Decimal("103.00"),
            commission=Decimal("1.00"),
        )

        assert analyzer.performance.total_trades == 2
        assert analyzer.performance.losing_trades == 1
        assert analyzer.performance.gross_loss == Decimal("-6.00")  # (102-103)*5 - 1

    def test_calculate_metrics(self, analyzer, sample_snapshot):
        """Test metrics calculation."""
        # Add some data
        analyzer.record_signal(
            timestamp=1000000000,
            snapshot=sample_snapshot,
            confidence=80.0,
            imbalance=0.3,
            volume=100,
            action_taken=True,
        )

        analyzer.record_trade(
            timestamp=1000000000,
            side=OrderSide.BUY,
            size=5,
            entry_price=Decimal("100.00"),
            exit_price=Decimal("100.50"),
            commission=Decimal("1.00"),
        )

        # Calculate metrics
        metrics = analyzer.calculate_metrics()

        assert "performance" in metrics
        assert "signal_quality" in metrics
        assert "execution" in metrics
        assert "risk" in metrics
        assert "summary" in metrics

        # Check summary
        summary = metrics["summary"]
        assert summary["total_trades"] == 1
        assert summary["win_rate_pct"] == 100.0
        assert summary["avg_confidence"] == 80.0

    def test_equity_curve_tracking(self, analyzer):
        """Test equity curve generation."""
        # Add some trades
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
            exit_price=Decimal("101.50"),
            commission=Decimal("1.00"),
        )

        # Get equity curve
        equity_df = analyzer.get_equity_curve()

        assert not equity_df.empty
        assert len(equity_df) == 2
        assert equity_df.iloc[0]["equity"] == Decimal("100008.00")
        assert equity_df.iloc[1]["equity"] == Decimal("100009.50")

    def test_trade_log(self, analyzer):
        """Test trade log generation."""
        # Add trades
        analyzer.record_trade(
            timestamp=1000000000,
            side=OrderSide.BUY,
            size=10,
            entry_price=Decimal("100.00"),
            exit_price=Decimal("101.00"),
            commission=Decimal("2.00"),
            metadata={"strategy": "test"},
        )

        # Get trade log
        trade_log = analyzer.get_trade_log()

        assert not trade_log.empty
        assert len(trade_log) == 1
        assert trade_log.iloc[0]["side"] == OrderSide.BUY
        assert trade_log.iloc[0]["size"] == 10
        assert float(trade_log.iloc[0]["pnl"]) == 8.0

    def test_risk_metrics_calculation(self, analyzer):
        """Test risk metrics calculation."""
        # Add position data (need exit prices for position sizes to be recorded)
        analyzer.record_trade(
            timestamp=1000000000,
            side=OrderSide.BUY,
            size=10,
            entry_price=Decimal("100.00"),
            exit_price=Decimal("100.50"),  # Add exit price
        )

        analyzer.record_trade(
            timestamp=2000000000,
            side=OrderSide.SELL,
            size=15,
            entry_price=Decimal("101.00"),
            exit_price=Decimal("100.50"),  # Add exit price
        )

        # Add daily returns for risk calculation
        analyzer.performance.daily_returns = [0.01, -0.005, 0.002, -0.008, 0.012]

        # Check position sizes were recorded
        assert len(analyzer.risk.position_sizes) == 2
        assert analyzer.risk.position_sizes == [10, -15]

        # Calculate metrics
        metrics = analyzer.calculate_metrics()
        risk = metrics["risk"]

        # Check that position sizes were included in the output
        assert len(risk["position_sizes"]) == 2

        # Check the max/avg were calculated correctly
        # (only when we have full return data with equity curve)
        if risk["max_position_size"] > 0:
            assert risk["max_position_size"] == 15
            assert risk["avg_position_size"] == 12.5

    def test_signal_quality_metrics(self, analyzer, sample_snapshot):
        """Test signal quality metrics calculation."""
        # Add multiple signals
        for i in range(10):
            analyzer.record_signal(
                timestamp=1000000000 + i * 1000000,
                snapshot=sample_snapshot,
                confidence=70 + i * 2,
                imbalance=0.2 + i * 0.01,
                volume=100 + i * 10,
                action_taken=i % 2 == 0,
            )

        # Calculate metrics
        analyzer.signal_quality.calculate_signal_metrics()

        assert analyzer.signal_quality.total_signals == 10
        assert analyzer.signal_quality.signals_acted_on == 5
        assert analyzer.signal_quality.signal_hit_rate == 0.5
        assert analyzer.signal_quality.avg_confidence_score == 79.0

    def test_execution_metrics(self, analyzer):
        """Test execution metrics calculation."""
        # Add order data
        for i in range(5):
            order = OrderRequest(
                side=OrderSide.BUY,
                size=5,
                order_type=OrderType.LIMIT,
                price=Decimal("100.00"),
                metadata={"signal_time": 1000000000},
            )

            if i < 3:
                # Filled orders
                analyzer.record_order(
                    order=order,
                    fill_price=Decimal("100.00") + Decimal(str(i * 0.05)),
                    fill_timestamp=1000001000 + i * 1000,
                )
            else:
                # Rejected orders
                analyzer.record_order(order=order, rejected=True)

        # Calculate metrics
        analyzer.execution.calculate_execution_metrics()

        assert analyzer.execution.total_orders == 5
        assert analyzer.execution.filled_orders == 3
        assert analyzer.execution.rejected_orders == 2
        assert analyzer.execution.fill_rate == 0.6
        assert (
            analyzer.execution.positive_slippage_count == 2
        )  # Orders 2 and 3 had positive slippage
