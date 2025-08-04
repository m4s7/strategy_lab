"""Tests for configuration models."""

from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError

from strategy_lab.core.config.models import (
    BacktestConfig,
    ConfigurationSet,
    LoggingConfig,
    LogLevel,
    OptimizationConfig,
    OptimizationMethod,
    PerformanceConfig,
    RiskConfig,
    SlippageModel,
    StrategyConfig,
    SystemConfig,
)


class TestLogLevelEnum:
    """Test LogLevel enumeration."""

    def test_valid_levels(self):
        """Test valid log levels."""
        assert LogLevel.DEBUG == "DEBUG"
        assert LogLevel.INFO == "INFO"
        assert LogLevel.WARNING == "WARNING"
        assert LogLevel.ERROR == "ERROR"
        assert LogLevel.CRITICAL == "CRITICAL"


class TestLoggingConfig:
    """Test LoggingConfig model."""

    def test_default_values(self):
        """Test default logging configuration."""
        config = LoggingConfig()
        assert config.level == LogLevel.INFO
        assert config.file is None
        assert config.console is True
        assert "%(asctime)s" in config.format

    def test_custom_values(self):
        """Test custom logging configuration."""
        config = LoggingConfig(
            level=LogLevel.DEBUG,
            file=Path("/var/log/test.log"),
            console=False,
            format="%(message)s",
        )
        assert config.level == LogLevel.DEBUG
        assert config.file == Path("/var/log/test.log")
        assert config.console is False
        assert config.format == "%(message)s"


class TestPerformanceConfig:
    """Test PerformanceConfig model."""

    def test_default_values(self):
        """Test default performance configuration."""
        config = PerformanceConfig()
        assert config.max_memory_gb == 16.0
        assert config.parallel_workers == 4
        assert config.chunk_size == 10000
        assert config.enable_profiling is False

    def test_validation(self):
        """Test performance configuration validation."""
        # Valid configuration
        config = PerformanceConfig(
            max_memory_gb=32.0, parallel_workers=8, chunk_size=50000
        )
        assert config.max_memory_gb == 32.0

        # Invalid memory (negative)
        with pytest.raises(ValidationError):
            PerformanceConfig(max_memory_gb=-1.0)

        # Invalid workers (zero)
        with pytest.raises(ValidationError):
            PerformanceConfig(parallel_workers=0)

        # Invalid chunk size (negative)
        with pytest.raises(ValidationError):
            PerformanceConfig(chunk_size=-100)


class TestRiskConfig:
    """Test RiskConfig model."""

    def test_default_values(self):
        """Test default risk configuration."""
        config = RiskConfig()
        assert config.max_position_size == 10
        assert config.stop_loss_pct == 2.0
        assert config.max_drawdown_pct == 10.0
        assert config.position_sizing_method == "fixed"
        assert config.risk_per_trade_pct == 1.0

    def test_validation(self):
        """Test risk configuration validation."""
        # Valid configuration
        config = RiskConfig(
            max_position_size=5, stop_loss_pct=1.0, max_drawdown_pct=5.0
        )
        assert config.max_position_size == 5

        # Invalid position size (zero)
        with pytest.raises(ValidationError):
            RiskConfig(max_position_size=0)

        # Invalid stop loss (negative)
        with pytest.raises(ValidationError):
            RiskConfig(stop_loss_pct=-1.0)

        # Invalid stop loss (over 100%)
        with pytest.raises(ValidationError):
            RiskConfig(stop_loss_pct=101.0)


class TestStrategyConfig:
    """Test StrategyConfig model."""

    def test_basic_strategy(self):
        """Test basic strategy configuration."""
        config = StrategyConfig(
            name="test_strategy",
            enabled=True,
            parameters={"lookback": 20, "threshold": 0.5},
        )
        assert config.name == "test_strategy"
        assert config.enabled is True
        assert config.parameters["lookback"] == 20
        assert config.parameters["threshold"] == 0.5

    def test_with_risk_management(self):
        """Test strategy with risk management."""
        risk_config = RiskConfig(max_position_size=5, stop_loss_pct=1.0)

        config = StrategyConfig(
            name="safe_strategy",
            parameters={"sensitivity": 0.8},
            risk_management=risk_config,
        )
        assert config.risk_management.max_position_size == 5
        assert config.risk_management.stop_loss_pct == 1.0


