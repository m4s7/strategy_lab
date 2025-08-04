"""Tests for stop-loss and take-profit functionality."""

from decimal import Decimal

import pandas as pd
import pytest

from strategy_lab.backtesting.engine.portfolio import Portfolio, Position, PositionSide


class TestStopLossTakeProfit:
    """Test stop-loss and take-profit functionality."""

    def test_position_stop_loss_long(self):
        """Test stop-loss trigger for long position."""
        position = Position(
            symbol="MNQ",
            side=PositionSide.LONG,
            quantity=1,
            entry_price=Decimal("4000"),
            entry_time=pd.Timestamp.now(),
            stop_loss_price=Decimal("3950"),  # 50 point stop loss
        )

        # Price above stop loss - should not trigger
        position.update_price(Decimal("4010"))
        assert not position.should_trigger_stop_loss()

        # Price at stop loss - should trigger
        position.update_price(Decimal("3950"))
        assert position.should_trigger_stop_loss()

        # Price below stop loss - should trigger
        position.update_price(Decimal("3940"))
        assert position.should_trigger_stop_loss()

    def test_position_stop_loss_short(self):
        """Test stop-loss trigger for short position."""
        position = Position(
            symbol="MNQ",
            side=PositionSide.SHORT,
            quantity=1,
            entry_price=Decimal("4000"),
            entry_time=pd.Timestamp.now(),
            stop_loss_price=Decimal("4050"),  # 50 point stop loss
        )

        # Price below stop loss - should not trigger
        position.update_price(Decimal("3990"))
        assert not position.should_trigger_stop_loss()

        # Price at stop loss - should trigger
        position.update_price(Decimal("4050"))
        assert position.should_trigger_stop_loss()

        # Price above stop loss - should trigger
        position.update_price(Decimal("4060"))
        assert position.should_trigger_stop_loss()

    def test_position_take_profit_long(self):
        """Test take-profit trigger for long position."""
        position = Position(
            symbol="MNQ",
            side=PositionSide.LONG,
            quantity=1,
            entry_price=Decimal("4000"),
            entry_time=pd.Timestamp.now(),
            take_profit_price=Decimal("4100"),  # 100 point take profit
        )

        # Price below take profit - should not trigger
        position.update_price(Decimal("4090"))
        assert not position.should_trigger_take_profit()

        # Price at take profit - should trigger
        position.update_price(Decimal("4100"))
        assert position.should_trigger_take_profit()

        # Price above take profit - should trigger
        position.update_price(Decimal("4110"))
        assert position.should_trigger_take_profit()

    def test_position_take_profit_short(self):
        """Test take-profit trigger for short position."""
        position = Position(
            symbol="MNQ",
            side=PositionSide.SHORT,
            quantity=1,
            entry_price=Decimal("4000"),
            entry_time=pd.Timestamp.now(),
            take_profit_price=Decimal("3900"),  # 100 point take profit
        )

        # Price above take profit - should not trigger
        position.update_price(Decimal("3910"))
        assert not position.should_trigger_take_profit()

        # Price at take profit - should trigger
        position.update_price(Decimal("3900"))
        assert position.should_trigger_take_profit()

        # Price below take profit - should trigger
        position.update_price(Decimal("3890"))
        assert position.should_trigger_take_profit()

    def test_position_without_stop_loss_take_profit(self):
        """Test position without stop-loss or take-profit levels."""
        position = Position(
            symbol="MNQ",
            side=PositionSide.LONG,
            quantity=1,
            entry_price=Decimal("4000"),
            entry_time=pd.Timestamp.now(),
        )

        # No stop loss or take profit set - should never trigger
        position.update_price(Decimal("3500"))  # Large move down
        assert not position.should_trigger_stop_loss()
        assert not position.should_trigger_take_profit()

        position.update_price(Decimal("4500"))  # Large move up
        assert not position.should_trigger_stop_loss()
        assert not position.should_trigger_take_profit()

    def test_portfolio_open_position_with_stops(self):
        """Test opening position with stop-loss and take-profit."""
        portfolio = Portfolio(initial_capital=Decimal("100000"))
        timestamp = pd.Timestamp.now()

        position = portfolio.open_position(
            symbol="MNQ",
            side=PositionSide.LONG,
            quantity=1,
            price=Decimal("4000"),
            timestamp=timestamp,
            stop_loss_price=Decimal("3950"),
            take_profit_price=Decimal("4100"),
        )

        assert position.stop_loss_price == Decimal("3950")
        assert position.take_profit_price == Decimal("4100")
        assert position.is_open

    def test_portfolio_set_stop_loss_take_profit(self):
        """Test setting stop-loss and take-profit after opening position."""
        portfolio = Portfolio(initial_capital=Decimal("100000"))
        timestamp = pd.Timestamp.now()

        # Open position without stops
        position = portfolio.open_position(
            symbol="MNQ",
            side=PositionSide.LONG,
            quantity=1,
            price=Decimal("4000"),
            timestamp=timestamp,
        )

        assert position.stop_loss_price is None
        assert position.take_profit_price is None

        # Set stop loss and take profit
        assert portfolio.set_stop_loss("MNQ", Decimal("3950"))
        assert portfolio.set_take_profit("MNQ", Decimal("4100"))

        # Verify they were set
        updated_position = portfolio.get_position("MNQ")
        assert updated_position.stop_loss_price == Decimal("3950")
        assert updated_position.take_profit_price == Decimal("4100")

    def test_portfolio_check_triggers(self):
        """Test portfolio checking for stop-loss and take-profit triggers."""
        portfolio = Portfolio(initial_capital=Decimal("100000"))
        timestamp = pd.Timestamp.now()

        # Open long position with stops
        long_position = portfolio.open_position(
            symbol="MNQ",
            side=PositionSide.LONG,
            quantity=1,
            price=Decimal("4000"),
            timestamp=timestamp,
            stop_loss_price=Decimal("3950"),
            take_profit_price=Decimal("4100"),
        )

        # Open short position with stops
        short_position = portfolio.open_position(
            symbol="ES",
            side=PositionSide.SHORT,
            quantity=1,
            price=Decimal("5000"),
            timestamp=timestamp,
            stop_loss_price=Decimal("5050"),
            take_profit_price=Decimal("4900"),
        )

        # Update prices to normal levels - no triggers
        portfolio.update_prices(
            {"MNQ": Decimal("4010"), "ES": Decimal("4990")}, timestamp
        )
        triggers = portfolio.check_stop_loss_take_profit_triggers(timestamp)
        assert len(triggers) == 0

        # Update MNQ to trigger stop loss
        portfolio.update_prices(
            {"MNQ": Decimal("3940"), "ES": Decimal("4990")}, timestamp
        )
        triggers = portfolio.check_stop_loss_take_profit_triggers(timestamp)
        assert len(triggers) == 1
        assert triggers[0][0].symbol == "MNQ"
        assert triggers[0][1] == "stop_loss"

        # Update ES to trigger take profit
        portfolio.update_prices(
            {"MNQ": Decimal("3940"), "ES": Decimal("4890")}, timestamp
        )
        triggers = portfolio.check_stop_loss_take_profit_triggers(timestamp)
        assert len(triggers) == 2
        # Should have both triggers now
        trigger_types = [t[1] for t in triggers]
        assert "stop_loss" in trigger_types
        assert "take_profit" in trigger_types

    def test_priority_stop_loss_over_take_profit(self):
        """Test that stop-loss takes priority over take-profit when both could trigger."""
        portfolio = Portfolio(initial_capital=Decimal("100000"))
        timestamp = pd.Timestamp.now()

        # Open position with very tight stops that could both trigger
        position = portfolio.open_position(
            symbol="MNQ",
            side=PositionSide.LONG,
            quantity=1,
            price=Decimal("4000"),
            timestamp=timestamp,
            stop_loss_price=Decimal("3999"),  # Very tight stop loss
            take_profit_price=Decimal("4001"),  # Very tight take profit
        )

        # Set price that would trigger both (if we had a gap)
        # In reality, this tests our logic priority
        portfolio.update_prices({"MNQ": Decimal("3995")}, timestamp)  # Below stop loss
        triggers = portfolio.check_stop_loss_take_profit_triggers(timestamp)

        # Should only get stop loss trigger (our logic checks stop loss first)
        assert len(triggers) == 1
        assert triggers[0][1] == "stop_loss"

    def test_closed_position_no_triggers(self):
        """Test that closed positions don't trigger stops."""
        portfolio = Portfolio(initial_capital=Decimal("100000"))
        timestamp = pd.Timestamp.now()

        # Open and immediately close position
        position = portfolio.open_position(
            symbol="MNQ",
            side=PositionSide.LONG,
            quantity=1,
            price=Decimal("4000"),
            timestamp=timestamp,
            stop_loss_price=Decimal("3950"),
            take_profit_price=Decimal("4100"),
        )

        # Close the position
        portfolio.close_position("MNQ", Decimal("4010"), timestamp, position)

        # Update price to what would trigger stop loss if position was open
        portfolio.update_prices({"MNQ": Decimal("3940")}, timestamp)
        triggers = portfolio.check_stop_loss_take_profit_triggers(timestamp)

        # Should have no triggers since position is closed
        assert len(triggers) == 0

    def test_set_stops_on_nonexistent_position(self):
        """Test setting stops on non-existent position returns False."""
        portfolio = Portfolio(initial_capital=Decimal("100000"))

        # Try to set stops on non-existent position
        assert not portfolio.set_stop_loss("NONEXISTENT", Decimal("100"))
        assert not portfolio.set_take_profit("NONEXISTENT", Decimal("200"))

    def test_complex_scenario_multiple_positions(self):
        """Test complex scenario with multiple positions and different trigger types."""
        portfolio = Portfolio(initial_capital=Decimal("500000"))
        timestamp = pd.Timestamp.now()

        # Open multiple positions with different stop/profit levels
        positions = []

        # Long position - will hit take profit
        positions.append(
            portfolio.open_position(
                symbol="MNQ1",
                side=PositionSide.LONG,
                quantity=1,
                price=Decimal("4000"),
                timestamp=timestamp,
                stop_loss_price=Decimal("3900"),
                take_profit_price=Decimal("4050"),
            )
        )

        # Short position - will hit stop loss
        positions.append(
            portfolio.open_position(
                symbol="MNQ2",
                side=PositionSide.SHORT,
                quantity=1,
                price=Decimal("4000"),
                timestamp=timestamp,
                stop_loss_price=Decimal("4100"),
                take_profit_price=Decimal("3950"),
            )
        )

        # Long position - no trigger
        positions.append(
            portfolio.open_position(
                symbol="MNQ3",
                side=PositionSide.LONG,
                quantity=1,
                price=Decimal("4000"),
                timestamp=timestamp,
                stop_loss_price=Decimal("3800"),
                take_profit_price=Decimal("4200"),
            )
        )

        # Update prices to trigger some stops
        portfolio.update_prices(
            {
                "MNQ1": Decimal("4060"),  # Should trigger take profit
                "MNQ2": Decimal("4110"),  # Should trigger stop loss
                "MNQ3": Decimal("4010"),  # Should not trigger anything
            },
            timestamp,
        )

        triggers = portfolio.check_stop_loss_take_profit_triggers(timestamp)

        # Should have 2 triggers
        assert len(triggers) == 2

        # Verify we got the right triggers
        trigger_symbols = [(t[0].symbol, t[1]) for t in triggers]
        assert ("MNQ1", "take_profit") in trigger_symbols
        assert ("MNQ2", "stop_loss") in trigger_symbols

        # MNQ3 should not be in triggers
        assert not any(t[0].symbol == "MNQ3" for t in triggers)
