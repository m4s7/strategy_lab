"""Moving Average Crossover Strategy Example.

This module demonstrates a complete implementation of a trading strategy
using the Strategy Lab framework. It implements a classic moving average
crossover strategy with risk management and proper signal generation.

The strategy:
1. Uses two moving averages (short and long period)
2. Generates buy signals when short MA crosses above long MA
3. Generates sell signals when short MA crosses below long MA
4. Includes position sizing and risk management
5. Demonstrates proper use of all template components
"""

import logging

from ...backtesting.hft_integration.data_feed import TickData
from ...backtesting.hft_integration.event_processor import Fill, OrderSide
from ..base import (
    Signal,
    SignalType,
    StrategyBase,
)

logger = logging.getLogger(__name__)


class MovingAverageCrossoverStrategy(StrategyBase):
    """Moving average crossover strategy implementation.

    This strategy demonstrates the complete usage of the Strategy Lab template:

    **Strategy Logic:**
    - Maintains two simple moving averages (short and long period)
    - Generates buy signal when short MA crosses above long MA (golden cross)
    - Generates sell signal when short MA crosses below long MA (death cross)
    - Only trades when signal strength exceeds minimum threshold
    - Includes proper position sizing and risk management

    **Configuration Parameters:**
    - short_period: Period for short moving average (default: 10)
    - long_period: Period for long moving average (default: 20)
    - min_signal_strength: Minimum signal strength to trade (default: 0.3)
    - position_size: Number of contracts per trade (default: 1)

    **Risk Management:**
    - Uses position manager for automatic stop losses
    - Respects maximum position size limits
    - Monitors daily loss limits
    - Includes drawdown protection

    Example:
        >>> config = StrategyConfig(
        ...     strategy_name="MA_Crossover",
        ...     max_position_size=5,
        ...     custom_params={
        ...         'short_period': 5,
        ...         'long_period': 15,
        ...         'min_signal_strength': 0.4
        ...     }
        ... )
        >>> strategy = MovingAverageCrossoverStrategy(config, adapter)
        >>> strategy.start()
    """

    def initialize(self) -> None:
        """Initialize strategy-specific state and parameters."""

        # Get parameters from configuration with defaults
        self.short_period = self.config.custom_params.get("short_period", 10)
        self.long_period = self.config.custom_params.get("long_period", 20)
        self.min_signal_strength = self.config.custom_params.get(
            "min_signal_strength", 0.3
        )
        self.position_size = self.config.custom_params.get("position_size", 1)

        # Validate parameters
        if self.short_period >= self.long_period:
            raise ValueError("Short period must be less than long period")

        if self.long_period <= 0 or self.short_period <= 0:
            raise ValueError("Moving average periods must be positive")

        if not (0 < self.min_signal_strength <= 1):
            raise ValueError("Min signal strength must be between 0 and 1")

        # Strategy state variables
        self.price_history = []
        self.current_signal: Signal | None = None
        self.last_crossover_timestamp = 0
        self.trades_today = 0

        # Moving average values
        self.short_ma = 0.0
        self.long_ma = 0.0
        self.prev_short_ma = 0.0
        self.prev_long_ma = 0.0

        # Store state for inspection
        self.strategy_data.update(
            {
                "short_period": self.short_period,
                "long_period": self.long_period,
                "min_signal_strength": self.min_signal_strength,
                "position_size": self.position_size,
                "initialization_timestamp": self.current_timestamp,
            }
        )

        logger.info(
            "Initialized MA Crossover Strategy: short=%d, long=%d, min_strength=%.2f",
            self.short_period,
            self.long_period,
            self.min_signal_strength,
        )

    def process_tick(self, tick: TickData) -> None:
        """Process market data tick and execute trading logic.

        Args:
            tick: New market data containing price, volume, and timestamp
        """

        # Update price history
        self.price_history.append(tick.price)

        # Keep only required history (long_period + buffer)
        max_history = self.long_period + 5
        if len(self.price_history) > max_history:
            self.price_history = self.price_history[-max_history:]

        # Need at least long_period prices to calculate both averages
        if len(self.price_history) < self.long_period:
            return

        # Update moving averages
        self._update_moving_averages()

        # Generate trading signal
        signal = self._generate_crossover_signal(tick)

        if signal:
            self.current_signal = signal

            # Check if we should act on this signal
            if self._should_trade_signal(signal):
                self._execute_signal(signal, tick)

        # Check for risk management triggers
        self._check_risk_management()

        # Update strategy state for inspection
        self.strategy_data.update(
            {
                "last_price": tick.price,
                "short_ma": self.short_ma,
                "long_ma": self.long_ma,
                "current_signal": signal.signal_type.value if signal else None,
                "signal_strength": signal.strength if signal else 0.0,
                "trades_today": self.trades_today,
                "price_history_length": len(self.price_history),
            }
        )

    def cleanup(self) -> None:
        """Cleanup strategy resources and close positions."""

        # Close any open positions
        if not self.position_manager.get_position_info().is_flat:
            logger.info("Closing open positions during strategy cleanup")
            self.close_all_positions()

        # Log final strategy statistics
        position = self.position_manager.get_position_info()
        risk_metrics = self.position_manager.get_risk_metrics()

        logger.info("Strategy cleanup summary:")
        logger.info("  Total trades today: %d", self.trades_today)
        logger.info("  Final realized P&L: %.2f", position.realized_pnl)
        logger.info("  Max drawdown: %.2f", risk_metrics["max_drawdown"])
        logger.info("  Win rate: %.1f%%", self.metrics.win_rate)

        # Save final state
        self.strategy_data.update(
            {
                "cleanup_timestamp": self.current_timestamp,
                "final_pnl": position.realized_pnl,
                "total_trades": self.trades_today,
                "final_drawdown": risk_metrics["current_drawdown"],
            }
        )

    def on_order_filled(self, fill: Fill) -> None:
        """Handle order fill events.

        Args:
            fill: Details of the order fill
        """

        self.trades_today += 1

        # Log the fill with strategy context
        logger.info(
            "MA Crossover fill: %s %d @ %.2f (Signal: %s, Strength: %.2f)",
            fill.side.name,
            fill.quantity,
            fill.price,
            self.current_signal.signal_type.value if self.current_signal else "None",
            self.current_signal.strength if self.current_signal else 0.0,
        )

        # Update strategy data
        self.strategy_data.update(
            {
                "last_fill_price": fill.price,
                "last_fill_side": fill.side.name,
                "last_fill_timestamp": fill.timestamp,
                "trades_today": self.trades_today,
            }
        )

    def on_market_open(self) -> None:
        """Handle market open event."""

        logger.info("Market opened - MA Crossover strategy active")

        # Reset daily counters
        self.trades_today = 0
        self.position_manager.reset_daily_metrics()

        # Clear any overnight signals
        self.current_signal = None
        self.last_crossover_timestamp = 0

        self.strategy_data.update(
            {"market_open_timestamp": self.current_timestamp, "trades_today": 0}
        )

    def on_market_close(self) -> None:
        """Handle market close event."""

        logger.info("Market closing - finalizing MA Crossover strategy")

        # Close any open positions before market close
        if not self.position_manager.get_position_info().is_flat:
            logger.info("Closing positions before market close")
            self.close_all_positions()

        # Log end-of-day summary
        position = self.position_manager.get_position_info()
        logger.info("End of day summary:")
        logger.info("  Trades executed: %d", self.trades_today)
        logger.info("  Realized P&L: %.2f", position.realized_pnl)
        logger.info("  Return: %.2f%%", position.return_pct)

        self.strategy_data.update(
            {
                "market_close_timestamp": self.current_timestamp,
                "eod_realized_pnl": position.realized_pnl,
                "eod_trades": self.trades_today,
            }
        )

    def _update_moving_averages(self) -> None:
        """Update short and long moving averages."""

        # Store previous values for crossover detection
        self.prev_short_ma = self.short_ma
        self.prev_long_ma = self.long_ma

        # Calculate current moving averages
        self.short_ma = (
            sum(self.price_history[-self.short_period :]) / self.short_period
        )
        self.long_ma = sum(self.price_history[-self.long_period :]) / self.long_period

    def _generate_crossover_signal(self, tick: TickData) -> Signal | None:
        """Generate signal based on moving average crossover.

        Args:
            tick: Current market data tick

        Returns:
            Trading signal or None if no crossover detected
        """

        # Need previous values to detect crossover
        if self.prev_short_ma == 0 or self.prev_long_ma == 0:
            return None

        # Detect crossovers
        current_above = self.short_ma > self.long_ma
        prev_above = self.prev_short_ma > self.prev_long_ma

        # Golden cross (bullish): short MA crosses above long MA
        if current_above and not prev_above:
            strength = min(1.0, abs(self.short_ma - self.long_ma) / self.long_ma)

            return Signal(
                signal_type=SignalType.BUY,
                strength=strength,
                price=tick.price,
                timestamp=tick.timestamp,
                confidence=0.7,
                metadata={
                    "strategy": "ma_crossover",
                    "crossover_type": "golden_cross",
                    "short_ma": self.short_ma,
                    "long_ma": self.long_ma,
                    "ma_diff": self.short_ma - self.long_ma,
                    "short_period": self.short_period,
                    "long_period": self.long_period,
                },
            )

        # Death cross (bearish): short MA crosses below long MA
        if not current_above and prev_above:
            strength = min(1.0, abs(self.long_ma - self.short_ma) / self.long_ma)

            return Signal(
                signal_type=SignalType.SELL,
                strength=strength,
                price=tick.price,
                timestamp=tick.timestamp,
                confidence=0.7,
                metadata={
                    "strategy": "ma_crossover",
                    "crossover_type": "death_cross",
                    "short_ma": self.short_ma,
                    "long_ma": self.long_ma,
                    "ma_diff": self.long_ma - self.short_ma,
                    "short_period": self.short_period,
                    "long_period": self.long_period,
                },
            )

        return None

    def _should_trade_signal(self, signal: Signal) -> bool:
        """Determine if signal should be traded.

        Args:
            signal: Generated trading signal

        Returns:
            True if signal should be acted upon
        """

        # Check signal strength threshold
        if signal.strength < self.min_signal_strength:
            logger.debug(
                "Signal strength too weak: %.2f < %.2f",
                signal.strength,
                self.min_signal_strength,
            )
            return False

        # Check position manager constraints
        if signal.signal_type == SignalType.BUY:
            if not self.position_manager.can_enter_long(self.position_size):
                logger.debug("Cannot enter long position due to risk limits")
                return False

        elif signal.signal_type == SignalType.SELL:
            if not self.position_manager.can_enter_short(self.position_size):
                logger.debug("Cannot enter short position due to risk limits")
                return False

        # Prevent rapid-fire signals (minimum 1 minute between crossovers)
        min_interval = 60_000_000_000  # 1 minute in nanoseconds
        if signal.timestamp - self.last_crossover_timestamp < min_interval:
            logger.debug("Signal too soon after last crossover")
            return False

        # Check daily trade limits
        max_daily_trades = self.config.custom_params.get("max_daily_trades", 20)
        if self.trades_today >= max_daily_trades:
            logger.debug("Daily trade limit reached: %d", self.trades_today)
            return False

        return True

    def _execute_signal(self, signal: Signal, tick: TickData) -> None:
        """Execute trading action based on signal.

        Args:
            signal: Trading signal to execute
            tick: Current market data tick
        """

        try:
            current_position = self.position_manager.get_position_info()

            if signal.signal_type == SignalType.BUY:
                # Handle buy signal
                if current_position.is_short:
                    # Close short position first
                    self.submit_market_order(
                        OrderSide.BUY, current_position.abs_quantity, tick.timestamp
                    )
                    logger.info("Closed short position on buy signal")

                if current_position.is_flat or current_position.is_short:
                    # Enter long position
                    self.submit_market_order(
                        OrderSide.BUY, self.position_size, tick.timestamp
                    )
                    self.last_crossover_timestamp = tick.timestamp
                    logger.info(
                        "Entered long position: %d contracts on golden cross (strength: %.2f)",
                        self.position_size,
                        signal.strength,
                    )

            elif signal.signal_type == SignalType.SELL:
                # Handle sell signal
                if current_position.is_long:
                    # Close long position first
                    self.submit_market_order(
                        OrderSide.SELL, current_position.abs_quantity, tick.timestamp
                    )
                    logger.info("Closed long position on sell signal")

                if current_position.is_flat or current_position.is_long:
                    # Enter short position
                    self.submit_market_order(
                        OrderSide.SELL, self.position_size, tick.timestamp
                    )
                    self.last_crossover_timestamp = tick.timestamp
                    logger.info(
                        "Entered short position: %d contracts on death cross (strength: %.2f)",
                        self.position_size,
                        signal.strength,
                    )

        except Exception as e:
            logger.error("Error executing signal: %s", e)
            self.on_error(e)

    def _check_risk_management(self) -> None:
        """Check risk management triggers and take action if needed."""

        # Check stop loss conditions
        if self.position_manager.should_stop_out():
            logger.warning("Stop loss triggered - closing all positions")
            self.close_all_positions()

        # Check take profit conditions
        elif self.position_manager.should_take_profit():
            logger.info("Take profit triggered - closing all positions")
            self.close_all_positions()

    def get_strategy_info(self) -> dict:
        """Get comprehensive strategy information for monitoring.

        Returns:
            Dictionary containing strategy state and performance metrics
        """

        position = self.position_manager.get_position_info()
        risk_metrics = self.position_manager.get_risk_metrics()

        return {
            "strategy_name": self.config.strategy_name,
            "strategy_type": "moving_average_crossover",
            "parameters": {
                "short_period": self.short_period,
                "long_period": self.long_period,
                "min_signal_strength": self.min_signal_strength,
                "position_size": self.position_size,
            },
            "current_state": {
                "state": self.state.value,
                "last_price": self.get_last_price(),
                "short_ma": self.short_ma,
                "long_ma": self.long_ma,
                "ma_spread": self.short_ma - self.long_ma,
                "current_signal": self.current_signal.signal_type.value
                if self.current_signal
                else None,
                "signal_strength": self.current_signal.strength
                if self.current_signal
                else 0.0,
            },
            "position": {
                "side": position.side.value,
                "quantity": position.quantity,
                "average_price": position.average_price,
                "current_price": position.current_price,
                "unrealized_pnl": position.unrealized_pnl,
                "realized_pnl": position.realized_pnl,
                "net_pnl": position.net_pnl,
                "return_pct": position.return_pct,
            },
            "risk_metrics": risk_metrics,
            "performance": {
                "trades_today": self.trades_today,
                "total_trades": self.metrics.total_trades,
                "win_rate": self.metrics.win_rate,
                "gross_pnl": self.metrics.gross_pnl,
            },
        }
