"""Tests for enhanced portfolio functionality with drawdown tracking."""

from decimal import Decimal

import pandas as pd

from strategy_lab.backtesting.engine.portfolio import Portfolio, PositionSide


class TestPortfolioDrawdownTracking:
    """Test portfolio drawdown tracking functionality."""

    def test_portfolio_initialization_with_drawdown(self):
        """Test portfolio initialization includes drawdown tracking."""
        initial_capital = Decimal("100000")
        portfolio = Portfolio(initial_capital=initial_capital)

        assert portfolio.initial_capital == initial_capital
        assert portfolio.cash == initial_capital
        assert portfolio.peak_equity == initial_capital
        assert portfolio.current_drawdown == Decimal("0")
        assert portfolio.max_drawdown == Decimal("0")

    def test_drawdown_calculation_with_gains(self):
        """Test drawdown calculation when portfolio gains value."""
        portfolio = Portfolio(initial_capital=Decimal("100000"))

        # Simulate price increase that increases portfolio value
        portfolio.cash = Decimal("110000")  # Simulate 10% gain
        portfolio._update_drawdown()

        # Peak should update, no drawdown
        assert portfolio.peak_equity == Decimal("110000")
        assert portfolio.current_drawdown == Decimal("0")
        assert portfolio.max_drawdown == Decimal("0")
        assert portfolio.current_drawdown_percent == Decimal("0")

    def test_drawdown_calculation_with_losses(self):
        """Test drawdown calculation when portfolio loses value."""
        portfolio = Portfolio(initial_capital=Decimal("100000"))

        # Set peak equity higher
        portfolio.peak_equity = Decimal("120000")

        # Simulate loss - cash decreases
        portfolio.cash = Decimal("90000")  # Down to 90k from 120k peak
        portfolio._update_drawdown()

        # Should calculate drawdown
        expected_drawdown = Decimal("30000")  # 120k - 90k
        assert portfolio.current_drawdown == expected_drawdown
        assert portfolio.max_drawdown == expected_drawdown

        # Test percentage calculation
        expected_percent = (expected_drawdown / Decimal("120000")) * Decimal("100")
        assert portfolio.current_drawdown_percent == expected_percent

    def test_max_drawdown_tracking(self):
        """Test maximum drawdown tracking over time."""
        portfolio = Portfolio(initial_capital=Decimal("100000"))

        # Simulate series of gains and losses
        portfolio.peak_equity = Decimal("150000")

        # First drawdown
        portfolio.cash = Decimal("120000")
        portfolio._update_drawdown()
        first_drawdown = Decimal("30000")
        assert portfolio.current_drawdown == first_drawdown
        assert portfolio.max_drawdown == first_drawdown

        # Recovery (partial)
        portfolio.cash = Decimal("140000")
        portfolio._update_drawdown()
        current_drawdown = Decimal("10000")
        assert portfolio.current_drawdown == current_drawdown
        assert portfolio.max_drawdown == first_drawdown  # Max should remain

        # Larger drawdown
        portfolio.cash = Decimal("100000")
        portfolio._update_drawdown()
        larger_drawdown = Decimal("50000")
        assert portfolio.current_drawdown == larger_drawdown
        assert portfolio.max_drawdown == larger_drawdown  # Max should update

    def test_drawdown_with_positions(self):
        """Test drawdown calculation with open positions."""
        portfolio = Portfolio(initial_capital=Decimal("100000"))

        # Open a position
        timestamp = pd.Timestamp.now()
        position = portfolio.open_position(
            symbol="MNQ",
            side=PositionSide.LONG,
            quantity=1,
            price=Decimal("4000"),
            timestamp=timestamp,
        )

        # Initial state - drawdown from commission and slippage
        portfolio._update_drawdown()
        expected_drawdown = Decimal("2.25")  # $2.00 commission + $0.25 slippage
        assert portfolio.current_drawdown == expected_drawdown

        # Price moves against position
        prices = {"MNQ": Decimal("3900")}  # $100 loss per contract
        portfolio.update_prices(prices, timestamp)

        # Should reflect drawdown from position loss
        assert portfolio.current_drawdown > Decimal("0")
        assert portfolio.max_drawdown >= portfolio.current_drawdown

    def test_drawdown_reset_on_new_peak(self):
        """Test drawdown resets when new equity peak is reached."""
        portfolio = Portfolio(initial_capital=Decimal("100000"))

        # Simulate drawdown
        portfolio.peak_equity = Decimal("120000")
        portfolio.cash = Decimal("90000")
        portfolio._update_drawdown()

        assert portfolio.current_drawdown == Decimal("30000")

        # New peak reached
        portfolio.cash = Decimal("130000")
        portfolio._update_drawdown()

        # Current drawdown should reset, but max should remain
        assert portfolio.current_drawdown == Decimal("0")
        assert portfolio.peak_equity == Decimal("130000")
        assert portfolio.max_drawdown == Decimal("30000")  # Historical max preserved

    def test_drawdown_percentage_calculations(self):
        """Test drawdown percentage calculations."""
        portfolio = Portfolio(initial_capital=Decimal("100000"))

        # Set up scenario
        portfolio.peak_equity = Decimal("200000")
        portfolio.cash = Decimal("150000")
        portfolio._update_drawdown()

        # Check percentage calculations
        expected_current_percent = Decimal("25.00")  # (50k / 200k) * 100
        expected_max_percent = Decimal("25.00")

        assert portfolio.current_drawdown_percent == expected_current_percent
        assert portfolio.max_drawdown_percent == expected_max_percent

    def test_zero_peak_equity_edge_case(self):
        """Test drawdown calculation edge case with zero peak equity."""
        portfolio = Portfolio(initial_capital=Decimal("0"))

        # Should handle zero peak equity gracefully
        assert portfolio.current_drawdown_percent == Decimal("0")
        assert portfolio.max_drawdown_percent == Decimal("0")

    def test_drawdown_integration_with_update_prices(self):
        """Test drawdown integration with price updates."""
        portfolio = Portfolio(initial_capital=Decimal("100000"))
        timestamp = pd.Timestamp.now()

        # Open position
        position = portfolio.open_position(
            symbol="MNQ",
            side=PositionSide.LONG,
            quantity=2,
            price=Decimal("4000"),
            timestamp=timestamp,
        )

        # Update prices - should trigger drawdown update
        prices = {"MNQ": Decimal("3800")}  # $200 loss per contract * 2 = $400 loss
        portfolio.update_prices(prices, timestamp)

        # Verify drawdown was calculated
        expected_loss = Decimal("400")  # Plus commission
        assert portfolio.current_drawdown >= expected_loss
        assert portfolio.max_drawdown >= portfolio.current_drawdown

        # Verify equity curve and timestamps updated
        assert len(portfolio.equity_curve) >= 2  # Initial + update
        assert len(portfolio.timestamps) >= 1

    def test_complex_drawdown_scenario(self):
        """Test complex scenario with multiple positions and price movements."""
        portfolio = Portfolio(
            initial_capital=Decimal("100000"),
            commission_per_trade=Decimal("2.00"),
            slippage_per_trade=Decimal("0.25"),
        )

        timestamp = pd.Timestamp.now()

        # Open long position
        long_position = portfolio.open_position(
            symbol="MNQ",
            side=PositionSide.LONG,
            quantity=1,
            price=Decimal("4000"),
            timestamp=timestamp,
        )

        # Price goes up - should increase peak
        prices = {"MNQ": Decimal("4200")}
        portfolio.update_prices(prices, timestamp)
        initial_peak = portfolio.peak_equity

        # Price crashes - should create drawdown
        prices = {"MNQ": Decimal("3700")}
        portfolio.update_prices(prices, timestamp)

        # Verify significant drawdown
        assert portfolio.current_drawdown > Decimal("0")
        assert portfolio.current_drawdown_percent > Decimal("0")
        assert portfolio.max_drawdown > Decimal("0")

        # Close position at a loss
        portfolio.close_position(
            symbol="MNQ",
            price=Decimal("3700"),
            timestamp=timestamp,
            position=long_position,
        )

        # Drawdown should still be tracked
        assert portfolio.max_drawdown > Decimal("0")


class TestPortfolioMetricsIntegration:
    """Test portfolio metrics integration with drawdown."""

    def test_portfolio_metrics_include_drawdown(self):
        """Test that portfolio metrics include drawdown information."""
        portfolio = Portfolio(initial_capital=Decimal("100000"))

        # Create some drawdown
        portfolio.peak_equity = Decimal("120000")
        portfolio.cash = Decimal("90000")
        portfolio._update_drawdown()

        metrics = portfolio.get_portfolio_metrics()

        # Check that drawdown metrics are included
        assert "current_drawdown" in metrics
        assert "max_drawdown" in metrics
        assert "current_drawdown_percent" in metrics
        assert "max_drawdown_percent" in metrics
        assert "peak_equity" in metrics

        # Verify values
        assert metrics["current_drawdown"] == portfolio.current_drawdown
        assert metrics["max_drawdown"] == portfolio.max_drawdown
        assert metrics["peak_equity"] == portfolio.peak_equity
