"""Simple Moving Average strategy example using pluggable architecture."""

import logging
from typing import Any

import pandas as pd

from ..base.pluggable_strategy import PluggableStrategy
from ..protocol import StrategyMetadata
from ..registry import register_strategy

logger = logging.getLogger(__name__)


@register_strategy(
    StrategyMetadata(
        name="SimpleMAStrategy",
        version="1.0.0",
        description="Simple moving average crossover strategy",
        author="Strategy Lab",
        tags=["trend-following", "moving-average", "example"],
        parameters={"fast_period": 10, "slow_period": 30, "min_data_points": 35},
        requirements={"data": ["price"], "min_history": 35},
    )
)
class SimpleMAStrategy(PluggableStrategy):
    """Simple moving average crossover strategy.

    This strategy generates buy signals when the fast MA crosses above
    the slow MA, and sell signals when the fast MA crosses below.
    """

    name = "SimpleMAStrategy"
    version = "1.0.0"
    description = "Simple moving average crossover strategy"

    def _initialize_strategy(self) -> None:
        """Initialize strategy-specific components."""
        # Get parameters with defaults
        self.fast_period = self._parameters.get("fast_period", 10)
        self.slow_period = self._parameters.get("slow_period", 30)
        self.min_data_points = self._parameters.get(
            "min_data_points", self.slow_period + 5
        )

        # Internal state
        self.fast_ma = 0.0
        self.slow_ma = 0.0
        self.prev_fast_ma = 0.0
        self.prev_slow_ma = 0.0
        self.position = 0  # Track current position

        logger.info(
            f"Initialized {self.name} with fast={self.fast_period}, "
            f"slow={self.slow_period}"
        )

    def _generate_signal(
        self,
        timestamp: pd.Timestamp,
        price: float,
        volume: int,
        bid: float,
        ask: float,
        **kwargs,
    ) -> int | None:
        """Generate trading signal based on MA crossover."""
        # Check if we have enough data
        if not self.has_enough_data(self.min_data_points):
            return None

        # Get price series
        prices = self.get_price_series()

        # Calculate moving averages
        self.prev_fast_ma = self.fast_ma
        self.prev_slow_ma = self.slow_ma

        self.fast_ma = prices.tail(self.fast_period).mean()
        self.slow_ma = prices.tail(self.slow_period).mean()

        # Skip if we don't have previous values
        if self.prev_fast_ma == 0 or self.prev_slow_ma == 0:
            return None

        # Detect crossovers
        prev_diff = self.prev_fast_ma - self.prev_slow_ma
        curr_diff = self.fast_ma - self.slow_ma

        signal = None

        # Fast MA crosses above slow MA - BUY signal
        if prev_diff <= 0 and curr_diff > 0:
            signal = 1
            self.position = 1
            logger.debug(
                f"BUY signal at {timestamp}: fast_ma={self.fast_ma:.2f}, "
                f"slow_ma={self.slow_ma:.2f}"
            )

        # Fast MA crosses below slow MA - SELL signal
        elif prev_diff >= 0 and curr_diff < 0:
            signal = -1
            self.position = -1
            logger.debug(
                f"SELL signal at {timestamp}: fast_ma={self.fast_ma:.2f}, "
                f"slow_ma={self.slow_ma:.2f}"
            )

        # Exit positions at crossover (flatten)
        elif self.position != 0 and abs(curr_diff) < 0.01:  # Near crossover
            signal = 0
            self.position = 0
            logger.debug(f"FLAT signal at {timestamp}: MAs converging")

        return signal

    def _get_custom_state(self) -> dict[str, Any] | None:
        """Get strategy-specific state."""
        return {
            "fast_ma": self.fast_ma,
            "slow_ma": self.slow_ma,
            "prev_fast_ma": self.prev_fast_ma,
            "prev_slow_ma": self.prev_slow_ma,
            "position": self.position,
        }

    def _set_custom_state(self, custom_state: dict[str, Any]) -> None:
        """Restore strategy-specific state."""
        self.fast_ma = custom_state.get("fast_ma", 0.0)
        self.slow_ma = custom_state.get("slow_ma", 0.0)
        self.prev_fast_ma = custom_state.get("prev_fast_ma", 0.0)
        self.prev_slow_ma = custom_state.get("prev_slow_ma", 0.0)
        self.position = custom_state.get("position", 0)

    def on_trade(self, trade_data: dict[str, Any]) -> None:
        """Handle trade execution notification."""
        logger.info(f"Trade executed: {trade_data}")

    def get_indicators(self) -> dict[str, float]:
        """Get current indicator values.

        Returns:
            Dictionary of indicator values
        """
        return {
            "fast_ma": self.fast_ma,
            "slow_ma": self.slow_ma,
            "ma_diff": self.fast_ma - self.slow_ma,
            "position": self.position,
        }
