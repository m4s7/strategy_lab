"""Bid-Ask Bounce Strategy implementation.

This strategy detects and trades bid-ask bounces using Level 1 tick data,
identifying when price touches bid/ask levels and reverses direction.
"""

import logging
from collections import deque
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

from ..base.pluggable_strategy import PluggableStrategy
from ..protocol import StrategyMetadata
from ..registry import register_strategy

logger = logging.getLogger(__name__)


@dataclass
class BounceDetection:
    """Represents a detected bounce pattern."""

    timestamp: pd.Timestamp
    bounce_type: str  # 'bid' or 'ask'
    touch_price: float
    bounce_price: float
    strength: float
    volume: int
    spread_at_bounce: float


@dataclass
class BounceState:
    """State tracking for bounce detection and trading."""

    price_history: deque = field(default_factory=lambda: deque(maxlen=20))
    volume_history: deque = field(default_factory=lambda: deque(maxlen=20))
    bid_history: deque = field(default_factory=lambda: deque(maxlen=20))
    ask_history: deque = field(default_factory=lambda: deque(maxlen=20))
    timestamp_history: deque = field(default_factory=lambda: deque(maxlen=20))

    detected_bounces: deque = field(default_factory=lambda: deque(maxlen=10))
    active_bounce: BounceDetection | None = None

    position_entry_time: pd.Timestamp | None = None
    position_entry_price: float | None = None
    position_direction: int = 0  # 1 for long, -1 for short

    last_signal: int = 0
    last_signal_time: pd.Timestamp | None = None

    # Performance tracking
    bounce_success_count: int = 0
    bounce_fail_count: int = 0
    entry_timing_delays: list[float] = field(default_factory=list)


