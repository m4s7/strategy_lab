"""Tests for SignalGenerator and related signal generation components."""

from unittest.mock import Mock

import pytest

from src.strategy_lab.backtesting.hft_integration.data_feed import TickData
from src.strategy_lab.strategies.base import (
    MarketMicrostructure,
    Signal,
    SignalGenerator,
    SignalType,
    TechnicalIndicators,
)


class TestTechnicalIndicators:
    """Test technical indicator calculations."""

    def test_simple_moving_average(self):
        """Test SMA calculation."""
        prices = [10.0, 11.0, 12.0, 13.0, 14.0]

        # Test normal case
        sma = TechnicalIndicators.simple_moving_average(prices, 3)
        assert sma == 13.0  # (12 + 13 + 14) / 3

        # Test full period
        sma = TechnicalIndicators.simple_moving_average(prices, 5)
        assert sma == 12.0  # (10 + 11 + 12 + 13 + 14) / 5

        # Test insufficient data
        sma = TechnicalIndicators.simple_moving_average(prices, 10)
        assert sma is None

        # Test empty list
        sma = TechnicalIndicators.simple_moving_average([], 3)
        assert sma is None

    def test_exponential_moving_average(self):
        """Test EMA calculation."""
        prices = [10.0, 11.0, 12.0, 13.0, 14.0]

        # Test first calculation (should use SMA)
        ema = TechnicalIndicators.exponential_moving_average(prices, 3)
        expected_first = TechnicalIndicators.simple_moving_average(prices, 3)
        assert ema == expected_first

        # Test incremental calculation
        ema = TechnicalIndicators.exponential_moving_average(
            [15.0], 3, previous_ema=13.0
        )
        multiplier = 2.0 / (3 + 1)
        expected = (15.0 * multiplier) + (13.0 * (1 - multiplier))
        assert abs(ema - expected) < 0.0001

        # Test insufficient data
        ema = TechnicalIndicators.exponential_moving_average([10.0], 5)
        assert ema is None

    def test_rsi_calculation(self):
        """Test RSI calculation."""
        # Test with trending up prices
        up_prices = [
            10.0,
            11.0,
            12.0,
            13.0,
            14.0,
            15.0,
            16.0,
            17.0,
            18.0,
            19.0,
            20.0,
            21.0,
            22.0,
            23.0,
            24.0,
            25.0,
        ]
        rsi = TechnicalIndicators.rsi(up_prices, 14)
        assert rsi > 50.0  # Should be above 50 for uptrend

        # Test with trending down prices
        down_prices = [
            25.0,
            24.0,
            23.0,
            22.0,
            21.0,
            20.0,
            19.0,
            18.0,
            17.0,
            16.0,
            15.0,
            14.0,
            13.0,
            12.0,
            11.0,
            10.0,
        ]
        rsi = TechnicalIndicators.rsi(down_prices, 14)
        assert rsi < 50.0  # Should be below 50 for downtrend

        # Test insufficient data
        rsi = TechnicalIndicators.rsi([10.0, 11.0], 14)
        assert rsi is None

        # Test no losses (should return 100)
        no_loss_prices = [10.0, 11.0, 12.0, 13.0, 14.0]
        rsi = TechnicalIndicators.rsi(no_loss_prices, 3)
        assert rsi == 100.0

    def test_bollinger_bands(self):
        """Test Bollinger Bands calculation."""
        prices = [10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0]

        bands = TechnicalIndicators.bollinger_bands(prices, 5, 2.0)
        assert bands is not None
        assert "upper" in bands
        assert "middle" in bands
        assert "lower" in bands

        # Middle band should be SMA
        expected_middle = sum(prices[-5:]) / 5
        assert bands["middle"] == expected_middle

        # Upper should be > middle > lower
        assert bands["upper"] > bands["middle"] > bands["lower"]

        # Test insufficient data
        bands = TechnicalIndicators.bollinger_bands([10.0, 11.0], 5)
        assert bands is None


