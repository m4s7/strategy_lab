# Strategy Lab Coding Standards

## Overview

This document defines the coding standards and best practices for the Strategy Lab futures trading backtesting framework. These standards ensure code quality, maintainability, and consistency across the codebase.

## General Principles

### Code Quality Standards
- **Clarity over cleverness**: Write code that is easy to understand and maintain
- **Consistent style**: Follow established Python conventions and project patterns
- **Performance awareness**: Consider performance implications, especially for tick processing
- **Error handling**: Implement comprehensive error handling with meaningful messages
- **Documentation**: All public APIs must be documented with docstrings

### Development Workflow
- **Test-driven development**: Write tests before implementation when possible
- **Code review**: All changes must pass automated quality checks
- **Version control**: Use meaningful commit messages following conventional commit format
- **Dependencies**: Minimize external dependencies and keep them up to date

## Python Style Guide

### Code Formatting
- **Formatter**: Use `black` for automated code formatting
- **Line length**: Maximum 88 characters (black default)
- **Import organization**: Use `ruff` for import sorting and organization
- **Quotes**: Prefer double quotes for strings unless single quotes avoid escaping

### Naming Conventions
```python
# Classes: PascalCase
class StrategyBase:
    pass

class OrderBookImbalanceStrategy:
    pass

# Functions and variables: snake_case
def calculate_metrics():
    pass

def process_tick_data():
    pass

backtest_results = {}
strategy_config = {}

# Constants: UPPER_SNAKE_CASE
MAX_POSITION_SIZE = 10
DEFAULT_TIMEOUT = 30

# Private members: leading underscore
def _internal_helper():
    pass

class Strategy:
    def __init__(self):
        self._position = 0
        self._state = {}
```

### Type Annotations
```python
from typing import Dict, List, Optional, Union, Protocol
from decimal import Decimal
import pandas as pd

# All function signatures must include type hints
def load_tick_data(
    file_path: str, 
    date_range: Optional[tuple[str, str]] = None
) -> pd.DataFrame:
    """Load tick data from Parquet file with optional date filtering."""
    pass

# Class attributes should be annotated
class BacktestConfig:
    start_date: str
    end_date: str
    initial_capital: Decimal
    commission_rate: float = 0.001

# Use protocols for interfaces
class StrategyProtocol(Protocol):
    def generate_signal(self, tick_data: pd.Series) -> Optional[str]:
        """Generate trading signal from tick data."""
        ...
```

### Documentation Standards
```python
def calculate_sharpe_ratio(
    returns: pd.Series, 
    risk_free_rate: float = 0.02
) -> float:
    """Calculate the Sharpe ratio for a return series.
    
    Args:
        returns: Series of period returns (daily, hourly, etc.)
        risk_free_rate: Annual risk-free rate (default: 2%)
        
    Returns:
        Sharpe ratio as a float. Returns NaN if insufficient data.
        
    Raises:
        ValueError: If returns series is empty or contains invalid values.
        
    Example:
        >>> returns = pd.Series([0.01, -0.02, 0.03, 0.01])
        >>> sharpe = calculate_sharpe_ratio(returns)
        >>> print(f"Sharpe ratio: {sharpe:.2f}")
    """
    pass
```

## Code Organization

### Module Structure
```python
# Standard library imports first
import os
import sys
from pathlib import Path
from decimal import Decimal
from typing import Dict, List, Optional

# Third-party imports second
import pandas as pd
import numpy as np
from hftbacktest import BacktestEngine

# Local imports last
from strategy_lab.core.config import Config
from strategy_lab.strategies.base import StrategyBase
from strategy_lab.utils.metrics import calculate_metrics
```

### Error Handling
```python
# Use specific exception types
class StrategyLabError(Exception):
    """Base exception for Strategy Lab errors."""
    pass

class DataValidationError(StrategyLabError):
    """Raised when data validation fails."""
    pass

class StrategyConfigError(StrategyLabError):
    """Raised when strategy configuration is invalid."""
    pass

# Implement proper error handling
def load_config(config_path: str) -> Dict:
    """Load and validate configuration file."""
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        raise StrategyConfigError(f"Configuration file not found: {config_path}")
    except yaml.YAMLError as e:
        raise StrategyConfigError(f"Invalid YAML in config file: {e}")
    
    # Validation logic here
    return config
```

