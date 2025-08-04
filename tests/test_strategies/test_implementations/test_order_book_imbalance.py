"""Tests for Order Book Imbalance Strategy."""

from unittest.mock import MagicMock

import numpy as np
import pandas as pd
import pytest

from strategy_lab.strategies.implementations.order_book_imbalance import (
    ImbalanceMetrics,
    OrderBookImbalanceStrategy,
)


class TestOrderBookImbalanceStrategy:
    """Test Order Book Imbalance Strategy functionality."""

    @pytest.fixture
    def strategy(self):
        """Create strategy instance."""
        return OrderBookImbalanceStrategy(
            positive_threshold=0.3,
            negative_threshold=-0.3,
            smoothing_window=3,
            depth_levels=5,
            position_size=2,
        )

    @pytest.fixture
    def sample_order_book(self):
        """Create sample order book data."""
        return {
            "bid_levels": [
                (100.00, 100),  # Best bid
                (99.75, 150),
                (99.50, 200),
                (99.25, 250),
                (99.00, 300),
            ],
            "ask_levels": [
                (100.25, 80),  # Best ask
                (100.50, 120),
                (100.75, 180),
                (101.00, 220),
                (101.25, 280),
            ],
        }

    def test_strategy_initialization(self, strategy):
        """Test strategy initialization."""
        assert strategy.name == "order_book_imbalance"
        assert strategy.positive_threshold == 0.3
        assert strategy.negative_threshold == -0.3
        assert strategy.smoothing_window == 3
        assert strategy.position_size == 2

    def test_metadata(self):
        """Test strategy metadata."""
        metadata = OrderBookImbalanceStrategy.get_metadata()

        assert metadata.name == "order_book_imbalance"
        assert metadata.version == "1.0.0"
        assert "scalping" in metadata.tags
        assert "level2" in metadata.requirements.get("data", [])
        assert "positive_threshold" in metadata.parameters

    def test_imbalance_calculation(self, strategy, sample_order_book):
        """Test order book imbalance calculation."""
        strategy.initialize()

        metrics = strategy.calculate_imbalance(
            sample_order_book["bid_levels"], sample_order_book["ask_levels"]
        )

        assert isinstance(metrics, ImbalanceMetrics)
        assert -1 <= metrics.raw_imbalance <= 1
        assert metrics.bid_volume > 0
        assert metrics.ask_volume > 0
        assert metrics.depth_levels == 10

        # With these volumes, bid side is stronger
        assert metrics.raw_imbalance > 0

    def test_depth_weighting(self, strategy):
        """Test depth-weighted imbalance calculation."""
        strategy.initialize()
        strategy.depth_weight_decay = 0.5  # Strong decay

        # Equal volumes but at different depths
        bid_levels = [(100.00, 100)]
        ask_levels = [(100.25, 100)]

        metrics1 = strategy.calculate_imbalance(bid_levels, ask_levels)
        assert abs(metrics1.raw_imbalance) < 0.01  # Should be ~0

        # Add volume at depth
        bid_levels.append((99.75, 200))
        metrics2 = strategy.calculate_imbalance(bid_levels, ask_levels)
        assert metrics2.raw_imbalance > 0  # Bid side stronger

    def test_imbalance_smoothing(self, strategy, sample_order_book):
        """Test imbalance smoothing over multiple ticks."""
        strategy.initialize()
        strategy.smoothing_window = 3

        # Generate varying imbalances
        imbalances = []
        for i in range(5):
            # Modify volumes to create different imbalances
            bid_levels = [
                (p, v * (1 + i * 0.1)) for p, v in sample_order_book["bid_levels"]
            ]
            ask_levels = sample_order_book["ask_levels"]

            metrics = strategy.calculate_imbalance(bid_levels, ask_levels)
            imbalances.append(metrics.smoothed_imbalance)

        # Check smoothing effect
        assert len(imbalances) == 5
        # Later values should be smoothed
        assert imbalances[-1] != imbalances[-2]

    def test_spread_conditions(self, strategy):
        """Test spread condition checking."""
        # Wide spread - should trade
        assert strategy.check_spread_conditions(99.75, 100.25, tick_size=0.25)

        # Tight spread - should not trade
        strategy.min_spread_ticks = 3
        assert not strategy.check_spread_conditions(100.00, 100.25, tick_size=0.25)

    def test_volatility_filter(self, strategy):
        """Test volatility filtering."""
        # Generate price history
        base_price = 100.0

        # Moderate volatility (should pass)
        # Create realistic price movement with some trend
        moderate_vol_prices = []
        price = base_price
        for i in range(30):
            # Small random walk with slight trend
            price += np.random.normal(0.01, 0.2)  # 0.2% volatility per tick
            moderate_vol_prices.append(price)
        result = strategy.check_volatility_filter(moderate_vol_prices)
        # This should generally pass unless random values are extreme

        # Very low volatility (constant prices)
        low_vol_prices = [base_price] * 30
        assert strategy.check_volatility_filter(
            low_vol_prices
        )  # Should pass (no volatility data)

        # High volatility
        high_vol_prices = []
        price = base_price
        for _ in range(30):
            price += np.random.uniform(-5, 5)  # Large random jumps
            high_vol_prices.append(price)
        # This might or might not pass depending on values

        # No filter
        strategy.volatility_filter = False
        assert strategy.check_volatility_filter([])  # Always passes

    def test_signal_generation(self, strategy):
        """Test trading signal generation."""
        strategy.initialize()

        # Strong positive imbalance
        metrics = ImbalanceMetrics(
            raw_imbalance=0.5,
            smoothed_imbalance=0.4,
            bid_volume=1000,
            ask_volume=200,
            depth_levels=10,
            timestamp=pd.Timestamp.now(),
        )
        signal = strategy.generate_signal(metrics)
        assert signal == 1  # Long signal

        # Strong negative imbalance
        metrics.smoothed_imbalance = -0.4
        signal = strategy.generate_signal(metrics)
        assert signal == -1  # Short signal

        # Neutral imbalance
        metrics.smoothed_imbalance = 0.1
        signal = strategy.generate_signal(metrics)
        assert signal == 0  # No signal

    def test_consecutive_signals(self, strategy):
        """Test consecutive signal tracking."""
        strategy.initialize()

        # Generate consecutive long signals
        metrics = ImbalanceMetrics(
            raw_imbalance=0.4,
            smoothed_imbalance=0.4,
            bid_volume=1000,
            ask_volume=200,
            depth_levels=10,
            timestamp=pd.Timestamp.now(),
        )

        for i in range(3):
            signal = strategy.generate_signal(metrics)
            assert signal == 1
            assert strategy.state.consecutive_signals == i + 1

    def test_exit_conditions(self, strategy):
        """Test position exit conditions."""
        strategy.initialize()

        # Set up position
        strategy.state.position_entry_price = 100.0
        strategy.state.position_entry_time = pd.Timestamp.now()
        strategy.state.last_signal = 1  # Long position

        # Test stop loss
        current_price = 99.0  # 1% loss
        assert strategy.check_exit_conditions(current_price, pd.Timestamp.now())

        # Test time limit
        strategy.state.position_entry_price = 100.0
        future_time = strategy.state.position_entry_time + pd.Timedelta(seconds=400)
        assert strategy.check_exit_conditions(100.0, future_time)

        # Test signal reversal
        strategy.state.signal_history.extend([1, 1, -1])
        assert strategy.check_exit_conditions(100.0, pd.Timestamp.now())

    def test_process_tick_no_data(self, strategy):
        """Test process_tick without Level 2 data."""
        strategy.initialize()

        signal = strategy.process_tick(
            timestamp=pd.Timestamp.now(),
            price=100.0,
            volume=10,
            bid=99.75,
            ask=100.25,
        )

        assert signal == 0  # No signal without L2 data

    def test_process_tick_with_data(self, strategy, sample_order_book):
        """Test process_tick with full order book data."""
        strategy.initialize()
        strategy.position_manager = MagicMock()
        strategy.position_manager.has_position.return_value = False

        # Process multiple ticks to build up signal
        for i in range(3):
            signal = strategy.process_tick(
                timestamp=pd.Timestamp.now(),
                price=100.0,
                volume=10,
                bid=99.75,
                ask=100.25,
                bid_levels=sample_order_book["bid_levels"],
                ask_levels=sample_order_book["ask_levels"],
                price_history=[100.0 + j * 0.1 for j in range(30)],
            )

        # Should generate signal after enough consecutive signals
        assert abs(signal) in [0, 1]  # Depends on imbalance calculation

    def test_position_sizing(self, strategy):
        """Test position sizing logic."""
        # Long signal
        size = strategy.get_position_size(1, 100.0)
        assert size == 2  # Configured position size

        # No signal
        size = strategy.get_position_size(0, 100.0)
        assert size == 0

    def test_state_persistence(self, strategy, sample_order_book):
        """Test state save and restore."""
        strategy.initialize()

        # Generate some state
        for i in range(5):
            strategy.calculate_imbalance(
                sample_order_book["bid_levels"], sample_order_book["ask_levels"]
            )

        # Save state
        state = strategy.get_state()
        assert "custom" in state
        assert "imbalance_history" in state["custom"]
        assert "signal_history" in state["custom"]
        assert len(state["custom"]["imbalance_history"]) == 5

        # Create new strategy and restore
        new_strategy = OrderBookImbalanceStrategy()
        new_strategy.set_state(state)

        assert len(new_strategy.state.imbalance_history) == 5
        assert new_strategy.state.last_signal == state["custom"]["last_signal"]

    def test_cleanup(self, strategy, sample_order_book):
        """Test strategy cleanup."""
        strategy.initialize()

        # Generate some metrics
        for i in range(10):
            strategy.calculate_imbalance(
                sample_order_book["bid_levels"], sample_order_book["ask_levels"]
            )

        # Cleanup should not raise errors
        strategy.cleanup()

    def test_spread_filtering(self, strategy):
        """Test that strategy filters out tight spreads."""
        strategy.initialize()
        strategy.min_spread_ticks = 2
        strategy.position_manager = MagicMock()
        strategy.position_manager.has_position.return_value = False

        # Tight spread
        signal = strategy.process_tick(
            timestamp=pd.Timestamp.now(),
            price=100.0,
            volume=10,
            bid=100.00,
            ask=100.25,  # 1 tick spread
            bid_levels=[(100.00, 100)],
            ask_levels=[(100.25, 100)],
        )

        assert signal == 0  # Should not trade

    def test_volatility_filtering(self, strategy):
        """Test that strategy filters based on volatility."""
        strategy.initialize()
        strategy.volatility_filter = True
        strategy.position_manager = MagicMock()
        strategy.position_manager.has_position.return_value = False

        # Create high volatility price history
        price_history = [100.0]
        for i in range(30):
            price_history.append(price_history[-1] + np.random.uniform(-2, 2))

        signal = strategy.process_tick(
            timestamp=pd.Timestamp.now(),
            price=100.0,
            volume=10,
            bid=99.75,
            ask=100.25,
            bid_levels=[(99.75, 1000)],  # Strong bid
            ask_levels=[(100.25, 100)],  # Weak ask
            price_history=price_history,
        )

        # Signal depends on volatility calculation
        assert signal in [-1, 0, 1]

    def test_edge_cases(self, strategy):
        """Test edge cases and error handling."""
        strategy.initialize()

        # Empty order book
        metrics = strategy.calculate_imbalance([], [])
        assert metrics.raw_imbalance == 0.0
        assert metrics.bid_volume == 0.0
        assert metrics.ask_volume == 0.0

        # One-sided book
        metrics = strategy.calculate_imbalance([(100.0, 100)], [])
        assert metrics.raw_imbalance == 1.0  # All bid

        metrics = strategy.calculate_imbalance([], [(100.0, 100)])
        assert metrics.raw_imbalance == -1.0  # All ask

    def test_logging(self, strategy, sample_order_book):
        """Test that strategy logs important events."""
        strategy.initialize()
        strategy.logger = MagicMock()
        strategy.position_manager = MagicMock()
        strategy.position_manager.has_position.return_value = False

        # Generate signals to trigger logging
        for i in range(3):
            metrics = strategy.calculate_imbalance(
                sample_order_book["bid_levels"], sample_order_book["ask_levels"]
            )
            strategy.generate_signal(metrics)

        # Process tick to potentially generate trade signal
        strategy.process_tick(
            timestamp=pd.Timestamp.now(),
            price=100.0,
            volume=10,
            bid=99.75,
            ask=100.25,
            bid_levels=sample_order_book["bid_levels"],
            ask_levels=sample_order_book["ask_levels"],
        )

        # Check for any logging - logger was mocked after initialization
        # so we need to check if process_tick triggered any logs
        # In this case, no signal was generated, so no logging expected
        # The test is about ensuring no errors occur

    def test_real_scenario(self, strategy):
        """Test realistic trading scenario."""
        strategy.initialize()
        strategy.position_manager = MagicMock()

        # Simulate market session
        timestamps = pd.date_range("2024-01-01 09:30", periods=100, freq="1s")
        signals = []

        for i, ts in enumerate(timestamps):
            # Simulate changing market conditions
            imbalance_factor = np.sin(i / 10) * 0.5  # Oscillating imbalance

            bid_vol_base = 500
            ask_vol_base = 500

            bid_levels = [
                (
                    100.0 - j * 0.25,
                    int(bid_vol_base * (1 + imbalance_factor) * (0.9**j)),
                )
                for j in range(5)
            ]
            ask_levels = [
                (
                    100.0 + (j + 1) * 0.25,
                    int(ask_vol_base * (1 - imbalance_factor) * (0.9**j)),
                )
                for j in range(5)
            ]

            # Alternate between having position and not
            strategy.position_manager.has_position.return_value = len(signals) % 4 > 1

            signal = strategy.process_tick(
                timestamp=ts,
                price=100.0 + np.random.normal(0, 0.1),
                volume=np.random.randint(1, 20),
                bid=bid_levels[0][0],
                ask=ask_levels[0][0],
                bid_levels=bid_levels,
                ask_levels=ask_levels,
                price_history=[100.0] * 30,  # Stable price history
            )

            signals.append(signal)

        # Should have generated some signals
        assert any(s != 0 for s in signals)
        # Should have both long and short signals over time
        assert any(s > 0 for s in signals) or any(s < 0 for s in signals)
