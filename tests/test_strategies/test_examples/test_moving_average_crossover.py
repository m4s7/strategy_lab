"""Tests for MovingAverageCrossoverStrategy example."""

from unittest.mock import Mock

import pytest

from src.strategy_lab.backtesting.hft_integration.adapter import HftBacktestAdapter
from src.strategy_lab.backtesting.hft_integration.data_feed import TickData
from src.strategy_lab.backtesting.hft_integration.event_processor import Fill, OrderSide
from src.strategy_lab.strategies.base import SignalType, StrategyConfig
from src.strategy_lab.strategies.examples import MovingAverageCrossoverStrategy


class TestMovingAverageCrossoverStrategy:
    """Test MovingAverageCrossoverStrategy implementation."""

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
        adapter.submit_market_order.return_value = 123
        return adapter

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return StrategyConfig(
            strategy_name="TestMAStrategy",
            max_position_size=5,
            custom_params={
                "short_period": 5,
                "long_period": 10,
                "min_signal_strength": 0.3,
                "position_size": 2,
            },
        )

    @pytest.fixture
    def strategy(self, config, mock_adapter):
        """Create strategy instance for testing."""
        return MovingAverageCrossoverStrategy(config, mock_adapter)

    def test_initialization(self, strategy, config):
        """Test strategy initialization."""
        strategy.initialize()

        assert strategy.short_period == 5
        assert strategy.long_period == 10
        assert strategy.min_signal_strength == 0.3
        assert strategy.position_size == 2
        assert strategy.price_history == []
        assert strategy.short_ma == 0.0
        assert strategy.long_ma == 0.0
        assert strategy.trades_today == 0

        # Check strategy data was populated
        assert strategy.strategy_data["short_period"] == 5
        assert strategy.strategy_data["long_period"] == 10

    def test_initialization_validation(self, config, mock_adapter):
        """Test parameter validation during initialization."""

        # Test short_period >= long_period
        config.custom_params["short_period"] = 15
        config.custom_params["long_period"] = 10
        strategy = MovingAverageCrossoverStrategy(config, mock_adapter)

        with pytest.raises(
            ValueError, match="Short period must be less than long period"
        ):
            strategy.initialize()

        # Test negative periods
        config.custom_params["short_period"] = -5
        config.custom_params["long_period"] = 10
        strategy = MovingAverageCrossoverStrategy(config, mock_adapter)

        with pytest.raises(ValueError, match="Moving average periods must be positive"):
            strategy.initialize()

        # Test invalid signal strength
        config.custom_params["short_period"] = 5
        config.custom_params["long_period"] = 10
        config.custom_params["min_signal_strength"] = 1.5
        strategy = MovingAverageCrossoverStrategy(config, mock_adapter)

        with pytest.raises(
            ValueError, match="Min signal strength must be between 0 and 1"
        ):
            strategy.initialize()

    def test_tick_processing_insufficient_data(self, strategy):
        """Test tick processing with insufficient price history."""
        strategy.initialize()

        # Process a few ticks (less than long_period=10)
        for i in range(5):
            tick = TickData(
                timestamp=1609459200000000000 + i * 1000000000,
                price=13000.0 + i,
                qty=5.0,
                side=1,
            )
            strategy.process_tick(tick)

        # Should have price history but no moving averages calculated
        assert len(strategy.price_history) == 5
        assert strategy.short_ma == 0.0
        assert strategy.long_ma == 0.0

    def test_moving_average_calculation(self, strategy):
        """Test moving average calculation."""
        strategy.initialize()

        # Add enough data for moving averages
        prices = [
            13000.0,
            13001.0,
            13002.0,
            13003.0,
            13004.0,
            13005.0,
            13006.0,
            13007.0,
            13008.0,
            13009.0,
            13010.0,
        ]

        for i, price in enumerate(prices):
            tick = TickData(
                timestamp=1609459200000000000 + i * 1000000000,
                price=price,
                qty=5.0,
                side=1,
            )
            strategy.process_tick(tick)

        # Check moving averages are calculated
        assert strategy.short_ma > 0
        assert strategy.long_ma > 0

        # Short MA should be higher than long MA in uptrend
        assert strategy.short_ma > strategy.long_ma

        # Verify calculations
        expected_short_ma = sum(prices[-5:]) / 5  # Last 5 prices
        expected_long_ma = sum(prices[-10:]) / 10  # Last 10 prices
        assert abs(strategy.short_ma - expected_short_ma) < 0.001
        assert abs(strategy.long_ma - expected_long_ma) < 0.001

    def test_crossover_signal_generation(self, strategy):
        """Test crossover signal generation."""
        strategy.initialize()

        # Create data with crossover pattern
        # First, stable prices for long MA baseline
        stable_prices = [13000.0] * 10
        for i, price in enumerate(stable_prices):
            tick = TickData(
                timestamp=1609459200000000000 + i * 1000000000,
                price=price,
                qty=5.0,
                side=1,
            )
            strategy.process_tick(tick)

        # Add one more tick to establish previous MAs
        tick = TickData(
            timestamp=1609459200000000000 + 10 * 1000000000,
            price=13000.0,
            qty=5.0,
            side=1,
        )
        strategy.process_tick(tick)

        # Now add rising prices to create golden cross
        rising_prices = [13002.0, 13004.0, 13006.0, 13008.0, 13010.0]
        for i, price in enumerate(rising_prices):
            tick = TickData(
                timestamp=1609459200000000000 + (11 + i) * 1000000000,
                price=price,
                qty=5.0,
                side=1,
            )
            strategy.process_tick(tick)

        # Should have generated signals
        assert strategy.current_signal is not None
        # In this uptrend, should eventually get a buy signal when short MA crosses above long MA

    def test_signal_trading_execution(self, strategy, mock_adapter):
        """Test signal execution and order placement."""
        strategy.initialize()

        # Mock position manager methods
        strategy.position_manager.can_enter_long = Mock(return_value=True)
        strategy.position_manager.can_enter_short = Mock(return_value=True)
        strategy.position_manager.get_position_info = Mock()
        strategy.position_manager.get_position_info.return_value.is_flat = True
        strategy.position_manager.get_position_info.return_value.is_long = False
        strategy.position_manager.get_position_info.return_value.is_short = False
        strategy.position_manager.get_position_info.return_value.abs_quantity = 0

        # Create a strong buy signal manually
        tick = TickData(timestamp=1609459200000000000, price=13100.0, qty=5.0, side=1)

        # Set up moving averages to create crossover
        strategy.price_history = [13000.0] * 10 + [13100.0] * 5  # Recent higher prices
        strategy._update_moving_averages()
        strategy.prev_short_ma = 13000.0  # Previous short MA below long MA
        strategy.prev_long_ma = 13050.0
        strategy.short_ma = 13080.0  # Current short MA above long MA
        strategy.long_ma = 13050.0

        # Process tick - should generate and execute buy signal
        strategy.process_tick(tick)

        # Verify order was placed
        if (
            strategy.current_signal
            and strategy.current_signal.signal_type == SignalType.BUY
        ):
            mock_adapter.submit_market_order.assert_called_with(
                OrderSide.BUY, strategy.position_size, tick.timestamp
            )

    def test_should_trade_signal_conditions(self, strategy):
        """Test signal trading validation."""
        strategy.initialize()

        # Mock a signal
        from src.strategy_lab.strategies.base.signal_generator import Signal

        signal = Signal(
            signal_type=SignalType.BUY,
            strength=0.2,  # Below min_signal_strength=0.3
            price=13100.0,
            timestamp=1609459200000000000,
        )

        # Should reject weak signal
        assert strategy._should_trade_signal(signal) is False

        # Test with strong signal
        signal.strength = 0.8

        # Mock position manager to allow entry
        strategy.position_manager.can_enter_long = Mock(return_value=True)

        assert strategy._should_trade_signal(signal) is True

        # Test position manager rejection
        strategy.position_manager.can_enter_long = Mock(return_value=False)
        assert strategy._should_trade_signal(signal) is False

    def test_fill_handling(self, strategy):
        """Test order fill handling."""
        strategy.initialize()

        fill = Fill(
            order_id=123,
            timestamp=1609459200000000000,
            price=13100.0,
            quantity=2,
            side=OrderSide.BUY,
            commission=2.0,
        )

        strategy.on_order_filled(fill)

        assert strategy.trades_today == 1
        assert strategy.strategy_data["last_fill_price"] == 13100.0
        assert strategy.strategy_data["last_fill_side"] == "BUY"
        assert strategy.strategy_data["trades_today"] == 1

    def test_market_open_close_handling(self, strategy):
        """Test market open/close event handling."""
        strategy.initialize()

        # Set some state
        strategy.trades_today = 5
        strategy.current_signal = Mock()
        strategy.last_crossover_timestamp = 1609459200000000000

        # Test market open
        strategy.on_market_open()

        assert strategy.trades_today == 0
        assert strategy.current_signal is None
        assert strategy.last_crossover_timestamp == 0
        assert "market_open_timestamp" in strategy.strategy_data

        # Test market close with open position
        mock_position = Mock()
        mock_position.is_flat = False
        strategy.position_manager.get_position_info = Mock(return_value=mock_position)
        strategy.close_all_positions = Mock()

        strategy.on_market_close()

        strategy.close_all_positions.assert_called_once()
        assert "market_close_timestamp" in strategy.strategy_data

    def test_cleanup(self, strategy):
        """Test strategy cleanup."""
        strategy.initialize()

        # Set some state
        strategy.trades_today = 3
        mock_position = Mock()
        mock_position.is_flat = False
        mock_position.realized_pnl = 150.0
        strategy.position_manager.get_position_info = Mock(return_value=mock_position)
        strategy.position_manager.get_risk_metrics = Mock(
            return_value={"max_drawdown": 50.0, "current_drawdown": 25.0}
        )
        strategy.close_all_positions = Mock()

        strategy.cleanup()

        strategy.close_all_positions.assert_called_once()
        assert "cleanup_timestamp" in strategy.strategy_data
        assert strategy.strategy_data["final_pnl"] == 150.0
        assert strategy.strategy_data["total_trades"] == 3

    def test_risk_management_checks(self, strategy):
        """Test risk management trigger checks."""
        strategy.initialize()

        # Mock position manager methods
        strategy.position_manager.should_stop_out = Mock(return_value=True)
        strategy.close_all_positions = Mock()

        strategy._check_risk_management()

        # Should close positions on stop out
        strategy.close_all_positions.assert_called_once()

        # Reset and test take profit
        strategy.close_all_positions.reset_mock()
        strategy.position_manager.should_stop_out = Mock(return_value=False)
        strategy.position_manager.should_take_profit = Mock(return_value=True)

        strategy._check_risk_management()

        # Should close positions on take profit
        strategy.close_all_positions.assert_called_once()

    def test_get_strategy_info(self, strategy):
        """Test comprehensive strategy info retrieval."""
        strategy.initialize()

        # Set up some state
        strategy.short_ma = 13050.0
        strategy.long_ma = 13040.0
        strategy.trades_today = 2
        strategy.last_tick = TickData(
            timestamp=1609459200000000000, price=13055.0, qty=5.0, side=1
        )

        # Mock current signal
        from src.strategy_lab.strategies.base.signal_generator import Signal

        strategy.current_signal = Signal(
            signal_type=SignalType.BUY,
            strength=0.7,
            price=13055.0,
            timestamp=1609459200000000000,
        )

        # Mock position and metrics
        mock_position = Mock()
        mock_position.side.value = "long"
        mock_position.quantity = 2
        mock_position.realized_pnl = 100.0
        mock_position.net_pnl = 150.0
        strategy.position_manager.get_position_info = Mock(return_value=mock_position)
        strategy.position_manager.get_risk_metrics = Mock(
            return_value={"max_drawdown": 25.0}
        )

        info = strategy.get_strategy_info()

        assert info["strategy_name"] == "TestMAStrategy"
        assert info["strategy_type"] == "moving_average_crossover"
        assert info["parameters"]["short_period"] == 5
        assert info["parameters"]["long_period"] == 10
        assert info["current_state"]["short_ma"] == 13050.0
        assert info["current_state"]["long_ma"] == 13040.0
        assert info["current_state"]["current_signal"] == "buy"
        assert info["current_state"]["signal_strength"] == 0.7
        assert info["performance"]["trades_today"] == 2
        assert "position" in info
        assert "risk_metrics" in info

    def test_default_parameters(self, mock_adapter):
        """Test strategy with default parameters."""
        config = StrategyConfig(strategy_name="DefaultTest")
        strategy = MovingAverageCrossoverStrategy(config, mock_adapter)
        strategy.initialize()

        # Should use default values
        assert strategy.short_period == 10
        assert strategy.long_period == 20
        assert strategy.min_signal_strength == 0.3
        assert strategy.position_size == 1

    def test_price_history_management(self, strategy):
        """Test price history buffer management."""
        strategy.initialize()

        # Add many ticks to test buffer limit
        for i in range(100):
            tick = TickData(
                timestamp=1609459200000000000 + i * 1000000000,
                price=13000.0 + i * 0.1,
                qty=5.0,
                side=1,
            )
            strategy.process_tick(tick)

        # Should keep only required history (long_period + buffer = 20 + 5 = 25)
        max_expected = strategy.long_period + 5
        assert len(strategy.price_history) <= max_expected

        # Should contain most recent prices
        assert strategy.price_history[-1] == 13000.0 + 99 * 0.1

    def test_rapid_signal_filtering(self, strategy):
        """Test filtering of rapid-fire signals."""
        strategy.initialize()

        # Mock signal generation
        from src.strategy_lab.strategies.base.signal_generator import Signal

        signal = Signal(
            signal_type=SignalType.BUY,
            strength=0.8,
            price=13100.0,
            timestamp=1609459200000000000,
        )

        # First signal should be allowed
        strategy.last_crossover_timestamp = 0
        assert strategy._should_trade_signal(signal) is True

        # Signal too soon after last one should be rejected
        strategy.last_crossover_timestamp = (
            signal.timestamp - 30_000_000_000
        )  # 30 seconds ago
        assert strategy._should_trade_signal(signal) is False

        # Signal after sufficient time should be allowed
        strategy.last_crossover_timestamp = (
            signal.timestamp - 120_000_000_000
        )  # 2 minutes ago
        strategy.position_manager.can_enter_long = Mock(return_value=True)
        assert strategy._should_trade_signal(signal) is True
