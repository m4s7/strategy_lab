"""Event processor for handling hftbacktest events and order management."""

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class OrderType(Enum):
    """Order types supported by the system."""

    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderStatus(Enum):
    """Order execution status."""

    PENDING = "pending"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class OrderSide(Enum):
    """Order side (buy/sell)."""

    BUY = 1
    SELL = -1


@dataclass
class Order:
    """Order representation for hftbacktest integration."""

    order_id: int
    timestamp: int
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: int
    price: float | None = None
    stop_price: float | None = None
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: int = 0
    average_fill_price: float = 0.0
    commission: float = 0.0

    @property
    def remaining_quantity(self) -> int:
        """Get remaining unfilled quantity."""
        return self.quantity - self.filled_quantity

    @property
    def is_complete(self) -> bool:
        """Check if order is completely filled."""
        return (
            self.status == OrderStatus.FILLED or self.filled_quantity >= self.quantity
        )

    def to_hftbacktest_order(self) -> dict[str, Any]:
        """Convert to hftbacktest order format."""
        return {
            "order_id": self.order_id,
            "timestamp": self.timestamp,
            "side": self.side.value,
            "qty": self.quantity,
            "price": self.price,
            "order_type": self.order_type.value,
        }


@dataclass
class Fill:
    """Order fill/execution event."""

    order_id: int
    timestamp: int
    price: float
    quantity: int
    side: OrderSide
    commission: float = 0.0

    @property
    def notional_value(self) -> float:
        """Calculate notional value of the fill."""
        return self.price * self.quantity


@dataclass
class Position:
    """Position tracking for a symbol."""

    symbol: str
    quantity: int = 0
    average_price: float = 0.0
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    total_commission: float = 0.0

    @property
    def market_value(self) -> float:
        """Get current market value of position."""
        return self.quantity * self.average_price

    @property
    def is_long(self) -> bool:
        """Check if position is long."""
        return self.quantity > 0

    @property
    def is_short(self) -> bool:
        """Check if position is short."""
        return self.quantity < 0

    @property
    def is_flat(self) -> bool:
        """Check if position is flat."""
        return self.quantity == 0

    def update_position(self, fill: Fill):
        """Update position with new fill."""
        if self.quantity == 0:
            # Opening position
            self.quantity = fill.quantity * fill.side.value
            self.average_price = fill.price
        else:
            # Adding to or closing position
            old_value = self.quantity * self.average_price
            fill_value = fill.quantity * fill.price * fill.side.value

            new_quantity = self.quantity + (fill.quantity * fill.side.value)

            if new_quantity == 0:
                # Position closed - calculate realized PnL correctly
                # For a buy position being closed with a sell: sell_price - avg_price
                # For a short position being closed with a buy: avg_price - buy_price
                if self.quantity > 0:  # Long position being closed
                    self.realized_pnl += (fill.price - self.average_price) * abs(
                        self.quantity
                    )
                else:  # Short position being closed
                    self.realized_pnl += (self.average_price - fill.price) * abs(
                        self.quantity
                    )
                self.average_price = 0.0
            else:
                # Position adjusted
                self.average_price = (old_value + fill_value) / new_quantity

            self.quantity = new_quantity

        self.total_commission += fill.commission


@dataclass
class PerformanceMetrics:
    """Performance metrics tracking."""

    start_time: float = field(default_factory=time.time)
    end_time: float | None = None

    # Order metrics
    orders_submitted: int = 0
    orders_filled: int = 0
    orders_cancelled: int = 0
    orders_rejected: int = 0

    # Fill metrics
    total_fills: int = 0
    total_volume: int = 0
    total_commission: float = 0.0

    # Latency metrics
    order_latencies: list[float] = field(default_factory=list)
    fill_latencies: list[float] = field(default_factory=list)

    # PnL metrics
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    gross_pnl: float = 0.0
    net_pnl: float = 0.0

    @property
    def duration(self) -> float:
        """Get total duration in seconds."""
        end = self.end_time or time.time()
        return end - self.start_time

    @property
    def fill_rate(self) -> float:
        """Get order fill rate percentage."""
        if self.orders_submitted == 0:
            return 0.0
        return (self.orders_filled / self.orders_submitted) * 100

    @property
    def average_order_latency(self) -> float:
        """Get average order latency in nanoseconds."""
        return (
            sum(self.order_latencies) / len(self.order_latencies)
            if self.order_latencies
            else 0.0
        )

    @property
    def average_fill_latency(self) -> float:
        """Get average fill latency in nanoseconds."""
        return (
            sum(self.fill_latencies) / len(self.fill_latencies)
            if self.fill_latencies
            else 0.0
        )


