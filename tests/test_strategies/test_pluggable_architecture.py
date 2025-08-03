"""Tests for pluggable strategy architecture."""


import pandas as pd
import pytest

from strategy_lab.strategies.base.pluggable_strategy import PluggableStrategy
from strategy_lab.strategies.factory import StrategyFactory
from strategy_lab.strategies.protocol import StrategyMetadata, StrategyProtocol
from strategy_lab.strategies.registry import (
    StrategyRegistry,
    register_strategy,
    registry,
)


class MockTestStrategy(PluggableStrategy):
    """Test strategy for unit tests."""

    name = "TestStrategy"
    version = "1.0.0"
    description = "Test strategy"

    def _initialize_strategy(self) -> None:
        """Initialize test strategy."""
        self.threshold = self._parameters.get("threshold", 100.0)
        self.signal_count = 0

    def _generate_signal(
        self,
        timestamp: pd.Timestamp,
        price: float,
        volume: int,
        bid: float,
        ask: float,
        **kwargs,
    ) -> int | None:
        """Generate test signals."""
        if price > self.threshold:
            self.signal_count += 1
            return 1
        if price < self.threshold * 0.9:
            self.signal_count += 1
            return -1
        return None


class TestStrategyProtocol:
    """Test the strategy protocol interface."""

    def test_protocol_implementation(self):
        """Test that MockTestStrategy implements StrategyProtocol."""
        assert isinstance(MockTestStrategy, type)

        # Check required methods
        required_methods = ["initialize", "process_tick", "cleanup"]
        for method in required_methods:
            assert hasattr(MockTestStrategy, method)

        # Check properties
        assert hasattr(MockTestStrategy, "name")
        assert hasattr(MockTestStrategy, "version")
        assert hasattr(MockTestStrategy, "description")

    def test_protocol_runtime_check(self):
        """Test runtime protocol checking."""
        strategy = MockTestStrategy()
        assert isinstance(strategy, StrategyProtocol)


class TestStrategyRegistry:
    """Test the strategy registry functionality."""

    def setup_method(self):
        """Setup for each test."""
        # Clear registry
        self.registry = StrategyRegistry()
        self.registry._strategies.clear()
        self.registry._metadata.clear()

    def test_singleton_pattern(self):
        """Test registry is a singleton."""
        registry1 = StrategyRegistry()
        registry2 = StrategyRegistry()
        assert registry1 is registry2

    def test_register_strategy(self):
        """Test registering a strategy."""
        self.registry.register(MockTestStrategy)

        assert "TestStrategy" in self.registry.list_strategies()
        assert self.registry.get_strategy("TestStrategy") == MockTestStrategy

    def test_register_with_metadata(self):
        """Test registering with custom metadata."""
        metadata = StrategyMetadata(
            name="CustomTest",
            version="2.0.0",
            description="Custom test strategy",
            tags=["test", "example"],
        )

        self.registry.register(MockTestStrategy, metadata)

        retrieved_meta = self.registry.get_metadata("CustomTest")
        assert retrieved_meta.version == "2.0.0"
        assert "test" in retrieved_meta.tags

    def test_unregister_strategy(self):
        """Test unregistering a strategy."""
        self.registry.register(MockTestStrategy)
        assert "TestStrategy" in self.registry.list_strategies()

        self.registry.unregister("TestStrategy")
        assert "TestStrategy" not in self.registry.list_strategies()

    def test_create_strategy(self):
        """Test creating strategy instance through registry."""
        self.registry.register(MockTestStrategy)

        strategy = self.registry.create_strategy("TestStrategy", threshold=150.0)

        assert isinstance(strategy, MockTestStrategy)
        assert strategy.parameters["threshold"] == 150.0

    def test_get_strategies_by_tag(self):
        """Test filtering strategies by tag."""
        metadata1 = StrategyMetadata(
            name="Strategy1",
            version="1.0.0",
            description="Test",
            tags=["trend", "momentum"],
        )
        metadata2 = StrategyMetadata(
            name="Strategy2",
            version="1.0.0",
            description="Test",
            tags=["mean-reversion", "statistical"],
        )

        self.registry.register(MockTestStrategy, metadata1)
        self.registry.register(MockTestStrategy, metadata2)

        trend_strategies = self.registry.get_strategies_by_tag("trend")
        assert "Strategy1" in trend_strategies
        assert "Strategy2" not in trend_strategies

    def test_validate_strategy(self):
        """Test strategy validation."""
        self.registry.register(MockTestStrategy)

        results = self.registry.validate_strategy("TestStrategy")
        assert results["valid"]
        assert len(results["errors"]) == 0

    def test_decorator_registration(self):
        """Test decorator-based registration."""

        @register_strategy
        class DecoratedStrategy(MockTestStrategy):
            name = "DecoratedStrategy"

        # Use global registry instance
        assert "DecoratedStrategy" in registry.list_strategies()

    def test_decorator_with_metadata(self):
        """Test decorator with metadata."""
        metadata = StrategyMetadata(
            name="MetaDecoratedStrategy",
            version="3.0.0",
            description="Decorated with metadata",
            tags=["decorated"],
        )

        @register_strategy(metadata)
        class MetaDecoratedStrategy(MockTestStrategy):
            pass

        # Use global registry instance
        meta = registry.get_metadata("MetaDecoratedStrategy")
        assert meta.version == "3.0.0"
        assert "decorated" in meta.tags


