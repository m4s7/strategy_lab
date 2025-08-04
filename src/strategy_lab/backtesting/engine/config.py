"""Backtest configuration management."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pandas as pd
from pydantic import BaseModel, Field, validator


class StrategyConfig(BaseModel):
    """Strategy-specific configuration."""

    name: str = Field(..., description="Strategy name")
    module: str = Field(..., description="Strategy module path")
    parameters: dict[str, Any] = Field(
        default_factory=dict, description="Strategy parameters"
    )

    @validator("module")
    def validate_module(cls, v):
        """Ensure module path is valid."""
        if not v or not isinstance(v, str):
            raise ValueError("Module path must be a non-empty string")
        return v


class DataConfig(BaseModel):
    """Data source configuration."""

    symbol: str = Field("MNQ", description="Trading symbol")
    data_path: Path = Field(..., description="Path to data files")
    file_pattern: str = Field("*.parquet", description="File pattern to match")

    # Contract selection
    contracts: list[str] | None = Field(
        None, description="Contract months to include (e.g., ['03-24', '06-24'])"
    )

    # Streaming parameters
    chunk_size: int = Field(100_000, description="Data chunk size for streaming")
    memory_limit_mb: int = Field(1000, description="Memory limit for data loading")
    validate_data: bool = Field(True, description="Whether to validate data integrity")

    @validator("data_path")
    def validate_path(cls, v):
        """Ensure data path exists."""
        path = Path(v)
        if not path.exists():
            raise ValueError(f"Data path does not exist: {path}")
        return path

    @validator("chunk_size")
    def validate_chunk_size(cls, v):
        """Ensure chunk size is positive."""
        if v <= 0:
            raise ValueError("Chunk size must be positive")
        return v

    @validator("memory_limit_mb")
    def validate_memory_limit(cls, v):
        """Ensure memory limit is positive."""
        if v <= 0:
            raise ValueError("Memory limit must be positive")
        return v


class ExecutionConfig(BaseModel):
    """Execution-specific configuration."""

    start_date: datetime | None = Field(None, description="Backtest start date")
    end_date: datetime | None = Field(None, description="Backtest end date")
    initial_capital: Decimal = Field(Decimal("100000"), description="Starting capital")
    commission: Decimal = Field(Decimal("2.00"), description="Commission per trade")
    slippage: Decimal = Field(Decimal("0.25"), description="Slippage per trade")

    # Resource limits
    max_memory_gb: float = Field(4.0, description="Maximum memory usage in GB")
    max_cpu_percent: float = Field(80.0, description="Maximum CPU usage percentage")

    # Progress reporting
    progress_interval: int = Field(1000, description="Progress update interval (ticks)")

    @validator("end_date")
    def validate_date_range(cls, v, values):
        """Ensure end date is after start date."""
        if v and "start_date" in values and values["start_date"]:
            if v <= values["start_date"]:
                raise ValueError("End date must be after start date")
        return v

    @validator("initial_capital", "commission", "slippage")
    def validate_positive(cls, v):
        """Ensure values are positive."""
        if v < 0:
            raise ValueError("Value must be non-negative")
        return v


class BacktestConfig(BaseModel):
    """Complete backtest configuration."""

    name: str = Field(..., description="Backtest name")
    description: str = Field("", description="Backtest description")

    # Component configurations
    strategy: StrategyConfig
    data: DataConfig
    execution: ExecutionConfig

    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    version: str = Field("1.0", description="Configuration version")
    tags: list[str] = Field(default_factory=list, description="Tags for categorization")

    # Output settings
    output_dir: Path = Field(
        Path("results"), description="Output directory for results"
    )
    save_trades: bool = Field(True, description="Save individual trades")
    save_equity_curve: bool = Field(True, description="Save equity curve data")

    @validator("output_dir")
    def ensure_output_dir(cls, v):
        """Ensure output directory exists."""
        path = Path(v)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary."""
        data = self.model_dump()
        # Convert Path objects to strings
        data["data"]["data_path"] = str(data["data"]["data_path"])
        data["output_dir"] = str(data["output_dir"])
        # Convert Decimal to float
        data["execution"]["initial_capital"] = float(
            data["execution"]["initial_capital"]
        )
        data["execution"]["commission"] = float(data["execution"]["commission"])
        data["execution"]["slippage"] = float(data["execution"]["slippage"])
        # Convert datetime to ISO format
        data["created_at"] = data["created_at"].isoformat()
        if data["execution"]["start_date"]:
            data["execution"]["start_date"] = data["execution"][
                "start_date"
            ].isoformat()
        if data["execution"]["end_date"]:
            data["execution"]["end_date"] = data["execution"]["end_date"].isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BacktestConfig":
        """Create configuration from dictionary."""
        return cls(**data)

    def validate(self) -> list[str]:
        """Validate configuration completeness.

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Check strategy configuration
        if not self.strategy.name:
            errors.append("Strategy name is required")
        if not self.strategy.module:
            errors.append("Strategy module is required")

        # Check data configuration
        if not self.data.data_path.exists():
            errors.append(f"Data path does not exist: {self.data.data_path}")

        # Check execution configuration
        if self.execution.max_memory_gb <= 0:
            errors.append("Maximum memory must be positive")
        if self.execution.max_cpu_percent <= 0 or self.execution.max_cpu_percent > 100:
            errors.append("Maximum CPU percentage must be between 0 and 100")

        return errors

    def get_date_range(self) -> tuple[pd.Timestamp | None, pd.Timestamp | None]:
        """Get date range as pandas timestamps.

        Returns:
            Tuple of (start_date, end_date) as pandas Timestamps
        """
        start = (
            pd.Timestamp(self.execution.start_date)
            if self.execution.start_date
            else None
        )
        end = pd.Timestamp(self.execution.end_date) if self.execution.end_date else None
        return start, end


@dataclass
class ConfigTemplate:
    """Pre-defined configuration templates."""

    @staticmethod
    def default_config(strategy_name: str, strategy_module: str) -> BacktestConfig:
        """Create default configuration.

        Args:
            strategy_name: Name of the strategy
            strategy_module: Module path to strategy

        Returns:
            Default BacktestConfig
        """
        return BacktestConfig(
            name=f"{strategy_name}_backtest",
            description=f"Backtest of {strategy_name} strategy",
            strategy=StrategyConfig(
                name=strategy_name, module=strategy_module, parameters={}
            ),
            data=DataConfig(
                symbol="MNQ",
                data_path=Path("data/MNQ"),
                file_pattern="*.parquet",
                contracts=None,
                chunk_size=100_000,
                memory_limit_mb=1000,
                validate_data=True,
            ),
            execution=ExecutionConfig(
                initial_capital=Decimal("100000"),
                commission=Decimal("2.00"),
                slippage=Decimal("0.25"),
            ),
        )

    @staticmethod
    def optimization_config(
        strategy_name: str, strategy_module: str, param_ranges: dict[str, list[Any]]
    ) -> BacktestConfig:
        """Create configuration for optimization.

        Args:
            strategy_name: Name of the strategy
            strategy_module: Module path to strategy
            param_ranges: Parameter ranges for optimization

        Returns:
            Optimization BacktestConfig
        """
        config = ConfigTemplate.default_config(strategy_name, strategy_module)
        config.name = f"{strategy_name}_optimization"
        config.description = f"Parameter optimization for {strategy_name}"
        config.tags = ["optimization"]

        # Store parameter ranges in strategy config
        config.strategy.parameters["_param_ranges"] = param_ranges

        return config
