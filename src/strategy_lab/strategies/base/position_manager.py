"""Position management utilities for trading strategies.

This module provides position tracking, risk management, and P&L calculation
functionality that strategies can use to manage their market exposure.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

from ...backtesting.hft_integration.event_processor import Fill

logger = logging.getLogger(__name__)


class PositionSide(Enum):
    """Position side indicators."""

    FLAT = "flat"
    LONG = "long"
    SHORT = "short"


@dataclass
class RiskLimits:
    """Risk management limits configuration."""

    max_position_size: int = 10
    max_daily_loss: float = 1000.0
    max_drawdown: float = 2000.0
    position_stop_loss_pct: float = 0.02  # 2%
    position_take_profit_pct: float = 0.04  # 4%

    def validate(self) -> bool:
        """Validate risk limit parameters."""
        errors = []

        if self.max_position_size <= 0:
            errors.append("max_position_size must be positive")

        if self.max_daily_loss <= 0:
            errors.append("max_daily_loss must be positive")

        if self.max_drawdown <= 0:
            errors.append("max_drawdown must be positive")

        if not (0 < self.position_stop_loss_pct < 1):
            errors.append("position_stop_loss_pct must be between 0 and 1")

        if not (0 < self.position_take_profit_pct < 1):
            errors.append("position_take_profit_pct must be between 0 and 1")

        if errors:
            raise ValueError(f"Risk limits validation failed: {'; '.join(errors)}")

        return True


@dataclass
class PositionInfo:
    """Current position information."""

    quantity: int = 0
    average_price: float = 0.0
    market_value: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    total_cost: float = 0.0
    current_price: float = 0.0

    @property
    def side(self) -> PositionSide:
        """Get position side."""
        if self.quantity == 0:
            return PositionSide.FLAT
        if self.quantity > 0:
            return PositionSide.LONG
        return PositionSide.SHORT

    @property
    def is_flat(self) -> bool:
        """Check if position is flat."""
        return self.quantity == 0

    @property
    def is_long(self) -> bool:
        """Check if position is long."""
        return self.quantity > 0

    @property
    def is_short(self) -> bool:
        """Check if position is short."""
        return self.quantity < 0

    @property
    def abs_quantity(self) -> int:
        """Get absolute position size."""
        return abs(self.quantity)

    @property
    def net_pnl(self) -> float:
        """Get total P&L (realized + unrealized)."""
        return self.realized_pnl + self.unrealized_pnl

    @property
    def return_pct(self) -> float:
        """Get return percentage based on cost basis."""
        if self.total_cost == 0:
            return 0.0
        return (self.net_pnl / abs(self.total_cost)) * 100


class PositionManager:
    """Position tracking and risk management for trading strategies."""

    def __init__(self, config: Any):
        """Initialize position manager with configuration.

        Args:
            config: Strategy configuration object
        """
        self.config = config

        # Initialize risk limits from config
        self.risk_limits = RiskLimits(
            max_position_size=getattr(config, "max_position_size", 10),
            max_daily_loss=getattr(config, "max_daily_loss", 1000.0),
            position_stop_loss_pct=getattr(config, "stop_loss_pct", 0.02),
        )

        # Validate risk limits
        self.risk_limits.validate()

        # Position state
        self.position = PositionInfo()

        # Trade tracking
        self.fill_history: list[Fill] = []
        self.daily_pnl: float = 0.0
        self.peak_pnl: float = 0.0
        self.current_drawdown: float = 0.0
        self.max_drawdown: float = 0.0

        logger.debug("Initialized PositionManager")

    def process_fill(self, fill: Fill) -> None:
        """Process an order fill and update position.

        Args:
            fill: Order fill to process
        """
        self.fill_history.append(fill)

        fill_value = fill.quantity * fill.side.value

        if self.position.is_flat:
            # Opening new position
            self.position.quantity = fill_value
            self.position.average_price = fill.price
            self.position.total_cost = abs(fill_value * fill.price)

            logger.debug(
                "Opened position: %s %d @ %.2f",
                "LONG" if fill_value > 0 else "SHORT",
                abs(fill_value),
                fill.price,
            )

        elif (fill_value > 0) == (self.position.quantity > 0):
            # Adding to existing position
            old_cost = self.position.total_cost
            add_cost = abs(fill_value * fill.price)
            new_quantity = self.position.quantity + fill_value

            # Update average price using weighted average
            self.position.average_price = (old_cost + add_cost) / abs(new_quantity)
            self.position.quantity = new_quantity
            self.position.total_cost = old_cost + add_cost

            logger.debug(
                "Added to position: %d @ %.2f (Total: %d @ %.2f)",
                abs(fill_value),
                fill.price,
                abs(new_quantity),
                self.position.average_price,
            )

        else:
            # Reducing or closing position
            old_quantity = self.position.quantity
            new_quantity = self.position.quantity + fill_value

            if new_quantity == 0:
                # Position fully closed
                realized_pnl = self._calculate_realized_pnl(fill, abs(old_quantity))
                self.position.realized_pnl += realized_pnl
                self.position.quantity = 0
                self.position.average_price = 0.0
                self.position.total_cost = 0.0
                self.position.unrealized_pnl = 0.0

                logger.debug(
                    "Closed position: %d @ %.2f (Realized P&L: %.2f)",
                    abs(old_quantity),
                    fill.price,
                    realized_pnl,
                )

            elif abs(new_quantity) < abs(old_quantity):
                # Partial position reduction
                closed_quantity = abs(fill_value)
                realized_pnl = self._calculate_realized_pnl(fill, closed_quantity)
                self.position.realized_pnl += realized_pnl
                self.position.quantity = new_quantity

                # Update total cost proportionally
                remaining_ratio = abs(new_quantity) / abs(old_quantity)
                self.position.total_cost *= remaining_ratio

                logger.debug(
                    "Reduced position: %d @ %.2f (Remaining: %d, Realized P&L: %.2f)",
                    closed_quantity,
                    fill.price,
                    abs(new_quantity),
                    realized_pnl,
                )

            else:
                # Position reversed (closed and reopened in opposite direction)
                # First close the existing position
                closed_quantity = abs(old_quantity)
                realized_pnl = self._calculate_realized_pnl(fill, closed_quantity)
                self.position.realized_pnl += realized_pnl

                # Then open new position in opposite direction
                remaining_quantity = abs(fill_value) - closed_quantity
                self.position.quantity = remaining_quantity * (
                    1 if fill_value > 0 else -1
                )
                self.position.average_price = fill.price
                self.position.total_cost = remaining_quantity * fill.price

                logger.debug(
                    "Reversed position: Closed %d, Opened %d @ %.2f (Realized P&L: %.2f)",
                    closed_quantity,
                    remaining_quantity,
                    fill.price,
                    realized_pnl,
                )

        # Update daily P&L tracking
        self._update_pnl_tracking()

    def update_current_price(self, price: float) -> None:
        """Update current market price and unrealized P&L.

        Args:
            price: Current market price
        """
        self.position.current_price = price

        if not self.position.is_flat:
            # Calculate unrealized P&L
            if self.position.is_long:
                self.position.unrealized_pnl = (
                    price - self.position.average_price
                ) * self.position.quantity
            else:
                self.position.unrealized_pnl = (
                    self.position.average_price - price
                ) * abs(self.position.quantity)

            # Update market value
            self.position.market_value = self.position.quantity * price
        else:
            self.position.unrealized_pnl = 0.0
            self.position.market_value = 0.0

        # Update drawdown tracking
        self._update_drawdown_tracking()

    def can_enter_long(self, quantity: int = 1) -> bool:
        """Check if strategy can enter a long position.

        Args:
            quantity: Intended position size

        Returns:
            True if long entry is allowed
        """
        return self._can_enter_position(quantity)

    def can_enter_short(self, quantity: int = 1) -> bool:
        """Check if strategy can enter a short position.

        Args:
            quantity: Intended position size

        Returns:
            True if short entry is allowed
        """
        return self._can_enter_position(-quantity)

    def can_add_to_long(self, quantity: int = 1) -> bool:
        """Check if strategy can add to existing long position.

        Args:
            quantity: Additional quantity to add

        Returns:
            True if addition is allowed
        """
        if not self.position.is_long:
            return False

        new_size = self.position.quantity + quantity
        return abs(new_size) <= self.risk_limits.max_position_size

    def can_add_to_short(self, quantity: int = 1) -> bool:
        """Check if strategy can add to existing short position.

        Args:
            quantity: Additional quantity to add

        Returns:
            True if addition is allowed
        """
        if not self.position.is_short:
            return False

        new_size = self.position.quantity - quantity
        return abs(new_size) <= self.risk_limits.max_position_size

    def should_stop_out(self) -> bool:
        """Check if position should be stopped out due to loss.

        Returns:
            True if stop loss should be triggered
        """
        if self.position.is_flat:
            return False

        # Check position-level stop loss
        if self.position.current_price > 0:
            loss_pct = abs(self.position.unrealized_pnl) / self.position.total_cost
            if loss_pct >= self.risk_limits.position_stop_loss_pct:
                logger.warning(
                    "Position stop loss triggered: %.2f%% loss", loss_pct * 100
                )
                return True

        # Check daily loss limit
        if abs(self.daily_pnl) >= self.risk_limits.max_daily_loss:
            logger.warning("Daily loss limit reached: %.2f", self.daily_pnl)
            return True

        # Check maximum drawdown
        if self.current_drawdown >= self.risk_limits.max_drawdown:
            logger.warning("Maximum drawdown exceeded: %.2f", self.current_drawdown)
            return True

        return False

    def should_take_profit(self) -> bool:
        """Check if position should be closed for profit taking.

        Returns:
            True if profit should be taken
        """
        if self.position.is_flat:
            return False

        # Check position-level take profit
        if self.position.current_price > 0 and self.position.unrealized_pnl > 0:
            profit_pct = self.position.unrealized_pnl / self.position.total_cost
            if profit_pct >= self.risk_limits.position_take_profit_pct:
                logger.info("Take profit triggered: %.2f%% profit", profit_pct * 100)
                return True

        return False

    def get_position_info(self) -> PositionInfo:
        """Get current position information.

        Returns:
            Copy of current position info
        """
        return PositionInfo(
            quantity=self.position.quantity,
            average_price=self.position.average_price,
            market_value=self.position.market_value,
            unrealized_pnl=self.position.unrealized_pnl,
            realized_pnl=self.position.realized_pnl,
            total_cost=self.position.total_cost,
            current_price=self.position.current_price,
        )

    def get_risk_metrics(self) -> dict[str, Any]:
        """Get current risk metrics.

        Returns:
            Dictionary of risk metrics
        """
        return {
            "position_size": self.position.abs_quantity,
            "max_position_size": self.risk_limits.max_position_size,
            "position_utilization": (
                self.position.abs_quantity / self.risk_limits.max_position_size * 100
                if self.risk_limits.max_position_size > 0
                else 0
            ),
            "daily_pnl": self.daily_pnl,
            "max_daily_loss": self.risk_limits.max_daily_loss,
            "daily_loss_utilization": (
                abs(self.daily_pnl) / self.risk_limits.max_daily_loss * 100
                if self.risk_limits.max_daily_loss > 0
                else 0
            ),
            "current_drawdown": self.current_drawdown,
            "max_drawdown": self.max_drawdown,
            "peak_pnl": self.peak_pnl,
            "net_pnl": self.position.net_pnl,
            "return_pct": self.position.return_pct,
        }

    def reset_daily_metrics(self) -> None:
        """Reset daily tracking metrics (call at start of new trading day)."""
        self.daily_pnl = 0.0
        self.peak_pnl = 0.0
        self.current_drawdown = 0.0

        logger.debug("Reset daily metrics")

    def _can_enter_position(self, quantity: int) -> bool:
        """Check if a position of given size can be entered.

        Args:
            quantity: Signed quantity (positive for long, negative for short)

        Returns:
            True if position can be entered
        """
        # Check position size limits
        if abs(quantity) > self.risk_limits.max_position_size:
            return False

        # Check if adding to existing position exceeds limits
        if not self.position.is_flat:
            new_size = self.position.quantity + quantity
            if abs(new_size) > self.risk_limits.max_position_size:
                return False

        # Check daily loss limits
        if abs(self.daily_pnl) >= self.risk_limits.max_daily_loss:
            return False

        # Check drawdown limits
        if self.current_drawdown >= self.risk_limits.max_drawdown:
            return False

        return True

    def _calculate_realized_pnl(self, fill: Fill, quantity: int) -> float:
        """Calculate realized P&L for a position-closing fill.

        Args:
            fill: Fill that closes position
            quantity: Quantity being closed

        Returns:
            Realized P&L for the closed quantity
        """
        if self.position.is_long:
            # Closing long position
            return (fill.price - self.position.average_price) * quantity
        # Closing short position
        return (self.position.average_price - fill.price) * quantity

    def _update_pnl_tracking(self) -> None:
        """Update daily P&L and peak tracking."""
        self.daily_pnl = self.position.realized_pnl + self.position.unrealized_pnl

        self.peak_pnl = max(self.peak_pnl, self.daily_pnl)

    def _update_drawdown_tracking(self) -> None:
        """Update drawdown metrics."""
        current_pnl = self.position.realized_pnl + self.position.unrealized_pnl

        # Update peak if we have new high
        if current_pnl > self.peak_pnl:
            self.peak_pnl = current_pnl
            self.current_drawdown = 0.0
        else:
            # Calculate drawdown from peak
            self.current_drawdown = self.peak_pnl - current_pnl

        # Update maximum drawdown
        self.max_drawdown = max(self.max_drawdown, self.current_drawdown)