class HftEventProcessor:
    """Event processor for handling hftbacktest events and order management."""

    def __init__(self, config):
        """Initialize event processor with configuration."""
        self.config = config
        self.orders: dict[int, Order] = {}
        self.positions: dict[str, Position] = {}
        self.fills: list[Fill] = []
        self.metrics = PerformanceMetrics()

        # Event callbacks
        self.on_order_filled: Callable[[Fill], None] | None = None
        self.on_position_updated: Callable[[Position], None] | None = None
        self.on_order_rejected: Callable[[Order], None] | None = None

        self._next_order_id = 1

        logger.info("Initialized HftEventProcessor for %s", config.symbol)

    def generate_order_id(self) -> int:
        """Generate unique order ID."""
        order_id = self._next_order_id
        self._next_order_id += 1
        return order_id

    def submit_order(
        self,
        timestamp: int,
        side: OrderSide,
        quantity: int,
        order_type: OrderType = OrderType.MARKET,
        price: float | None = None,
        stop_price: float | None = None,
    ) -> Order:
        """Submit a new order."""

        order_id = self.generate_order_id()

        order = Order(
            order_id=order_id,
            timestamp=timestamp,
            symbol=self.config.symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            stop_price=stop_price,
        )

        # Validate order
        if not self._validate_order(order):
            order.status = OrderStatus.REJECTED
            self.metrics.orders_rejected += 1
            if self.on_order_rejected:
                self.on_order_rejected(order)
            return order

        # Store order
        self.orders[order_id] = order
        self.metrics.orders_submitted += 1

        logger.debug(
            "Submitted order %d: %s %d @ %s", order_id, side.name, quantity, price
        )
        return order

    def _validate_order(self, order: Order) -> bool:
        """Validate order parameters."""
        # Check quantity limits
        if order.quantity <= 0:
            logger.warning("Invalid quantity: %d", order.quantity)
            return False

        if order.quantity > self.config.max_order_size:
            logger.warning(
                "Order size %d exceeds limit %d",
                order.quantity,
                self.config.max_order_size,
            )
            return False

        # Check price validity for limit orders
        if order.order_type in [OrderType.LIMIT, OrderType.STOP_LIMIT] and (
            order.price is None or order.price <= 0
        ):
            logger.warning(
                "Invalid price for %s: %s", order.order_type, order.price
            )
            return False

        # Check stop price for stop orders
        if order.order_type in [OrderType.STOP, OrderType.STOP_LIMIT] and (
            order.stop_price is None or order.stop_price <= 0
        ):
            logger.warning(
                "Invalid stop price for %s: %s",
                order.order_type,
                order.stop_price,
            )
            return False

        # Check position limits
        current_position = self.get_position(order.symbol)
        new_position_size = current_position.quantity + (
            order.quantity * order.side.value
        )

        if abs(new_position_size) > self.config.position_limit:
            logger.warning(
                "Order would exceed position limit: %d > %d",
                new_position_size,
                self.config.position_limit,
            )
            return False

        return True

    def process_fill(
        self, order_id: int, timestamp: int, fill_price: float, fill_quantity: int
    ) -> Fill | None:
        """Process order fill from hftbacktest."""

        if order_id not in self.orders:
            logger.warning("Fill for unknown order: %d", order_id)
            return None

        order = self.orders[order_id]

        # Calculate commission
        commission = self._calculate_commission(fill_price, fill_quantity)

        # Create fill
        fill = Fill(
            order_id=order_id,
            timestamp=timestamp,
            price=fill_price,
            quantity=fill_quantity,
            side=order.side,
            commission=commission,
        )

        # Update order
        order.filled_quantity += fill_quantity
        order.commission += commission

        if order.filled_quantity >= order.quantity:
            order.status = OrderStatus.FILLED
            self.metrics.orders_filled += 1
        else:
            order.status = OrderStatus.PARTIALLY_FILLED

        # Calculate average fill price
        total_filled_value = order.average_fill_price * (
            order.filled_quantity - fill_quantity
        )
        total_filled_value += fill_price * fill_quantity
        order.average_fill_price = total_filled_value / order.filled_quantity

        # Store fill
        self.fills.append(fill)
        self.metrics.total_fills += 1
        self.metrics.total_volume += fill_quantity
        self.metrics.total_commission += commission

        # Update position
        self._update_position(fill)

        # Calculate latency
        fill_latency = timestamp - order.timestamp
        self.metrics.fill_latencies.append(fill_latency)

        # Trigger callbacks
        if self.on_order_filled:
            self.on_order_filled(fill)

        logger.debug(
            "Fill: Order %d, %d @ %.2f", order_id, fill_quantity, fill_price
        )
        return fill

    def _calculate_commission(self, price: float, quantity: int) -> float:
        """Calculate commission for a fill."""
        notional_value = (
            Decimal(str(price))
            * Decimal(str(quantity))
            * self.config.contract_multiplier
        )
        return float(
            self.config.commission.calculate_total_commission(quantity, notional_value)
        )

    def _update_position(self, fill: Fill):
        """Update position with new fill."""
        symbol = self.config.symbol

        if symbol not in self.positions:
            self.positions[symbol] = Position(symbol=symbol)

        position = self.positions[symbol]
        old_realized_pnl = position.realized_pnl

        position.update_position(fill)

        # Update metrics
        self.metrics.realized_pnl += position.realized_pnl - old_realized_pnl

        # Trigger callback
        if self.on_position_updated:
            self.on_position_updated(position)

    def cancel_order(self, order_id: int, timestamp: int = 0) -> bool:
        """Cancel an order."""
        if order_id not in self.orders:
            logger.warning("Cannot cancel unknown order: %d", order_id)
            return False

        order = self.orders[order_id]

        if order.is_complete:
            logger.warning("Cannot cancel completed order: %d", order_id)
            return False

        order.status = OrderStatus.CANCELLED
        self.metrics.orders_cancelled += 1

        logger.debug("Cancelled order %d", order_id)
        return True

    def get_position(self, symbol: str) -> Position:
        """Get current position for symbol."""
        if symbol not in self.positions:
            self.positions[symbol] = Position(symbol=symbol)
        return self.positions[symbol]

    def update_unrealized_pnl(self, current_price: float):
        """Update unrealized PnL based on current market price."""
        symbol = self.config.symbol
        position = self.get_position(symbol)

        if not position.is_flat:
            market_value = position.quantity * current_price
            cost_basis = position.quantity * position.average_price
            position.unrealized_pnl = market_value - cost_basis
        else:
            position.unrealized_pnl = 0.0

        # Update metrics
        self.metrics.unrealized_pnl = position.unrealized_pnl
        self.metrics.gross_pnl = self.metrics.realized_pnl + self.metrics.unrealized_pnl
        self.metrics.net_pnl = self.metrics.gross_pnl - self.metrics.total_commission

    def get_open_orders(self) -> list[Order]:
        """Get all open orders."""
        return [
            order
            for order in self.orders.values()
            if order.status in [OrderStatus.PENDING, OrderStatus.PARTIALLY_FILLED]
        ]

    def get_performance_summary(self) -> dict[str, Any]:
        """Get comprehensive performance summary."""
        self.metrics.end_time = time.time()

        return {
            "duration_seconds": self.metrics.duration,
            "orders_submitted": self.metrics.orders_submitted,
            "orders_filled": self.metrics.orders_filled,
            "orders_cancelled": self.metrics.orders_cancelled,
            "orders_rejected": self.metrics.orders_rejected,
            "fill_rate_percent": self.metrics.fill_rate,
            "total_fills": self.metrics.total_fills,
            "total_volume": self.metrics.total_volume,
            "total_commission": self.metrics.total_commission,
            "realized_pnl": self.metrics.realized_pnl,
            "unrealized_pnl": self.metrics.unrealized_pnl,
            "gross_pnl": self.metrics.gross_pnl,
            "net_pnl": self.metrics.net_pnl,
            "avg_order_latency_ns": self.metrics.average_order_latency,
            "avg_fill_latency_ns": self.metrics.average_fill_latency,
            "positions": {
                symbol: {
                    "quantity": pos.quantity,
                    "average_price": pos.average_price,
                    "market_value": pos.market_value,
                    "unrealized_pnl": pos.unrealized_pnl,
                    "realized_pnl": pos.realized_pnl,
                }
                for symbol, pos in self.positions.items()
                if not pos.is_flat
            },
        }

    def reset(self):
        """Reset processor state for new backtest."""
        self.orders.clear()
        self.positions.clear()
        self.fills.clear()
        self.metrics = PerformanceMetrics()
        self._next_order_id = 1

        logger.debug("Event processor reset")


