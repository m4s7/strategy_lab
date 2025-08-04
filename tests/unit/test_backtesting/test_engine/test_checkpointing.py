"""Tests for checkpointing functionality."""

import tempfile
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock

import pandas as pd
import pytest

from strategy_lab.backtesting.engine.config import (
    BacktestConfig,
    DataConfig,
    ExecutionConfig,
    StrategyConfig,
)
from strategy_lab.backtesting.engine.execution_enhanced import (
    EnhancedBacktestExecutor,
    EnhancedExecutionContext,
)
from strategy_lab.backtesting.engine.portfolio import Portfolio, PositionSide
from strategy_lab.backtesting.metrics.realtime import MetricsAggregator


class MockStrategy:
    """Mock strategy for testing."""

    name = "MockStrategy"

    def __init__(self, **kwargs):
        self.parameters = kwargs
        self.initialized = False

    def initialize(self):
        self.initialized = True

    def process_tick(self, **kwargs):
        return 0  # Flat signal

    def cleanup(self):
        self.initialized = False


class TestCheckpointing:
    """Test checkpointing functionality."""

    def create_test_config(self, data_path: Path) -> BacktestConfig:
        """Create test backtest configuration."""
        return BacktestConfig(
            name="test_checkpointing",
            strategy=StrategyConfig(
                name="MockStrategy", module="test.module", parameters={}
            ),
            data=DataConfig(
                symbol="MNQ",
                data_path=data_path,
                contracts=["03-24"],
                chunk_size=100,
                memory_limit_mb=500,
                validate_data=False,
            ),
            execution=ExecutionConfig(
                initial_capital=Decimal("100000"),
                commission=Decimal("2.00"),
                slippage=Decimal("0.25"),
            ),
        )

    def test_checkpoint_creation_basic(self):
        """Test basic checkpoint creation."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config = self.create_test_config(Path(tmp_dir))
            checkpoint_dir = Path(tmp_dir) / "checkpoints"

            # Create context
            portfolio = Portfolio(initial_capital=Decimal("100000"))
            metrics = MetricsAggregator(starting_equity=Decimal("100000"))
            mock_strategy = MockStrategy()
            mock_data_provider = MagicMock()

            context = EnhancedExecutionContext(
                config=config,
                portfolio=portfolio,
                metrics=metrics,
                strategy=mock_strategy,
                data_provider=mock_data_provider,
            )
            context.checkpoint_dir = checkpoint_dir
            context.processed_ticks = 5000

            # Create checkpoint
            checkpoint_path = context.create_checkpoint()

            # Verify checkpoint file was created
            assert Path(checkpoint_path).exists()
            assert checkpoint_path.startswith(str(checkpoint_dir))
            assert "checkpoint_5000_" in checkpoint_path

    def test_checkpoint_should_create_logic(self):
        """Test logic for when checkpoints should be created."""
        config = self.create_test_config(Path("/tmp"))
        portfolio = Portfolio(initial_capital=Decimal("100000"))
        metrics = MetricsAggregator(starting_equity=Decimal("100000"))
        mock_strategy = MockStrategy()
        mock_data_provider = MagicMock()

        context = EnhancedExecutionContext(
            config=config,
            portfolio=portfolio,
            metrics=metrics,
            strategy=mock_strategy,
            data_provider=mock_data_provider,
        )

        # No checkpoint directory - should not create
        assert not context.should_create_checkpoint()

        # Set checkpoint directory
        context.checkpoint_dir = Path("/tmp/checkpoints")

        # Not enough ticks processed - should not create
        context.processed_ticks = 5000
        context.last_checkpoint_tick = 0
        context.checkpoint_interval = 10000
        assert not context.should_create_checkpoint()

        # Enough ticks processed - should create
        context.processed_ticks = 10000
        assert context.should_create_checkpoint()

        # After checkpoint created
        context.last_checkpoint_tick = 10000
        context.processed_ticks = 15000
        assert not context.should_create_checkpoint()

        # Next checkpoint interval
        context.processed_ticks = 20000
        assert context.should_create_checkpoint()

    def test_portfolio_serialization(self):
        """Test portfolio state serialization for checkpointing."""
        config = self.create_test_config(Path("/tmp"))
        portfolio = Portfolio(initial_capital=Decimal("100000"))
        metrics = MetricsAggregator(starting_equity=Decimal("100000"))
        mock_strategy = MockStrategy()
        mock_data_provider = MagicMock()

        context = EnhancedExecutionContext(
            config=config,
            portfolio=portfolio,
            metrics=metrics,
            strategy=mock_strategy,
            data_provider=mock_data_provider,
        )

        # Add some positions and equity history
        timestamp = pd.Timestamp.now()
        portfolio.open_position(
            symbol="MNQ",
            side=PositionSide.LONG,
            quantity=1,
            price=Decimal("4000"),
            timestamp=timestamp,
            stop_loss_price=Decimal("3950"),
            take_profit_price=Decimal("4100"),
        )

        # Serialize portfolio
        portfolio_state = context._serialize_portfolio()

        # Verify serialization
        assert "cash" in portfolio_state
        assert "positions" in portfolio_state
        assert "equity_curve" in portfolio_state
        assert "peak_equity" in portfolio_state
        assert "current_drawdown" in portfolio_state
        assert "max_drawdown" in portfolio_state

        # Check position data
        assert len(portfolio_state["positions"]) == 1
        position_data = portfolio_state["positions"][0]
        assert position_data["symbol"] == "MNQ"
        assert position_data["side"] == "LONG"
        assert position_data["quantity"] == 1
        assert position_data["entry_price"] == 4000.0
        assert position_data["stop_loss_price"] == 3950.0
        assert position_data["take_profit_price"] == 4100.0

    def test_strategy_serialization(self):
        """Test strategy state serialization."""
        config = self.create_test_config(Path("/tmp"))
        portfolio = Portfolio(initial_capital=Decimal("100000"))
        metrics = MetricsAggregator(starting_equity=Decimal("100000"))
        mock_strategy = MockStrategy(param1="value1", param2=42)
        mock_data_provider = MagicMock()

        context = EnhancedExecutionContext(
            config=config,
            portfolio=portfolio,
            metrics=metrics,
            strategy=mock_strategy,
            data_provider=mock_data_provider,
        )

        # Serialize strategy
        strategy_state = context._serialize_strategy_state()

        # Verify serialization
        assert "class_name" in strategy_state
        assert "parameters" in strategy_state
        assert strategy_state["class_name"] == "MockStrategy"
        assert strategy_state["parameters"]["param1"] == "value1"
        assert strategy_state["parameters"]["param2"] == 42

    def test_executor_initialization_with_checkpointing(self):
        """Test executor initialization with checkpoint directory."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config = self.create_test_config(Path(tmp_dir))
            checkpoint_dir = Path(tmp_dir) / "checkpoints"

            executor = EnhancedBacktestExecutor(config, checkpoint_dir)

            assert executor.checkpoint_dir == checkpoint_dir
            assert executor.config == config

    def test_load_from_checkpoint_file_not_found(self):
        """Test loading from non-existent checkpoint file."""
        config = self.create_test_config(Path("/tmp"))

        with pytest.raises(FileNotFoundError):
            EnhancedBacktestExecutor.load_from_checkpoint(
                Path("/nonexistent/checkpoint.pkl"), config
            )

    def test_checkpoint_data_structure(self):
        """Test the structure of checkpoint data."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config = self.create_test_config(Path(tmp_dir))
            checkpoint_dir = Path(tmp_dir) / "checkpoints"

            # Create context with some state
            portfolio = Portfolio(initial_capital=Decimal("100000"))
            metrics = MetricsAggregator(starting_equity=Decimal("100000"))
            mock_strategy = MockStrategy()
            mock_data_provider = MagicMock()

            context = EnhancedExecutionContext(
                config=config,
                portfolio=portfolio,
                metrics=metrics,
                strategy=mock_strategy,
                data_provider=mock_data_provider,
            )
            context.checkpoint_dir = checkpoint_dir
            context.processed_ticks = 15000
            context.max_observed_drawdown = 0.05
            context.position_violations = 2
            context.signal_validation_errors = 1

            # Create checkpoint
            checkpoint_path = context.create_checkpoint()

            # Load and verify checkpoint data structure
            import pickle

            with open(checkpoint_path, "rb") as f:
                checkpoint_data = pickle.load(f)

            # Verify required fields
            assert "processed_ticks" in checkpoint_data
            assert "portfolio_state" in checkpoint_data
            assert "risk_metrics" in checkpoint_data
            assert "strategy_state" in checkpoint_data
            assert "timestamp" in checkpoint_data

            # Verify values
            assert checkpoint_data["processed_ticks"] == 15000

            risk_metrics = checkpoint_data["risk_metrics"]
            assert risk_metrics["max_observed_drawdown"] == 0.05
            assert risk_metrics["position_violations"] == 2
            assert risk_metrics["signal_validation_errors"] == 1
            assert risk_metrics["circuit_breaker_triggered"] is False

    def test_checkpoint_interval_customization(self):
        """Test customizing checkpoint intervals."""
        config = self.create_test_config(Path("/tmp"))
        portfolio = Portfolio(initial_capital=Decimal("100000"))
        metrics = MetricsAggregator(starting_equity=Decimal("100000"))
        mock_strategy = MockStrategy()
        mock_data_provider = MagicMock()

        context = EnhancedExecutionContext(
            config=config,
            portfolio=portfolio,
            metrics=metrics,
            strategy=mock_strategy,
            data_provider=mock_data_provider,
        )
        context.checkpoint_dir = Path("/tmp/checkpoints")

        # Default interval
        assert context.checkpoint_interval == 10000

        # Custom interval
        context.checkpoint_interval = 5000
        context.processed_ticks = 5000
        context.last_checkpoint_tick = 0

        assert context.should_create_checkpoint()

        # After checkpoint
        context.last_checkpoint_tick = 5000
        context.processed_ticks = 7000
        assert not context.should_create_checkpoint()

        context.processed_ticks = 10000
        assert context.should_create_checkpoint()

    def test_multiple_checkpoints_cleanup(self):
        """Test that multiple checkpoints can be created."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config = self.create_test_config(Path(tmp_dir))
            checkpoint_dir = Path(tmp_dir) / "checkpoints"

            portfolio = Portfolio(initial_capital=Decimal("100000"))
            metrics = MetricsAggregator(starting_equity=Decimal("100000"))
            mock_strategy = MockStrategy()
            mock_data_provider = MagicMock()

            context = EnhancedExecutionContext(
                config=config,
                portfolio=portfolio,
                metrics=metrics,
                strategy=mock_strategy,
                data_provider=mock_data_provider,
            )
            context.checkpoint_dir = checkpoint_dir
            context.checkpoint_interval = 1000

            # Create multiple checkpoints
            checkpoints = []
            for i in range(3):
                context.processed_ticks = (i + 1) * 1000
                context.last_checkpoint_tick = i * 1000

                checkpoint_path = context.create_checkpoint()
                checkpoints.append(Path(checkpoint_path))

            # Verify all checkpoints exist
            for checkpoint_path in checkpoints:
                assert checkpoint_path.exists()

            # Verify they have different names
            checkpoint_names = [cp.name for cp in checkpoints]
            assert len(set(checkpoint_names)) == 3  # All unique names