class TestStrategyFactory:
    """Test the strategy factory functionality."""

    def setup_method(self):
        """Setup for each test."""
        # Register test strategy
        registry.register(MockTestStrategy)

        # Create new factory
        self.factory = StrategyFactory()

    def test_create_strategy(self):
        """Test creating strategy through factory."""
        strategy = self.factory.create_strategy(
            "TestStrategy", "test_instance", threshold=200.0
        )

        assert isinstance(strategy, MockTestStrategy)
        assert self.factory.get_strategy("test_instance") == strategy
        assert strategy._initialized

    def test_list_active_strategies(self):
        """Test listing active strategies."""
        self.factory.create_strategy("TestStrategy", "instance1")
        self.factory.create_strategy("TestStrategy", "instance2")

        active = self.factory.list_active_strategies()
        assert len(active) == 2
        assert active["instance1"] == "TestStrategy"
        assert active["instance2"] == "TestStrategy"

    def test_hot_swap_strategy(self):
        """Test hot-swapping strategies."""
        # Create initial strategy
        strategy1 = self.factory.create_strategy(
            "TestStrategy", "swap_test", threshold=100.0
        )

        # Process some ticks to build state
        for i in range(5):
            strategy1.process_tick(
                pd.Timestamp.now(), float(95 + i * 2), 100, 95.0, 96.0
            )

        initial_tick_count = strategy1._tick_count

        # Hot swap to new strategy
        strategy2 = self.factory.hot_swap_strategy(
            "swap_test", "TestStrategy", preserve_state=True, threshold=110.0
        )

        assert isinstance(strategy2, MockTestStrategy)
        assert strategy2.parameters["threshold"] == 110.0
        assert self.factory.get_strategy("swap_test") == strategy2

    def test_hot_swap_without_state(self):
        """Test hot-swapping without preserving state."""
        # Create and use initial strategy
        strategy1 = self.factory.create_strategy("TestStrategy", "no_state_test")
        strategy1.process_tick(pd.Timestamp.now(), 105.0, 100, 104.0, 106.0)

        # Hot swap without state
        strategy2 = self.factory.hot_swap_strategy(
            "no_state_test", "TestStrategy", preserve_state=False
        )

        assert strategy2._tick_count == 0  # State not preserved

    def test_remove_strategy(self):
        """Test removing a strategy."""
        self.factory.create_strategy("TestStrategy", "remove_test")
        assert "remove_test" in self.factory.list_active_strategies()

        self.factory.remove_strategy("remove_test")
        assert "remove_test" not in self.factory.list_active_strategies()
        assert self.factory.get_strategy("remove_test") is None

    def test_save_all_states(self):
        """Test saving states of all strategies."""
        # Create multiple strategies
        strategy1 = self.factory.create_strategy("TestStrategy", "save1")
        strategy2 = self.factory.create_strategy("TestStrategy", "save2")

        # Process some ticks
        strategy1.process_tick(pd.Timestamp.now(), 105.0, 100, 104.0, 106.0)
        strategy2.process_tick(pd.Timestamp.now(), 95.0, 100, 94.0, 96.0)

        # Save all states
        states = self.factory.save_all_states()

        assert len(states) == 2
        assert "save1" in states
        assert "save2" in states
        assert states["save1"]["tick_count"] == 1
        assert states["save2"]["tick_count"] == 1

    def test_cleanup_all(self):
        """Test cleaning up all strategies."""
        self.factory.create_strategy("TestStrategy", "cleanup1")
        self.factory.create_strategy("TestStrategy", "cleanup2")

        assert len(self.factory.list_active_strategies()) == 2

        self.factory.cleanup_all()

        assert len(self.factory.list_active_strategies()) == 0

    def test_clone_strategy(self):
        """Test cloning a strategy."""
        # Create original
        original = self.factory.create_strategy(
            "TestStrategy", "original", threshold=125.0
        )

        # Process some ticks
        original.process_tick(pd.Timestamp.now(), 130.0, 100, 129.0, 131.0)

        # Clone
        clone = self.factory.clone_strategy("original", "clone")

        assert isinstance(clone, MockTestStrategy)
        assert clone.parameters["threshold"] == 125.0
        assert clone._tick_count == original._tick_count


