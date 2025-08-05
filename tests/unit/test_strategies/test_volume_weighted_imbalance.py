"""Tests for Volume-Weighted Order Flow Imbalance Strategy."""

from decimal import Decimal
from unittest.mock import Mock

import pytest

from strategy_lab.data.synchronization import PriceLevel, UnifiedMarketSnapshot
from strategy_lab.strategies.implementations.volume_weighted_imbalance import (
    VolumeWeightedImbalanceStrategy,
    VWOFIParameters,
)
from strategy_lab.strategies.protocol_enhanced import (
    OrderSide,
    OrderType,
    StrategyContext,
)


class TestVolumeWeightedImbalanceStrategy:
    """Test Volume-Weighted Imbalance Strategy."""

    @pytest.fixture
    def strategy(self):
        """Create strategy instance with test parameters."""
        return VolumeWeightedImbalanceStrategy(
            depth_levels=3,
            imbalance_threshold=0.6,
            volume_window=50,
            confidence_threshold=60.0,
            max_position_size=5,
            stop_loss_ticks=5,
            take_profit_ticks=3,
        )

    @pytest.fixture
    def mock_context(self):
        """Create mock strategy context."""
        context = Mock(spec=StrategyContext)
        context.position = Mock()
        context.position.size = 0
        context.position.avg_price = None
        return context

    @pytest.fixture
    def sample_snapshot(self):
        """Create sample market snapshot with L1 and L2 data."""
        return UnifiedMarketSnapshot(
            timestamp=1000000000,
            # L1 data
            last_trade_price=Decimal("100.50"),
            last_trade_volume=10,
            bid_price=Decimal("100.25"),
            ask_price=Decimal("100.50"),
            bid_volume=50,
            ask_volume=30,
            # L2 data
            bid_levels=[
                PriceLevel(Decimal("100.25"), 50),
                PriceLevel(Decimal("100.00"), 100),
                PriceLevel(Decimal("99.75"), 150),
            ],
            ask_levels=[
                PriceLevel(Decimal("100.50"), 30),
                PriceLevel(Decimal("100.75"), 80),
                PriceLevel(Decimal("101.00"), 120),
            ],
        )

    def test_strategy_initialization(self):
        """Test strategy initialization with parameters."""
        params = VWOFIParameters(
            depth_levels=5,
            imbalance_threshold=0.7,
            volume_window=100,
            confidence_threshold=75.0,
        )

        strategy = VolumeWeightedImbalanceStrategy(
            depth_levels=params.depth_levels,
            imbalance_threshold=params.imbalance_threshold,
            volume_window=params.volume_window,
            confidence_threshold=params.confidence_threshold,
        )

        assert strategy.params.depth_levels == 5
        assert strategy.params.imbalance_threshold == 0.7
        assert strategy.params.volume_window == 100
        assert strategy.params.confidence_threshold == 75.0
        assert strategy.imbalance_ema == 0.0
        assert strategy.signal_count == 0

    def test_insufficient_data_handling(self, strategy, mock_context):
        """Test handling of insufficient market data."""
        # Snapshot with no L2 data
        snapshot = UnifiedMarketSnapshot(
            timestamp=1000000000,
            bid_price=Decimal("100.25"),
            ask_price=Decimal("100.50"),
        )

        orders = strategy.on_market_data(snapshot, mock_context)
        assert len(orders) == 0

        # Snapshot with insufficient depth
        snapshot = UnifiedMarketSnapshot(
            timestamp=1000000000,
            bid_price=Decimal("100.25"),
            ask_price=Decimal("100.50"),
            bid_levels=[PriceLevel(Decimal("100.25"), 50)],
            ask_levels=[PriceLevel(Decimal("100.50"), 30)],
        )

        orders = strategy.on_market_data(snapshot, mock_context)
        assert len(orders) == 0

    def test_order_book_imbalance_calculation(self, strategy, sample_snapshot):
        """Test raw order book imbalance calculation."""
        imbalance = strategy._calculate_order_book_imbalance(sample_snapshot)

        # Bid volume at depth 3: 50 + 100 + 150 = 300
        # Ask volume at depth 3: 30 + 80 + 120 = 230
        # Imbalance = (300 - 230) / (300 + 230) = 70 / 530 ≈ 0.132

        assert abs(imbalance - 0.132) < 0.01

    def test_volume_history_update(self, strategy, sample_snapshot):
        """Test volume history tracking."""
        strategy._update_volume_history(sample_snapshot)

        assert len(strategy.volume_history) == 1
        assert strategy.volume_history[0]["volume"] == 10
        assert strategy.volume_history[0]["price"] == Decimal("100.50")

        # Test window size limit
        for i in range(60):
            snapshot = UnifiedMarketSnapshot(
                timestamp=1000000000 + i * 1000000,
                last_trade_price=Decimal("100.50"),
                last_trade_volume=5 + i,
            )
            strategy._update_volume_history(snapshot)

        assert len(strategy.volume_history) == strategy.params.volume_window

    def test_confidence_calculation(self, strategy, sample_snapshot):
        """Test confidence score calculation."""
        # Add some volume history
        for i in range(10):
            strategy.volume_history.append(
                {
                    "timestamp": sample_snapshot.timestamp - i * 1000000,
                    "volume": 15,
                    "price": Decimal("100.50"),
                    "spread": Decimal("0.25"),
                    "mid_price": Decimal("100.375"),
                }
            )

        confidence = strategy._calculate_confidence(0.5, sample_snapshot)

        # Should have reasonable confidence with 50% imbalance
        assert 40 <= confidence <= 80

    def test_buy_signal_generation(self, strategy, sample_snapshot, mock_context):
        """Test buy signal generation with positive imbalance."""
        # Initialize strategy first
        strategy.initialize()

        # Add volume history with enough data
        for i in range(20):
            strategy.volume_history.append(
                {
                    "timestamp": sample_snapshot.timestamp - (i + 1) * 1000000,
                    "volume": 20,
                    "price": Decimal("100.50"),
                    "spread": Decimal("0.25"),
                    "mid_price": Decimal("100.375"),
                }
            )

        # Create a snapshot with strong positive imbalance
        positive_imbalance_snapshot = UnifiedMarketSnapshot(
            timestamp=sample_snapshot.timestamp,
            last_trade_price=Decimal("100.50"),
            last_trade_volume=25,  # Good volume
            bid_price=Decimal("100.25"),
            ask_price=Decimal("100.50"),
            bid_levels=[
                PriceLevel(Decimal("100.25"), 200),  # Much more bid volume
                PriceLevel(Decimal("100.00"), 300),
                PriceLevel(Decimal("99.75"), 400),
            ],
            ask_levels=[
                PriceLevel(Decimal("100.50"), 30),  # Less ask volume
                PriceLevel(Decimal("100.75"), 40),
                PriceLevel(Decimal("101.00"), 50),
            ],
        )

        # Process multiple snapshots to build up EMA
        for _ in range(5):
            strategy.on_market_data(positive_imbalance_snapshot, mock_context)

        # Reset position and signal time for fresh signal
        mock_context.position.size = 0
        strategy.last_signal_time = 0

        # Generate signal
        orders = strategy.on_market_data(positive_imbalance_snapshot, mock_context)

        # Should generate buy order
        assert len(orders) == 1
        order = orders[0]
        assert order.side == OrderSide.BUY
        assert order.order_type == OrderType.MARKET
        assert order.size > 0
        assert order.size <= strategy.params.max_position_size

    def test_sell_signal_generation(self, strategy, mock_context):
        """Test sell signal generation with negative imbalance."""
        # Create snapshot with negative imbalance
        snapshot = UnifiedMarketSnapshot(
            timestamp=2000000000,
            last_trade_price=Decimal("100.50"),
            last_trade_volume=15,
            bid_price=Decimal("100.25"),
            ask_price=Decimal("100.50"),
            bid_levels=[
                PriceLevel(Decimal("100.25"), 30),  # Less bid volume
                PriceLevel(Decimal("100.00"), 50),
                PriceLevel(Decimal("99.75"), 70),
            ],
            ask_levels=[
                PriceLevel(Decimal("100.50"), 100),  # More ask volume
                PriceLevel(Decimal("100.75"), 150),
                PriceLevel(Decimal("101.00"), 200),
            ],
        )

        # Set up state
        strategy.imbalance_ema = -0.7  # Strong negative imbalance
        strategy.last_signal_time = 0

        # Add volume history
        for i in range(20):
            strategy.volume_history.append(
                {
                    "timestamp": snapshot.timestamp - i * 1000000,
                    "volume": 20,
                    "price": Decimal("100.50"),
                    "spread": Decimal("0.25"),
                    "mid_price": Decimal("100.375"),
                }
            )

        orders = strategy.on_market_data(snapshot, mock_context)

        # Should generate sell order
        assert len(orders) == 1
        order = orders[0]
        assert order.side == OrderSide.SELL

    def test_stop_loss_exit(self, strategy, sample_snapshot, mock_context):
        """Test stop loss exit condition."""
        # Set up position
        mock_context.position.size = 5  # Long position
        strategy.position_entry_price = Decimal("100.50")
        strategy.position_entry_time = sample_snapshot.timestamp - 10000000000

        # Create snapshot with loss
        loss_snapshot = UnifiedMarketSnapshot(
            timestamp=sample_snapshot.timestamp + 30000000000,
            bid_price=Decimal("99.00"),  # Down 6 ticks
            ask_price=Decimal("99.25"),
            bid_levels=sample_snapshot.bid_levels,
            ask_levels=sample_snapshot.ask_levels,
        )

        orders = strategy.on_market_data(loss_snapshot, mock_context)

        # Should generate exit order
        assert len(orders) == 1
        order = orders[0]
        assert order.side == OrderSide.SELL  # Exit long
        assert order.size == 5
        assert order.metadata["exit_reason"] == "stop_loss"

    def test_take_profit_exit(self, strategy, sample_snapshot, mock_context):
        """Test take profit exit condition."""
        # Set up position
        mock_context.position.size = 5  # Long position
        strategy.position_entry_price = Decimal("100.50")
        strategy.position_entry_time = sample_snapshot.timestamp - 10000000000

        # Create snapshot with profit
        profit_snapshot = UnifiedMarketSnapshot(
            timestamp=sample_snapshot.timestamp + 30000000000,
            bid_price=Decimal("101.25"),  # Up 3 ticks
            ask_price=Decimal("101.50"),
            bid_levels=sample_snapshot.bid_levels,
            ask_levels=sample_snapshot.ask_levels,
        )

        orders = strategy.on_market_data(profit_snapshot, mock_context)

        # Should generate exit order
        assert len(orders) == 1
        order = orders[0]
        assert order.side == OrderSide.SELL  # Exit long
        assert order.metadata["exit_reason"] == "take_profit"

    def test_time_based_exit(self, strategy, sample_snapshot, mock_context):
        """Test time-based exit condition."""
        # Set up position
        mock_context.position.size = -3  # Short position
        strategy.position_entry_price = Decimal("100.50")
        strategy.position_entry_time = sample_snapshot.timestamp
        strategy.params.hold_time_seconds = 30

        # Create snapshot after hold time
        late_snapshot = UnifiedMarketSnapshot(
            timestamp=sample_snapshot.timestamp + 31000000000,  # 31 seconds later
            bid_price=Decimal("100.25"),
            ask_price=Decimal("100.50"),
            bid_levels=sample_snapshot.bid_levels,
            ask_levels=sample_snapshot.ask_levels,
        )

        orders = strategy.on_market_data(late_snapshot, mock_context)

        # Should generate exit order
        assert len(orders) == 1
        order = orders[0]
        assert order.side == OrderSide.BUY  # Exit short
        assert order.metadata["exit_reason"] == "time_exit"

    def test_signal_cooldown(self, strategy, sample_snapshot, mock_context):
        """Test signal cooldown prevents rapid signals."""
        # Initialize strategy
        strategy.initialize()

        # Add volume history
        for i in range(20):
            strategy.volume_history.append(
                {
                    "timestamp": sample_snapshot.timestamp - (i + 1) * 1000000,
                    "volume": 20,
                    "price": Decimal("100.50"),
                    "spread": Decimal("0.25"),
                    "mid_price": Decimal("100.375"),
                }
            )

        # Create a snapshot with strong imbalance
        imbalanced_snapshot = UnifiedMarketSnapshot(
            timestamp=sample_snapshot.timestamp,
            last_trade_price=Decimal("100.50"),
            last_trade_volume=25,
            bid_price=Decimal("100.25"),
            ask_price=Decimal("100.50"),
            bid_levels=[
                PriceLevel(Decimal("100.25"), 200),
                PriceLevel(Decimal("100.00"), 300),
                PriceLevel(Decimal("99.75"), 400),
            ],
            ask_levels=[
                PriceLevel(Decimal("100.50"), 30),
                PriceLevel(Decimal("100.75"), 40),
                PriceLevel(Decimal("101.00"), 50),
            ],
        )

        # Build up EMA
        for _ in range(5):
            strategy.on_market_data(imbalanced_snapshot, mock_context)

        # Reset for fresh signal
        mock_context.position.size = 0
        strategy.last_signal_time = 0

        # Generate first signal
        orders = strategy.on_market_data(imbalanced_snapshot, mock_context)
        assert len(orders) == 1

        # Try to generate another signal immediately
        mock_context.position.size = 0  # Reset position

        snapshot2 = UnifiedMarketSnapshot(
            timestamp=sample_snapshot.timestamp + 100000000,  # 100ms later
            last_trade_price=Decimal("100.50"),
            last_trade_volume=10,
            bid_price=sample_snapshot.bid_price,
            ask_price=sample_snapshot.ask_price,
            bid_levels=sample_snapshot.bid_levels,
            ask_levels=sample_snapshot.ask_levels,
        )

        orders = strategy.on_market_data(snapshot2, mock_context)
        assert len(orders) == 0  # Should be blocked by cooldown

    def test_metadata_and_state(self, strategy):
        """Test strategy metadata and state methods."""
        metadata = strategy.get_metadata()

        assert metadata.name == "volume_weighted_imbalance"
        assert metadata.version == "1.0.0"
        assert "microstructure" in metadata.tags
        assert "level-1+2" in metadata.tags

        state = strategy.get_state()
        assert "imbalance_ema" in state
        assert "signal_count" in state
        assert "avg_confidence" in state
