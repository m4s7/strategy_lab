"""Tests for enhanced backtest execution engine."""

import tempfile
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
from strategy_lab.backtesting.engine.execution_enhanced import (
    EnhancedBacktestExecutor,
    RiskLimits,
)


class MockStrategy:
    """Mock strategy for testing."""

    name = "MockStrategy"
    version = "1.0.0"
    description = "Mock strategy for testing"

    def __init__(self, **kwargs):
        self.parameters = kwargs
        self.initialized = False
        self.tick_count = 0
        self.signal_sequence = kwargs.get("signal_sequence", [1, -1, 0])
        self.signal_index = 0

    def initialize(self):
        self.initialized = True

    def process_tick(self, timestamp, price, volume, bid, ask, **kwargs):
        self.tick_count += 1

        # Return signals in sequence
        if self.signal_index < len(self.signal_sequence):
            signal = self.signal_sequence[self.signal_index]
            self.signal_index = (self.signal_index + 1) % len(self.signal_sequence)
            return signal
        return 0

    def cleanup(self):
        self.initialized = False


class TestRiskLimits:
    """Test risk management limits."""

    def test_risk_limits_defaults(self):
        """Test default risk limits."""
        limits = RiskLimits()

        assert limits.max_position_size == 10
        assert limits.max_drawdown_percent == 0.20
        assert limits.position_size_limit_enabled is True
        assert limits.drawdown_circuit_breaker_enabled is True
        assert limits.validate_signals is True

    def test_risk_limits_custom(self):
        """Test custom risk limits."""
        limits = RiskLimits(
            max_position_size=5,
            max_drawdown_percent=0.15,
            position_size_limit_enabled=False,
            drawdown_circuit_breaker_enabled=False,
            validate_signals=False,
        )

        assert limits.max_position_size == 5
        assert limits.max_drawdown_percent == 0.15
        assert limits.position_size_limit_enabled is False
        assert limits.drawdown_circuit_breaker_enabled is False
        assert limits.validate_signals is False