# Utility functions for event processing
def create_simple_order_manager(config) -> HftEventProcessor:
    """Create a simple order manager with basic callbacks."""

    processor = HftEventProcessor(config)

    def log_fill(fill: Fill):
        logger.info(
            "Fill: %d @ %.2f, Commission: %.2f",
            fill.quantity,
            fill.price,
            fill.commission,
        )

    def log_position_update(position: Position):
        if not position.is_flat:
            logger.info(
                "Position: %d @ %.2f, UnrealizedPnL: %.2f",
                position.quantity,
                position.average_price,
                position.unrealized_pnl,
            )

    def log_rejection(order: Order):
        logger.warning("Order rejected: %d", order.order_id)

    processor.on_order_filled = log_fill
    processor.on_position_updated = log_position_update
    processor.on_order_rejected = log_rejection

    return processor


def simulate_market_order_execution(
    processor: HftEventProcessor,
    timestamp: int,
    side: OrderSide,
    quantity: int,
    execution_price: float,
) -> Fill | None:
    """Simulate immediate market order execution."""

    # Submit market order
    order = processor.submit_order(
        timestamp=timestamp, side=side, quantity=quantity, order_type=OrderType.MARKET
    )

    if order.status == OrderStatus.REJECTED:
        return None

    # Simulate immediate fill
    return processor.process_fill(
        order_id=order.order_id,
        timestamp=timestamp + 1000,  # 1 microsecond execution delay
        fill_price=execution_price,
        fill_quantity=quantity,
    )
