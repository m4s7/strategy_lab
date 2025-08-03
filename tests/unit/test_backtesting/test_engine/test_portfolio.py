"""Tests for portfolio management."""

from decimal import Decimal

import pandas as pd
import pytest

from strategy_lab.backtesting.engine.portfolio import (
    Portfolio,
    Position,
    PositionSide,
)


class TestPosition:
    """Test Position functionality."""

    def test_position_creation(self):
        """Test creating a position."""
        position = Position(
            symbol="MNQ",
            side=PositionSide.LONG,
            quantity=10,
            entry_price=Decimal("100.00"),
            entry_time=pd.Timestamp("2024-01-01"),
            commission=Decimal("2.00"),
        )

        assert position.symbol == "MNQ"
        assert position.side == PositionSide.LONG
        assert position.quantity == 10
        assert position.is_open
        assert not position.is_closed

    def test_position_update_price(self):
        """Test updating position price and P&L."""
        position = Position(
            symbol="MNQ",
            side=PositionSide.LONG,
            quantity=10,
            entry_price=Decimal("100.00"),
            entry_time=pd.Timestamp("2024-01-01"),
            commission=Decimal("2.00"),
        )

        # Update price - profit scenario
        position.update_price(Decimal("105.00"))
        assert position.current_price == Decimal("105.00")
        # P&L = (105 - 100) * 10 - 2 = 48
        assert position.unrealized_pnl == Decimal("48.00")

        # Update price - loss scenario
        position.update_price(Decimal("95.00"))
        # P&L = (95 - 100) * 10 - 2 = -52
        assert position.unrealized_pnl == Decimal("-52.00")

    def test_short_position_pnl(self):
        """Test P&L calculation for short positions."""
        position = Position(
            symbol="MNQ",
            side=PositionSide.SHORT,
            quantity=10,
            entry_price=Decimal("100.00"),
            entry_time=pd.Timestamp("2024-01-01"),
            commission=Decimal("2.00"),
        )

        # Price drops - profit for short
        position.update_price(Decimal("95.00"))
        # P&L = (100 - 95) * 10 - 2 = 48
        assert position.unrealized_pnl == Decimal("48.00")

        # Price rises - loss for short
        position.update_price(Decimal("105.00"))
        # P&L = (100 - 105) * 10 - 2 = -52
        assert position.unrealized_pnl == Decimal("-52.00")

    def test_position_close(self):
        """Test closing a position."""
        position = Position(
            symbol="MNQ",
            side=PositionSide.LONG,
            quantity=10,
            entry_price=Decimal("100.00"),
            entry_time=pd.Timestamp("2024-01-01"),
            commission=Decimal("2.00"),
            slippage=Decimal("1.00"),
        )

        # Close with profit
        realized_pnl = position.close(
            exit_price=Decimal("110.00"), exit_time=pd.Timestamp("2024-01-02")
        )

        assert position.is_closed
        assert not position.is_open
        assert position.exit_price == Decimal("110.00")
        # P&L = (110 - 100) * 10 - 2 - 1 = 97
        assert position.realized_pnl == Decimal("97.00")
        assert position.unrealized_pnl == Decimal("0")
        assert realized_pnl == Decimal("97.00")

    def test_close_already_closed(self):
        """Test closing an already closed position."""
        position = Position(
            symbol="MNQ",
            side=PositionSide.LONG,
            quantity=10,
            entry_price=Decimal("100.00"),
            entry_time=pd.Timestamp("2024-01-01"),
        )

        # Close once
        position.close(Decimal("105.00"), pd.Timestamp("2024-01-02"))

        # Try to close again
        with pytest.raises(ValueError, match="Position already closed"):
            position.close(Decimal("106.00"), pd.Timestamp("2024-01-03"))


