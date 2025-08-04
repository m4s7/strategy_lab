"""Portfolio management for backtest execution."""

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Any

import pandas as pd


class PositionSide(Enum):
    """Position side enumeration."""

    LONG = "LONG"
    SHORT = "SHORT"
    FLAT = "FLAT"


@dataclass
class Position:
    """Represents a trading position."""

    symbol: str
    side: PositionSide
    quantity: int
    entry_price: Decimal
    entry_time: pd.Timestamp

    # Optional fields
    exit_price: Decimal | None = None
    exit_time: pd.Timestamp | None = None
    commission: Decimal = Decimal("0")
    slippage: Decimal = Decimal("0")

    # Stop loss and take profit levels
    stop_loss_price: Decimal | None = None
    take_profit_price: Decimal | None = None

    # Calculated fields
    current_price: Decimal = Decimal("0")
    unrealized_pnl: Decimal = Decimal("0")
    realized_pnl: Decimal = Decimal("0")

    @property
    def is_open(self) -> bool:
        """Check if position is open."""
        return self.exit_price is None

    @property
    def is_closed(self) -> bool:
        """Check if position is closed."""
        return self.exit_price is not None

    @property
    def market_value(self) -> Decimal:
        """Calculate current market value."""
        if self.is_open:
            return self.current_price * self.quantity
        return Decimal("0")

    def update_price(self, price: Decimal) -> None:
        """Update current price and unrealized P&L.

        Args:
            price: Current market price
        """
        self.current_price = price

        if self.is_open:
            if self.side == PositionSide.LONG:
                self.unrealized_pnl = (price - self.entry_price) * self.quantity
            elif self.side == PositionSide.SHORT:
                self.unrealized_pnl = (self.entry_price - price) * self.quantity

            # Subtract commission from unrealized P&L
            self.unrealized_pnl -= self.commission

    def should_trigger_stop_loss(self) -> bool:
        """Check if current price should trigger stop loss.

        Returns:
            True if stop loss should be triggered
        """
        if not self.is_open or self.stop_loss_price is None:
            return False

        if self.side == PositionSide.LONG:
            return self.current_price <= self.stop_loss_price
        elif self.side == PositionSide.SHORT:
            return self.current_price >= self.stop_loss_price
        return False

    def should_trigger_take_profit(self) -> bool:
        """Check if current price should trigger take profit.

        Returns:
            True if take profit should be triggered
        """
        if not self.is_open or self.take_profit_price is None:
            return False

        if self.side == PositionSide.LONG:
            return self.current_price >= self.take_profit_price
        elif self.side == PositionSide.SHORT:
            return self.current_price <= self.take_profit_price
        return False

    def close(self, exit_price: Decimal, exit_time: pd.Timestamp) -> Decimal:
        """Close the position.

        Args:
            exit_price: Exit price
            exit_time: Exit timestamp

        Returns:
            Realized P&L
        """
        if self.is_closed:
            raise ValueError("Position already closed")

        self.exit_price = exit_price
        self.exit_time = exit_time

        # Calculate realized P&L
        if self.side == PositionSide.LONG:
            gross_pnl = (exit_price - self.entry_price) * self.quantity
        elif self.side == PositionSide.SHORT:
            gross_pnl = (self.entry_price - exit_price) * self.quantity
        else:
            gross_pnl = Decimal("0")

        # Apply commission and slippage
        self.realized_pnl = gross_pnl - self.commission - self.slippage
        self.unrealized_pnl = Decimal("0")

        return self.realized_pnl


