"""Tests for backtest execution."""

from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from strategy_lab.backtesting.engine.config import (
    BacktestConfig,
    DataConfig,
    ExecutionConfig,
    StrategyConfig,
)
from strategy_lab.backtesting.engine.execution import (
    BacktestExecutor,
    ExecutionContext,
    execute_backtest_parallel,
)
from strategy_lab.backtesting.engine.portfolio import Portfolio, PositionSide
from strategy_lab.backtesting.metrics import MetricsAggregator


class MockStrategy:
    """Mock strategy for testing."""

    def __init__(self, test_param: str = "default"):
        self.test_param = test_param
        self.initialized = False
        self.tick_count = 0

    def initialize(self):
        """Initialize strategy."""
        self.initialized = True

    def process_tick(self, timestamp, price, volume, bid, ask):
        """Process a single tick."""
        self.tick_count += 1

        # Simple test strategy: buy at tick 0, sell at tick 5
        if self.tick_count == 1:
            return 1  # Buy signal
        if self.tick_count == 5:
            return -1  # Sell signal
        if self.tick_count == 8:
            return 0  # Flat signal
        return 0  # No signal

    def cleanup(self):
        """Cleanup strategy."""


class TestExecutionContext:
    """Test ExecutionContext functionality."""

    def test_context_creation(self):
        """Test creating execution context."""
        config = BacktestConfig(
            name="test",
            strategy=StrategyConfig(name="test", module="test.module"),
            data=DataConfig(data_path=Path()),
            execution=ExecutionConfig(),
        )

        portfolio = Portfolio(initial_capital=Decimal("10000"))
        metrics = MetricsAggregator()
        strategy = MockStrategy()
        data_loader = MagicMock()

        context = ExecutionContext(
            config=config,
            portfolio=portfolio,
            metrics=metrics,
            strategy=strategy,
            data_loader=data_loader,
        )

        assert context.config == config
        assert context.portfolio == portfolio
        assert context.metrics == metrics
        assert context.strategy == strategy
        assert context.total_ticks == 0
        assert context.processed_ticks == 0

    def test_progress_tracking(self):
        """Test progress tracking functionality."""
        config = BacktestConfig(
            name="test",
            strategy=StrategyConfig(name="test", module="test.module"),
            data=DataConfig(data_path=Path()),
            execution=ExecutionConfig(),
        )

        context = ExecutionContext(
            config=config,
            portfolio=MagicMock(),
            metrics=MagicMock(),
            strategy=MagicMock(),
            data_loader=MagicMock(),
        )

        context.total_ticks = 100
        context.processed_ticks = 25

        assert context.progress_percent == 25.0

        # Update progress
        with patch("psutil.Process") as mock_process:
            mock_proc_inst = MagicMock()
            mock_proc_inst.memory_info.return_value.rss = 100 * 1024 * 1024  # 100 MB
            mock_proc_inst.cpu_percent.return_value = 50.0
            mock_process.return_value = mock_proc_inst

            context.update_progress()

        assert context.processed_ticks == 26
        assert context.peak_memory_mb == 100.0
        assert len(context.cpu_samples) == 1
        assert context.avg_cpu_percent == 50.0

    def test_eta_calculation(self):
        """Test ETA calculation."""
        config = BacktestConfig(
            name="test",
            strategy=StrategyConfig(name="test", module="test.module"),
            data=DataConfig(data_path=Path()),
            execution=ExecutionConfig(),
        )

        context = ExecutionContext(
            config=config,
            portfolio=MagicMock(),
            metrics=MagicMock(),
            strategy=MagicMock(),
            data_loader=MagicMock(),
        )

        # No progress yet
        assert context.eta_seconds == 0.0

        # Simulate some progress
        context.total_ticks = 1000
        context.processed_ticks = 100
        context.start_time -= 10  # 10 seconds ago

        # Should estimate ~90 seconds remaining
        eta = context.eta_seconds
        assert 85 < eta < 95  # Allow some variance