class TestPluggableStrategy:
    """Test the PluggableStrategy base class."""

    def test_initialization(self):
        """Test strategy initialization."""
        strategy = MockTestStrategy(threshold=150.0)

        assert strategy.name == "TestStrategy"
        assert strategy.version == "1.0.0"
        assert strategy.parameters["threshold"] == 150.0
        assert not strategy._initialized

        strategy.initialize()
        assert strategy._initialized
        assert strategy.threshold == 150.0

    def test_process_tick(self):
        """Test tick processing."""
        strategy = MockTestStrategy()
        strategy.initialize()

        # Generate buy signal
        signal = strategy.process_tick(
            pd.Timestamp.now(), 105.0, 100, 104.0, 106.0  # Above threshold
        )

        assert signal == 1
        assert strategy._tick_count == 1
        assert len(strategy._price_history) == 1

    def test_data_buffers(self):
        """Test data buffer management."""
        strategy = MockTestStrategy(max_buffer_size=5)
        strategy.initialize()

        # Fill buffer beyond limit
        for i in range(10):
            strategy.process_tick(
                pd.Timestamp.now(), 100.0 + i, 100 + i, 99.0 + i, 101.0 + i
            )

        assert len(strategy._price_history) == 5  # Limited by buffer size
        assert strategy._price_history[-1] == 109.0  # Most recent price

    def test_get_price_series(self):
        """Test getting price series."""
        strategy = MockTestStrategy()
        strategy.initialize()

        # Add some data
        base_time = pd.Timestamp.now()
        for i in range(5):
            strategy.process_tick(
                base_time + pd.Timedelta(minutes=i), 100.0 + i, 100, 99.0, 101.0
            )

        # Get full series
        prices = strategy.get_price_series()
        assert len(prices) == 5
        assert prices.iloc[-1] == 104.0

        # Get with lookback
        recent_prices = strategy.get_price_series(lookback=3)
        assert len(recent_prices) == 3
        assert recent_prices.iloc[0] == 102.0

    def test_state_management(self):
        """Test state save and restore."""
        strategy1 = MockTestStrategy(threshold=175.0)
        strategy1.initialize()

        # Process some ticks
        for i in range(3):
            strategy1.process_tick(
                pd.Timestamp.now(), 170.0 + i * 10, 100, 169.0, 171.0
            )

        # Save state
        state = strategy1.get_state()

        assert state["tick_count"] == 3
        assert state["parameters"]["threshold"] == 175.0

        # Create new strategy and restore state
        strategy2 = MockTestStrategy()
        strategy2.set_state(state)

        assert strategy2._tick_count == 3
        assert strategy2._parameters["threshold"] == 175.0

    def test_cleanup(self):
        """Test strategy cleanup."""
        strategy = MockTestStrategy()
        strategy.initialize()

        strategy.process_tick(pd.Timestamp.now(), 105.0, 100, 104.0, 106.0)
        assert strategy._initialized

        strategy.cleanup()
        assert not strategy._initialized
        assert strategy._state_data["tick_count"] == 1


class TestStrategyIsolation:
    """Test strategy isolation and error handling."""

    def test_strategy_isolation(self):
        """Test that strategies are isolated from each other."""
        factory = StrategyFactory()

        # Create two strategies
        strategy1 = factory.create_strategy("TestStrategy", "iso1", threshold=100.0)
        strategy2 = factory.create_strategy("TestStrategy", "iso2", threshold=200.0)

        # Modify one strategy's state
        strategy1.process_tick(pd.Timestamp.now(), 150.0, 100, 149.0, 151.0)

        # Check other strategy is unaffected
        assert strategy1._tick_count == 1
        assert strategy2._tick_count == 0
        assert strategy1.parameters["threshold"] == 100.0
        assert strategy2.parameters["threshold"] == 200.0

    def test_error_containment(self):
        """Test that errors in one strategy don't affect others."""

        class ErrorStrategy(MockTestStrategy):
            name = "ErrorStrategy"

            def _generate_signal(self, *args, **kwargs):
                if self._tick_count > 2:
                    raise ValueError("Test error")
                return super()._generate_signal(*args, **kwargs)

        registry.register(ErrorStrategy)
        factory = StrategyFactory()

        # Create strategies
        good_strategy = factory.create_strategy("TestStrategy", "good")
        bad_strategy = factory.create_strategy("ErrorStrategy", "bad")

        # Process ticks on good strategy
        good_strategy.process_tick(pd.Timestamp.now(), 105.0, 100, 104.0, 106.0)

        # Process ticks on bad strategy (will error after 2 ticks)
        bad_strategy.process_tick(pd.Timestamp.now(), 105.0, 100, 104.0, 106.0)
        bad_strategy.process_tick(pd.Timestamp.now(), 105.0, 100, 104.0, 106.0)

        # This should raise error
        with pytest.raises(ValueError):
            bad_strategy.process_tick(pd.Timestamp.now(), 105.0, 100, 104.0, 106.0)

        # Good strategy should still work
        signal = good_strategy.process_tick(
            pd.Timestamp.now(), 105.0, 100, 104.0, 106.0
        )
        assert signal == 1  # Still generates signals
