"""Tests for StrategyBase abstract class and related components."""

from unittest.mock import Mock

import pytest

from src.strategy_lab.backtesting.hft_integration.adapter import HftBacktestAdapter
from src.strategy_lab.backtesting.hft_integration.data_feed import TickData
from src.strategy_lab.backtesting.hft_integration.event_processor import Fill, OrderSide
from src.strategy_lab.strategies.base import (
    MarketState,
    StrategyBase,
    StrategyConfig,
    StrategyMetrics,
    StrategyState,
)


class TestStrategyConfig:
    """Test StrategyConfig dataclass."""

    def test_default_config_creation(self):
        """Test creating config with default values."""
        config = StrategyConfig(strategy_name="test")

        assert config.strategy_name == "test"
        assert config.version == "1.0.0"
        assert config.max_position_size == 10
        assert config.max_daily_loss == 1000.0
        assert config.default_order_size == 1
        assert config.enable_stop_loss is True
        assert config.stop_loss_pct == 0.005

    def test_custom_config_creation(self):
        """Test creating config with custom values."""
        config = StrategyConfig(
            strategy_name="custom",
            version="2.0.0",
            max_position_size=5,
            max_daily_loss=500.0,
            custom_params={"param1": "value1"},
        )

        assert config.strategy_name == "custom"
        assert config.version == "2.0.0"
        assert config.max_position_size == 5
        assert config.max_daily_loss == 500.0
        assert config.custom_params["param1"] == "value1"

    def test_config_validation_success(self):
        """Test successful config validation."""
        config = StrategyConfig(strategy_name="test")
        assert config.validate() is True

    def test_config_validation_failures(self):
        """Test config validation with invalid parameters."""

        # Invalid max_position_size
        config = StrategyConfig(strategy_name="test", max_position_size=0)
        with pytest.raises(ValueError, match="max_position_size must be positive"):
            config.validate()

        # Invalid max_daily_loss
        config = StrategyConfig(strategy_name="test", max_daily_loss=-100)
        with pytest.raises(ValueError, match="max_daily_loss must be positive"):
            config.validate()

        # Invalid stop_loss_pct
        config = StrategyConfig(strategy_name="test", stop_loss_pct=1.5)
        with pytest.raises(ValueError, match="stop_loss_pct must be between 0 and 1"):
            config.validate()


class TestStrategyMetrics:
    """Test StrategyMetrics dataclass."""

    def test_default_metrics(self):
        """Test metrics with default values."""
        metrics = StrategyMetrics()

        assert metrics.total_trades == 0
        assert metrics.winning_trades == 0
        assert metrics.losing_trades == 0
        assert metrics.gross_pnl == 0.0
        assert metrics.win_rate == 0.0
        assert metrics.net_pnl == 0.0

    def test_win_rate_calculation(self):
        """Test win rate calculation."""
        metrics = StrategyMetrics(total_trades=10, winning_trades=7)
        assert metrics.win_rate == 70.0

        # Test with zero trades
        metrics = StrategyMetrics()
        assert metrics.win_rate == 0.0

    def test_net_pnl_calculation(self):
        """Test net P&L calculation."""
        metrics = StrategyMetrics(realized_pnl=100.0, unrealized_pnl=50.0)
        assert metrics.net_pnl == 150.0


class ConcreteStrategy(StrategyBase):
    """Concrete strategy implementation for testing."""

    def __init__(self, config, adapter):
        super().__init__(config, adapter)
        self.initialized = False
        self.processed_ticks = []
        self.cleaned_up = False

    def initialize(self):
        self.initialized = True

    def process_tick(self, tick):
        self.processed_ticks.append(tick)

    def cleanup(self):
        self.cleaned_up = True


