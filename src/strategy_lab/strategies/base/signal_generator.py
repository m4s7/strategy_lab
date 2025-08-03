"""Signal generation utilities for trading strategies.

This module provides reusable signal generation components that strategies
can use to identify trading opportunities based on market data patterns.
"""

import logging
from collections import deque
from dataclasses import dataclass
from enum import Enum
from typing import Any

from ...backtesting.hft_integration.data_feed import TickData

logger = logging.getLogger(__name__)


class SignalType(Enum):
    """Types of trading signals."""

    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    EXIT_LONG = "exit_long"
    EXIT_SHORT = "exit_short"


@dataclass
class Signal:
    """Trading signal with metadata."""

    signal_type: SignalType
    strength: float  # Signal strength (0.0 to 1.0)
    price: float
    timestamp: int
    confidence: float = 0.5  # Confidence level (0.0 to 1.0)
    metadata: dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class TechnicalIndicators:
    """Collection of technical analysis indicators."""

    @staticmethod
    def simple_moving_average(prices: list[float], period: int) -> float | None:
        """Calculate Simple Moving Average.

        Args:
            prices: List of price values
            period: Number of periods for average

        Returns:
            SMA value or None if insufficient data
        """
        if len(prices) < period:
            return None

        return sum(prices[-period:]) / period

    @staticmethod
    def exponential_moving_average(
        prices: list[float], period: int, previous_ema: float | None = None
    ) -> float | None:
        """Calculate Exponential Moving Average.

        Args:
            prices: List of price values
            period: Number of periods for average
            previous_ema: Previous EMA value for incremental calculation

        Returns:
            EMA value or None if insufficient data
        """
        if len(prices) == 0:
            return None

        if len(prices) < period and previous_ema is None:
            return None

        current_price = prices[-1]

        if previous_ema is None:
            # First calculation - use SMA as starting point
            if len(prices) >= period:
                return TechnicalIndicators.simple_moving_average(prices, period)
            return None

        # Incremental EMA calculation
        multiplier = 2.0 / (period + 1)
        return (current_price * multiplier) + (previous_ema * (1 - multiplier))

    @staticmethod
    def rsi(prices: list[float], period: int = 14) -> float | None:
        """Calculate Relative Strength Index.

        Args:
            prices: List of price values
            period: RSI period (default 14)

        Returns:
            RSI value (0-100) or None if insufficient data
        """
        if len(prices) < period + 1:
            return None

        # Calculate price changes
        price_changes = []
        for i in range(1, len(prices)):
            price_changes.append(prices[i] - prices[i - 1])

        if len(price_changes) < period:
            return None

        # Separate gains and losses
        gains = [max(0, change) for change in price_changes[-period:]]
        losses = [abs(min(0, change)) for change in price_changes[-period:]]

        # Calculate average gain and loss
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period

        if avg_loss == 0:
            return 100.0  # No losses = max RSI

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    @staticmethod
    def bollinger_bands(
        prices: list[float], period: int = 20, std_dev: float = 2.0
    ) -> dict[str, float] | None:
        """Calculate Bollinger Bands.

        Args:
            prices: List of price values
            period: Period for moving average
            std_dev: Standard deviation multiplier

        Returns:
            Dict with 'upper', 'middle', 'lower' bands or None
        """
        if len(prices) < period:
            return None

        recent_prices = prices[-period:]
        middle = sum(recent_prices) / period

        # Calculate standard deviation
        variance = sum((p - middle) ** 2 for p in recent_prices) / period
        std = variance**0.5

        upper = middle + (std_dev * std)
        lower = middle - (std_dev * std)

        return {"upper": upper, "middle": middle, "lower": lower}


class MarketMicrostructure:
    """Market microstructure analysis tools."""

    @staticmethod
    def calculate_spread(bid: float, ask: float) -> float:
        """Calculate bid-ask spread.

        Args:
            bid: Best bid price
            ask: Best ask price

        Returns:
            Absolute spread
        """
        return ask - bid

    @staticmethod
    def calculate_spread_bps(
        bid: float, ask: float, mid_price: float | None = None
    ) -> float:
        """Calculate bid-ask spread in basis points.

        Args:
            bid: Best bid price
            ask: Best ask price
            mid_price: Mid price (defaults to (bid+ask)/2)

        Returns:
            Spread in basis points
        """
        if mid_price is None:
            mid_price = (bid + ask) / 2

        if mid_price == 0:
            return 0.0

        spread = ask - bid
        return (spread / mid_price) * 10000  # Convert to basis points

    @staticmethod
    def calculate_order_flow_imbalance(bid_size: float, ask_size: float) -> float:
        """Calculate order book imbalance.

        Args:
            bid_size: Total bid volume
            ask_size: Total ask volume

        Returns:
            Imbalance ratio (-1 to 1, positive = more bids)
        """
        total_size = bid_size + ask_size
        if total_size == 0:
            return 0.0

        return (bid_size - ask_size) / total_size