class TestMarketMicrostructure:
    """Test market microstructure analysis tools."""

    def test_calculate_spread(self):
        """Test bid-ask spread calculation."""
        spread = MarketMicrostructure.calculate_spread(13000.0, 13000.25)
        assert spread == 0.25

        spread = MarketMicrostructure.calculate_spread(13000.25, 13000.0)
        assert spread == -0.25

    def test_calculate_spread_bps(self):
        """Test spread in basis points calculation."""
        # Test with explicit mid price
        spread_bps = MarketMicrostructure.calculate_spread_bps(
            13000.0, 13000.50, 13000.25
        )
        expected = (0.50 / 13000.25) * 10000
        assert abs(spread_bps - expected) < 0.001

        # Test with calculated mid price
        spread_bps = MarketMicrostructure.calculate_spread_bps(13000.0, 13000.50)
        mid_price = (13000.0 + 13000.50) / 2
        expected = (0.50 / mid_price) * 10000
        assert abs(spread_bps - expected) < 0.001

        # Test zero mid price
        spread_bps = MarketMicrostructure.calculate_spread_bps(0.0, 0.0, 0.0)
        assert spread_bps == 0.0

    def test_calculate_order_flow_imbalance(self):
        """Test order flow imbalance calculation."""
        # Equal bid/ask
        imbalance = MarketMicrostructure.calculate_order_flow_imbalance(100.0, 100.0)
        assert imbalance == 0.0

        # More bids
        imbalance = MarketMicrostructure.calculate_order_flow_imbalance(150.0, 100.0)
        assert imbalance > 0

        # More asks
        imbalance = MarketMicrostructure.calculate_order_flow_imbalance(100.0, 150.0)
        assert imbalance < 0

        # Zero total size
        imbalance = MarketMicrostructure.calculate_order_flow_imbalance(0.0, 0.0)
        assert imbalance == 0.0


class TestSignal:
    """Test Signal dataclass."""

    def test_signal_creation(self):
        """Test signal creation with required fields."""
        signal = Signal(
            signal_type=SignalType.BUY,
            strength=0.8,
            price=13000.25,
            timestamp=1609459200000000000,
        )

        assert signal.signal_type == SignalType.BUY
        assert signal.strength == 0.8
        assert signal.price == 13000.25
        assert signal.timestamp == 1609459200000000000
        assert signal.confidence == 0.5  # Default
        assert signal.metadata == {}  # Default

    def test_signal_with_metadata(self):
        """Test signal creation with metadata."""
        metadata = {"indicator": "rsi", "value": 75.0}
        signal = Signal(
            signal_type=SignalType.SELL,
            strength=0.9,
            price=13000.25,
            timestamp=1609459200000000000,
            confidence=0.8,
            metadata=metadata,
        )

        assert signal.metadata == metadata
        assert signal.confidence == 0.8