class TestBacktestExecutor:
    """Test BacktestExecutor functionality."""

    @pytest.fixture
    def test_config(self, tmp_path):
        """Create test configuration."""
        # Create test data directory
        data_path = tmp_path / "data"
        data_path.mkdir()

        return BacktestConfig(
            name="test_backtest",
            strategy=StrategyConfig(
                name="MockStrategy",
                module="tests.unit.test_backtesting.test_engine.test_execution",
                parameters={"test_param": "test_value"},
            ),
            data=DataConfig(data_path=data_path),
            execution=ExecutionConfig(
                initial_capital=Decimal("10000"),
                commission=Decimal("1.0"),
                slippage=Decimal("0.1"),
            ),
            output_dir=tmp_path / "results",
        )

    def test_executor_initialization(self, test_config):
        """Test executor initialization."""
        executor = BacktestExecutor(test_config)
        assert executor.config == test_config
        assert executor.context is None

    @patch("strategy_lab.backtesting.engine.execution.DataLoader")
    def test_load_strategy(self, mock_data_loader, test_config):
        """Test strategy loading."""
        executor = BacktestExecutor(test_config)

        # Mock data loader
        mock_loader_inst = MagicMock()
        mock_data_loader.return_value = mock_loader_inst

        # Initialize context manually for testing
        executor._initialize_context()

        # Check strategy was loaded correctly
        assert executor.context.strategy.__class__.__name__ == "MockStrategy"
        assert executor.context.strategy.test_param == "test_value"

    @patch("strategy_lab.backtesting.engine.execution.DataLoader")
    def test_execute_signal_buy(self, mock_data_loader, test_config):
        """Test executing buy signal."""
        executor = BacktestExecutor(test_config)

        # Initialize context
        mock_loader_inst = MagicMock()
        mock_data_loader.return_value = mock_loader_inst
        executor._initialize_context()

        # Execute buy signal
        executor._execute_signal(
            signal=1, price=Decimal("100.0"), timestamp=pd.Timestamp("2024-01-01")
        )

        # Check position was opened
        assert executor.context.portfolio.has_position("MNQ")
        position = executor.context.portfolio.get_position("MNQ")
        assert position.side == PositionSide.LONG
        assert position.entry_price == Decimal("100.0")

    @patch("strategy_lab.backtesting.engine.execution.DataLoader")
    def test_execute_signal_sell(self, mock_data_loader, test_config):
        """Test executing sell signal."""
        executor = BacktestExecutor(test_config)

        # Initialize context
        mock_loader_inst = MagicMock()
        mock_data_loader.return_value = mock_loader_inst
        executor._initialize_context()

        # Execute sell signal
        executor._execute_signal(
            signal=-1, price=Decimal("100.0"), timestamp=pd.Timestamp("2024-01-01")
        )

        # Check position was opened
        assert executor.context.portfolio.has_position("MNQ")
        position = executor.context.portfolio.get_position("MNQ")
        assert position.side == PositionSide.SHORT
        assert position.entry_price == Decimal("100.0")

    @patch("strategy_lab.backtesting.engine.execution.DataLoader")
    def test_execute_signal_close(self, mock_data_loader, test_config):
        """Test executing close signal."""
        executor = BacktestExecutor(test_config)

        # Initialize context
        mock_loader_inst = MagicMock()
        mock_data_loader.return_value = mock_loader_inst
        executor._initialize_context()

        # Open a position first
        executor._execute_signal(
            signal=1, price=Decimal("100.0"), timestamp=pd.Timestamp("2024-01-01")
        )

        # Execute flat signal
        executor._execute_signal(
            signal=0, price=Decimal("105.0"), timestamp=pd.Timestamp("2024-01-02")
        )

        # Check position was closed
        assert not executor.context.portfolio.has_position("MNQ")
        assert len(executor.context.portfolio.closed_positions) == 1

    @patch("strategy_lab.backtesting.engine.execution.DataLoader")
    def test_resource_limit_checking(self, mock_data_loader, test_config):
        """Test resource limit enforcement."""
        # Set low memory limit
        test_config.execution.max_memory_gb = 0.0001  # Very low limit
        executor = BacktestExecutor(test_config)

        # Initialize context
        mock_loader_inst = MagicMock()
        mock_data_loader.return_value = mock_loader_inst
        executor._initialize_context()

        # Should raise memory error
        with pytest.raises(MemoryError, match="Memory limit exceeded"):
            executor._check_resource_limits()

    @patch("strategy_lab.backtesting.engine.execution.DataLoader")
    def test_full_backtest_execution(self, mock_data_loader, test_config):
        """Test full backtest execution."""
        executor = BacktestExecutor(test_config)

        # Create test data
        test_data = pd.DataFrame(
            {
                "price": [
                    100.0,
                    101.0,
                    102.0,
                    103.0,
                    104.0,
                    105.0,
                    104.0,
                    103.0,
                    102.0,
                    101.0,
                ],
                "volume": [100] * 10,
                "bid": [
                    99.9,
                    100.9,
                    101.9,
                    102.9,
                    103.9,
                    104.9,
                    103.9,
                    102.9,
                    101.9,
                    100.9,
                ],
                "ask": [
                    100.1,
                    101.1,
                    102.1,
                    103.1,
                    104.1,
                    105.1,
                    104.1,
                    103.1,
                    102.1,
                    101.1,
                ],
            },
            index=pd.date_range("2024-01-01", periods=10, freq="min"),
        )

        # Mock data loader
        mock_loader_inst = MagicMock()
        mock_loader_inst.load_data.return_value = test_data
        mock_data_loader.return_value = mock_loader_inst

        # Execute backtest
        result = executor.execute()

        # Verify results
        assert result is not None
        assert result.config == test_config
        assert result.total_ticks == 10
        assert result.total_trades > 0
        assert result.execution_time > 0
        assert len(result.equity_curve) > 0


def test_parallel_execution():
    """Test parallel backtest execution."""
    # Create test configs
    configs = []
    for i in range(3):
        config = BacktestConfig(
            name=f"test_{i}",
            strategy=StrategyConfig(
                name="MockStrategy",
                module="tests.unit.test_backtesting.test_engine.test_execution",
            ),
            data=DataConfig(data_path=Path()),
            execution=ExecutionConfig(),
        )
        configs.append(config)

    # Mock at the pool level to avoid pickling issues
    with patch("multiprocessing.Pool") as mock_pool:
        mock_pool_inst = MagicMock()
        mock_results = [MagicMock() for _ in range(3)]
        mock_pool_inst.map.return_value = mock_results
        mock_pool.return_value.__enter__.return_value = mock_pool_inst

        results = execute_backtest_parallel(configs, max_workers=2)

        assert len(results) == 3
        assert mock_pool_inst.map.call_count == 1
        assert mock_pool.call_args[1]["processes"] == 2