class SignalGenerator:
    """Main signal generation engine for trading strategies."""

    def __init__(self, config: Any):
        """Initialize signal generator with configuration.

        Args:
            config: Strategy configuration object
        """
        self.config = config

        # Price history buffers
        self.price_history: deque[float] = deque(maxlen=200)
        self.volume_history: deque[float] = deque(maxlen=200)
        self.timestamp_history: deque[int] = deque(maxlen=200)

        # Technical indicator state
        self.indicators: dict[str, Any] = {}

        # Signal history
        self.signal_history: deque[Signal] = deque(maxlen=50)

        logger.debug("Initialized SignalGenerator")

    def update(self, tick: TickData) -> None:
        """Update signal generator with new market data.

        Args:
            tick: New market data tick
        """
        # Update price history
        self.price_history.append(tick.price)
        self.volume_history.append(tick.qty)
        self.timestamp_history.append(tick.timestamp)

        # Update indicators
        self._update_indicators()

    def generate_signal(self, tick: TickData) -> Signal | None:
        """Generate trading signal based on current market conditions.

        This is a template method that can be overridden by specific strategies.

        Args:
            tick: Current market data tick

        Returns:
            Trading signal or None if no signal
        """
        # Update internal state
        self.update(tick)

        # Default implementation - no signal
        return None

    def generate_mean_reversion_signal(
        self, tick: TickData, lookback_period: int = 20, threshold_std: float = 2.0
    ) -> Signal | None:
        """Generate mean reversion signal using Bollinger Bands.

        Args:
            tick: Current market data tick
            lookback_period: Period for Bollinger Bands calculation
            threshold_std: Standard deviation threshold for signals

        Returns:
            Mean reversion signal or None
        """
        self.update(tick)

        if len(self.price_history) < lookback_period:
            return None

        # Calculate Bollinger Bands
        bands = TechnicalIndicators.bollinger_bands(
            list(self.price_history), lookback_period, threshold_std
        )

        if bands is None:
            return None

        current_price = tick.price

        # Generate signals based on band touches
        if current_price <= bands["lower"]:
            # Price at lower band - potential buy signal
            strength = min(
                1.0,
                (bands["middle"] - current_price) / (bands["middle"] - bands["lower"]),
            )
            return Signal(
                signal_type=SignalType.BUY,
                strength=strength,
                price=current_price,
                timestamp=tick.timestamp,
                confidence=0.7,
                metadata={
                    "indicator": "bollinger_bands",
                    "bands": bands,
                    "lookback_period": lookback_period,
                },
            )

        if current_price >= bands["upper"]:
            # Price at upper band - potential sell signal
            strength = min(
                1.0,
                (current_price - bands["middle"]) / (bands["upper"] - bands["middle"]),
            )
            return Signal(
                signal_type=SignalType.SELL,
                strength=strength,
                price=current_price,
                timestamp=tick.timestamp,
                confidence=0.7,
                metadata={
                    "indicator": "bollinger_bands",
                    "bands": bands,
                    "lookback_period": lookback_period,
                },
            )

        return None

    def generate_momentum_signal(
        self, tick: TickData, short_period: int = 5, long_period: int = 20
    ) -> Signal | None:
        """Generate momentum signal using moving average crossover.

        Args:
            tick: Current market data tick
            short_period: Short-term moving average period
            long_period: Long-term moving average period

        Returns:
            Momentum signal or None
        """
        self.update(tick)

        if len(self.price_history) < long_period:
            return None

        prices = list(self.price_history)

        # Calculate moving averages
        short_ma = TechnicalIndicators.simple_moving_average(prices, short_period)
        long_ma = TechnicalIndicators.simple_moving_average(prices, long_period)

        if short_ma is None or long_ma is None:
            return None

        # Get previous short MA for crossover detection
        if len(self.price_history) < long_period + 1:
            return None

        prev_short_ma = TechnicalIndicators.simple_moving_average(
            prices[:-1], short_period
        )
        prev_long_ma = TechnicalIndicators.simple_moving_average(
            prices[:-1], long_period
        )

        if prev_short_ma is None or prev_long_ma is None:
            return None

        # Detect crossovers
        current_above = short_ma > long_ma
        prev_above = prev_short_ma > prev_long_ma

        if current_above and not prev_above:
            # Golden cross - bullish signal
            strength = min(1.0, (short_ma - long_ma) / long_ma)
            return Signal(
                signal_type=SignalType.BUY,
                strength=strength,
                price=tick.price,
                timestamp=tick.timestamp,
                confidence=0.6,
                metadata={
                    "indicator": "ma_crossover",
                    "short_ma": short_ma,
                    "long_ma": long_ma,
                    "short_period": short_period,
                    "long_period": long_period,
                },
            )

        if not current_above and prev_above:
            # Death cross - bearish signal
            strength = min(1.0, (long_ma - short_ma) / long_ma)
            return Signal(
                signal_type=SignalType.SELL,
                strength=strength,
                price=tick.price,
                timestamp=tick.timestamp,
                confidence=0.6,
                metadata={
                    "indicator": "ma_crossover",
                    "short_ma": short_ma,
                    "long_ma": long_ma,
                    "short_period": short_period,
                    "long_period": long_period,
                },
            )

        return None

    def generate_rsi_signal(
        self,
        tick: TickData,
        period: int = 14,
        oversold_threshold: float = 30.0,
        overbought_threshold: float = 70.0,
    ) -> Signal | None:
        """Generate RSI-based signal.

        Args:
            tick: Current market data tick
            period: RSI calculation period
            oversold_threshold: RSI threshold for oversold condition
            overbought_threshold: RSI threshold for overbought condition

        Returns:
            RSI signal or None
        """
        self.update(tick)

        if len(self.price_history) < period + 1:
            return None

        rsi = TechnicalIndicators.rsi(list(self.price_history), period)

        if rsi is None:
            return None

        # Generate signals based on RSI levels
        if rsi <= oversold_threshold:
            # Oversold - potential buy signal
            strength = (oversold_threshold - rsi) / oversold_threshold
            return Signal(
                signal_type=SignalType.BUY,
                strength=strength,
                price=tick.price,
                timestamp=tick.timestamp,
                confidence=0.65,
                metadata={
                    "indicator": "rsi",
                    "rsi_value": rsi,
                    "threshold": oversold_threshold,
                    "condition": "oversold",
                },
            )

        if rsi >= overbought_threshold:
            # Overbought - potential sell signal
            strength = (rsi - overbought_threshold) / (100 - overbought_threshold)
            return Signal(
                signal_type=SignalType.SELL,
                strength=strength,
                price=tick.price,
                timestamp=tick.timestamp,
                confidence=0.65,
                metadata={
                    "indicator": "rsi",
                    "rsi_value": rsi,
                    "threshold": overbought_threshold,
                    "condition": "overbought",
                },
            )

        return None

    def get_last_signal(self) -> Signal | None:
        """Get the most recent signal generated.

        Returns:
            Last signal or None if no signals generated
        """
        return self.signal_history[-1] if self.signal_history else None

    def get_signal_history(self, count: int = 10) -> list[Signal]:
        """Get recent signal history.

        Args:
            count: Number of recent signals to return

        Returns:
            List of recent signals
        """
        return list(self.signal_history)[-count:]

    def get_indicator_values(self) -> dict[str, Any]:
        """Get current indicator values.

        Returns:
            Dictionary of current indicator values
        """
        return self.indicators.copy()

    def _update_indicators(self) -> None:
        """Update all technical indicators with current data."""
        if len(self.price_history) < 2:
            return

        prices = list(self.price_history)

        # Update various indicators
        self.indicators["sma_5"] = TechnicalIndicators.simple_moving_average(prices, 5)
        self.indicators["sma_20"] = TechnicalIndicators.simple_moving_average(
            prices, 20
        )
        self.indicators["sma_50"] = TechnicalIndicators.simple_moving_average(
            prices, 50
        )

        self.indicators["rsi"] = TechnicalIndicators.rsi(prices)

        self.indicators["bb"] = TechnicalIndicators.bollinger_bands(prices)

        # Current price levels
        if len(prices) >= 1:
            self.indicators["last_price"] = prices[-1]

        if len(prices) >= 2:
            self.indicators["price_change"] = prices[-1] - prices[-2]
            self.indicators["price_change_pct"] = (
                (prices[-1] - prices[-2]) / prices[-2] * 100 if prices[-2] != 0 else 0.0
            )
