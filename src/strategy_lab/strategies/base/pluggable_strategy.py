"""Pluggable base strategy implementation following the protocol."""

import logging
from abc import ABC, abstractmethod
from typing import Any

import pandas as pd

from ..protocol import StrategyProtocol

logger = logging.getLogger(__name__)


class PluggableStrategy(ABC, StrategyProtocol):
    """Base class for pluggable strategies.

    This class provides common functionality while enforcing the
    StrategyProtocol interface for all strategies.
    """

    # Class-level metadata (can be overridden by subclasses)
    name: str = "PluggableStrategy"
    version: str = "1.0.0"
    description: str = "Base pluggable strategy"

    def __init__(self, **kwargs):
        """Initialize the strategy with parameters.

        Args:
            **kwargs: Strategy-specific parameters
        """
        # Store parameters
        self._parameters = kwargs

        # Internal state
        self._initialized = False
        self._tick_count = 0
        self._last_signal = 0
        self._state_data: dict[str, Any] = {}

        # Data buffers
        self._price_history: list[float] = []
        self._volume_history: list[int] = []
        self._timestamp_history: list[pd.Timestamp] = []

        # Performance tracking
        self._signal_count = 0
        self._last_tick_time: pd.Timestamp | None = None

        logger.info(f"Created {self.name} v{self.version}")

    @property
    def parameters(self) -> dict[str, Any]:
        """Get current strategy parameters."""
        return self._parameters.copy()

    def initialize(self, **kwargs) -> None:
        """Initialize strategy state and resources.

        Args:
            **kwargs: Additional initialization parameters
        """
        # Update parameters if provided
        self._parameters.update(kwargs)

        # Call strategy-specific initialization
        self._initialize_strategy()

        self._initialized = True
        logger.info(f"{self.name} initialized with parameters: {self._parameters}")

    @abstractmethod
    def _initialize_strategy(self) -> None:
        """Strategy-specific initialization logic.

        Subclasses must implement this method to set up their
        specific indicators, thresholds, etc.
        """

    def process_tick(
        self,
        timestamp: pd.Timestamp,
        price: float,
        volume: int,
        bid: float,
        ask: float,
        **kwargs,
    ) -> int | None:
        """Process a market data tick and generate trading signal.

        Args:
            timestamp: Tick timestamp
            price: Current price
            volume: Trade volume
            bid: Best bid price
            ask: Best ask price
            **kwargs: Additional tick data

        Returns:
            Trading signal: 1 (buy), -1 (sell), 0 (flat), None (no action)
        """
        if not self._initialized:
            raise RuntimeError(f"{self.name} not initialized")

        # Update internal tracking
        self._tick_count += 1
        self._last_tick_time = timestamp

        # Store data in buffers
        self._price_history.append(price)
        self._volume_history.append(volume)
        self._timestamp_history.append(timestamp)

        # Limit buffer size (configurable)
        max_buffer = self._parameters.get("max_buffer_size", 1000)
        if len(self._price_history) > max_buffer:
            self._price_history.pop(0)
            self._volume_history.pop(0)
            self._timestamp_history.pop(0)

        # Generate signal using strategy-specific logic
        signal = self._generate_signal(timestamp, price, volume, bid, ask, **kwargs)

        # Track signal generation
        if signal is not None and signal != 0:
            self._signal_count += 1
            self._last_signal = signal

        return signal

    @abstractmethod
    def _generate_signal(
        self,
        timestamp: pd.Timestamp,
        price: float,
        volume: int,
        bid: float,
        ask: float,
        **kwargs,
    ) -> int | None:
        """Generate trading signal based on strategy logic.

        Subclasses must implement this method with their specific
        signal generation logic.

        Args:
            timestamp: Tick timestamp
            price: Current price
            volume: Trade volume
            bid: Best bid price
            ask: Best ask price
            **kwargs: Additional tick data

        Returns:
            Trading signal or None
        """

    def cleanup(self) -> None:
        """Cleanup strategy resources and save state."""
        # Save any important state
        self._state_data["tick_count"] = self._tick_count
        self._state_data["signal_count"] = self._signal_count
        self._state_data["last_signal"] = self._last_signal

        # Call strategy-specific cleanup
        self._cleanup_strategy()

        self._initialized = False
        logger.info(f"{self.name} cleaned up after {self._tick_count} ticks")

    def _cleanup_strategy(self) -> None:
        """Strategy-specific cleanup logic.

        Subclasses can override this method to perform custom cleanup.
        """

    def get_state(self) -> dict[str, Any]:
        """Get current strategy state for persistence.

        Returns:
            Dictionary containing strategy state
        """
        state = {
            "parameters": self._parameters,
            "tick_count": self._tick_count,
            "signal_count": self._signal_count,
            "last_signal": self._last_signal,
            "state_data": self._state_data.copy(),
            "buffer_size": len(self._price_history),
        }

        # Add strategy-specific state
        custom_state = self._get_custom_state()
        if custom_state:
            state["custom"] = custom_state

        return state

    def _get_custom_state(self) -> dict[str, Any] | None:
        """Get strategy-specific state.

        Subclasses can override this to save custom state.

        Returns:
            Custom state dictionary or None
        """
        return None

    def set_state(self, state: dict[str, Any]) -> None:
        """Restore strategy state from persistence.

        Args:
            state: Previously saved state dictionary
        """
        # Restore basic state
        self._parameters = state.get("parameters", {})
        self._tick_count = state.get("tick_count", 0)
        self._signal_count = state.get("signal_count", 0)
        self._last_signal = state.get("last_signal", 0)
        self._state_data = state.get("state_data", {})

        # Restore custom state
        if "custom" in state:
            self._set_custom_state(state["custom"])

        logger.info(f"{self.name} state restored")

    def _set_custom_state(self, custom_state: dict[str, Any]) -> None:
        """Set strategy-specific state.

        Subclasses can override this to restore custom state.

        Args:
            custom_state: Custom state dictionary
        """

    # Utility methods for subclasses

    def get_price_series(self, lookback: int | None = None) -> pd.Series:
        """Get price history as pandas Series.

        Args:
            lookback: Number of periods to include (None for all)

        Returns:
            Price series with timestamp index
        """
        if lookback:
            prices = self._price_history[-lookback:]
            timestamps = self._timestamp_history[-lookback:]
        else:
            prices = self._price_history
            timestamps = self._timestamp_history

        if not prices:
            return pd.Series(dtype=float)

        return pd.Series(prices, index=timestamps)

    def get_volume_series(self, lookback: int | None = None) -> pd.Series:
        """Get volume history as pandas Series.

        Args:
            lookback: Number of periods to include (None for all)

        Returns:
            Volume series with timestamp index
        """
        if lookback:
            volumes = self._volume_history[-lookback:]
            timestamps = self._timestamp_history[-lookback:]
        else:
            volumes = self._volume_history
            timestamps = self._timestamp_history

        if not volumes:
            return pd.Series(dtype=int)

        return pd.Series(volumes, index=timestamps)

    def has_enough_data(self, required_periods: int) -> bool:
        """Check if strategy has enough data for calculations.

        Args:
            required_periods: Minimum periods needed

        Returns:
            True if enough data available
        """
        return len(self._price_history) >= required_periods