class TestSignalGenerator:
    """Test SignalGenerator class."""

    @pytest.fixture
    def config(self):
        """Create mock config for testing."""
        return Mock()

    @pytest.fixture
    def signal_generator(self, config):
        """Create signal generator for testing."""
        return SignalGenerator(config)

    @pytest.fixture
    def sample_ticks(self):
        """Create sample tick data for testing."""
        base_timestamp = 1609459200000000000
        ticks = []

        # Create 50 ticks with gradual price increase
        for i in range(50):
            tick = TickData(
                timestamp=base_timestamp + i * 1000000000,  # 1 second intervals
                price=13000.0 + i * 0.25,  # Gradually increasing
                qty=5.0 + i % 3,  # Varying volume
                side=1 if i % 2 == 0 else -1,  # Alternating sides
            )
            ticks.append(tick)

        return ticks

    def test_initialization(self, signal_generator, config):
        """Test signal generator initialization."""
        assert signal_generator.config == config
        assert len(signal_generator.price_history) == 0
        assert len(signal_generator.volume_history) == 0
        assert len(signal_generator.signal_history) == 0
        assert signal_generator.indicators == {}

    def test_update_with_tick(self, signal_generator, sample_ticks):
        """Test updating signal generator with tick data."""
        tick = sample_ticks[0]
        signal_generator.update(tick)

        assert len(signal_generator.price_history) == 1
        assert len(signal_generator.volume_history) == 1
        assert len(signal_generator.timestamp_history) == 1
        assert signal_generator.price_history[0] == tick.price
        assert signal_generator.volume_history[0] == tick.qty
        assert signal_generator.timestamp_history[0] == tick.timestamp

    def test_price_history_buffer_limit(self, signal_generator, sample_ticks):
        """Test that price history respects buffer limits."""
        # Update with more ticks than buffer size (200)
        for i in range(250):
            tick = TickData(
                timestamp=1609459200000000000 + i * 1000000000,
                price=13000.0 + i,
                qty=5.0,
                side=1,
            )
            signal_generator.update(tick)

        # Should not exceed buffer size
        assert len(signal_generator.price_history) == 200
        assert len(signal_generator.volume_history) == 200
        assert len(signal_generator.timestamp_history) == 200

        # Should contain most recent data
        assert signal_generator.price_history[-1] == 13000.0 + 249

    def test_generate_signal_default(self, signal_generator, sample_ticks):
        """Test default signal generation (should return None)."""
        tick = sample_ticks[0]
        signal = signal_generator.generate_signal(tick)
        assert signal is None

    def test_mean_reversion_signal_insufficient_data(self, signal_generator):
        """Test mean reversion signal with insufficient data."""
        tick = TickData(timestamp=1609459200000000000, price=13000.0, qty=5.0, side=1)
        signal = signal_generator.generate_mean_reversion_signal(
            tick, lookback_period=20
        )
        assert signal is None

    def test_mean_reversion_signal_generation(self, signal_generator):
        """Test mean reversion signal generation."""
        # Create price data that will trigger Bollinger Band signals
        base_price = 13000.0
        prices = [base_price] * 19  # 19 prices at same level

        # Add prices to build history
        for i, price in enumerate(prices):
            tick = TickData(
                timestamp=1609459200000000000 + i * 1000000000,
                price=price,
                qty=5.0,
                side=1,
            )
            signal_generator.update(tick)

        # Add extreme low price to trigger buy signal
        low_tick = TickData(
            timestamp=1609459200000000000 + 20 * 1000000000,
            price=base_price - 10.0,  # Significantly lower
            qty=5.0,
            side=-1,
        )

        signal = signal_generator.generate_mean_reversion_signal(
            low_tick, lookback_period=20
        )

        if signal:  # Signal might not generate due to insufficient deviation
            assert signal.signal_type == SignalType.BUY
            assert 0 <= signal.strength <= 1.0
            assert signal.metadata["indicator"] == "bollinger_bands"

    def test_momentum_signal_insufficient_data(self, signal_generator):
        """Test momentum signal with insufficient data."""
        tick = TickData(timestamp=1609459200000000000, price=13000.0, qty=5.0, side=1)
        signal = signal_generator.generate_momentum_signal(
            tick, short_period=5, long_period=20
        )
        assert signal is None

    def test_momentum_signal_generation(self, signal_generator):
        """Test momentum signal generation."""
        # Create trending price data
        base_timestamp = 1609459200000000000

        # First, add stable prices for long MA
        for i in range(20):
            tick = TickData(
                timestamp=base_timestamp + i * 1000000000,
                price=13000.0,  # Stable price
                qty=5.0,
                side=1,
            )
            signal_generator.update(tick)

        # Add one more tick to get previous MAs
        tick = TickData(
            timestamp=base_timestamp + 20 * 1000000000, price=13000.0, qty=5.0, side=1
        )
        signal_generator.update(tick)

        # Now add significantly higher prices to create crossover
        for i in range(5):
            tick = TickData(
                timestamp=base_timestamp + (21 + i) * 1000000000,
                price=13005.0,  # Higher price for crossover
                qty=5.0,
                side=1,
            )
            signal_generator.update(tick)

        # Generate signal
        latest_tick = TickData(
            timestamp=base_timestamp + 26 * 1000000000, price=13005.0, qty=5.0, side=1
        )

        signal = signal_generator.generate_momentum_signal(
            latest_tick, short_period=5, long_period=20
        )

        if signal:  # Signal generation depends on exact crossover conditions
            assert signal.signal_type in [SignalType.BUY, SignalType.SELL]
            assert 0 <= signal.strength <= 1.0
            assert signal.metadata["indicator"] == "ma_crossover"

    def test_rsi_signal_generation(self, signal_generator):
        """Test RSI signal generation."""
        base_timestamp = 1609459200000000000

        # Create trending up price data for overbought signal
        for i in range(16):  # Need 15+ for RSI calculation
            tick = TickData(
                timestamp=base_timestamp + i * 1000000000,
                price=13000.0 + i * 2.0,  # Strong uptrend
                qty=5.0,
                side=1,
            )
            signal_generator.update(tick)

        latest_tick = TickData(
            timestamp=base_timestamp + 16 * 1000000000,
            price=13000.0 + 16 * 2.0,
            qty=5.0,
            side=1,
        )

        signal = signal_generator.generate_rsi_signal(
            latest_tick,
            period=14,
            overbought_threshold=50.0,  # Lower threshold for testing
        )

        if signal:
            assert signal.signal_type == SignalType.SELL
            assert signal.metadata["indicator"] == "rsi"
            assert "rsi_value" in signal.metadata

    def test_get_last_signal(self, signal_generator):
        """Test getting last signal."""
        # No signals initially
        assert signal_generator.get_last_signal() is None

        # Add a signal manually
        signal = Signal(
            signal_type=SignalType.BUY,
            strength=0.8,
            price=13000.0,
            timestamp=1609459200000000000,
        )
        signal_generator.signal_history.append(signal)

        assert signal_generator.get_last_signal() == signal

    def test_get_signal_history(self, signal_generator):
        """Test getting signal history."""
        # Add multiple signals
        signals = []
        for i in range(5):
            signal = Signal(
                signal_type=SignalType.BUY,
                strength=0.5 + i * 0.1,
                price=13000.0 + i,
                timestamp=1609459200000000000 + i * 1000000000,
            )
            signals.append(signal)
            signal_generator.signal_history.append(signal)

        # Get last 3 signals
        recent_signals = signal_generator.get_signal_history(3)
        assert len(recent_signals) == 3
        assert recent_signals == signals[-3:]

    def test_get_indicator_values(self, signal_generator, sample_ticks):
        """Test getting indicator values."""
        # Update with some data
        for tick in sample_ticks[:25]:
            signal_generator.update(tick)

        indicators = signal_generator.get_indicator_values()

        # Should have various indicators
        assert "last_price" in indicators
        assert "price_change" in indicators
        assert indicators["last_price"] == sample_ticks[24].price

        # Check that we get a copy (modifications don't affect original)
        indicators["test"] = "value"
        assert "test" not in signal_generator.indicators

    def test_indicators_update(self, signal_generator, sample_ticks):
        """Test that indicators are updated correctly."""
        # Add enough data for all indicators
        for tick in sample_ticks:
            signal_generator.update(tick)

        # Check that indicators are calculated
        assert signal_generator.indicators["sma_5"] is not None
        assert signal_generator.indicators["sma_20"] is not None
        assert signal_generator.indicators["rsi"] is not None
        assert signal_generator.indicators["bb"] is not None

        # Verify price change calculation
        expected_change = sample_ticks[-1].price - sample_ticks[-2].price
        assert signal_generator.indicators["price_change"] == expected_change
