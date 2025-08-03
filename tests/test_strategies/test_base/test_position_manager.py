"""Tests for PositionManager and related position tracking components."""

from unittest.mock import Mock

import pytest

from src.strategy_lab.backtesting.hft_integration.event_processor import Fill, OrderSide
from src.strategy_lab.strategies.base import (
    PositionInfo,
    PositionManager,
    PositionSide,
    RiskLimits,
)


class TestRiskLimits:
    """Test RiskLimits dataclass."""

    def test_default_risk_limits(self):
        """Test creating risk limits with default values."""
        limits = RiskLimits()

        assert limits.max_position_size == 10
        assert limits.max_daily_loss == 1000.0
        assert limits.max_drawdown == 2000.0
        assert limits.position_stop_loss_pct == 0.02
        assert limits.position_take_profit_pct == 0.04

    def test_custom_risk_limits(self):
        """Test creating risk limits with custom values."""
        limits = RiskLimits(
            max_position_size=5, max_daily_loss=500.0, position_stop_loss_pct=0.01
        )

        assert limits.max_position_size == 5
        assert limits.max_daily_loss == 500.0
        assert limits.position_stop_loss_pct == 0.01

    def test_risk_limits_validation_success(self):
        """Test successful risk limits validation."""
        limits = RiskLimits()
        assert limits.validate() is True

    def test_risk_limits_validation_failures(self):
        """Test risk limits validation with invalid parameters."""

        # Invalid max_position_size
        limits = RiskLimits(max_position_size=0)
        with pytest.raises(ValueError, match="max_position_size must be positive"):
            limits.validate()

        # Invalid stop loss percentage
        limits = RiskLimits(position_stop_loss_pct=1.5)
        with pytest.raises(
            ValueError, match="position_stop_loss_pct must be between 0 and 1"
        ):
            limits.validate()


class TestPositionInfo:
    """Test PositionInfo dataclass."""

    def test_default_position_info(self):
        """Test position info with default values."""
        position = PositionInfo()

        assert position.quantity == 0
        assert position.average_price == 0.0
        assert position.side == PositionSide.FLAT
        assert position.is_flat is True
        assert position.is_long is False
        assert position.is_short is False
        assert position.abs_quantity == 0
        assert position.net_pnl == 0.0
        assert position.return_pct == 0.0

    def test_long_position_info(self):
        """Test position info for long position."""
        position = PositionInfo(
            quantity=5, average_price=13000.0, unrealized_pnl=250.0, realized_pnl=100.0
        )

        assert position.side == PositionSide.LONG
        assert position.is_long is True
        assert position.is_flat is False
        assert position.is_short is False
        assert position.abs_quantity == 5
        assert position.net_pnl == 350.0  # 250 + 100

    def test_short_position_info(self):
        """Test position info for short position."""
        position = PositionInfo(
            quantity=-3, average_price=13000.0, unrealized_pnl=-150.0, realized_pnl=50.0
        )

        assert position.side == PositionSide.SHORT
        assert position.is_short is True
        assert position.is_flat is False
        assert position.is_long is False
        assert position.abs_quantity == 3
        assert position.net_pnl == -100.0  # -150 + 50

    def test_return_percentage_calculation(self):
        """Test return percentage calculation."""
        position = PositionInfo(
            quantity=2,
            total_cost=26000.0,  # 2 * 13000
            realized_pnl=500.0,
            unrealized_pnl=300.0,
        )

        expected_return = (800.0 / 26000.0) * 100  # (500 + 300) / 26000 * 100
        assert abs(position.return_pct - expected_return) < 0.01

        # Test with zero cost
        position.total_cost = 0.0
        assert position.return_pct == 0.0


