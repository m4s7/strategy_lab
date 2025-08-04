"""Tests for Bid-Ask Bounce Strategy."""

import pandas as pd
import pytest

from strategy_lab.strategies.implementations.bid_ask_bounce import (
    BidAskBounceStrategy,
    BounceDetection,
    BounceState,
)


class TestBidAskBounceStrategy:
    """Test suite for BidAskBounceStrategy."""

    @pytest.fixture
    def strategy(self):
        """Create a strategy instance with test parameters."""
        return BidAskBounceStrategy(
            bounce_sensitivity=0.7,
            min_bounce_strength=0.5,
            profit_target_ticks=2,
            stop_loss_ticks=1,
            max_spread_ticks=2,
            min_volume=10,
            max_holding_seconds=120,
            confirmation_ticks=2,
        )

    @pytest.fixture
    def base_timestamp(self):
        """Base timestamp for tests."""
        return pd.Timestamp("2024-01-01 09:30:00", tz="US/Eastern")

    def test_initialization(self, strategy):
        """Test strategy initialization."""
        assert strategy.name == "bid_ask_bounce"
        assert strategy.version == "1.0.0"
        assert strategy.bounce_sensitivity == 0.7
        assert strategy.min_bounce_strength == 0.5
        assert strategy.profit_target_ticks == 2
        assert strategy.stop_loss_ticks == 1
        assert strategy.tick_size == 0.25

        # Check state initialization
        assert isinstance(strategy.state, BounceState)
        assert strategy.state.position_direction == 0
        assert len(strategy.state.price_history) == 0

    def test_metadata(self):
        """Test strategy metadata."""
        metadata = BidAskBounceStrategy.get_metadata()

        assert metadata.name == "bid_ask_bounce"
        assert metadata.version == "1.0.0"
        assert "scalping" in metadata.tags
        assert "level1" in metadata.tags
        assert "mean-reversion" in metadata.tags

        # Check requirements
        assert "trades" in metadata.requirements["data"]
        assert "best_bid_ask" in metadata.requirements["data"]

    def test_bid_bounce_detection(self, strategy, base_timestamp):
        """Test detection of bid bounce patterns."""
        strategy.initialize()

        # Simulate price touching bid and bouncing up
        tick_data = [
            # (timestamp_offset, price, volume, bid, ask)
            (0, 5000.00, 15, 4999.75, 5000.00),  # Normal spread
            (1, 4999.75, 20, 4999.75, 5000.00),  # Touch bid
            (2, 4999.75, 18, 4999.75, 5000.00),  # At bid
            (3, 5000.00, 25, 4999.75, 5000.00),  # Bounce up
            (4, 5000.25, 30, 5000.00, 5000.25),  # Continue up
        ]

        signal = None
        for offset, price, volume, bid, ask in tick_data:
            timestamp = base_timestamp + pd.Timedelta(seconds=offset)
            signal = strategy.process_tick(timestamp, price, volume, bid, ask)

        # Should generate long signal on bid bounce
        assert signal == 1
        assert strategy.state.position_direction == 1
        assert strategy.state.active_bounce is not None
        assert strategy.state.active_bounce.bounce_type == "bid"

    def test_ask_bounce_detection(self, strategy, base_timestamp):
        """Test detection of ask bounce patterns."""
        strategy.initialize()

        # Simulate price touching ask and bouncing down
        tick_data = [
            # (timestamp_offset, price, volume, bid, ask)
            (0, 5000.00, 15, 4999.75, 5000.00),  # Normal spread
            (1, 5000.00, 20, 4999.75, 5000.00),  # Touch ask
            (2, 5000.00, 18, 4999.75, 5000.00),  # At ask
            (3, 4999.75, 25, 4999.75, 5000.00),  # Bounce down
            (4, 4999.50, 30, 4999.50, 4999.75),  # Continue down
        ]

        signal = None
        for offset, price, volume, bid, ask in tick_data:
            timestamp = base_timestamp + pd.Timedelta(seconds=offset)
            signal = strategy.process_tick(timestamp, price, volume, bid, ask)

        # Should generate short signal on ask bounce
        assert signal == -1
        assert strategy.state.position_direction == -1
        assert strategy.state.active_bounce is not None
        assert strategy.state.active_bounce.bounce_type == "ask"

    def test_profit_target_exit(self, strategy, base_timestamp):
        """Test profit target exit logic."""
        strategy.initialize()

        # Pre-fill some price history
        for i in range(5):
            strategy.state.price_history.append(5000.00)
            strategy.state.volume_history.append(20)
            strategy.state.bid_history.append(4999.75)
            strategy.state.ask_history.append(5000.00)
            strategy.state.timestamp_history.append(
                base_timestamp - pd.Timedelta(seconds=5 - i)
            )

        # Set up a long position
        strategy.state.position_direction = 1
        strategy.state.position_entry_price = 5000.00
        strategy.state.position_entry_time = base_timestamp

        # Simulate price movement hitting profit target (2 ticks = 0.50)
        tick_data = [
            (0, 5000.25, 20, 5000.00, 5000.25),  # +1 tick
            (1, 5000.50, 25, 5000.25, 5000.50),  # +2 ticks - profit target
        ]

        signal = None
        for offset, price, volume, bid, ask in tick_data:
            timestamp = base_timestamp + pd.Timedelta(seconds=offset)
            signal = strategy.process_tick(timestamp, price, volume, bid, ask)

        # Should exit at profit target
        assert signal == 0  # Flatten signal
        assert strategy.state.position_direction == 0
        assert strategy.state.bounce_success_count == 1

    def test_stop_loss_exit(self, strategy, base_timestamp):
        """Test stop loss exit logic."""
        strategy.initialize()

        # Pre-fill some price history
        for i in range(5):
            strategy.state.price_history.append(5000.00)
            strategy.state.volume_history.append(20)
            strategy.state.bid_history.append(4999.75)
            strategy.state.ask_history.append(5000.00)
            strategy.state.timestamp_history.append(
                base_timestamp - pd.Timedelta(seconds=5 - i)
            )

        # Set up a long position
        strategy.state.position_direction = 1
        strategy.state.position_entry_price = 5000.00
        strategy.state.position_entry_time = base_timestamp

        # Simulate price movement hitting stop loss (1 tick = 0.25)
        tick_data = [
            (0, 4999.75, 20, 4999.50, 4999.75),  # -1 tick - stop loss
        ]

        for offset, price, volume, bid, ask in tick_data:
            timestamp = base_timestamp + pd.Timedelta(seconds=offset)
            signal = strategy.process_tick(timestamp, price, volume, bid, ask)

        # Should exit at stop loss
        assert signal == 0  # Flatten signal
        assert strategy.state.position_direction == 0
        assert strategy.state.bounce_fail_count == 1

    def test_time_based_exit(self, strategy, base_timestamp):
        """Test time-based exit logic."""
        strategy.initialize()
        strategy.max_holding_seconds = 10  # Short holding time for test

        # Pre-fill some price history
        for i in range(5):
            strategy.state.price_history.append(5000.00)
            strategy.state.volume_history.append(20)
            strategy.state.bid_history.append(4999.75)
            strategy.state.ask_history.append(5000.00)
            strategy.state.timestamp_history.append(
                base_timestamp - pd.Timedelta(seconds=5 - i)
            )

        # Set up a long position
        strategy.state.position_direction = 1
        strategy.state.position_entry_price = 5000.00
        strategy.state.position_entry_time = base_timestamp

        # Simulate holding position past max time
        timestamp = base_timestamp + pd.Timedelta(seconds=15)
        signal = strategy.process_tick(timestamp, 5000.00, 20, 4999.75, 5000.00)

        # Should exit due to time
        assert signal == 0  # Flatten signal
        assert strategy.state.position_direction == 0

    def test_spread_filter(self, strategy, base_timestamp):
        """Test spread filtering logic."""
        strategy.initialize()

        # Simulate wide spread condition
        wide_spread_ticks = [
            (0, 5000.00, 20, 4999.50, 5000.25),  # 3 tick spread - too wide
            (1, 4999.50, 25, 4999.50, 5000.25),  # Touch bid with wide spread
            (2, 5000.00, 30, 4999.50, 5000.25),  # Bounce but spread still wide
        ]

        signal = None
        for offset, price, volume, bid, ask in wide_spread_ticks:
            timestamp = base_timestamp + pd.Timedelta(seconds=offset)
            signal = strategy.process_tick(timestamp, price, volume, bid, ask)

        # Should not trade due to wide spread
        assert signal is None
        assert strategy.state.position_direction == 0

    def test_volume_filter(self, strategy, base_timestamp):
        """Test volume filtering logic."""
        strategy.initialize()

        # Simulate low volume bounce
        low_volume_ticks = [
            (0, 5000.00, 2, 4999.75, 5000.00),  # Low volume
            (1, 4999.75, 3, 4999.75, 5000.00),  # Touch bid, low volume
            (2, 5000.00, 2, 4999.75, 5000.00),  # Bounce but low volume
        ]

        signal = None
        for offset, price, volume, bid, ask in low_volume_ticks:
            timestamp = base_timestamp + pd.Timedelta(seconds=offset)
            signal = strategy.process_tick(timestamp, price, volume, bid, ask)

        # Should not trade due to low volume
        assert signal is None
        assert strategy.state.position_direction == 0

    def test_momentum_exit(self, strategy, base_timestamp):
        """Test momentum-based exit logic."""
        strategy.initialize()

        # Set up a long position
        strategy.state.position_direction = 1
        strategy.state.position_entry_price = 5000.00
        strategy.state.position_entry_time = base_timestamp
        strategy.state.active_bounce = BounceDetection(
            timestamp=base_timestamp,
            bounce_type="bid",
            touch_price=4999.75,
            bounce_price=5000.00,
            strength=1.0,
            volume=50,
            spread_at_bounce=0.25,
        )

        # Fill price history for momentum check
        for i in range(10):
            strategy.state.price_history.append(5000.00)
            strategy.state.volume_history.append(20)
            strategy.state.bid_history.append(4999.75)
            strategy.state.ask_history.append(5000.00)
            strategy.state.timestamp_history.append(
                base_timestamp + pd.Timedelta(seconds=i)
            )

        # Simulate momentum fading (prices moving down gradually)
        fading_momentum = [
            (0, 5000.10, 20, 4999.85, 5000.10),  # Still positive but less
            (1, 5000.00, 25, 4999.75, 5000.00),  # Back to entry
            (2, 4999.90, 30, 4999.65, 4999.90),  # Below entry - consistent down
        ]

        signal = None
        for offset, price, volume, bid, ask in fading_momentum:
            timestamp = base_timestamp + pd.Timedelta(seconds=offset + 10)
            signal = strategy.process_tick(timestamp, price, volume, bid, ask)
            if signal == 0:  # Exit found
                break

        # Should exit due to momentum fade
        assert signal == 0
        assert strategy.state.position_direction == 0

    def test_state_persistence(self, strategy, base_timestamp):
        """Test state save and restore functionality."""
        strategy.initialize()

        # Create some state
        strategy.state.bounce_success_count = 5
        strategy.state.bounce_fail_count = 2
        strategy.state.entry_timing_delays = [1.2, 0.8, 1.5]
        strategy.current_volatility = 0.002

        # Save state
        state = strategy.get_state()

        # Create new strategy and restore state
        new_strategy = BidAskBounceStrategy()
        new_strategy.initialize()
        new_strategy.set_state(state)

        # Verify state restored correctly
        assert new_strategy.state.bounce_success_count == 5
        assert new_strategy.state.bounce_fail_count == 2
        assert new_strategy.state.entry_timing_delays == [1.2, 0.8, 1.5]
        assert new_strategy.current_volatility == 0.002

    def test_performance_metrics(self, strategy):
        """Test performance metrics calculation."""
        strategy.state.bounce_success_count = 7
        strategy.state.bounce_fail_count = 3
        strategy.state.entry_timing_delays = [1.0, 1.5, 0.8, 1.2]
        strategy.current_volatility = 0.0015

        # Add some detected bounces
        for i in range(5):
            strategy.state.detected_bounces.append(
                BounceDetection(
                    timestamp=pd.Timestamp.now(),
                    bounce_type="bid" if i % 2 == 0 else "ask",
                    touch_price=5000.0,
                    bounce_price=5000.25,
                    strength=1.0,
                    volume=20,
                    spread_at_bounce=0.25,
                )
            )

        metrics = strategy.get_performance_metrics()

        assert metrics["bounce_success_rate"] == 70.0  # 7/10 * 100
        assert metrics["total_bounces_detected"] == 5
        assert metrics["total_bounces_traded"] == 10
        assert metrics["avg_entry_delay"] == 1.125  # Mean of delays
        assert metrics["current_volatility"] == 0.0015

    def test_weak_bounce_rejection(self, strategy, base_timestamp):
        """Test that weak bounces are rejected."""
        strategy.initialize()

        # Simulate weak bounce (below min_bounce_strength)
        weak_bounce_ticks = [
            (0, 5000.00, 20, 4999.75, 5000.00),
            (1, 4999.75, 25, 4999.75, 5000.00),  # Touch bid
            (2, 4999.85, 22, 4999.75, 5000.00),  # Weak bounce (< 0.5 ticks)
        ]

        signal = None
        for offset, price, volume, bid, ask in weak_bounce_ticks:
            timestamp = base_timestamp + pd.Timedelta(seconds=offset)
            signal = strategy.process_tick(timestamp, price, volume, bid, ask)

        # Should not trade on weak bounce
        assert signal is None
        assert strategy.state.position_direction == 0

    def test_consecutive_signal_filtering(self, strategy, base_timestamp):
        """Test filtering of consecutive signals too close together."""
        strategy.initialize()

        # Generate first signal
        strategy.state.last_signal_time = base_timestamp
        strategy.state.last_signal = 1

        # Try to generate another signal quickly
        bounce = BounceDetection(
            timestamp=base_timestamp + pd.Timedelta(seconds=3),  # Only 3 seconds later
            bounce_type="ask",
            touch_price=5000.00,
            bounce_price=4999.75,
            strength=1.0,
            volume=50,
            spread_at_bounce=0.25,
        )

        # Should reject due to time filter
        assert not strategy._validate_bounce_entry(bounce, spread_ticks=1.0)
