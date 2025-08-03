"""Tests for backtest configuration."""

from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError

from strategy_lab.backtesting.engine.config import (
    BacktestConfig,
    ConfigTemplate,
    DataConfig,
    ExecutionConfig,
    StrategyConfig,
)


class TestStrategyConfig:
    """Test StrategyConfig validation."""

    def test_valid_config(self):
        """Test creating valid strategy config."""
        config = StrategyConfig(
            name="TestStrategy",
            module="strategies.test_strategy",
            parameters={"param1": 10, "param2": 0.5},
        )

        assert config.name == "TestStrategy"
        assert config.module == "strategies.test_strategy"
        assert config.parameters["param1"] == 10

    def test_empty_module(self):
        """Test validation of empty module."""
        with pytest.raises(ValidationError) as exc_info:
            StrategyConfig(name="TestStrategy", module="", parameters={})

        assert "Module path must be a non-empty string" in str(exc_info.value)


class TestDataConfig:
    """Test DataConfig validation."""

    def test_valid_config(self, tmp_path):
        """Test creating valid data config."""
        # Create test directory
        data_path = tmp_path / "data"
        data_path.mkdir()

        config = DataConfig(symbol="MNQ", data_path=data_path, file_pattern="*.parquet")

        assert config.symbol == "MNQ"
        assert config.data_path == data_path
        assert config.file_pattern == "*.parquet"

    def test_invalid_path(self):
        """Test validation of non-existent path."""
        with pytest.raises(ValidationError) as exc_info:
            DataConfig(
                symbol="MNQ",
                data_path=Path("/non/existent/path"),
                file_pattern="*.parquet",
            )

        assert "Data path does not exist" in str(exc_info.value)


class TestExecutionConfig:
    """Test ExecutionConfig validation."""

    def test_valid_config(self):
        """Test creating valid execution config."""
        config = ExecutionConfig(
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31),
            initial_capital=Decimal("50000"),
            commission=Decimal("1.50"),
            slippage=Decimal("0.10"),
        )

        assert config.initial_capital == Decimal("50000")
        assert config.commission == Decimal("1.50")
        assert config.max_memory_gb == 4.0  # Default

    def test_invalid_date_range(self):
        """Test validation of invalid date range."""
        with pytest.raises(ValidationError) as exc_info:
            ExecutionConfig(
                start_date=datetime(2024, 12, 31), end_date=datetime(2024, 1, 1)
            )

        assert "End date must be after start date" in str(exc_info.value)

    def test_negative_values(self):
        """Test validation of negative values."""
        with pytest.raises(ValidationError):
            ExecutionConfig(initial_capital=Decimal("-1000"))

        with pytest.raises(ValidationError):
            ExecutionConfig(commission=Decimal("-1"))


class TestBacktestConfig:
    """Test BacktestConfig functionality."""

    def create_test_config(self, tmp_path):
        """Create a test configuration."""
        data_path = tmp_path / "data"
        data_path.mkdir()

        return BacktestConfig(
            name="TestBacktest",
            description="Test backtest configuration",
            strategy=StrategyConfig(
                name="TestStrategy",
                module="strategies.test",
                parameters={"threshold": 0.5},
            ),
            data=DataConfig(
                symbol="MNQ", data_path=data_path, file_pattern="*.parquet"
            ),
            execution=ExecutionConfig(
                initial_capital=Decimal("100000"), commission=Decimal("2.00")
            ),
            output_dir=tmp_path / "results",
        )

    def test_valid_config(self, tmp_path):
        """Test creating valid backtest config."""
        config = self.create_test_config(tmp_path)

        assert config.name == "TestBacktest"
        assert config.strategy.name == "TestStrategy"
        assert config.data.symbol == "MNQ"
        assert config.execution.initial_capital == Decimal("100000")

    def test_config_serialization(self, tmp_path):
        """Test config to/from dict conversion."""
        config = self.create_test_config(tmp_path)

        # Convert to dict
        config_dict = config.to_dict()
        assert isinstance(config_dict, dict)
        assert config_dict["name"] == "TestBacktest"

        # Convert back from dict
        config2 = BacktestConfig.from_dict(config_dict)
        assert config2.name == config.name
        assert config2.strategy.name == config.strategy.name

    def test_config_validation(self, tmp_path):
        """Test configuration validation."""
        config = self.create_test_config(tmp_path)

        # Valid config should have no errors
        errors = config.validate()
        assert len(errors) == 0

        # Invalid config should have errors
        config.execution.max_cpu_percent = 150  # Invalid
        errors = config.validate()
        assert len(errors) > 0
        assert "CPU percentage" in errors[0]

    def test_date_range_extraction(self, tmp_path):
        """Test date range extraction."""
        config = self.create_test_config(tmp_path)

        # No dates set
        start, end = config.get_date_range()
        assert start is None
        assert end is None

        # With dates
        config.execution.start_date = datetime(2024, 1, 1)
        config.execution.end_date = datetime(2024, 12, 31)
        start, end = config.get_date_range()

        assert start.year == 2024
        assert start.month == 1
        assert end.year == 2024
        assert end.month == 12

    def test_output_dir_creation(self, tmp_path):
        """Test automatic output directory creation."""
        output_dir = tmp_path / "new_results"
        assert not output_dir.exists()

        config = BacktestConfig(
            name="Test",
            strategy=StrategyConfig(name="Test", module="test"),
            data=DataConfig(symbol="MNQ", data_path=tmp_path),
            execution=ExecutionConfig(),
            output_dir=output_dir,
        )

        # Directory should be created
        assert output_dir.exists()


class TestConfigTemplate:
    """Test configuration templates."""

    def test_default_config(self):
        """Test default configuration template."""
        config = ConfigTemplate.default_config(
            strategy_name="MyStrategy", strategy_module="strategies.my_strategy"
        )

        assert config.name == "MyStrategy_backtest"
        assert config.strategy.name == "MyStrategy"
        assert config.strategy.module == "strategies.my_strategy"
        assert config.execution.initial_capital == Decimal("100000")

    def test_optimization_config(self):
        """Test optimization configuration template."""
        param_ranges = {"threshold": [0.1, 0.2, 0.3], "lookback": [10, 20, 30]}

        config = ConfigTemplate.optimization_config(
            strategy_name="OptStrategy",
            strategy_module="strategies.opt",
            param_ranges=param_ranges,
        )

        assert config.name == "OptStrategy_optimization"
        assert "optimization" in config.tags
        assert "_param_ranges" in config.strategy.parameters
        assert config.strategy.parameters["_param_ranges"] == param_ranges