class TestPositionManager:
    """Test PositionManager class."""

    @pytest.fixture
    def config(self):
        """Create mock config for testing."""
        config = Mock()
        config.max_position_size = 5
        config.max_daily_loss = 1000.0
        config.stop_loss_pct = 0.02
        return config

    @pytest.fixture
    def position_manager(self, config):
        """Create position manager for testing."""
        return PositionManager(config)

    def test_initialization(self, position_manager, config):
        """Test position manager initialization."""
        assert position_manager.config == config
        assert position_manager.risk_limits.max_position_size == 5
        assert position_manager.risk_limits.max_daily_loss == 1000.0
        assert position_manager.risk_limits.position_stop_loss_pct == 0.02
        assert position_manager.position.is_flat is True
        assert len(position_manager.fill_history) == 0
        assert position_manager.daily_pnl == 0.0

    def test_opening_long_position(self, position_manager):
        """Test opening a long position."""
        fill = Fill(
            order_id=123,
            timestamp=1609459200000000000,
            price=13000.0,
            quantity=3,
            side=OrderSide.BUY,
            commission=3.0,
        )

        position_manager.process_fill(fill)

        assert position_manager.position.quantity == 3
        assert position_manager.position.average_price == 13000.0
        assert position_manager.position.total_cost == 39000.0  # 3 * 13000
        assert position_manager.position.is_long is True
        assert len(position_manager.fill_history) == 1

    def test_opening_short_position(self, position_manager):
        """Test opening a short position."""
        fill = Fill(
            order_id=124,
            timestamp=1609459200000000000,
            price=13000.0,
            quantity=2,
            side=OrderSide.SELL,
            commission=2.0,
        )

        position_manager.process_fill(fill)

        assert position_manager.position.quantity == -2
        assert position_manager.position.average_price == 13000.0
        assert position_manager.position.total_cost == 26000.0  # 2 * 13000
        assert position_manager.position.is_short is True

    def test_adding_to_long_position(self, position_manager):
        """Test adding to an existing long position."""
        # Open initial position
        fill1 = Fill(
            order_id=123,
            timestamp=1609459200000000000,
            price=13000.0,
            quantity=2,
            side=OrderSide.BUY,
            commission=2.0,
        )
        position_manager.process_fill(fill1)

        # Add to position at different price
        fill2 = Fill(
            order_id=124,
            timestamp=1609459200000000000,
            price=13100.0,
            quantity=1,
            side=OrderSide.BUY,
            commission=1.0,
        )
        position_manager.process_fill(fill2)

        assert position_manager.position.quantity == 3
        # Weighted average: (2*13000 + 1*13100) / 3 = 39100/3
        expected_avg = 39100.0 / 3
        assert abs(position_manager.position.average_price - expected_avg) < 0.01
        assert position_manager.position.total_cost == 39100.0

    def test_closing_long_position(self, position_manager):
        """Test completely closing a long position."""
        # Open long position
        open_fill = Fill(
            order_id=123,
            timestamp=1609459200000000000,
            price=13000.0,
            quantity=3,
            side=OrderSide.BUY,
            commission=3.0,
        )
        position_manager.process_fill(open_fill)

        # Close position at profit
        close_fill = Fill(
            order_id=124,
            timestamp=1609459200000000000,
            price=13100.0,
            quantity=3,
            side=OrderSide.SELL,
            commission=3.0,
        )
        position_manager.process_fill(close_fill)

        assert position_manager.position.is_flat is True
        assert position_manager.position.quantity == 0
        assert position_manager.position.average_price == 0.0
        # Profit: (13100 - 13000) * 3 = 300
        assert position_manager.position.realized_pnl == 300.0
        assert position_manager.position.unrealized_pnl == 0.0

    def test_partial_position_reduction(self, position_manager):
        """Test partially reducing a position."""
        # Open position
        open_fill = Fill(
            order_id=123,
            timestamp=1609459200000000000,
            price=13000.0,
            quantity=4,
            side=OrderSide.BUY,
            commission=4.0,
        )
        position_manager.process_fill(open_fill)

        # Partial close
        partial_fill = Fill(
            order_id=124,
            timestamp=1609459200000000000,
            price=13050.0,
            quantity=1,
            side=OrderSide.SELL,
            commission=1.0,
        )
        position_manager.process_fill(partial_fill)

        assert position_manager.position.quantity == 3
        assert position_manager.position.average_price == 13000.0  # Unchanged
        # Realized P&L: (13050 - 13000) * 1 = 50
        assert position_manager.position.realized_pnl == 50.0
        # Total cost reduced proportionally: 52000 * (3/4) = 39000
        assert position_manager.position.total_cost == 39000.0

    def test_position_reversal(self, position_manager):
        """Test reversing position (long to short)."""
        # Open long position
        open_fill = Fill(
            order_id=123,
            timestamp=1609459200000000000,
            price=13000.0,
            quantity=2,
            side=OrderSide.BUY,
            commission=2.0,
        )
        position_manager.process_fill(open_fill)

        # Reverse to short (sell more than position size)
        reverse_fill = Fill(
            order_id=124,
            timestamp=1609459200000000000,
            price=13050.0,
            quantity=5,  # Sell 5, was long 2, now short 3
            side=OrderSide.SELL,
            commission=5.0,
        )
        position_manager.process_fill(reverse_fill)

        assert position_manager.position.quantity == -3  # Short 3
        assert position_manager.position.average_price == 13050.0  # New position price
        # Realized P&L from closing long: (13050 - 13000) * 2 = 100
        assert position_manager.position.realized_pnl == 100.0
        # New position cost: 3 * 13050 = 39150
        assert position_manager.position.total_cost == 39150.0

    def test_update_current_price(self, position_manager):
        """Test updating current price and unrealized P&L."""
        # Open long position
        fill = Fill(
            order_id=123,
            timestamp=1609459200000000000,
            price=13000.0,
            quantity=2,
            side=OrderSide.BUY,
            commission=2.0,
        )
        position_manager.process_fill(fill)

        # Update price
        position_manager.update_current_price(13100.0)

        assert position_manager.position.current_price == 13100.0
        # Unrealized P&L: (13100 - 13000) * 2 = 200
        assert position_manager.position.unrealized_pnl == 200.0
        # Market value: 2 * 13100 = 26200
        assert position_manager.position.market_value == 26200.0

        # Test with short position
        position_manager.position.quantity = -2
        position_manager.update_current_price(12900.0)  # Price down, profit for short

        # Unrealized P&L for short: (13000 - 12900) * 2 = 200
        assert position_manager.position.unrealized_pnl == 200.0

    def test_can_enter_position_checks(self, position_manager):
        """Test position entry validation."""

        # Should allow normal position entry
        assert position_manager.can_enter_long(3) is True
        assert position_manager.can_enter_short(3) is True

        # Should reject oversized position
        assert (
            position_manager.can_enter_long(10) is False
        )  # Exceeds max_position_size=5
        assert position_manager.can_enter_short(10) is False

        # Test with existing position
        fill = Fill(
            order_id=123,
            timestamp=1609459200000000000,
            price=13000.0,
            quantity=3,
            side=OrderSide.BUY,
            commission=3.0,
        )
        position_manager.process_fill(fill)

        # Should allow adding within limits
        assert position_manager.can_add_to_long(2) is True  # 3 + 2 = 5 (at limit)
        assert position_manager.can_add_to_long(3) is False  # 3 + 3 = 6 (exceeds)

        # Should not allow adding to wrong side
        assert position_manager.can_add_to_short(1) is False  # Currently long

    def test_stop_loss_triggers(self, position_manager):
        """Test stop loss trigger conditions."""

        # Open position
        fill = Fill(
            order_id=123,
            timestamp=1609459200000000000,
            price=13000.0,
            quantity=2,
            side=OrderSide.BUY,
            commission=2.0,
        )
        position_manager.process_fill(fill)

        # No stop loss initially
        position_manager.update_current_price(13000.0)
        assert position_manager.should_stop_out() is False

        # Trigger position stop loss (2% = 0.02, so 2% of 26000 = 520)
        # Need loss > 520, so price needs to drop by > 260 per contract
        # 13000 - 260 = 12740, but use 12500 to be sure
        position_manager.update_current_price(12500.0)
        assert position_manager.should_stop_out() is True

        # Test daily loss limit
        position_manager.daily_pnl = -1500.0  # Exceeds max_daily_loss=1000
        assert position_manager.should_stop_out() is True

    def test_take_profit_triggers(self, position_manager):
        """Test take profit trigger conditions."""

        # Open position
        fill = Fill(
            order_id=123,
            timestamp=1609459200000000000,
            price=13000.0,
            quantity=2,
            side=OrderSide.BUY,
            commission=2.0,
        )
        position_manager.process_fill(fill)

        # No profit taking initially
        position_manager.update_current_price(13000.0)
        assert position_manager.should_take_profit() is False

        # Trigger take profit (4% = 0.04, so 4% of 26000 = 1040)
        # Need profit > 1040, so price needs to rise by > 520 per contract
        # 13000 + 520 = 13520, but use 13600 to be sure
        position_manager.update_current_price(13600.0)
        assert position_manager.should_take_profit() is True

    def test_get_position_info(self, position_manager):
        """Test getting position info copy."""

        # Open position
        fill = Fill(
            order_id=123,
            timestamp=1609459200000000000,
            price=13000.0,
            quantity=3,
            side=OrderSide.BUY,
            commission=3.0,
        )
        position_manager.process_fill(fill)
        position_manager.update_current_price(13100.0)

        position_info = position_manager.get_position_info()

        assert isinstance(position_info, PositionInfo)
        assert position_info.quantity == 3
        assert position_info.average_price == 13000.0
        assert position_info.current_price == 13100.0
        assert position_info.unrealized_pnl == 300.0  # (13100-13000)*3

        # Verify it's a copy (modifications don't affect original)
        position_info.quantity = 999
        assert position_manager.position.quantity == 3

    def test_get_risk_metrics(self, position_manager):
        """Test getting risk metrics."""

        # Open position and set some state
        fill = Fill(
            order_id=123,
            timestamp=1609459200000000000,
            price=13000.0,
            quantity=4,
            side=OrderSide.BUY,
            commission=4.0,
        )
        position_manager.process_fill(fill)
        position_manager.update_current_price(13100.0)
        position_manager.peak_pnl = 500.0
        position_manager.max_drawdown = 200.0

        metrics = position_manager.get_risk_metrics()

        assert metrics["position_size"] == 4
        assert metrics["max_position_size"] == 5
        assert metrics["position_utilization"] == 80.0  # 4/5 * 100
        assert metrics["peak_pnl"] == 500.0
        assert metrics["max_drawdown"] == 200.0
        assert "daily_pnl" in metrics
        assert "net_pnl" in metrics
        assert "return_pct" in metrics

    def test_reset_daily_metrics(self, position_manager):
        """Test resetting daily metrics."""

        # Set some daily metrics
        position_manager.daily_pnl = 150.0
        position_manager.peak_pnl = 200.0
        position_manager.current_drawdown = 50.0

        position_manager.reset_daily_metrics()

        assert position_manager.daily_pnl == 0.0
        assert position_manager.peak_pnl == 0.0
        assert position_manager.current_drawdown == 0.0

    def test_drawdown_tracking(self, position_manager):
        """Test drawdown calculation and tracking."""

        # Open position
        fill = Fill(
            order_id=123,
            timestamp=1609459200000000000,
            price=13000.0,
            quantity=2,
            side=OrderSide.BUY,
            commission=2.0,
        )
        position_manager.process_fill(fill)

        # Price goes up - establish peak
        position_manager.update_current_price(13200.0)  # +400 unrealized
        assert position_manager.peak_pnl == 400.0
        assert position_manager.current_drawdown == 0.0

        # Price comes down - create drawdown
        position_manager.update_current_price(13100.0)  # +200 unrealized
        assert position_manager.peak_pnl == 400.0  # Peak unchanged
        assert position_manager.current_drawdown == 200.0  # 400 - 200
        assert position_manager.max_drawdown == 200.0

        # Price goes down further - increase drawdown
        position_manager.update_current_price(12950.0)  # -100 unrealized
        assert position_manager.current_drawdown == 500.0  # 400 - (-100)
        assert position_manager.max_drawdown == 500.0

        # Price recovers to new high - reset drawdown
        position_manager.update_current_price(13300.0)  # +600 unrealized
        assert position_manager.peak_pnl == 600.0
        assert position_manager.current_drawdown == 0.0
        assert position_manager.max_drawdown == 500.0  # Historical max preserved

    def test_empty_position_price_update(self, position_manager):
        """Test price updates with no position."""

        position_manager.update_current_price(13100.0)

        assert position_manager.position.current_price == 13100.0
        assert position_manager.position.unrealized_pnl == 0.0
        assert position_manager.position.market_value == 0.0