### Logging Standards
```python
import logging
from strategy_lab.core.logging import get_logger

# Use structured logging
logger = get_logger(__name__)

def process_backtest(strategy: str, config: Dict) -> Dict:
    """Process a backtest with proper logging."""
    logger.info(
        "Starting backtest",
        extra={
            "strategy": strategy,
            "start_date": config["start_date"],
            "end_date": config["end_date"]
        }
    )
    
    try:
        results = run_backtest(strategy, config)
        logger.info(
            "Backtest completed successfully",
            extra={
                "strategy": strategy,
                "total_trades": results["trade_count"],
                "pnl": results["total_pnl"]
            }
        )
        return results
    except Exception as e:
        logger.error(
            "Backtest failed",
            extra={
                "strategy": strategy,
                "error": str(e)
            },
            exc_info=True
        )
        raise
```

## Performance Guidelines

### Memory Management
```python
# Use generators for large datasets
def process_tick_files(file_paths: List[str]) -> Generator[pd.DataFrame, None, None]:
    """Process tick files one at a time to manage memory."""
    for file_path in file_paths:
        df = pd.read_parquet(file_path)
        yield df
        # DataFrame goes out of scope and can be garbage collected

# Efficient pandas operations
def calculate_rolling_metrics(data: pd.DataFrame) -> pd.DataFrame:
    """Calculate rolling metrics efficiently."""
    # Use vectorized operations
    data['sma_20'] = data['price'].rolling(20).mean()
    data['volatility'] = data['returns'].rolling(20).std()
    
    # Avoid apply() when possible, use vectorized alternatives
    return data
```

### Processing Optimization
```python
# Use appropriate data types
def optimize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Optimize DataFrame memory usage."""
    # Use category for repeated strings
    if 'symbol' in df.columns:
        df['symbol'] = df['symbol'].astype('category')
    
    # Use appropriate numeric types
    if 'volume' in df.columns:
        df['volume'] = pd.to_numeric(df['volume'], downcast='integer')
    
    if 'price' in df.columns:
        df['price'] = pd.to_numeric(df['price'], downcast='float')
    
    return df
```

## Testing Standards

### Unit Test Structure
```python
import pytest
import pandas as pd
from unittest.mock import Mock, patch
from strategy_lab.strategies.order_book_imbalance import OrderBookImbalanceStrategy

class TestOrderBookImbalanceStrategy:
    """Test suite for OrderBookImbalanceStrategy."""
    
    @pytest.fixture
    def sample_tick_data(self) -> pd.DataFrame:
        """Create sample tick data for testing."""
        return pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=100, freq='1s'),
            'price': np.random.randn(100).cumsum() + 100,
            'volume': np.random.randint(1, 100, 100)
        })
    
    @pytest.fixture
    def strategy(self) -> OrderBookImbalanceStrategy:
        """Create strategy instance with test configuration."""
        config = {
            'imbalance_threshold': 0.7,
            'position_size': 1,
            'stop_loss': 0.5
        }
        return OrderBookImbalanceStrategy(config)
    
    def test_signal_generation(self, strategy, sample_tick_data):
        """Test signal generation logic."""
        # Test specific signal generation scenarios
        signal = strategy.generate_signal(sample_tick_data.iloc[0])
        assert signal in ['BUY', 'SELL', None]
    
    def test_invalid_config_raises_error(self):
        """Test that invalid configuration raises appropriate error."""
        with pytest.raises(StrategyConfigError):
            OrderBookImbalanceStrategy({'invalid': 'config'})
```

### Integration Test Guidelines
```python
@pytest.mark.integration
class TestBacktestPipeline:
    """Integration tests for complete backtest pipeline."""
    
    def test_end_to_end_backtest(self, sample_data_file):
        """Test complete backtest from data loading to results."""
        # Test realistic scenarios with actual data files
        config = load_test_config()
        results = run_complete_backtest(config)
        
        # Validate results structure and content
        assert 'total_pnl' in results
        assert 'trade_count' in results
        assert results['trade_count'] >= 0
```

## Configuration Management

