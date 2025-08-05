"""Volume-Weighted Order Flow Imbalance Strategy.

This strategy combines order book imbalance from Level 2 data with actual
trade volume from Level 1 data to generate high-confidence trading signals.
"""

import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

import numpy as np
import pandas as pd

from strategy_lab.data.synchronization import UnifiedMarketSnapshot
from strategy_lab.strategies.base.pluggable_strategy import PluggableStrategy
from strategy_lab.strategies.protocol_enhanced import (
    OrderRequest,
    OrderSide,
    OrderType,
    StrategyContext,
    StrategyMetadata,
)

logger = logging.getLogger(__name__)


@dataclass
class VWOFIParameters:
    """Parameters for Volume-Weighted Order Flow Imbalance strategy."""

    # Imbalance calculation
    depth_levels: int = 5  # Number of book levels to consider
    imbalance_threshold: float = 0.65  # Min imbalance ratio for signal

    # Volume weighting
    volume_window: int = 100  # Ticks to accumulate volume
    volume_decay: float = 0.95  # Exponential decay factor
    min_volume: int = 10  # Minimum contracts for valid signal

    # Signal generation
    signal_smoothing: int = 5  # EMA period for signal smoothing
    confidence_threshold: float = 70.0  # Min confidence to trade

    # Risk management
    max_position_size: int = 10
    stop_loss_ticks: int = 8
    take_profit_ticks: int = 6
    hold_time_seconds: int = 60

    # Signal cooldown
    signal_cooldown_ms: int = 500  # Minimum time between signals


