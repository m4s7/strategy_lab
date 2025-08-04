"""Order queueing system for batch processing."""

import logging
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Any

import pandas as pd

from .portfolio import Portfolio, PositionSide

logger = logging.getLogger(__name__)


class OrderType(Enum):
    """Order type enumeration."""

    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"


class OrderStatus(Enum):
    """Order status enumeration."""

    PENDING = "PENDING"
    EXECUTED = "EXECUTED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


@dataclass
class Order:
    """Represents a trading order."""

    # Core order fields
    order_id: str
    symbol: str
    side: PositionSide
    quantity: int
    order_type: OrderType = OrderType.MARKET

    # Price fields
    price: Decimal | None = None  # For limit orders
    stop_price: Decimal | None = None  # For stop orders

    # Timing and execution
    timestamp: pd.Timestamp = field(default_factory=pd.Timestamp.now)
    expires_at: pd.Timestamp | None = None

    # Status and execution details
    status: OrderStatus = OrderStatus.PENDING
    executed_price: Decimal | None = None
    executed_quantity: int = 0
    executed_at: pd.Timestamp | None = None

    # Risk management
    stop_loss_price: Decimal | None = None
    take_profit_price: Decimal | None = None

    # Metadata
    strategy_id: str | None = None
    notes: str | None = None

    @property
    def is_pending(self) -> bool:
        """Check if order is pending."""
        return self.status == OrderStatus.PENDING

    @property
    def is_executed(self) -> bool:
        """Check if order is executed."""
        return self.status == OrderStatus.EXECUTED

    @property
    def is_cancelled(self) -> bool:
        """Check if order is cancelled."""
        return self.status == OrderStatus.CANCELLED

    @property
    def remaining_quantity(self) -> int:
        """Get remaining quantity to execute."""
        return self.quantity - self.executed_quantity

    def can_execute_at_price(self, current_price: Decimal) -> bool:
        """Check if order can be executed at current price.

        Args:
            current_price: Current market price

        Returns:
            True if order can be executed
        """
        if not self.is_pending:
            return False

        if self.order_type == OrderType.MARKET:
            return True

        elif self.order_type == OrderType.LIMIT:
            if self.price is None:
                return False
            if self.side == PositionSide.LONG:
                return current_price <= self.price
            elif self.side == PositionSide.SHORT:
                return current_price >= self.price

        elif self.order_type == OrderType.STOP:
            if self.stop_price is None:
                return False
            if self.side == PositionSide.LONG:
                return current_price >= self.stop_price
            elif self.side == PositionSide.SHORT:
                return current_price <= self.stop_price

        elif self.order_type == OrderType.STOP_LIMIT:
            # First check if stop is triggered
            if self.stop_price is None:
                return False
            stop_triggered = False
            if self.side == PositionSide.LONG:
                stop_triggered = current_price >= self.stop_price
            elif self.side == PositionSide.SHORT:
                stop_triggered = current_price <= self.stop_price

            # If stop triggered, check limit price
            if stop_triggered and self.price is not None:
                if self.side == PositionSide.LONG:
                    return current_price <= self.price
                elif self.side == PositionSide.SHORT:
                    return current_price >= self.price

        return False

    def is_expired(self, current_time: pd.Timestamp) -> bool:
        """Check if order has expired.

        Args:
            current_time: Current timestamp

        Returns:
            True if order has expired
        """
        if self.expires_at is None:
            return False
        return current_time >= self.expires_at


