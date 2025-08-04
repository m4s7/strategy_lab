"""Configuration data models using Pydantic for validation."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator


class LogLevel(str, Enum):
    """Logging level enumeration."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class SlippageModel(str, Enum):
    """Slippage model types."""

    NONE = "none"
    LINEAR = "linear"
    SQUARE_ROOT = "square_root"
    MARKET_IMPACT = "market_impact"


class OptimizationMethod(str, Enum):
    """Optimization method types."""

    GRID_SEARCH = "grid_search"
    RANDOM_SEARCH = "random_search"
    GENETIC_ALGORITHM = "genetic_algorithm"
    BAYESIAN = "bayesian"


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: LogLevel = Field(default=LogLevel.INFO, description="Logging level")
    file: Path | None = Field(default=None, description="Log file path")
    console: bool = Field(default=True, description="Enable console logging")
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log message format",
    )


class PerformanceConfig(BaseModel):
    """Performance configuration."""

    max_memory_gb: float = Field(
        default=16.0, gt=0, description="Maximum memory usage in GB"
    )
    parallel_workers: int = Field(
        default=4, ge=1, description="Number of parallel workers"
    )
    chunk_size: int = Field(
        default=10000, gt=0, description="Data processing chunk size"
    )
    enable_profiling: bool = Field(
        default=False, description="Enable performance profiling"
    )


class DataConfig(BaseModel):
    """Data configuration."""

    data_path: Path = Field(description="Path to market data")
    cache_enabled: bool = Field(default=True, description="Enable data caching")
    cache_path: Path | None = Field(default=None, description="Cache directory")
    preload_data: bool = Field(
        default=False, description="Preload all data into memory"
    )


class RiskConfig(BaseModel):
    """Risk management configuration."""

    max_position_size: int = Field(
        default=10, ge=1, description="Maximum position size"
    )
    stop_loss_pct: float = Field(
        default=2.0, gt=0, le=100, description="Stop loss percentage"
    )
    max_drawdown_pct: float = Field(
        default=10.0, gt=0, le=100, description="Maximum drawdown percentage"
    )
    position_sizing_method: str = Field(
        default="fixed", description="Position sizing method"
    )
    risk_per_trade_pct: float = Field(
        default=1.0, gt=0, le=10, description="Risk per trade percentage"
    )


class StrategyParameterConfig(BaseModel):
    """Base strategy parameter configuration."""

    model_config = {"extra": "allow"}  # Allow additional fields for flexibility

    # Common parameters that all strategies might have
    lookback_period: int | None = Field(default=None, ge=1)
    position_size: int | None = Field(default=1, ge=1)

    @field_validator("*", mode="before")
    @classmethod
    def validate_numeric_ranges(cls, v, info):
        """Validate numeric parameters are within reasonable ranges."""
        if (
            isinstance(v, (int, float))
            and hasattr(info, "field_name")
            and info.field_name
        ):
            # Add custom validation logic based on parameter names
            if "threshold" in info.field_name and not -1 <= v <= 1:
                raise ValueError(f"{info.field_name} must be between -1 and 1")
            if "period" in info.field_name and v < 1:
                raise ValueError(f"{info.field_name} must be positive")
        return v


class StrategyConfig(BaseModel):
    """Strategy configuration."""

    name: str = Field(description="Strategy name")
    enabled: bool = Field(default=True, description="Whether strategy is enabled")
    parameters: dict[str, Any] = Field(
        default_factory=dict, description="Strategy-specific parameters"
    )
    risk_management: RiskConfig = Field(
        default_factory=RiskConfig, description="Risk management settings"
    )

    @field_validator("parameters")
    @classmethod
    def validate_parameters(cls, v, info):
        """Validate strategy parameters based on strategy name."""
        # This would be extended with strategy-specific validation
        return v


class BacktestEngineConfig(BaseModel):
    """Backtesting engine configuration."""

    commission_rate: float = Field(
        default=0.001, ge=0, le=0.1, description="Commission rate (0.1%)"
    )
    slippage_model: SlippageModel = Field(
        default=SlippageModel.LINEAR, description="Slippage model type"
    )
    slippage_factor: float = Field(default=0.0001, ge=0, description="Slippage factor")
    enable_shorting: bool = Field(default=True, description="Enable short positions")
    margin_requirement: float = Field(
        default=0.5, gt=0, le=1, description="Margin requirement"
    )


class BacktestConfig(BaseModel):
    """Backtesting configuration."""

    start_date: datetime = Field(description="Backtest start date")
    end_date: datetime = Field(description="Backtest end date")
    initial_capital: Decimal = Field(
        default=Decimal("100000"), gt=0, description="Initial capital"
    )
    engine: BacktestEngineConfig = Field(
        default_factory=BacktestEngineConfig, description="Engine settings"
    )

    @field_validator("end_date")
    @classmethod
    def validate_dates(cls, v, values):
        """Ensure end date is after start date."""
        if "start_date" in values.data and v <= values.data["start_date"]:
            raise ValueError("end_date must be after start_date")
        return v


class OptimizationConfig(BaseModel):
    """Optimization configuration."""

    method: OptimizationMethod = Field(
        default=OptimizationMethod.GRID_SEARCH, description="Optimization method"
    )
    metric: str = Field(default="sharpe_ratio", description="Optimization metric")
    direction: str = Field(
        default="maximize",
        pattern="^(maximize|minimize)$",
        description="Optimization direction",
    )
    max_iterations: int = Field(default=1000, ge=1, description="Maximum iterations")
    parallel: bool = Field(default=True, description="Enable parallel optimization")
    random_seed: int | None = Field(
        default=None, description="Random seed for reproducibility"
    )


class SystemConfig(BaseModel):
    """Top-level system configuration."""

    version: str = Field(default="1.0.0", description="Configuration version")
    environment: str = Field(
        default="development",
        pattern="^(development|staging|production|test)$",
        description="Environment name",
    )
    logging: LoggingConfig = Field(
        default_factory=LoggingConfig, description="Logging settings"
    )
    performance: PerformanceConfig = Field(
        default_factory=PerformanceConfig, description="Performance settings"
    )
    data: DataConfig = Field(description="Data settings")


class ConfigurationSet(BaseModel):
    """Complete configuration set."""

    system: SystemConfig = Field(description="System configuration")
    strategies: dict[str, StrategyConfig] = Field(
        default_factory=dict, description="Strategy configurations"
    )
    backtesting: BacktestConfig | None = Field(
        default=None, description="Backtesting configuration"
    )
    optimization: OptimizationConfig | None = Field(
        default=None, description="Optimization configuration"
    )

    @field_validator("strategies")
    @classmethod
    def validate_strategy_names(cls, v):
        """Ensure strategy names match dictionary keys."""
        for key, strategy in v.items():
            if strategy.name != key:
                strategy.name = key  # Sync the name with the key
        return v