class TestEnhancedBacktestExecutor:
    """Test enhanced backtest executor."""

    def create_test_config(self, data_path: Path) -> BacktestConfig:
        """Create test backtest configuration."""
        return BacktestConfig(
            name="test_enhanced_backtest",
            strategy=StrategyConfig(
                name="MockStrategy",
                module="test.module",
                parameters={
                    "signal_sequence": [1, -1, 0, 1],
                    "max_position_size": 5,
                    "max_drawdown_percent": 0.15,
                    "enable_position_limits": True,
                    "enable_circuit_breaker": True,
                    "validate_signals": True,
                },
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

    def create_test_data_structure(self, tmp_dir: Path) -> Path:
        """Create test data directory structure."""
        data_dir = tmp_dir / "MNQ"
        contract_dir = data_dir / "03-24"
        contract_dir.mkdir(parents=True)

        # Create test parquet file with realistic tick data
        sample_data = pd.DataFrame(
            {
                "level": ["1"] * 10,
                "timestamp": [
                    1609459200000000000 + i * 1000000  # 1 second intervals
                    for i in range(10)
                ],
                "mdt": [2] * 10,  # All trades
                "price": [100.0 + i * 0.25 for i in range(10)],  # Rising prices
                "volume": [1000] * 10,
                "operation": [0] * 10,
            }
        )

        test_file = contract_dir / "20240315.parquet"
        sample_data.to_parquet(test_file)

        return data_dir

    @patch("strategy_lab.backtesting.engine.execution_enhanced.strategy_registry")
    def test_executor_initialization(self, mock_registry):
        """Test enhanced executor initialization."""
        # Mock strategy registry
        mock_registry.list_strategies.return_value = ["MockStrategy"]
        mock_registry.create_strategy.return_value = MockStrategy()

        with tempfile.TemporaryDirectory() as tmp_dir:
            data_dir = self.create_test_data_structure(Path(tmp_dir))
            config = self.create_test_config(data_dir)

            executor = EnhancedBacktestExecutor(config)

            assert executor.config == config
            assert executor.context is None
            assert executor._progress_bar is None

    @patch("strategy_lab.backtesting.engine.execution_enhanced.strategy_registry")
    def test_strategy_loading_from_registry(self, mock_registry):
        """Test strategy loading from registry."""
        mock_strategy = MockStrategy()
        mock_registry.list_strategies.return_value = ["MockStrategy"]
        mock_registry.create_strategy.return_value = mock_strategy

        with tempfile.TemporaryDirectory() as tmp_dir:
            data_dir = self.create_test_data_structure(Path(tmp_dir))
            config = self.create_test_config(data_dir)

            executor = EnhancedBacktestExecutor(config)
            executor._initialize_context()

            assert executor.context is not None
            assert executor.context.strategy == mock_strategy
            mock_registry.create_strategy.assert_called_once()

    @patch("strategy_lab.backtesting.engine.execution_enhanced.strategy_registry")
    def test_strategy_loading_fallback(self, mock_registry):
        """Test strategy loading fallback to module loading."""
        # Mock registry to not have the strategy
        mock_registry.list_strategies.return_value = []

        with tempfile.TemporaryDirectory() as tmp_dir:
            data_dir = self.create_test_data_structure(Path(tmp_dir))
            config = self.create_test_config(data_dir)

            executor = EnhancedBacktestExecutor(config)

            # This should fail since we don't have a real module
            with pytest.raises(RuntimeError, match="Strategy loading failed"):
                executor._initialize_context()

    @patch("strategy_lab.backtesting.engine.execution_enhanced.strategy_registry")
    def test_signal_validation(self, mock_registry):
        """Test signal validation logic."""
        mock_registry.list_strategies.return_value = ["MockStrategy"]
        mock_registry.create_strategy.return_value = MockStrategy()

        with tempfile.TemporaryDirectory() as tmp_dir:
            data_dir = self.create_test_data_structure(Path(tmp_dir))
            config = self.create_test_config(data_dir)

            executor = EnhancedBacktestExecutor(config)
            executor._initialize_context()

            # Test valid signals
            assert executor._validate_signal(1) is True
            assert executor._validate_signal(-1) is True
            assert executor._validate_signal(0) is True
            assert executor._validate_signal(None) is True

            # Test invalid signals
            assert executor._validate_signal(2) is False
            assert executor._validate_signal("invalid") is False
            assert executor._validate_signal(1.5) is False

    @patch("strategy_lab.backtesting.engine.execution_enhanced.strategy_registry")
    def test_position_limit_validation(self, mock_registry):
        """Test position size limit validation."""
        mock_registry.list_strategies.return_value = ["MockStrategy"]
        mock_registry.create_strategy.return_value = MockStrategy()

        with tempfile.TemporaryDirectory() as tmp_dir:
            data_dir = self.create_test_data_structure(Path(tmp_dir))
            config = self.create_test_config(data_dir)

            executor = EnhancedBacktestExecutor(config)
            executor._initialize_context()

            # Test position limit logic
            assert executor._would_violate_position_limits(1, None) is False  # New long
            assert (
                executor._would_violate_position_limits(-1, None) is False
            )  # New short
            assert executor._would_violate_position_limits(0, None) is False  # Flat

    @patch("strategy_lab.backtesting.engine.execution_enhanced.strategy_registry")
    def test_circuit_breaker_logic(self, mock_registry):
        """Test circuit breaker functionality."""
        mock_registry.list_strategies.return_value = ["MockStrategy"]
        mock_registry.create_strategy.return_value = MockStrategy()

        with tempfile.TemporaryDirectory() as tmp_dir:
            data_dir = self.create_test_data_structure(Path(tmp_dir))
            config = self.create_test_config(data_dir)

            executor = EnhancedBacktestExecutor(config)
            executor._initialize_context()

            # Test circuit breaker logic
            assert executor.context.should_trigger_circuit_breaker() is False

            # Simulate large drawdown
            executor.context.portfolio.peak_equity = Decimal("100000")
            executor.context.portfolio.current_drawdown = Decimal(
                "25000"
            )  # 25% drawdown

            assert executor.context.should_trigger_circuit_breaker() is True

    @patch("strategy_lab.backtesting.engine.execution_enhanced.strategy_registry")
    def test_enhanced_execution_with_data_stream(self, mock_registry):
        """Test enhanced execution with data stream integration."""
        mock_strategy = MockStrategy(signal_sequence=[1, 0, -1, 0])
        mock_registry.list_strategies.return_value = ["MockStrategy"]
        mock_registry.create_strategy.return_value = mock_strategy

        with tempfile.TemporaryDirectory() as tmp_dir:
            data_dir = self.create_test_data_structure(Path(tmp_dir))
            config = self.create_test_config(data_dir)

            executor = EnhancedBacktestExecutor(config)

            # Execute the backtest
            result = executor.execute()

            # Verify results
            assert result is not None
            assert result.config == config
            assert result.total_ticks > 0
            assert result.execution_time > 0
            assert "circuit_breaker_triggered" in result.custom_metrics
            assert "data_pipeline_version" in result.custom_metrics
            assert result.custom_metrics["data_pipeline_version"] == "5.1"

            # Verify strategy was used
            assert mock_strategy.initialized is False  # Should be cleaned up
            assert mock_strategy.tick_count > 0

    @patch("strategy_lab.backtesting.engine.execution_enhanced.strategy_registry")
    def test_risk_management_integration(self, mock_registry):
        """Test integration of risk management features."""
        # Create strategy with specific risk parameters
        mock_strategy = MockStrategy(
            signal_sequence=[1, -1, 1, -1],  # Alternating signals
            max_position_size=2,
            max_drawdown_percent=0.10,
        )
        mock_registry.list_strategies.return_value = ["MockStrategy"]
        mock_registry.create_strategy.return_value = mock_strategy

        with tempfile.TemporaryDirectory() as tmp_dir:
            data_dir = self.create_test_data_structure(Path(tmp_dir))
            config = self.create_test_config(data_dir)

            executor = EnhancedBacktestExecutor(config)
            result = executor.execute()

            # Verify risk management metrics are tracked
            assert "position_violations" in result.custom_metrics
            assert "signal_validation_errors" in result.custom_metrics
            assert "max_observed_drawdown" in result.custom_metrics

            # Values should be non-negative
            assert result.custom_metrics["position_violations"] >= 0
            assert result.custom_metrics["signal_validation_errors"] >= 0
            assert result.custom_metrics["max_observed_drawdown"] >= 0

    @patch("strategy_lab.backtesting.engine.execution_enhanced.strategy_registry")
    def test_error_handling_during_execution(self, mock_registry):
        """Test error handling during backtest execution."""

        # Create strategy that raises exceptions
        class ErrorStrategy(MockStrategy):
            def process_tick(self, *args, **kwargs):
                if self.tick_count > 2:
                    raise ValueError("Strategy error")
                return super().process_tick(*args, **kwargs)

        mock_registry.list_strategies.return_value = ["ErrorStrategy"]
        mock_registry.create_strategy.return_value = ErrorStrategy()

        with tempfile.TemporaryDirectory() as tmp_dir:
            data_dir = self.create_test_data_structure(Path(tmp_dir))
            config = self.create_test_config(data_dir)

            executor = EnhancedBacktestExecutor(config)

            # Should handle errors gracefully
            with pytest.raises(Exception):
                executor.execute()

    @patch("strategy_lab.backtesting.engine.execution_enhanced.strategy_registry")
    def test_progress_tracking(self, mock_registry):
        """Test progress tracking functionality."""
        mock_strategy = MockStrategy()
        mock_registry.list_strategies.return_value = ["MockStrategy"]
        mock_registry.create_strategy.return_value = mock_strategy

        with tempfile.TemporaryDirectory() as tmp_dir:
            data_dir = self.create_test_data_structure(Path(tmp_dir))
            config = self.create_test_config(data_dir)

            executor = EnhancedBacktestExecutor(config)
            executor._initialize_context()

            # Test progress tracking
            initial_ticks = executor.context.processed_ticks
            executor._update_progress()

            assert executor.context.processed_ticks == initial_ticks + 1
            assert executor.context.elapsed_time > 0

    def test_cleanup_functionality(self):
        """Test cleanup functionality."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            data_dir = self.create_test_data_structure(Path(tmp_dir))
            config = self.create_test_config(data_dir)

            executor = EnhancedBacktestExecutor(config)

            # Create mock progress bar
            executor._progress_bar = MagicMock()

            # Test cleanup
            executor._cleanup()

            executor._progress_bar.close.assert_called_once()
            assert executor.context is None