class VolumeWeightedImbalanceStrategy(PluggableStrategy):
    """Volume-Weighted Order Flow Imbalance trading strategy."""

    def __init__(self, **kwargs):
        """Initialize strategy with parameters."""
        super().__init__(**kwargs)

        # Load parameters
        self.params = VWOFIParameters(**kwargs)

        # State tracking
        self.volume_history: list[dict[str, Any]] = []
        self.imbalance_ema = 0.0
        self.last_signal_time = 0
        self.position_entry_price: Decimal | None = None
        self.position_entry_time: int | None = None

        # Performance tracking
        self.signal_count = 0
        self.confidence_scores: list[float] = []

    def _initialize_strategy(self) -> None:
        """Strategy-specific initialization."""
        # Reset state
        self.volume_history.clear()
        self.imbalance_ema = 0.0
        self.last_signal_time = 0
        self.signal_count = 0
        self.confidence_scores.clear()

    def _generate_signal(
        self,
        timestamp: pd.Timestamp,  # noqa: ARG002
        price: float,  # noqa: ARG002
        volume: int,  # noqa: ARG002
        bid: float,  # noqa: ARG002
        ask: float,  # noqa: ARG002
        **kwargs,  # noqa: ARG002
    ) -> int | None:
        """Generate trading signal - not used for L1+L2 strategy."""
        # This method is required by base class but we use on_market_data instead
        return None

    def on_market_data(
        self, snapshot: UnifiedMarketSnapshot, context: StrategyContext
    ) -> list[OrderRequest]:
        """Process unified market snapshot and generate signals."""
        orders = []

        # Check if we have sufficient data
        if not self._has_sufficient_data(snapshot):
            return orders

        # Update volume history
        self._update_volume_history(snapshot)

        # Calculate raw imbalance
        raw_imbalance = self._calculate_order_book_imbalance(snapshot)

        # Weight imbalance by volume
        weighted_imbalance = self._weight_by_volume(raw_imbalance, snapshot)

        # Update smoothed signal
        self._update_signal_ema(weighted_imbalance)

        # Generate confidence score
        confidence = self._calculate_confidence(weighted_imbalance, snapshot)
        self.confidence_scores.append(confidence)

        # Check for exit conditions first if we have a position
        if context.position.size != 0:
            exit_orders = self._check_exit_conditions(snapshot, context)
            if exit_orders:
                orders.extend(exit_orders)
                return orders  # Exit takes priority

        # Check for signal generation
        if self._should_generate_signal(confidence, snapshot.timestamp):
            # Determine signal direction
            signal_side = self._determine_signal_side(weighted_imbalance)

            # Generate entry order if flat
            if context.position.size == 0:
                entry_order = self._generate_entry_order(
                    signal_side, confidence, snapshot, context
                )
                if entry_order:
                    orders.append(entry_order)
                    self.signal_count += 1

        return orders

    def _has_sufficient_data(self, snapshot: UnifiedMarketSnapshot) -> bool:
        """Check if we have sufficient data for signal generation."""
        # Need both L1 and L2 data
        if not snapshot.bid_price or not snapshot.ask_price:
            return False

        if not snapshot.bid_levels or not snapshot.ask_levels:
            return False

        # Need minimum depth levels
        return (
            len(snapshot.bid_levels) >= self.params.depth_levels
            and len(snapshot.ask_levels) >= self.params.depth_levels
        )

    def _update_volume_history(self, snapshot: UnifiedMarketSnapshot):
        """Update volume history with latest data."""
        if snapshot.last_trade_volume:
            volume_data = {
                "timestamp": snapshot.timestamp,
                "price": snapshot.last_trade_price,
                "volume": snapshot.last_trade_volume,
                "spread": snapshot.spread,
                "mid_price": snapshot.mid_price,
            }

            self.volume_history.append(volume_data)

            # Maintain window size
            if len(self.volume_history) > self.params.volume_window:
                self.volume_history.pop(0)

    def _calculate_order_book_imbalance(self, snapshot: UnifiedMarketSnapshot) -> float:
        """Calculate raw order book imbalance from Level 2 data."""
        # Calculate volume at specified depth
        bid_volume = sum(
            level.volume for level in snapshot.bid_levels[: self.params.depth_levels]
        )

        ask_volume = sum(
            level.volume for level in snapshot.ask_levels[: self.params.depth_levels]
        )

        # Calculate imbalance ratio
        total_volume = bid_volume + ask_volume
        if total_volume == 0:
            return 0.0

        return (bid_volume - ask_volume) / total_volume

    def _weight_by_volume(
        self, raw_imbalance: float, snapshot: UnifiedMarketSnapshot
    ) -> float:
        """Weight imbalance by recent trade volume."""
        if not self.volume_history:
            return raw_imbalance

        # Calculate recent volume with exponential decay
        current_time = snapshot.timestamp
        weighted_volume = 0.0
        total_weight = 0.0

        for i, vol_data in enumerate(reversed(self.volume_history)):
            # Time-based decay
            time_diff_ms = (current_time - vol_data["timestamp"]) / 1_000_000
            if time_diff_ms > 5000:  # Ignore data older than 5 seconds
                break

            # Calculate weight with exponential decay
            weight = self.params.volume_decay**i
            weighted_volume += vol_data["volume"] * weight
            total_weight += weight

        # Calculate average volume
        avg_volume = weighted_volume / total_weight if total_weight > 0 else 0

        # Calculate volume ratio
        if avg_volume < self.params.min_volume:
            return 0.0  # Insufficient volume

        # Volume factor (capped at 2x for safety)
        volume_factor = min(2.0, avg_volume / self.params.min_volume)

        # Direction factor based on recent trade direction
        direction_factor = self._calculate_direction_factor()

        # Weight the imbalance
        return raw_imbalance * volume_factor * direction_factor

    def _calculate_direction_factor(self) -> float:
        """Calculate directional bias from recent trades."""
        if len(self.volume_history) < 5:
            return 1.0

        # Check recent price movement
        recent_trades = self.volume_history[-5:]

        buy_volume = 0
        sell_volume = 0

        for i in range(1, len(recent_trades)):
            curr_trade = recent_trades[i]
            prev_trade = recent_trades[i - 1]

            if curr_trade["price"] > prev_trade["mid_price"]:
                buy_volume += curr_trade["volume"]
            elif curr_trade["price"] < prev_trade["mid_price"]:
                sell_volume += curr_trade["volume"]

        total_directional_volume = buy_volume + sell_volume
        if total_directional_volume == 0:
            return 1.0

        # Return directional bias (0.5 to 1.5)
        return 0.5 + (buy_volume / total_directional_volume)

    def _update_signal_ema(self, weighted_imbalance: float):
        """Update exponentially weighted moving average of signal."""
        alpha = 2.0 / (self.params.signal_smoothing + 1)
        self.imbalance_ema = (
            alpha * weighted_imbalance + (1 - alpha) * self.imbalance_ema
        )

    def _calculate_confidence(
        self, weighted_imbalance: float, snapshot: UnifiedMarketSnapshot
    ) -> float:
        """Calculate confidence score for the signal."""
        # Base confidence from imbalance strength
        imbalance_strength = abs(weighted_imbalance)
        base_confidence = min(100, imbalance_strength * 100)

        # Volume confirmation factor
        volume_factor = 1.0
        if self.volume_history:
            recent_volume = np.mean([v["volume"] for v in self.volume_history[-10:]])
            if recent_volume > self.params.min_volume * 2:
                volume_factor = 1.2
            elif recent_volume < self.params.min_volume:
                volume_factor = 0.5

        # Spread factor (tighter spread = higher confidence)
        spread_factor = 1.0
        if snapshot.spread and snapshot.mid_price:
            spread_bps = float(snapshot.spread / snapshot.mid_price) * 10000
            if spread_bps < 2:  # Very tight spread
                spread_factor = 1.1
            elif spread_bps > 5:  # Wide spread
                spread_factor = 0.8

        # Calculate final confidence
        confidence = base_confidence * volume_factor * spread_factor

        return min(100, confidence)

    def _should_generate_signal(self, confidence: float, timestamp: int) -> bool:
        """Check if we should generate a trading signal."""
        # Check confidence threshold
        if confidence < self.params.confidence_threshold:
            return False

        # Check signal cooldown
        time_since_last_signal = (timestamp - self.last_signal_time) / 1_000_000
        if time_since_last_signal < self.params.signal_cooldown_ms:
            return False

        # Check imbalance threshold
        return abs(self.imbalance_ema) >= self.params.imbalance_threshold

    def _determine_signal_side(self, weighted_imbalance: float) -> OrderSide:
        """Determine signal direction from weighted imbalance."""
        return OrderSide.BUY if weighted_imbalance > 0 else OrderSide.SELL

    def _generate_entry_order(
        self,
        side: OrderSide,
        confidence: float,
        snapshot: UnifiedMarketSnapshot,
        context: StrategyContext,  # noqa: ARG002
    ) -> OrderRequest | None:
        """Generate entry order based on signal."""
        # Calculate position size based on confidence
        base_size = min(
            self.params.max_position_size,
            int(confidence / 20),  # 1 contract per 20% confidence
        )

        # Ensure minimum size
        size = max(1, base_size)

        # Determine entry price
        price = snapshot.ask_price if side == OrderSide.BUY else snapshot.bid_price

        if not price:
            return None

        # Create order
        order = OrderRequest(
            side=side,
            size=size,
            order_type=OrderType.MARKET,
            price=price,
            time_in_force="IOC",  # Immediate or cancel
            metadata={
                "strategy": "volume_weighted_imbalance",
                "confidence": confidence,
                "imbalance": self.imbalance_ema,
                "signal_time": snapshot.timestamp,
            },
        )

        # Update tracking
        self.position_entry_price = price
        self.position_entry_time = snapshot.timestamp
        self.last_signal_time = snapshot.timestamp

        logger.info(
            f"VWI Entry Signal: {side.name} {size} @ {price} "
            f"(confidence: {confidence:.1f}%, imbalance: {self.imbalance_ema:.3f})"
        )

        return order

    def _check_exit_conditions(
        self, snapshot: UnifiedMarketSnapshot, context: StrategyContext
    ) -> list[OrderRequest]:
        """Check exit conditions for current position."""
        orders = []

        if not self.position_entry_price or not self.position_entry_time:
            return orders

        position = context.position
        current_price = snapshot.mid_price

        if not current_price:
            return orders

        # Calculate PnL in ticks
        tick_size = Decimal("0.25")
        if position.size > 0:  # Long position
            pnl_ticks = int((current_price - self.position_entry_price) / tick_size)
        else:  # Short position
            pnl_ticks = int((self.position_entry_price - current_price) / tick_size)

        # Check stop loss
        if pnl_ticks <= -self.params.stop_loss_ticks:
            exit_order = self._create_exit_order(position, snapshot, "stop_loss")
            if exit_order:
                orders.append(exit_order)
                logger.info(f"VWI Stop Loss triggered: PnL {pnl_ticks} ticks")

        # Check take profit
        elif pnl_ticks >= self.params.take_profit_ticks:
            exit_order = self._create_exit_order(position, snapshot, "take_profit")
            if exit_order:
                orders.append(exit_order)
                logger.info(f"VWI Take Profit triggered: PnL {pnl_ticks} ticks")

        # Check time-based exit
        else:
            time_in_position = (
                snapshot.timestamp - self.position_entry_time
            ) / 1_000_000_000
            if time_in_position >= self.params.hold_time_seconds:
                exit_order = self._create_exit_order(position, snapshot, "time_exit")
                if exit_order:
                    orders.append(exit_order)
                    logger.info(f"VWI Time exit: held for {time_in_position:.1f}s")

        return orders

    def _create_exit_order(
        self, position: Any, snapshot: UnifiedMarketSnapshot, reason: str
    ) -> OrderRequest | None:
        """Create exit order to close position."""
        # Determine exit side (opposite of position)
        exit_side = OrderSide.SELL if position.size > 0 else OrderSide.BUY

        # Determine exit price
        price = snapshot.ask_price if exit_side == OrderSide.BUY else snapshot.bid_price

        if not price:
            return None

        # Create order
        order = OrderRequest(
            side=exit_side,
            size=abs(position.size),
            order_type=OrderType.MARKET,
            price=price,
            time_in_force="IOC",
            metadata={
                "strategy": "volume_weighted_imbalance",
                "exit_reason": reason,
                "exit_time": snapshot.timestamp,
            },
        )

        # Reset tracking
        self.position_entry_price = None
        self.position_entry_time = None

        return order

    def get_metadata(self) -> StrategyMetadata:
        """Return strategy metadata."""
        return StrategyMetadata(
            name="volume_weighted_imbalance",
            version="1.0.0",
            description="Trades based on volume-weighted order book imbalances",
            author="Strategy Lab",
            tags=["microstructure", "level-1+2", "order-book", "volume", "imbalance"],
            parameters={
                "depth_levels": self.params.depth_levels,
                "imbalance_threshold": self.params.imbalance_threshold,
                "volume_window": self.params.volume_window,
                "confidence_threshold": self.params.confidence_threshold,
                "max_position_size": self.params.max_position_size,
            },
        )

    def get_state(self) -> dict[str, Any]:
        """Get current strategy state."""
        return {
            "imbalance_ema": self.imbalance_ema,
            "signal_count": self.signal_count,
            "avg_confidence": (
                np.mean(self.confidence_scores) if self.confidence_scores else 0
            ),
            "volume_history_size": len(self.volume_history),
            "position_entry_price": (
                str(self.position_entry_price) if self.position_entry_price else None
            ),
        }
