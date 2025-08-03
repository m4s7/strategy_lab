"""Base strategy template for all trading strategies.

This module provides the foundational abstract base class that all trading strategies
must inherit from, ensuring consistent interface and common functionality.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ...backtesting.hft_integration.adapter import HftBacktestAdapter
from ...backtesting.hft_integration.data_feed import TickData
from ...backtesting.hft_integration.event_processor import Fill, OrderSide
from .position_manager import PositionManager
from .signal_generator import SignalGenerator

logger = logging.getLogger(__name__)


class StrategyState(Enum):
    """Strategy execution states."""

    INACTIVE = "inactive"
    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"


class MarketState(Enum):
    """Market session states."""

    PRE_MARKET = "pre_market"
    MARKET_OPEN = "market_open"
    MARKET_CLOSE = "market_close"
    AFTER_HOURS = "after_hours"


@dataclass
class StrategyConfig:
    """Configuration container for strategy parameters."""

    # Strategy identification
    strategy_name: str
    version: str = "1.0.0"

    # Risk management
    max_position_size: int = 10
    max_daily_loss: float = 1000.0
    max_daily_trades: int = 100

    # Order management
    default_order_size: int = 1
    enable_stop_loss: bool = True
    stop_loss_pct: float = 0.005  # 0.5%

    # Timing controls
    trading_start_time: str = "09:30:00"
    trading_end_time: str = "16:00:00"

    # Custom parameters
    custom_params: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> bool:
        """Validate configuration parameters."""
        errors = []

        if self.max_position_size <= 0:
            errors.append("max_position_size must be positive")

        if self.max_daily_loss <= 0:
            errors.append("max_daily_loss must be positive")

        if self.default_order_size <= 0:
            errors.append("default_order_size must be positive")

        if not (0 < self.stop_loss_pct < 1):
            errors.append("stop_loss_pct must be between 0 and 1")

        if errors:
            raise ValueError(f"Configuration validation failed: {'; '.join(errors)}")

        return True


@dataclass
class StrategyMetrics:
    """Strategy performance metrics tracking."""

    # Trade metrics
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0

    # P&L metrics
    gross_pnl: float = 0.0
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0

    # Risk metrics
    max_drawdown: float = 0.0
    current_drawdown: float = 0.0
    max_position_held: int = 0

    # Timing metrics
    avg_trade_duration: float = 0.0
    total_time_in_market: float = 0.0

    @property
    def win_rate(self) -> float:
        """Calculate win rate percentage."""
        if self.total_trades == 0:
            return 0.0
        return (self.winning_trades / self.total_trades) * 100

    @property
    def net_pnl(self) -> float:
        """Calculate net P&L."""
        return self.realized_pnl + self.unrealized_pnl


class StrategyBase(ABC):
    """Abstract base class for all trading strategies.

    This class provides the foundational interface and common functionality
    that all trading strategies must implement. It handles:

    - Strategy lifecycle management
    - Data access standardization
    - Order management integration
    - State persistence
    - Performance metrics tracking

    Example:
        >>> class MyStrategy(StrategyBase):
        ...     def initialize(self):
        ...         self.moving_average = 0.0
        ...
        ...     def process_tick(self, tick: TickData) -> None:
        ...         if self.should_enter_position(tick):
        ...             self.submit_market_order(OrderSide.BUY, 1)
        ...
        ...     def should_enter_position(self, tick: TickData) -> bool:
        ...         return tick.price > self.moving_average
    """

    def __init__(self, config: StrategyConfig, adapter: HftBacktestAdapter):
        """Initialize strategy with configuration and adapter.

        Args:
            config: Strategy configuration parameters
            adapter: HftBacktest adapter for order management and data access
        """
        self.config = config
        self.adapter = adapter

        # Validate configuration
        self.config.validate()

        # Initialize components
        self.position_manager = PositionManager(config)
        self.signal_generator = SignalGenerator(config)

        # Strategy state
        self.state = StrategyState.INACTIVE
        self.market_state = MarketState.PRE_MARKET
        self.metrics = StrategyMetrics()

        # Runtime state
        self.strategy_data: dict[str, Any] = {}
        self.last_tick: TickData | None = None
        self.current_timestamp: int = 0

        # Setup callbacks
        self.adapter.set_strategy_callback(self._on_tick)
        self.adapter.set_fill_callback(self._on_fill)

        logger.info("Initialized strategy %s v%s", config.strategy_name, config.version)

    # Abstract methods that must be implemented by concrete strategies

    @abstractmethod
    def initialize(self) -> None:
        """Initialize strategy-specific state and indicators.

        This method is called once before the strategy starts processing ticks.
        Use this to set up any indicators, state variables, or configuration
        that your strategy needs.

        Example:
            >>> def initialize(self):
            ...     self.sma_period = 20
            ...     self.price_history = []
            ...     self.last_signal = None
        """

    @abstractmethod
    def process_tick(self, tick: TickData) -> None:
        """Process a new market data tick.

        This is the main strategy logic method that gets called for every
        market data update. Implement your trading logic here.

        Args:
            tick: New market data tick containing price, volume, side info

        Example:
            >>> def process_tick(self, tick: TickData) -> None:
            ...     self.update_indicators(tick)
            ...     signal = self.generate_signal(tick)
            ...     if signal == "BUY" and self.position_manager.can_enter_long():
            ...         self.submit_market_order(OrderSide.BUY, self.config.default_order_size)
        """

    @abstractmethod
    def cleanup(self) -> None:
        """Cleanup strategy resources and finalize state.

        This method is called when the strategy is shutting down.
        Use this to close any open positions, save state, or cleanup resources.

        Example:
            >>> def cleanup(self):
            ...     if not self.position_manager.is_flat():
            ...         self.close_all_positions()
            ...     self.save_strategy_state()
        """

    # Optional hook methods for customization

    def on_market_open(self) -> None:
        """Hook called when market opens.

        Override this method to implement custom logic when trading begins.
        """
        logger.info("Market opened for strategy %s", self.config.strategy_name)
        self.market_state = MarketState.MARKET_OPEN

    def on_market_close(self) -> None:
        """Hook called when market closes.

        Override this method to implement end-of-day logic.
        """
        logger.info("Market closed for strategy %s", self.config.strategy_name)
        self.market_state = MarketState.MARKET_CLOSE

    def on_order_filled(self, fill: Fill) -> None:
        """Hook called when an order is filled.

        Override this method to implement custom fill handling logic.

        Args:
            fill: Order fill details
        """
        logger.debug(
            "Order filled: %d @ %.2f (Side: %s)",
            fill.quantity,
            fill.price,
            fill.side.name,
        )

    def on_error(self, error: Exception) -> None:
        """Hook called when an error occurs.

        Override this method to implement custom error handling.

        Args:
            error: Exception that occurred
        """
        logger.error("Strategy error: %s", error)
        self.state = StrategyState.ERROR

    # Data access methods

    def get_last_price(self) -> float:
        """Get the last traded price.

        Returns:
            Last price from most recent tick, or 0.0 if no data
        """
        return self.last_tick.price if self.last_tick else 0.0

    def get_last_volume(self) -> float:
        """Get the last traded volume.

        Returns:
            Volume from most recent tick, or 0.0 if no data
        """
        return self.last_tick.qty if self.last_tick else 0.0

    def get_current_position(self) -> dict[str, Any]:
        """Get current position information.

        Returns:
            Dictionary containing position details including quantity,
            average price, P&L, and position state
        """
        return self.adapter.get_current_position()

    def get_strategy_state(self) -> dict[str, Any]:
        """Get current strategy state for persistence.

        Returns:
            Dictionary containing strategy state that can be serialized
        """
        return {
            "strategy_data": self.strategy_data,
            "metrics": {
                "total_trades": self.metrics.total_trades,
                "gross_pnl": self.metrics.gross_pnl,
                "realized_pnl": self.metrics.realized_pnl,
            },
            "state": self.state.value,
            "timestamp": self.current_timestamp,
        }

    def set_strategy_state(self, state: dict[str, Any]) -> None:
        """Restore strategy state from persistence.

        Args:
            state: Previously saved state dictionary
        """
        self.strategy_data = state.get("strategy_data", {})

        metrics_data = state.get("metrics", {})
        self.metrics.total_trades = metrics_data.get("total_trades", 0)
        self.metrics.gross_pnl = metrics_data.get("gross_pnl", 0.0)
        self.metrics.realized_pnl = metrics_data.get("realized_pnl", 0.0)

        self.state = StrategyState(state.get("state", StrategyState.INACTIVE.value))
        self.current_timestamp = state.get("timestamp", 0)

    # Order management methods

    def submit_market_order(
        self, side: OrderSide, quantity: int, timestamp: int | None = None
    ) -> int:
        """Submit a market order.

        Args:
            side: Order side (BUY or SELL)
            quantity: Number of contracts
            timestamp: Optional timestamp, uses current if not provided

        Returns:
            Order ID

        Raises:
            ValueError: If order validation fails
        """
        if not self._validate_order(side, quantity):
            raise ValueError("Order validation failed")

        order_id = self.adapter.submit_market_order(side, quantity, timestamp)
        self.metrics.total_trades += 1

        logger.debug(
            "Submitted market order: %s %d contracts (ID: %d)",
            side.name,
            quantity,
            order_id,
        )

        return order_id

    def submit_limit_order(
        self, side: OrderSide, quantity: int, price: float, timestamp: int | None = None
    ) -> int:
        """Submit a limit order.

        Args:
            side: Order side (BUY or SELL)
            quantity: Number of contracts
            price: Limit price
            timestamp: Optional timestamp, uses current if not provided

        Returns:
            Order ID

        Raises:
            ValueError: If order validation fails
        """
        if not self._validate_order(side, quantity):
            raise ValueError("Order validation failed")

        order_id = self.adapter.submit_limit_order(side, quantity, price, timestamp)

        logger.debug(
            "Submitted limit order: %s %d @ %.2f (ID: %d)",
            side.name,
            quantity,
            price,
            order_id,
        )

        return order_id

    def cancel_order(self, order_id: int, timestamp: int | None = None) -> bool:
        """Cancel an existing order.

        Args:
            order_id: ID of order to cancel
            timestamp: Optional timestamp, uses current if not provided

        Returns:
            True if cancellation was successful
        """
        success = self.adapter.cancel_order(order_id, timestamp)

        if success:
            logger.debug("Cancelled order %d", order_id)
        else:
            logger.warning("Failed to cancel order %d", order_id)

        return success

    def close_all_positions(self) -> None:
        """Close all open positions with market orders."""
        position = self.get_current_position()

        if not position["is_flat"]:
            quantity = abs(position["quantity"])
            side = OrderSide.SELL if position["quantity"] > 0 else OrderSide.BUY

            self.submit_market_order(side, quantity)
            logger.info("Closing position: %s %d contracts", side.name, quantity)

    # Strategy lifecycle methods

    def start(self) -> None:
        """Start the strategy execution."""
        if self.state != StrategyState.INACTIVE:
            logger.warning("Strategy %s already started", self.config.strategy_name)
            return

        try:
            self.initialize()
            self.state = StrategyState.ACTIVE
            logger.info("Started strategy %s", self.config.strategy_name)

        except Exception as e:
            self.on_error(e)
            raise

    def stop(self) -> None:
        """Stop the strategy execution."""
        if self.state == StrategyState.INACTIVE:
            logger.warning("Strategy %s already stopped", self.config.strategy_name)
            return

        try:
            self.cleanup()
            self.state = StrategyState.INACTIVE
            logger.info("Stopped strategy %s", self.config.strategy_name)

        except Exception as e:
            self.on_error(e)
            raise

    def pause(self) -> None:
        """Pause strategy execution."""
        if self.state == StrategyState.ACTIVE:
            self.state = StrategyState.PAUSED
            logger.info("Paused strategy %s", self.config.strategy_name)

    def resume(self) -> None:
        """Resume strategy execution."""
        if self.state == StrategyState.PAUSED:
            self.state = StrategyState.ACTIVE
            logger.info("Resumed strategy %s", self.config.strategy_name)

    # Internal methods

    def _on_tick(self, tick: TickData) -> None:
        """Internal tick handler that calls strategy process_tick method."""
        try:
            self.last_tick = tick
            self.current_timestamp = tick.timestamp

            # Update position manager
            self.position_manager.update_current_price(tick.price)

            # Only process if strategy is active
            if self.state == StrategyState.ACTIVE:
                self.process_tick(tick)

        except Exception as e:
            self.on_error(e)

    def _on_fill(self, fill: Fill) -> None:
        """Internal fill handler that updates metrics and calls hook."""
        try:
            # Update metrics
            self.position_manager.process_fill(fill)
            self._update_metrics(fill)

            # Call user hook
            self.on_order_filled(fill)

        except Exception as e:
            self.on_error(e)

    def _validate_order(self, side: OrderSide, quantity: int) -> bool:
        """Validate order parameters against risk limits."""
        # Check basic parameters
        if quantity <= 0:
            logger.warning("Invalid order quantity: %d", quantity)
            return False

        # Check position limits
        current_pos = self.get_current_position()
        new_position = current_pos["quantity"] + (quantity * side.value)

        if abs(new_position) > self.config.max_position_size:
            logger.warning(
                "Order would exceed position limit: %d > %d",
                abs(new_position),
                self.config.max_position_size,
            )
            return False

        # Check daily trade limit
        if self.metrics.total_trades >= self.config.max_daily_trades:
            logger.warning(
                "Daily trade limit reached: %d >= %d",
                self.metrics.total_trades,
                self.config.max_daily_trades,
            )
            return False

        return True

    def _update_metrics(self, fill: Fill) -> None:
        """Update strategy performance metrics with new fill."""
        # Update trade counts
        if fill.quantity * fill.side.value > 0:  # Opening position
            pass  # Trade count updated in submit_market_order
        else:  # Closing position - evaluate trade result
            position = self.get_current_position()
            if position["realized_pnl"] > 0:
                self.metrics.winning_trades += 1
            else:
                self.metrics.losing_trades += 1

        # Update P&L metrics
        position = self.get_current_position()
        self.metrics.realized_pnl = position["realized_pnl"]
        self.metrics.unrealized_pnl = position["unrealized_pnl"]
        self.metrics.gross_pnl = self.metrics.realized_pnl + self.metrics.unrealized_pnl

        # Update position tracking
        abs_position = abs(position["quantity"])
        self.metrics.max_position_held = max(
            self.metrics.max_position_held, abs_position
        )