@register_strategy
class BidAskBounceStrategy(PluggableStrategy):
    """Strategy that trades bounces off bid and ask levels.

    This Level 1 data strategy detects when price touches bid/ask levels
    and reverses, entering positions on confirmed bounce patterns.
    """

    # Strategy metadata
    name = "bid_ask_bounce"
    version = "1.0.0"
    description = "Trades bounces off bid/ask levels using Level 1 data"

    @classmethod
    def get_metadata(cls) -> StrategyMetadata:
        """Get strategy metadata."""
        return StrategyMetadata(
            name=cls.name,
            version=cls.version,
            description=cls.description,
            author="Strategy Lab",
            parameters={
                "bounce_sensitivity": {
                    "type": "float",
                    "default": 0.7,
                    "min": 0.1,
                    "max": 1.0,
                    "description": "Sensitivity for detecting bounces (0.1-1.0)",
                },
                "min_bounce_strength": {
                    "type": "float",
                    "default": 0.5,
                    "min": 0.1,
                    "max": 2.0,
                    "description": "Minimum bounce strength in ticks",
                },
                "profit_target_ticks": {
                    "type": "int",
                    "default": 2,
                    "min": 1,
                    "max": 10,
                    "description": "Profit target in ticks",
                },
                "stop_loss_ticks": {
                    "type": "int",
                    "default": 1,
                    "min": 1,
                    "max": 5,
                    "description": "Stop loss in ticks",
                },
                "max_spread_ticks": {
                    "type": "int",
                    "default": 2,
                    "min": 1,
                    "max": 5,
                    "description": "Maximum spread to allow trading",
                },
                "min_volume": {
                    "type": "int",
                    "default": 10,
                    "min": 1,
                    "max": 100,
                    "description": "Minimum volume for signal validity",
                },
                "max_holding_seconds": {
                    "type": "int",
                    "default": 120,
                    "min": 10,
                    "max": 600,
                    "description": "Maximum position holding time in seconds",
                },
                "confirmation_ticks": {
                    "type": "int",
                    "default": 2,
                    "min": 1,
                    "max": 5,
                    "description": "Ticks needed to confirm bounce",
                },
                "volatility_lookback": {
                    "type": "int",
                    "default": 20,
                    "min": 10,
                    "max": 100,
                    "description": "Lookback period for volatility calculation",
                },
            },
            tags=["scalping", "level1", "mean-reversion", "microstructure"],
            requirements={
                "data": ["trades", "best_bid_ask"],
                "min_tick_rate": 100,  # Minimum ticks per minute
            },
        )

    def __init__(self, **kwargs):
        """Initialize strategy with parameters."""
        super().__init__(**kwargs)

        # Strategy parameters
        self.bounce_sensitivity = kwargs.get("bounce_sensitivity", 0.7)
        self.min_bounce_strength = kwargs.get("min_bounce_strength", 0.5)
        self.profit_target_ticks = kwargs.get("profit_target_ticks", 2)
        self.stop_loss_ticks = kwargs.get("stop_loss_ticks", 1)
        self.max_spread_ticks = kwargs.get("max_spread_ticks", 2)
        self.min_volume = kwargs.get("min_volume", 10)
        self.max_holding_seconds = kwargs.get("max_holding_seconds", 120)
        self.confirmation_ticks = kwargs.get("confirmation_ticks", 2)
        self.volatility_lookback = kwargs.get("volatility_lookback", 20)

        # MNQ tick size
        self.tick_size = 0.25

        # Initialize state
        self.state = BounceState()

        # Volatility tracking
        self.current_volatility = 0.0
        self.volatility_threshold = 0.0

        logger.info(
            f"Initialized {self.name} with sensitivity={self.bounce_sensitivity}"
        )

    def _initialize_strategy(self) -> None:
        """Strategy-specific initialization."""
        # Calculate volatility threshold based on parameters
        self.volatility_threshold = self.min_bounce_strength * self.tick_size * 2

        # Reset state
        self.state = BounceState()

        logger.debug(
            f"Strategy initialized with volatility threshold={self.volatility_threshold}"
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
        """Generate trading signal based on bounce detection.

        Returns:
            1 for long, -1 for short, 0 for flat, None for no action
        """
        # Update state histories
        self.state.price_history.append(price)
        self.state.volume_history.append(volume)
        self.state.bid_history.append(bid)
        self.state.ask_history.append(ask)
        self.state.timestamp_history.append(timestamp)

        # Need minimum data for calculations
        if len(self.state.price_history) < self.confirmation_ticks + 2:
            return None

        # Calculate current spread and volatility
        spread = ask - bid
        spread_ticks = spread / self.tick_size

        # Update volatility estimate
        if len(self.state.price_history) >= self.volatility_lookback:
            prices = list(self.state.price_history)[-self.volatility_lookback :]
            returns = np.diff(prices) / prices[:-1]
            self.current_volatility = np.std(returns) if len(returns) > 0 else 0.0

        # Check market condition filters
        if not self._check_market_conditions(spread_ticks, volume):
            return None

        # Check if we have an active position
        if self.state.position_direction != 0:
            # Check exit conditions
            exit_signal = self._check_exit_conditions(timestamp, price, bid, ask)
            if exit_signal is not None:
                return exit_signal
            return None

        # Detect new bounce patterns
        bounce = self._detect_bounce(timestamp, price, volume, bid, ask)
        if bounce:
            self.state.detected_bounces.append(bounce)

            # Check if bounce meets entry criteria
            if self._validate_bounce_entry(bounce, spread_ticks):
                # Generate entry signal
                signal = 1 if bounce.bounce_type == "bid" else -1

                # Set position state
                self.state.position_direction = signal
                self.state.position_entry_time = timestamp
                self.state.position_entry_price = price
                self.state.active_bounce = bounce
                self.state.last_signal = signal
                self.state.last_signal_time = timestamp

                # Track entry timing
                entry_delay = (timestamp - bounce.timestamp).total_seconds()
                self.state.entry_timing_delays.append(entry_delay)

                logger.debug(
                    f"Bounce entry signal={signal} at {price}, "
                    f"bounce_type={bounce.bounce_type}, strength={bounce.strength:.2f}"
                )

                return signal

        return None

    def _detect_bounce(
        self, timestamp: pd.Timestamp, price: float, volume: int, bid: float, ask: float
    ) -> BounceDetection | None:
        """Detect bounce patterns from bid/ask levels."""
        prices = list(self.state.price_history)
        bids = list(self.state.bid_history)
        asks = list(self.state.ask_history)
        volumes = list(self.state.volume_history)

        # Look for bid bounce (price touches bid and reverses up)
        if self._check_bid_bounce(prices, bids, volumes):
            touch_idx = self._find_touch_point(prices, bids, is_bid=True)
            if touch_idx is not None:
                touch_price = prices[touch_idx]
                bounce_price = prices[-1]
                strength = (bounce_price - touch_price) / self.tick_size

                if strength >= self.min_bounce_strength * self.bounce_sensitivity:
                    return BounceDetection(
                        timestamp=timestamp,
                        bounce_type="bid",
                        touch_price=touch_price,
                        bounce_price=bounce_price,
                        strength=strength,
                        volume=sum(volumes[touch_idx:]),
                        spread_at_bounce=asks[-1] - bids[-1],
                    )

        # Look for ask bounce (price touches ask and reverses down)
        if self._check_ask_bounce(prices, asks, volumes):
            touch_idx = self._find_touch_point(prices, asks, is_bid=False)
            if touch_idx is not None:
                touch_price = prices[touch_idx]
                bounce_price = prices[-1]
                strength = (touch_price - bounce_price) / self.tick_size

                if strength >= self.min_bounce_strength * self.bounce_sensitivity:
                    return BounceDetection(
                        timestamp=timestamp,
                        bounce_type="ask",
                        touch_price=touch_price,
                        bounce_price=bounce_price,
                        strength=strength,
                        volume=sum(volumes[touch_idx:]),
                        spread_at_bounce=asks[-1] - bids[-1],
                    )

        return None

    def _check_bid_bounce(
        self, prices: list[float], bids: list[float], volumes: list[int]
    ) -> bool:
        """Check if price pattern indicates a bounce off bid."""
        if len(prices) < self.confirmation_ticks + 2:
            return False

        # Look for price touching or going below bid
        touch_window = self.confirmation_ticks + 1
        for i in range(-touch_window, -1):
            if prices[i] <= bids[i] + self.tick_size * 0.1:  # Small tolerance
                # Check if price is now moving up (simpler check)
                if (
                    prices[-1] > prices[i] + self.tick_size * 0.5
                ):  # At least half a tick bounce
                    # Confirm we have some upward movement
                    if (
                        i < -2 and prices[-2] > prices[i]
                    ):  # Intermediate price also higher
                        return True

        return False

    def _check_ask_bounce(
        self, prices: list[float], asks: list[float], volumes: list[int]
    ) -> bool:
        """Check if price pattern indicates a bounce off ask."""
        if len(prices) < self.confirmation_ticks + 2:
            return False

        # Look for price touching or going above ask
        touch_window = self.confirmation_ticks + 1
        for i in range(-touch_window, -1):
            if prices[i] >= asks[i] - self.tick_size * 0.1:  # Small tolerance
                # Check if price is now moving down (simpler check)
                if (
                    prices[-1] < prices[i] - self.tick_size * 0.5
                ):  # At least half a tick bounce
                    # Confirm we have some downward movement
                    if (
                        i < -2 and prices[-2] < prices[i]
                    ):  # Intermediate price also lower
                        return True

        return False

    def _find_touch_point(
        self, prices: list[float], levels: list[float], is_bid: bool
    ) -> int | None:
        """Find the index where price touched the bid/ask level."""
        touch_window = self.confirmation_ticks + 1

        for i in range(-touch_window, -1):
            if is_bid:
                if prices[i] <= levels[i] + self.tick_size * 0.1:
                    return i
            else:
                if prices[i] >= levels[i] - self.tick_size * 0.1:
                    return i

        return None

    def _validate_bounce_entry(
        self, bounce: BounceDetection, spread_ticks: float
    ) -> bool:
        """Validate if bounce meets entry criteria."""
        # Check spread
        if spread_ticks > self.max_spread_ticks:
            return False

        # Check volume
        if bounce.volume < self.min_volume:
            return False

        # Check bounce strength
        if bounce.strength < self.min_bounce_strength:
            return False

        # Check volatility filter
        if self.current_volatility > self.volatility_threshold * 2:
            return False

        # Avoid entering too soon after last signal
        if self.state.last_signal_time:
            time_since_last = (
                bounce.timestamp - self.state.last_signal_time
            ).total_seconds()
            if time_since_last < 5.0:  # Minimum 5 seconds between signals
                return False

        return True

    def _check_market_conditions(self, spread_ticks: float, volume: int) -> bool:
        """Check if market conditions are suitable for trading."""
        # Spread filter
        if spread_ticks > self.max_spread_ticks:
            return False

        # Volume filter
        recent_volumes = list(self.state.volume_history)[-5:]
        if recent_volumes and np.mean(recent_volumes) < self.min_volume * 0.5:
            return False

        # Volatility filter - avoid extreme volatility
        if self.current_volatility > self.volatility_threshold * 3:
            return False

        return True

    def _check_exit_conditions(
        self, timestamp: pd.Timestamp, price: float, bid: float, ask: float
    ) -> int | None:
        """Check exit conditions for active position."""
        if (
            self.state.position_direction == 0
            or self.state.position_entry_price is None
        ):
            return None

        # First update price history for momentum check
        if len(self.state.price_history) < 3:
            return None

        position_pnl_ticks = (price - self.state.position_entry_price) / self.tick_size
        if self.state.position_direction == -1:
            position_pnl_ticks = -position_pnl_ticks

        # Check profit target
        if position_pnl_ticks >= self.profit_target_ticks:
            logger.debug(f"Profit target hit: {position_pnl_ticks:.1f} ticks")
            self.state.bounce_success_count += 1
            self._reset_position_state()
            return 0  # Flatten position

        # Check stop loss
        if position_pnl_ticks <= -self.stop_loss_ticks:
            logger.debug(f"Stop loss hit: {position_pnl_ticks:.1f} ticks")
            self.state.bounce_fail_count += 1
            self._reset_position_state()
            return 0  # Flatten position

        # Check time-based exit
        if self.state.position_entry_time:
            holding_time = (timestamp - self.state.position_entry_time).total_seconds()
            if holding_time >= self.max_holding_seconds:
                logger.debug(f"Time exit: held for {holding_time:.1f} seconds")
                # Track success/fail based on PnL
                if position_pnl_ticks > 0:
                    self.state.bounce_success_count += 1
                else:
                    self.state.bounce_fail_count += 1
                self._reset_position_state()
                return 0  # Flatten position

        # Check momentum exit - if bounce momentum has faded
        if self.state.active_bounce and len(self.state.price_history) >= 3:
            recent_prices = list(self.state.price_history)[-3:]

            if self.state.position_direction == 1:  # Long position
                # Exit if price is moving down consistently
                down_moves = sum(
                    1
                    for i in range(len(recent_prices) - 1)
                    if recent_prices[i] > recent_prices[i + 1]
                )
                if down_moves >= 2:  # At least 2 down moves out of 3
                    logger.debug("Momentum exit: upward momentum faded")
                    if position_pnl_ticks > 0:
                        self.state.bounce_success_count += 1
                    else:
                        self.state.bounce_fail_count += 1
                    self._reset_position_state()
                    return 0

            elif self.state.position_direction == -1:  # Short position
                # Exit if price is moving up consistently
                up_moves = sum(
                    1
                    for i in range(len(recent_prices) - 1)
                    if recent_prices[i] < recent_prices[i + 1]
                )
                if up_moves >= 2:  # At least 2 up moves out of 3
                    logger.debug("Momentum exit: downward momentum faded")
                    if position_pnl_ticks > 0:
                        self.state.bounce_success_count += 1
                    else:
                        self.state.bounce_fail_count += 1
                    self._reset_position_state()
                    return 0

        return None

    def _reset_position_state(self) -> None:
        """Reset position-related state after exit."""
        self.state.position_direction = 0
        self.state.position_entry_time = None
        self.state.position_entry_price = None
        self.state.active_bounce = None

    def _cleanup_strategy(self) -> None:
        """Strategy-specific cleanup."""
        # Calculate and log performance metrics
        total_bounces = self.state.bounce_success_count + self.state.bounce_fail_count
        if total_bounces > 0:
            success_rate = self.state.bounce_success_count / total_bounces * 100
            logger.info(
                f"Bounce strategy performance: "
                f"success_rate={success_rate:.1f}%, "
                f"total_bounces={total_bounces}"
            )

        if self.state.entry_timing_delays:
            avg_delay = np.mean(self.state.entry_timing_delays)
            logger.info(f"Average entry delay: {avg_delay:.2f} seconds")

    def _get_custom_state(self) -> dict[str, Any]:
        """Get strategy-specific state for persistence."""
        return {
            "bounce_success_count": self.state.bounce_success_count,
            "bounce_fail_count": self.state.bounce_fail_count,
            "entry_timing_delays": self.state.entry_timing_delays[
                -100:
            ],  # Keep last 100
            "current_volatility": self.current_volatility,
            "position_direction": self.state.position_direction,
            "position_entry_price": self.state.position_entry_price,
            "position_entry_time": self.state.position_entry_time.isoformat()
            if self.state.position_entry_time
            else None,
        }

    def _set_custom_state(self, custom_state: dict[str, Any]) -> None:
        """Restore strategy-specific state."""
        self.state.bounce_success_count = custom_state.get("bounce_success_count", 0)
        self.state.bounce_fail_count = custom_state.get("bounce_fail_count", 0)
        self.state.entry_timing_delays = custom_state.get("entry_timing_delays", [])
        self.current_volatility = custom_state.get("current_volatility", 0.0)
        self.state.position_direction = custom_state.get("position_direction", 0)
        self.state.position_entry_price = custom_state.get("position_entry_price")

        entry_time_str = custom_state.get("position_entry_time")
        if entry_time_str:
            self.state.position_entry_time = pd.Timestamp(entry_time_str)

    def get_performance_metrics(self) -> dict[str, Any]:
        """Get strategy-specific performance metrics."""
        total_bounces = self.state.bounce_success_count + self.state.bounce_fail_count

        metrics = {
            "bounce_success_rate": self.state.bounce_success_count / total_bounces * 100
            if total_bounces > 0
            else 0.0,
            "total_bounces_detected": len(self.state.detected_bounces),
            "total_bounces_traded": total_bounces,
            "avg_entry_delay": np.mean(self.state.entry_timing_delays)
            if self.state.entry_timing_delays
            else 0.0,
            "current_volatility": self.current_volatility,
        }

        return metrics