class OrderQueue:
    """Order queue for batch processing."""

    def __init__(self, batch_size: int = 10, process_interval: int = 100):
        """Initialize order queue.

        Args:
            batch_size: Number of orders to process in each batch
            process_interval: Number of ticks between batch processing
        """
        self.batch_size = batch_size
        self.process_interval = process_interval

        # Order storage
        self.pending_orders: dict[str, Order] = {}
        self.executed_orders: list[Order] = []
        self.cancelled_orders: list[Order] = []

        # Processing state
        self.last_process_tick = 0
        self.order_counter = 0

        # Statistics
        self.total_orders_submitted = 0
        self.total_orders_executed = 0
        self.total_orders_cancelled = 0

    def submit_order(
        self,
        symbol: str,
        side: PositionSide,
        quantity: int,
        order_type: OrderType = OrderType.MARKET,
        price: Decimal | None = None,
        stop_price: Decimal | None = None,
        expires_at: pd.Timestamp | None = None,
        stop_loss_price: Decimal | None = None,
        take_profit_price: Decimal | None = None,
        strategy_id: str | None = None,
        notes: str | None = None,
    ) -> str:
        """Submit a new order to the queue.

        Args:
            symbol: Trading symbol
            side: Order side (LONG/SHORT)
            quantity: Order quantity
            order_type: Type of order
            price: Limit price (for limit orders)
            stop_price: Stop price (for stop orders)
            expires_at: Order expiration time
            stop_loss_price: Stop loss level for position
            take_profit_price: Take profit level for position
            strategy_id: Strategy that created the order
            notes: Additional notes

        Returns:
            Order ID
        """
        self.order_counter += 1
        order_id = f"ORD_{self.order_counter:06d}"

        order = Order(
            order_id=order_id,
            symbol=symbol,
            side=side,
            quantity=quantity,
            order_type=order_type,
            price=price,
            stop_price=stop_price,
            expires_at=expires_at,
            stop_loss_price=stop_loss_price,
            take_profit_price=take_profit_price,
            strategy_id=strategy_id,
            notes=notes,
        )

        self.pending_orders[order_id] = order
        self.total_orders_submitted += 1

        logger.debug(
            f"Submitted order {order_id}: {side.value} {quantity} {symbol} @ {order_type.value}"
        )

        return order_id

    def cancel_order(self, order_id: str) -> bool:
        """Cancel a pending order.

        Args:
            order_id: Order ID to cancel

        Returns:
            True if order was cancelled successfully
        """
        if order_id in self.pending_orders:
            order = self.pending_orders.pop(order_id)
            order.status = OrderStatus.CANCELLED
            self.cancelled_orders.append(order)
            self.total_orders_cancelled += 1

            logger.debug(f"Cancelled order {order_id}")
            return True

        return False

    def should_process_batch(self, current_tick: int) -> bool:
        """Check if batch processing should occur.

        Args:
            current_tick: Current tick number

        Returns:
            True if batch should be processed
        """
        # Process if we have enough orders or enough time has passed
        return (
            len(self.pending_orders) >= self.batch_size
            or (current_tick - self.last_process_tick) >= self.process_interval
        )

    def process_batch(
        self,
        current_prices: dict[str, Decimal],
        current_time: pd.Timestamp,
        portfolio: Portfolio,
        current_tick: int,
    ) -> list[Order]:
        """Process a batch of orders.

        Args:
            current_prices: Current market prices by symbol
            current_time: Current timestamp
            portfolio: Portfolio to execute orders against
            current_tick: Current tick number

        Returns:
            List of executed orders
        """
        if not self.pending_orders:
            return []

        executed_orders = []
        expired_orders = []

        # Process each pending order
        for order_id, order in list(self.pending_orders.items()):
            # Check for expiration first
            if order.is_expired(current_time):
                expired_orders.append(order_id)
                continue

            # Check if we have price for this symbol
            if order.symbol not in current_prices:
                continue

            current_price = current_prices[order.symbol]

            # Check if order can be executed
            if order.can_execute_at_price(current_price):
                # Execute the order
                executed_order = self._execute_order(
                    order, current_price, current_time, portfolio
                )
                if executed_order:
                    executed_orders.append(executed_order)

        # Remove executed orders from pending
        for order in executed_orders:
            self.pending_orders.pop(order.order_id, None)

        # Cancel expired orders
        for order_id in expired_orders:
            self.cancel_order(order_id)

        self.last_process_tick = current_tick

        if executed_orders:
            logger.info(f"Processed batch: {len(executed_orders)} orders executed")

        return executed_orders

    def _execute_order(
        self,
        order: Order,
        execution_price: Decimal,
        execution_time: pd.Timestamp,
        portfolio: Portfolio,
    ) -> Order | None:
        """Execute a single order.

        Args:
            order: Order to execute
            execution_price: Price to execute at
            execution_time: Execution timestamp
            portfolio: Portfolio to execute against

        Returns:
            Executed order or None if execution failed
        """
        try:
            # Check if we need to close existing positions first
            existing_position = portfolio.get_position(order.symbol)

            if order.side == PositionSide.LONG:
                # Close short position if exists, then open long
                if existing_position and existing_position.side == PositionSide.SHORT:
                    portfolio.close_position(
                        order.symbol, execution_price, execution_time, existing_position
                    )

                # Open long position
                portfolio.open_position(
                    symbol=order.symbol,
                    side=PositionSide.LONG,
                    quantity=order.quantity,
                    price=execution_price,
                    timestamp=execution_time,
                    stop_loss_price=order.stop_loss_price,
                    take_profit_price=order.take_profit_price,
                )

            elif order.side == PositionSide.SHORT:
                # Close long position if exists, then open short
                if existing_position and existing_position.side == PositionSide.LONG:
                    portfolio.close_position(
                        order.symbol, execution_price, execution_time, existing_position
                    )

                # Open short position
                portfolio.open_position(
                    symbol=order.symbol,
                    side=PositionSide.SHORT,
                    quantity=order.quantity,
                    price=execution_price,
                    timestamp=execution_time,
                    stop_loss_price=order.stop_loss_price,
                    take_profit_price=order.take_profit_price,
                )

            # Update order status
            order.status = OrderStatus.EXECUTED
            order.executed_price = execution_price
            order.executed_quantity = order.quantity
            order.executed_at = execution_time

            # Add to executed orders
            self.executed_orders.append(order)
            self.total_orders_executed += 1

            logger.debug(
                f"Executed order {order.order_id}: {order.side.value} {order.quantity} {order.symbol} @ {execution_price}"
            )

            return order

        except Exception as e:
            logger.error(f"Failed to execute order {order.order_id}: {e}")
            order.status = OrderStatus.REJECTED
            return None

    def get_order_status(self, order_id: str) -> OrderStatus | None:
        """Get status of an order.

        Args:
            order_id: Order ID to check

        Returns:
            Order status or None if not found
        """
        # Check pending orders
        if order_id in self.pending_orders:
            return self.pending_orders[order_id].status

        # Check executed orders
        for order in self.executed_orders:
            if order.order_id == order_id:
                return order.status

        # Check cancelled orders
        for order in self.cancelled_orders:
            if order.order_id == order_id:
                return order.status

        return None

    def get_pending_orders_count(self) -> int:
        """Get number of pending orders."""
        return len(self.pending_orders)

    def get_orders_for_symbol(self, symbol: str) -> list[Order]:
        """Get all orders for a specific symbol.

        Args:
            symbol: Trading symbol

        Returns:
            List of orders for the symbol
        """
        orders = []

        # Add pending orders
        for order in self.pending_orders.values():
            if order.symbol == symbol:
                orders.append(order)

        # Add executed orders
        for order in self.executed_orders:
            if order.symbol == symbol:
                orders.append(order)

        # Add cancelled orders
        for order in self.cancelled_orders:
            if order.symbol == symbol:
                orders.append(order)

        return orders

    def get_statistics(self) -> dict[str, Any]:
        """Get order queue statistics.

        Returns:
            Dictionary of statistics
        """
        return {
            "total_orders_submitted": self.total_orders_submitted,
            "total_orders_executed": self.total_orders_executed,
            "total_orders_cancelled": self.total_orders_cancelled,
            "pending_orders": len(self.pending_orders),
            "executed_orders": len(self.executed_orders),
            "cancelled_orders": len(self.cancelled_orders),
            "execution_rate": (
                self.total_orders_executed / self.total_orders_submitted
                if self.total_orders_submitted > 0
                else 0.0
            ),
        }

    def clear_completed_orders(self, keep_recent: int = 1000) -> None:
        """Clear old completed orders to manage memory.

        Args:
            keep_recent: Number of recent orders to keep
        """
        if len(self.executed_orders) > keep_recent:
            self.executed_orders = self.executed_orders[-keep_recent:]

        if len(self.cancelled_orders) > keep_recent:
            self.cancelled_orders = self.cancelled_orders[-keep_recent:]

        logger.debug("Cleared old completed orders")