class TestBacktestConfig:
    """Test BacktestConfig model."""

    def test_basic_backtest(self):
        """Test basic backtest configuration."""
        config = BacktestConfig(
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31),
            initial_capital=Decimal("50000"),
        )
        assert config.start_date == datetime(2024, 1, 1)
        assert config.end_date == datetime(2024, 12, 31)
        assert config.initial_capital == Decimal("50000")

    def test_date_validation(self):
        """Test date validation."""
        # End date before start date should fail
        with pytest.raises(ValidationError):
            BacktestConfig(
                start_date=datetime(2024, 12, 31), end_date=datetime(2024, 1, 1)
            )

    def test_engine_config(self):
        """Test engine configuration."""
        config = BacktestConfig(
            start_date=datetime(2024, 1, 1), end_date=datetime(2024, 12, 31)
        )
        assert config.engine.commission_rate == 0.001
        assert config.engine.slippage_model == SlippageModel.LINEAR
        assert config.engine.enable_shorting is True


class TestOptimizationConfig:
    """Test OptimizationConfig model."""

    def test_default_values(self):
        """Test default optimization configuration."""
        config = OptimizationConfig()
        assert config.method == OptimizationMethod.GRID_SEARCH
        assert config.metric == "sharpe_ratio"
        assert config.direction == "maximize"
        assert config.max_iterations == 1000
        assert config.parallel is True

    def test_custom_optimization(self):
        """Test custom optimization configuration."""
        config = OptimizationConfig(
            method=OptimizationMethod.GENETIC_ALGORITHM,
            metric="calmar_ratio",
            direction="minimize",
            max_iterations=5000,
            random_seed=42,
        )
        assert config.method == OptimizationMethod.GENETIC_ALGORITHM
        assert config.metric == "calmar_ratio"
        assert config.direction == "minimize"
        assert config.random_seed == 42

    def test_direction_validation(self):
        """Test direction validation."""
        # Valid directions
        config1 = OptimizationConfig(direction="maximize")
        config2 = OptimizationConfig(direction="minimize")
        assert config1.direction == "maximize"
        assert config2.direction == "minimize"

        # Invalid direction
        with pytest.raises(ValidationError):
            OptimizationConfig(direction="optimize")


class TestSystemConfig:
    """Test SystemConfig model."""

    def test_minimal_config(self):
        """Test minimal system configuration."""
        config = SystemConfig(data={"data_path": "/data/market"})
        assert config.version == "1.0.0"
        assert config.environment == "development"
        assert config.data.data_path == Path("/data/market")

    def test_environment_validation(self):
        """Test environment validation."""
        # Valid environments
        for env in ["development", "staging", "production"]:
            config = SystemConfig(environment=env, data={"data_path": "/data"})
            assert config.environment == env

        # Invalid environment
        with pytest.raises(ValidationError):
            SystemConfig(environment="testing", data={"data_path": "/data"})


class TestConfigurationSet:
    """Test ConfigurationSet model."""

    def test_minimal_configuration(self):
        """Test minimal configuration set."""
        config = ConfigurationSet(system={"data": {"data_path": "/data/market"}})
        assert config.system.version == "1.0.0"
        assert config.strategies == {}
        assert config.backtesting is None
        assert config.optimization is None

    def test_complete_configuration(self):
        """Test complete configuration set."""
        config = ConfigurationSet(
            system={
                "data": {"data_path": "/data/market"},
                "logging": {"level": "DEBUG"},
            },
            strategies={
                "test_strategy": {
                    "name": "test_strategy",
                    "parameters": {"threshold": 0.5},
                }
            },
            backtesting={
                "start_date": "2024-01-01T00:00:00",
                "end_date": "2024-12-31T23:59:59",
            },
            optimization={"method": "grid_search", "max_iterations": 2000},
        )
        assert config.system.logging.level == LogLevel.DEBUG
        assert "test_strategy" in config.strategies
        assert config.backtesting.start_date.year == 2024
        assert config.optimization.max_iterations == 2000

    def test_strategy_name_sync(self):
        """Test that strategy names are synced with dictionary keys."""
        config = ConfigurationSet(
            system={"data": {"data_path": "/data"}},
            strategies={
                "strategy_key": {
                    "name": "different_name",  # This should be synced
                    "parameters": {},
                }
            },
        )
        # Name should be synced to match the key
        assert config.strategies["strategy_key"].name == "strategy_key"
