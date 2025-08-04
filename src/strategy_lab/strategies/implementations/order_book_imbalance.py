"""Order Book Imbalance Strategy implementation.

This strategy uses Level 2 order book data to calculate imbalance
between bid and ask volumes, generating trading signals based on
significant imbalances.
"""

import logging
from collections import deque
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

from ..base.pluggable_strategy import PluggableStrategy
from ..base.position_manager import PositionManager
from ..protocol import StrategyMetadata
from ..registry import register_strategy


@dataclass
class ImbalanceMetrics:
    """Metrics for order book imbalance calculations."""

    raw_imbalance: float
    smoothed_imbalance: float
    bid_volume: float
    ask_volume: float
    depth_levels: int
    timestamp: pd.Timestamp


@dataclass
class ImbalanceState:
    """State tracking for imbalance calculations."""

    imbalance_history: deque = field(default_factory=lambda: deque(maxlen=100))
    signal_history: deque = field(default_factory=lambda: deque(maxlen=100))
    last_signal: int = 0
    position_entry_time: pd.Timestamp | None = None
    position_entry_price: float | None = None
    consecutive_signals: int = 0


@register_strategy(
    StrategyMetadata(
        name="order_book_imbalance",
        version="1.0.0",
        description="Trades based on order book volume imbalances using Level 2 data",
        author="Strategy Lab",
        tags=["microstructure", "level-2", "order-book", "imbalance"],
        parameters={
            "imbalance_threshold": 0.6,
            "smoothing_window": 5,
            "depth_levels": 5,
            "min_volume_ratio": 1.5,
            "signal_persistence": 3,
            "position_size": 1,
            "stop_loss_percent": 0.002,
            "take_profit_percent": 0.003,
        },
        requirements={
            "data": ["level-2", "order-book", "bid", "ask"],
            "min_history": 20,
        },
    )
)
class OrderBookImbalanceStrategy(PluggableStrategy):
    """Strategy that trades based on order book volume imbalances.

    This strategy calculates the imbalance between bid and ask volumes
    in the order book, using depth-weighted calculations to identify
    potential price movements.
    """

    # Strategy metadata
    name = "order_book_imbalance"
    version = "1.0.0"

    @classmethod
    def get_metadata(cls) -> StrategyMetadata:
        """Get strategy metadata."""
        return StrategyMetadata(
            name=cls.name,
            version=cls.version,
            description="Trades based on order book volume imbalances",
            parameters={
                "positive_threshold": "Threshold for long signals (0.0-1.0)",
                "negative_threshold": "Threshold for short signals (-1.0-0.0)",
                "smoothing_window": "Window size for imbalance smoothing",
                "depth_levels": "Number of order book levels to analyze",
                "depth_weight_decay": "Decay factor for deeper levels",
                "position_size": "Fixed position size",
                "stop_loss_pct": "Stop loss percentage",
                "max_holding_seconds": "Maximum position holding time",
                "min_spread_ticks": "Minimum spread in ticks to trade",
                "volatility_filter": "Enable volatility filtering",
            },
            tags=["scalping", "order-book", "microstructure"],
            requirements={"data": ["level2", "trades"]},
        )

    def __init__(self, **kwargs):
        """Initialize strategy with parameters."""
        super().__init__(**kwargs)

        # Strategy parameters with defaults
        self.positive_threshold = kwargs.get("positive_threshold", 0.3)
        self.negative_threshold = kwargs.get("negative_threshold", -0.3)
        self.smoothing_window = kwargs.get("smoothing_window", 5)
        self.depth_levels = kwargs.get("depth_levels", 5)
        self.depth_weight_decay = kwargs.get("depth_weight_decay", 0.8)
        self.position_size = kwargs.get("position_size", 1)
        self.stop_loss_pct = kwargs.get("stop_loss_pct", 0.5)
        self.max_holding_seconds = kwargs.get("max_holding_seconds", 300)
        self.min_spread_ticks = kwargs.get("min_spread_ticks", 1)
        self.volatility_filter = kwargs.get("volatility_filter", True)

        # Initialize state
        self.state = ImbalanceState()
        self._metrics_buffer: list[ImbalanceMetrics] = []

        # Initialize position manager with config
        config = type(
            "Config",
            (),
            {
                "max_position_size": kwargs.get("max_position_size", 10),
                "max_daily_loss": kwargs.get("max_daily_loss", 1000.0),
                "stop_loss_pct": self.stop_loss_pct / 100.0,  # Convert to decimal
            },
        )()
        self.position_manager = PositionManager(config)

        # Logger
        self.logger = logging.getLogger(self.__class__.__name__)

    def _initialize_strategy(self) -> None:
        """Strategy-specific initialization logic."""
        self.state = ImbalanceState()
        self._metrics_buffer.clear()
        # Reset position manager state
        self.position_manager.position = type(self.position_manager.position)()
        self.position_manager.daily_pnl = 0.0
        self.position_manager.fill_history.clear()
        self.logger.info(
            f"Initialized {self.name} with thresholds: "
            f"[{self.negative_threshold}, {self.positive_threshold}]"
        )

    def calculate_imbalance(
        self, bid_levels: list[tuple[float, int]], ask_levels: list[tuple[float, int]]
    ) -> ImbalanceMetrics:
        """Calculate order book imbalance with depth weighting.

        Args:
            bid_levels: List of (price, volume) tuples for bids
            ask_levels: List of (price, volume) tuples for asks

        Returns:
            ImbalanceMetrics with calculated values
        """
        # Limit to configured depth
        bid_levels = bid_levels[: self.depth_levels]
        ask_levels = ask_levels[: self.depth_levels]

        # Calculate weighted volumes
        bid_volume = 0.0
        ask_volume = 0.0

        for i, (price, volume) in enumerate(bid_levels):
            weight = self.depth_weight_decay**i
            bid_volume += volume * weight

        for i, (price, volume) in enumerate(ask_levels):
            weight = self.depth_weight_decay**i
            ask_volume += volume * weight

        # Calculate raw imbalance
        total_volume = bid_volume + ask_volume
        if total_volume > 0:
            raw_imbalance = (bid_volume - ask_volume) / total_volume
        else:
            raw_imbalance = 0.0

        # Add to history
        self.state.imbalance_history.append(raw_imbalance)

        # Calculate smoothed imbalance
        if len(self.state.imbalance_history) >= self.smoothing_window:
            recent_values = list(self.state.imbalance_history)[-self.smoothing_window :]
            smoothed_imbalance = np.mean(recent_values)
        else:
            smoothed_imbalance = raw_imbalance

        return ImbalanceMetrics(
            raw_imbalance=raw_imbalance,
            smoothed_imbalance=smoothed_imbalance,
            bid_volume=bid_volume,
            ask_volume=ask_volume,
            depth_levels=len(bid_levels) + len(ask_levels),
            timestamp=pd.Timestamp.now(),
        )

    def check_spread_conditions(
        self, best_bid: float, best_ask: float, tick_size: float = 0.25
    ) -> bool:
        """Check if spread conditions are favorable for trading.

        Args:
            best_bid: Best bid price
            best_ask: Best ask price
            tick_size: Minimum price increment

        Returns:
            True if spread conditions are met
        """
        spread_ticks = (best_ask - best_bid) / tick_size
        return spread_ticks >= self.min_spread_ticks

    def check_volatility_filter(self, price_history: list[float]) -> bool:
        """Check if volatility conditions are favorable.

        Args:
            price_history: Recent price history

        Returns:
            True if volatility conditions are met
        """
        if not self.volatility_filter or len(price_history) < 20:
            return True

        # Calculate simple volatility measure
        prices = np.array(price_history)
        returns = np.diff(prices) / prices[:-1]

        # Check for valid returns
        if len(returns) == 0 or np.all(returns == 0):
            return True  # No volatility data, allow trading

        volatility = np.std(returns) * np.sqrt(252 * 6.5 * 60 * 60)  # Annualized

        # Trade when volatility is in reasonable range (not too high, not too low)
        return 0.05 < volatility < 0.5

    def generate_signal(self, metrics: ImbalanceMetrics) -> int:
        """Generate trading signal based on imbalance metrics.

        Args:
            metrics: Current imbalance metrics

        Returns:
            Signal: 1 for long, -1 for short, 0 for neutral
        """
        imbalance = metrics.smoothed_imbalance

        # Check thresholds
        if imbalance > self.positive_threshold:
            signal = 1
        elif imbalance < self.negative_threshold:
            signal = -1
        else:
            signal = 0

        # Track consecutive signals
        if signal == self.state.last_signal and signal != 0:
            self.state.consecutive_signals += 1
        else:
            self.state.consecutive_signals = 1 if signal != 0 else 0

        self.state.last_signal = signal
        self.state.signal_history.append(signal)

        return signal

    def check_exit_conditions(
        self, current_price: float, current_time: pd.Timestamp
    ) -> bool:
        """Check if position should be exited.

        Args:
            current_price: Current market price
            current_time: Current timestamp

        Returns:
            True if position should be exited
        """
        if self.state.position_entry_price is None:
            return False

        # Check stop loss
        if self.state.last_signal == 1:  # Long position
            pnl_pct = (
                (current_price - self.state.position_entry_price)
                / self.state.position_entry_price
                * 100
            )
            if pnl_pct <= -self.stop_loss_pct:
                self.logger.info(f"Stop loss triggered: {pnl_pct:.2f}%")
                return True
        elif self.state.last_signal == -1:  # Short position
            pnl_pct = (
                (self.state.position_entry_price - current_price)
                / self.state.position_entry_price
                * 100
            )
            if pnl_pct <= -self.stop_loss_pct:
                self.logger.info(f"Stop loss triggered: {pnl_pct:.2f}%")
                return True

        # Check time limit
        if self.state.position_entry_time:
            holding_time = (
                current_time - self.state.position_entry_time
            ).total_seconds()
            if holding_time > self.max_holding_seconds:
                self.logger.info(f"Time limit reached: {holding_time:.0f}s")
                return True

        # Check if signal has reversed
        if len(self.state.signal_history) >= 2:
            if self.state.signal_history[-1] == -self.state.signal_history[-2]:
                self.logger.info("Signal reversal detected")
                return True

        return False

    def _generate_signal(
        self,
        timestamp: pd.Timestamp,
        price: float,
        volume: int,
        bid: float,
        ask: float,
        **kwargs,
    ) -> int | None:
        """Generate trading signal based on order book imbalance.

        Args:
            timestamp: Tick timestamp
            price: Last trade price
            volume: Trade volume
            bid: Best bid price
            ask: Best ask price
            **kwargs: Additional data including bid_levels and ask_levels

        Returns:
            Trading signal (-1, 0, 1) or None
        """
        # Extract Level 2 data from kwargs
        bid_levels = kwargs.get("bid_levels")
        ask_levels = kwargs.get("ask_levels")

        # Check if we have Level 2 data
        if bid_levels is None or ask_levels is None:
            return 0

        # Calculate imbalance metrics
        metrics = self.calculate_imbalance(bid_levels, ask_levels)
        self._metrics_buffer.append(metrics)

        # Check market conditions
        if not self.check_spread_conditions(bid, ask):
            return 0

        # Get price history for volatility check
        price_history = kwargs.get("price_history", self._price_history)
        if not self.check_volatility_filter(price_history):
            return 0

        # Check exit conditions for existing position
        if self.position_manager.has_position() and self.check_exit_conditions(
            price, timestamp
        ):
            self.state.position_entry_time = None
            self.state.position_entry_price = None
            return 0  # Exit signal

        # Generate new signal if flat
        if not self.position_manager.has_position():
            signal = self.generate_signal(metrics)

            # Only take signal if we have enough confirmation
            if signal != 0 and self.state.consecutive_signals >= 2:
                self.state.position_entry_time = timestamp
                self.state.position_entry_price = price

                self.logger.info(
                    f"Signal generated: {signal}, "
                    f"Imbalance: {metrics.smoothed_imbalance:.3f}, "
                    f"Bid Vol: {metrics.bid_volume:.0f}, "
                    f"Ask Vol: {metrics.ask_volume:.0f}"
                )

                return signal

        return 0

    def get_position_size(self, signal: int, current_price: float) -> int:
        """Get position size for signal.

        Args:
            signal: Trading signal
            current_price: Current market price

        Returns:
            Position size in contracts
        """
        # For now, use fixed position size
        # Could implement volatility-based or risk-based sizing
        return self.position_size if signal != 0 else 0

    def _cleanup_strategy(self) -> None:
        """Strategy-specific cleanup logic."""
        # Log summary statistics
        if self._metrics_buffer:
            imbalances = [m.smoothed_imbalance for m in self._metrics_buffer]
            self.logger.info(
                f"Strategy summary - "
                f"Avg Imbalance: {np.mean(imbalances):.3f}, "
                f"Std Imbalance: {np.std(imbalances):.3f}, "
                f"Total Ticks: {len(self._metrics_buffer)}"
            )

    def _get_custom_state(self) -> dict[str, Any] | None:
        """Get strategy-specific state."""
        return {
            "imbalance_history": list(self.state.imbalance_history),
            "signal_history": list(self.state.signal_history),
            "last_signal": self.state.last_signal,
            "consecutive_signals": self.state.consecutive_signals,
            "metrics_count": len(self._metrics_buffer),
        }

    def _set_custom_state(self, custom_state: dict[str, Any]) -> None:
        """Set strategy-specific state."""
        # Restore imbalance state
        if "imbalance_history" in custom_state:
            self.state.imbalance_history = deque(
                custom_state["imbalance_history"], maxlen=100
            )
        if "signal_history" in custom_state:
            self.state.signal_history = deque(
                custom_state["signal_history"], maxlen=100
            )
        self.state.last_signal = custom_state.get("last_signal", 0)
        self.state.consecutive_signals = custom_state.get("consecutive_signals", 0)