class TestStrategyBase:
    """Test StrategyBase abstract class."""

    @pytest.fixture
    def mock_adapter(self):
        """Create mock adapter for testing."""
        adapter = Mock(spec=HftBacktestAdapter)
        adapter.get_current_position.return_value = {
            "quantity": 0,
            "average_price": 0.0,
            "is_flat": True,
            "is_long": False,
            "is_short": False,
            "realized_pnl": 0.0,
            "unrealized_pnl": 0.0,
        }
        return adapter

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return StrategyConfig(
            strategy_name="TestStrategy", max_position_size=5, max_daily_loss=500.0
        )

    @pytest.fixture
    def strategy(self, config, mock_adapter):
        """Create test strategy instance."""
        return ConcreteStrategy(config, mock_adapter)

    def test_strategy_initialization(self, strategy, config, mock_adapter):
        """Test strategy initialization."""
        assert strategy.config == config
        assert strategy.adapter == mock_adapter
        assert strategy.state == StrategyState.INACTIVE
        assert strategy.market_state == MarketState.PRE_MARKET
        assert isinstance(strategy.metrics, StrategyMetrics)
        assert strategy.strategy_data == {}
        assert strategy.last_tick is None
        assert strategy.current_timestamp == 0

        # Verify callbacks were set
        mock_adapter.set_strategy_callback.assert_called_once()
        mock_adapter.set_fill_callback.assert_called_once()

    def test_strategy_lifecycle(self, strategy):
        """Test strategy start/stop lifecycle."""

        # Test start
        strategy.start()
        assert strategy.state == StrategyState.ACTIVE
        assert strategy.initialized is True

        # Test stop
        strategy.stop()
        assert strategy.state == StrategyState.INACTIVE
        assert strategy.cleaned_up is True

    def test_strategy_pause_resume(self, strategy):
        """Test strategy pause/resume functionality."""

        # Start strategy first
        strategy.start()
        assert strategy.state == StrategyState.ACTIVE

        # Test pause
        strategy.pause()
        assert strategy.state == StrategyState.PAUSED

        # Test resume
        strategy.resume()
        assert strategy.state == StrategyState.ACTIVE

    def test_tick_processing(self, strategy, mock_adapter):
        """Test tick processing functionality."""

        strategy.start()

        # Create test tick
        tick = TickData(timestamp=1609459200000000000, price=13000.25, qty=5.0, side=1)

        # Process tick through internal handler
        strategy._on_tick(tick)

        assert strategy.last_tick == tick
        assert strategy.current_timestamp == tick.timestamp
        assert len(strategy.processed_ticks) == 1
        assert strategy.processed_ticks[0] == tick

    def test_tick_processing_when_paused(self, strategy):
        """Test that ticks are not processed when strategy is paused."""

        strategy.start()
        strategy.pause()

        tick = TickData(timestamp=1609459200000000000, price=13000.25, qty=5.0, side=1)
        strategy._on_tick(tick)

        # Tick should be stored but not processed
        assert strategy.last_tick == tick
        assert len(strategy.processed_ticks) == 0

    def test_data_access_methods(self, strategy):
        """Test data access methods."""

        # Test with no tick data
        assert strategy.get_last_price() == 0.0
        assert strategy.get_last_volume() == 0.0

        # Set tick data
        tick = TickData(timestamp=1609459200000000000, price=13500.50, qty=10.0, side=1)
        strategy.last_tick = tick

        assert strategy.get_last_price() == 13500.50
        assert strategy.get_last_volume() == 10.0

    def test_state_persistence(self, strategy):
        """Test strategy state save/restore."""

        # Set some state
        strategy.strategy_data = {"test_param": "test_value"}
        strategy.metrics.total_trades = 5
        strategy.metrics.gross_pnl = 100.0
        strategy.current_timestamp = 1609459200000000000

        # Get state
        state = strategy.get_strategy_state()

        assert state["strategy_data"]["test_param"] == "test_value"
        assert state["metrics"]["total_trades"] == 5
        assert state["metrics"]["gross_pnl"] == 100.0
        assert state["timestamp"] == 1609459200000000000

        # Create new strategy and restore state
        new_strategy = ConcreteStrategy(strategy.config, strategy.adapter)
        new_strategy.set_strategy_state(state)

        assert new_strategy.strategy_data["test_param"] == "test_value"
        assert new_strategy.metrics.total_trades == 5
        assert new_strategy.metrics.gross_pnl == 100.0
        assert new_strategy.current_timestamp == 1609459200000000000

    def test_order_submission(self, strategy, mock_adapter):
        """Test order submission methods."""

        strategy.start()

        # Mock successful order submission
        mock_adapter.submit_market_order.return_value = 123
        mock_adapter.submit_limit_order.return_value = 124

        # Test market order
        order_id = strategy.submit_market_order(OrderSide.BUY, 2)
        assert order_id == 123
        assert strategy.metrics.total_trades == 1
        mock_adapter.submit_market_order.assert_called_with(OrderSide.BUY, 2, None)

        # Test limit order
        order_id = strategy.submit_limit_order(OrderSide.SELL, 1, 13000.0)
        assert order_id == 124
        mock_adapter.submit_limit_order.assert_called_with(
            OrderSide.SELL, 1, 13000.0, None
        )

    def test_order_validation(self, strategy, mock_adapter):
        """Test order validation logic."""

        strategy.start()

        # Test invalid quantity
        with pytest.raises(ValueError, match="Order validation failed"):
            strategy.submit_market_order(OrderSide.BUY, 0)

        # Test position size limit (config has max_position_size=5)
        with pytest.raises(ValueError, match="Order validation failed"):
            strategy.submit_market_order(OrderSide.BUY, 10)

    def test_order_cancellation(self, strategy, mock_adapter):
        """Test order cancellation."""

        strategy.start()

        mock_adapter.cancel_order.return_value = True

        success = strategy.cancel_order(123)
        assert success is True
        mock_adapter.cancel_order.assert_called_with(123, None)

    def test_fill_processing(self, strategy, mock_adapter):
        """Test order fill processing."""

        strategy.start()

        # Mock the position manager's process_fill method
        strategy.position_manager.process_fill = Mock()

        # Create test fill
        fill = Fill(
            order_id=123,
            timestamp=1609459200000000000,
            price=13000.25,
            quantity=2,
            side=OrderSide.BUY,
            commission=2.50,
        )

        # Process fill
        strategy._on_fill(fill)

        # Verify position manager was updated
        strategy.position_manager.process_fill.assert_called_once_with(fill)

    def test_close_all_positions(self, strategy, mock_adapter):
        """Test closing all positions."""

        strategy.start()

        # Mock current position
        mock_adapter.get_current_position.return_value = {
            "quantity": 3,
            "is_flat": False,
            "is_long": True,
            "is_short": False,
        }

        strategy.close_all_positions()

        # Should submit sell order to close long position (with timestamp=None)
        mock_adapter.submit_market_order.assert_called_with(OrderSide.SELL, 3, None)

    def test_error_handling(self, strategy):
        """Test error handling in strategy."""

        strategy.start()

        # Test that errors change strategy state
        test_error = Exception("Test error")
        strategy.on_error(test_error)

        assert strategy.state == StrategyState.ERROR

    def test_hook_methods(self, strategy):
        """Test optional hook methods."""

        # Test market open hook
        strategy.on_market_open()
        assert strategy.market_state == MarketState.MARKET_OPEN

        # Test market close hook
        strategy.on_market_close()
        assert strategy.market_state == MarketState.MARKET_CLOSE

        # Test fill hook (should not raise error)
        fill = Fill(
            order_id=123,
            timestamp=1609459200000000000,
            price=13000.25,
            quantity=1,
            side=OrderSide.BUY,
        )
        strategy.on_order_filled(fill)  # Should not raise exception

    def test_invalid_config_raises_error(self, mock_adapter):
        """Test that invalid configuration raises error during initialization."""

        invalid_config = StrategyConfig(
            strategy_name="test", max_position_size=0  # Invalid
        )

        with pytest.raises(ValueError):
            ConcreteStrategy(invalid_config, mock_adapter)