### Configuration File Structure
```yaml
# strategy_config.yaml
strategy:
  name: "order_book_imbalance"
  parameters:
    imbalance_threshold: 0.7
    position_size: 1
    stop_loss_pct: 0.5
    take_profit_pct: 1.0

backtest:
  start_date: "2024-01-01"
  end_date: "2024-12-31"
  initial_capital: 100000.0
  commission_rate: 0.001

data:
  tick_data_path: "./data/MNQ"
  contract_months: ["03-24", "06-24", "09-24"]

optimization:
  method: "grid_search"
  parallel_workers: 8
  parameters:
    imbalance_threshold:
      min: 0.5
      max: 0.9
      step: 0.1
```

### Configuration Validation
```python
from pydantic import BaseModel, validator
from typing import List
from decimal import Decimal

class StrategyConfig(BaseModel):
    """Configuration model for strategy parameters."""
    
    imbalance_threshold: float
    position_size: int
    stop_loss_pct: float
    take_profit_pct: float
    
    @validator('imbalance_threshold')
    def validate_imbalance_threshold(cls, v):
        if not 0.5 <= v <= 1.0:
            raise ValueError('imbalance_threshold must be between 0.5 and 1.0')
        return v
    
    @validator('position_size')
    def validate_position_size(cls, v):
        if v <= 0:
            raise ValueError('position_size must be positive')
        return v

class BacktestConfig(BaseModel):
    """Configuration model for backtest parameters."""
    
    start_date: str
    end_date: str
    initial_capital: Decimal
    commission_rate: float
    
    @validator('commission_rate')
    def validate_commission_rate(cls, v):
        if not 0 <= v <= 0.1:
            raise ValueError('commission_rate must be between 0 and 0.1')
        return v
```

## Version Control Standards

### Commit Message Format
```
type(scope): description

[optional body]

[optional footer]
```

Examples:
- `feat(strategy): add order book imbalance strategy`
- `fix(data): handle missing timestamps in tick data`
- `docs(readme): update installation instructions`
- `test(backtest): add integration tests for optimization`
- `refactor(core): improve memory efficiency in data pipeline`

### Branch Naming
- `feature/strategy-implementation`
- `bugfix/data-loading-error`
- `hotfix/performance-issue`
- `docs/architecture-update`

## Quality Assurance

### Automated Checks
```bash
# Code formatting
uv run black src tests

# Import sorting and linting
uv run ruff check src tests

# Type checking
uv run mypy src

# Test execution
uv run pytest tests/ --cov=src

# Security scanning
uv run bandit -r src/
```

### Pre-commit Configuration
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.1.0
    hooks:
      - id: black
  
  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.0.254
    hooks:
      - id: ruff
  
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.0.1
    hooks:
      - id: mypy
        additional_dependencies: [types-PyYAML]
```

### Code Complexity Guidelines
- **Function length**: Maximum 50 lines
- **Cyclomatic complexity**: Maximum 10
- **Function parameters**: Maximum 7 parameters
- **Class size**: Maximum 500 lines
- **File size**: Maximum 1000 lines

## Security Considerations

### Data Protection
```python
# Never log sensitive data
def process_api_key(api_key: str) -> str:
    """Process API key without logging the actual value."""
    logger.info("Processing API key", extra={"key_length": len(api_key)})
    # Process key without exposing it
    return process_key(api_key)

# Use environment variables for sensitive configuration
import os
from strategy_lab.core.config import get_env_var

DATABASE_URL = get_env_var('DATABASE_URL', required=True)
API_SECRET = get_env_var('API_SECRET', required=True)
```

### Input Validation
```python
def validate_file_path(file_path: str) -> str:
    """Validate and sanitize file path."""
    # Ensure path is within allowed directories
    allowed_dirs = ['/data/MNQ', './data']
    resolved_path = os.path.abspath(file_path)
    
    if not any(resolved_path.startswith(os.path.abspath(d)) for d in allowed_dirs):
        raise ValueError(f"File path not in allowed directories: {file_path}")
    
    return resolved_path
```

## Documentation Requirements

### README Files
Each module should include a README.md with:
- Purpose and overview
- Installation/setup instructions
- Usage examples
- API documentation links
- Contributing guidelines

### API Documentation
- All public functions and classes must have docstrings
- Use Google-style docstrings for consistency
- Include examples in docstrings when helpful
- Generate API documentation with Sphinx

### Architecture Documentation
- Keep architecture documents updated with code changes
- Document design decisions and trade-offs
- Include performance benchmarks and measurements
- Maintain troubleshooting guides

This coding standards document ensures consistency, quality, and maintainability across the Strategy Lab codebase while supporting high-performance requirements for financial data processing.