class TestPortfolio:
    """Test Portfolio functionality."""

    def test_portfolio_initialization(self):
        """Test portfolio initialization."""
        portfolio = Portfolio(
            initial_capital=Decimal("50000"),
            commission_per_trade=Decimal("1.50"),
            slippage_per_trade=Decimal("0.10"),
        )

        assert portfolio.cash == Decimal("50000")
        assert portfolio.initial_capital == Decimal("50000")
        assert portfolio.equity == Decimal("50000")
        assert portfolio.is_flat
        assert len(portfolio.equity_curve) == 1

    def test_open_position(self):
        """Test opening a position."""
        portfolio = Portfolio(initial_capital=Decimal("10000"))

        position = portfolio.open_position(
            symbol="MNQ",
            side=PositionSide.LONG,
            quantity=1,
            price=Decimal("100.00"),
            timestamp=pd.Timestamp("2024-01-01"),
        )

        assert position is not None
        assert portfolio.has_position("MNQ")
        assert portfolio.total_positions == 1
        assert not portfolio.is_flat

        # Cash reduced by position cost + commission + slippage
        # Cost = 100 * 1 + 2 + 0.25 * 1 = 102.25
        assert portfolio.cash == Decimal("9897.75")

    def test_insufficient_cash(self):
        """Test opening position with insufficient cash."""
        portfolio = Portfolio(initial_capital=Decimal("100"))

        with pytest.raises(ValueError, match="Insufficient cash"):
            portfolio.open_position(
                symbol="MNQ",
                side=PositionSide.LONG,
                quantity=10,
                price=Decimal("100.00"),
                timestamp=pd.Timestamp("2024-01-01"),
            )

    def test_close_position(self):
        """Test closing a position."""
        portfolio = Portfolio(initial_capital=Decimal("10000"))

        # Open position
        portfolio.open_position(
            symbol="MNQ",
            side=PositionSide.LONG,
            quantity=1,
            price=Decimal("100.00"),
            timestamp=pd.Timestamp("2024-01-01"),
        )

        # Close with profit
        closed_position = portfolio.close_position(
            symbol="MNQ", price=Decimal("110.00"), timestamp=pd.Timestamp("2024-01-02")
        )

        assert closed_position is not None
        assert closed_position.is_closed
        assert not portfolio.has_position("MNQ")
        assert portfolio.is_flat
        assert len(portfolio.closed_positions) == 1

        # Cash should increase by exit value + realized P&L
        # Initial: 9897.75, Exit: 110, P&L: 7.75
        # Final: 9897.75 + 110 + 7.75 = 10015.5
        assert portfolio.cash > portfolio.initial_capital

    def test_update_prices(self):
        """Test updating portfolio prices."""
        portfolio = Portfolio(initial_capital=Decimal("10000"))

        # Open two positions
        portfolio.open_position(
            symbol="MNQ",
            side=PositionSide.LONG,
            quantity=1,
            price=Decimal("100.00"),
            timestamp=pd.Timestamp("2024-01-01"),
        )

        portfolio.open_position(
            symbol="ES",
            side=PositionSide.SHORT,
            quantity=1,
            price=Decimal("4000.00"),
            timestamp=pd.Timestamp("2024-01-01"),
        )

        # Update prices
        prices = {"MNQ": Decimal("105.00"), "ES": Decimal("3990.00")}
        portfolio.update_prices(prices, pd.Timestamp("2024-01-02"))

        # Check positions updated
        mnq_position = portfolio.get_position("MNQ")
        es_position = portfolio.get_position("ES")

        assert mnq_position.current_price == Decimal("105.00")
        assert es_position.current_price == Decimal("3990.00")

        # Check equity curve updated
        assert len(portfolio.equity_curve) == 2
        assert len(portfolio.timestamps) == 1

    def test_portfolio_metrics(self):
        """Test portfolio metrics calculation."""
        portfolio = Portfolio(initial_capital=Decimal("10000"))

        # Open and close some positions
        portfolio.open_position(
            symbol="MNQ",
            side=PositionSide.LONG,
            quantity=1,
            price=Decimal("100.00"),
            timestamp=pd.Timestamp("2024-01-01"),
        )

        portfolio.close_position(
            symbol="MNQ", price=Decimal("110.00"), timestamp=pd.Timestamp("2024-01-02")
        )

        # Open another position
        portfolio.open_position(
            symbol="MNQ",
            side=PositionSide.SHORT,
            quantity=1,
            price=Decimal("110.00"),
            timestamp=pd.Timestamp("2024-01-03"),
        )

        # Get metrics
        metrics = portfolio.get_portfolio_metrics()

        assert metrics["initial_capital"] == 10000.0
        assert metrics["open_positions"] == 1
        assert metrics["closed_positions"] == 1
        assert metrics["total_trades"] == 2
        assert metrics["realized_pnl"] > 0  # First trade was profitable

    def test_portfolio_reset(self):
        """Test resetting portfolio."""
        portfolio = Portfolio(initial_capital=Decimal("10000"))

        # Make some trades
        portfolio.open_position(
            symbol="MNQ",
            side=PositionSide.LONG,
            quantity=1,
            price=Decimal("100.00"),
            timestamp=pd.Timestamp("2024-01-01"),
        )

        # Reset
        portfolio.reset()

        assert portfolio.cash == portfolio.initial_capital
        assert len(portfolio.positions) == 0
        assert len(portfolio.closed_positions) == 0
        assert portfolio.is_flat
        assert len(portfolio.equity_curve) == 1