@dataclass
class Portfolio:
    """Portfolio management for backtesting."""

    initial_capital: Decimal
    commission_per_trade: Decimal = Decimal("2.00")
    slippage_per_trade: Decimal = Decimal("0.25")

    # Portfolio state
    cash: Decimal = field(init=False)
    positions: dict[str, list[Position]] = field(default_factory=dict)
    closed_positions: list[Position] = field(default_factory=list)

    # Performance tracking
    equity_curve: list[Decimal] = field(default_factory=list)
    timestamps: list[pd.Timestamp] = field(default_factory=list)

    # Current values
    current_timestamp: pd.Timestamp | None = None

    # Drawdown tracking
    peak_equity: Decimal = field(init=False)
    current_drawdown: Decimal = field(init=False, default=Decimal("0"))
    max_drawdown: Decimal = field(init=False, default=Decimal("0"))

    def __post_init__(self):
        """Initialize portfolio state."""
        self.cash = self.initial_capital
        self.equity_curve.append(self.initial_capital)
        self.peak_equity = self.initial_capital

    @property
    def equity(self) -> Decimal:
        """Calculate current equity (cash + open positions)."""
        total = self.cash

        for symbol_positions in self.positions.values():
            for position in symbol_positions:
                if position.is_open:
                    total += position.market_value

        return total

    @property
    def total_positions(self) -> int:
        """Get total number of open positions."""
        count = 0
        for symbol_positions in self.positions.values():
            for position in symbol_positions:
                if position.is_open:
                    count += 1
        return count

    @property
    def is_flat(self) -> bool:
        """Check if portfolio has no open positions."""
        return self.total_positions == 0

    def get_position(self, symbol: str) -> Position | None:
        """Get current position for symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Current position or None
        """
        if self.positions.get(symbol):
            # Return the most recent open position
            for position in reversed(self.positions[symbol]):
                if position.is_open:
                    return position
        return None

    def has_position(self, symbol: str) -> bool:
        """Check if has open position in symbol.

        Args:
            symbol: Trading symbol

        Returns:
            True if has open position
        """
        return self.get_position(symbol) is not None

    @property
    def current_drawdown_percent(self) -> Decimal:
        """Get current drawdown as percentage.

        Returns:
            Current drawdown percentage (negative value)
        """
        if self.peak_equity == 0:
            return Decimal("0")
        return (self.current_drawdown / self.peak_equity) * Decimal("100")

    @property
    def max_drawdown_percent(self) -> Decimal:
        """Get maximum drawdown as percentage.

        Returns:
            Maximum drawdown percentage (negative value)
        """
        if self.peak_equity == 0:
            return Decimal("0")
        return (self.max_drawdown / self.peak_equity) * Decimal("100")

    def _update_drawdown(self) -> None:
        """Update drawdown calculations."""
        current_equity = self.equity

        # Update peak equity
        if current_equity > self.peak_equity:
            self.peak_equity = current_equity
            self.current_drawdown = Decimal("0")
        else:
            # Calculate current drawdown
            self.current_drawdown = self.peak_equity - current_equity
            # Update max drawdown
            if self.current_drawdown > self.max_drawdown:
                self.max_drawdown = self.current_drawdown

    def open_position(
        self,
        symbol: str,
        side: PositionSide,
        quantity: int,
        price: Decimal,
        timestamp: pd.Timestamp,
        stop_loss_price: Decimal | None = None,
        take_profit_price: Decimal | None = None,
    ) -> Position:
        """Open a new position.

        Args:
            symbol: Trading symbol
            side: Position side (LONG/SHORT)
            quantity: Position quantity
            price: Entry price
            timestamp: Entry timestamp
            stop_loss_price: Optional stop loss trigger price
            take_profit_price: Optional take profit trigger price

        Returns:
            Created Position
        """
        if side == PositionSide.FLAT:
            raise ValueError("Cannot open FLAT position")

        # Calculate costs
        commission = self.commission_per_trade
        slippage = self.slippage_per_trade * quantity
        total_cost = price * quantity + commission + slippage

        # Check if enough cash
        if self.cash < total_cost:
            raise ValueError(f"Insufficient cash: {self.cash} < {total_cost}")

        # Create position
        position = Position(
            symbol=symbol,
            side=side,
            quantity=quantity,
            entry_price=price,
            entry_time=timestamp,
            commission=commission,
            slippage=slippage,
            current_price=price,
            stop_loss_price=stop_loss_price,
            take_profit_price=take_profit_price,
        )

        # Update portfolio
        self.cash -= total_cost

        if symbol not in self.positions:
            self.positions[symbol] = []
        self.positions[symbol].append(position)

        return position

    def close_position(
        self,
        symbol: str,
        price: Decimal,
        timestamp: pd.Timestamp,
        position: Position | None = None,
    ) -> Position | None:
        """Close a position.

        Args:
            symbol: Trading symbol
            price: Exit price
            timestamp: Exit timestamp
            position: Specific position to close (or most recent)

        Returns:
            Closed position or None
        """
        if position is None:
            position = self.get_position(symbol)

        if position is None or position.is_closed:
            return None

        # Close the position
        realized_pnl = position.close(price, timestamp)

        # Update cash
        exit_value = price * position.quantity
        self.cash += exit_value + realized_pnl

        # Move to closed positions
        self.closed_positions.append(position)

        return position

    def update_prices(
        self, prices: dict[str, Decimal], timestamp: pd.Timestamp
    ) -> None:
        """Update current prices and equity.

        Args:
            prices: Dict of symbol -> price
            timestamp: Current timestamp
        """
        self.current_timestamp = timestamp

        # Update position prices
        for symbol, symbol_positions in self.positions.items():
            if symbol in prices:
                for position in symbol_positions:
                    if position.is_open:
                        position.update_price(prices[symbol])

        # Update equity curve
        current_equity = self.equity
        self.equity_curve.append(current_equity)
        self.timestamps.append(timestamp)

        # Update drawdown tracking
        self._update_drawdown()

    def check_stop_loss_take_profit_triggers(
        self, timestamp: pd.Timestamp
    ) -> list[tuple[Position, str]]:
        """Check all positions for stop-loss and take-profit triggers.

        Args:
            timestamp: Current timestamp

        Returns:
            List of (position, trigger_type) tuples where trigger_type is 'stop_loss' or 'take_profit'
        """
        triggers = []

        for symbol_positions in self.positions.values():
            for position in symbol_positions:
                if position.is_open:
                    if position.should_trigger_stop_loss():
                        triggers.append((position, "stop_loss"))
                    elif position.should_trigger_take_profit():
                        triggers.append((position, "take_profit"))

        return triggers

    def set_stop_loss(self, symbol: str, stop_loss_price: Decimal) -> bool:
        """Set stop loss price for a position.

        Args:
            symbol: Trading symbol
            stop_loss_price: Stop loss trigger price

        Returns:
            True if stop loss was set successfully
        """
        position = self.get_position(symbol)
        if position and position.is_open:
            position.stop_loss_price = stop_loss_price
            return True
        return False

    def set_take_profit(self, symbol: str, take_profit_price: Decimal) -> bool:
        """Set take profit price for a position.

        Args:
            symbol: Trading symbol
            take_profit_price: Take profit trigger price

        Returns:
            True if take profit was set successfully
        """
        position = self.get_position(symbol)
        if position and position.is_open:
            position.take_profit_price = take_profit_price
            return True
        return False

    def get_portfolio_metrics(self) -> dict[str, Any]:
        """Get current portfolio metrics.

        Returns:
            Dictionary of portfolio metrics
        """
        open_positions = []
        for symbol_positions in self.positions.values():
            open_positions.extend([p for p in symbol_positions if p.is_open])

        total_unrealized = sum(p.unrealized_pnl for p in open_positions)
        total_realized = sum(p.realized_pnl for p in self.closed_positions)

        return {
            "cash": float(self.cash),
            "equity": float(self.equity),
            "initial_capital": float(self.initial_capital),
            "total_pnl": float(total_realized + total_unrealized),
            "realized_pnl": float(total_realized),
            "unrealized_pnl": float(total_unrealized),
            "open_positions": len(open_positions),
            "closed_positions": len(self.closed_positions),
            "total_trades": len(open_positions) + len(self.closed_positions),
            # Drawdown metrics
            "peak_equity": float(self.peak_equity),
            "current_drawdown": float(self.current_drawdown),
            "max_drawdown": float(self.max_drawdown),
            "current_drawdown_percent": float(self.current_drawdown_percent),
            "max_drawdown_percent": float(self.max_drawdown_percent),
        }

    def reset(self) -> None:
        """Reset portfolio to initial state."""
        self.cash = self.initial_capital
        self.positions.clear()
        self.closed_positions.clear()
        self.equity_curve = [self.initial_capital]
        self.timestamps = []
        self.current_timestamp = None
