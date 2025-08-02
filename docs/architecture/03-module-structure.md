# Strategy Lab Technical Architecture - Module Structure

## Module Organization

The Strategy Lab follows a clear hierarchical module structure designed for maintainability and logical separation of concerns.

```
strategy_lab/
├── src/
│   ├── core/                          # Core infrastructure
│   │   ├── __init__.py
│   │   ├── config.py                  # Configuration management
│   │   ├── logging.py                 # Centralized logging
│   │   ├── exceptions.py              # Custom exceptions
│   │   └── utils.py                   # Common utilities
│   │
│   ├── data/                          # Data layer
│   │   ├── __init__.py
│   │   ├── ingestion.py              # Parquet data loading
│   │   ├── validation.py             # Data quality checks
│   │   ├── orderbook.py              # Order book reconstruction
│   │   ├── contracts.py              # Contract rollover logic
│   │   └── streaming.py              # Memory-efficient streaming
│   │
│   ├── backtesting/                   # Backtesting engine
│   │   ├── __init__.py
│   │   ├── engine.py                 # Main backtesting engine
│   │   ├── executor.py               # Trade execution logic
│   │   ├── market_sim.py             # Market simulation
│   │   └── event_handler.py          # Event processing
│   │
│   ├── strategies/                    # Strategy framework
│   │   ├── __init__.py
│   │   ├── base.py                   # Base strategy class
│   │   ├── registry.py               # Strategy registry
│   │   ├── config_manager.py         # Strategy configuration
│   │   ├── examples/                 # Example implementations
│   │   │   ├── __init__.py
│   │   │   ├── orderbook_imbalance.py
│   │   │   └── bid_ask_bounce.py
│   │   └── utils.py                  # Strategy utilities
│   │
│   ├── optimization/                  # Optimization framework
│   │   ├── __init__.py
│   │   ├── base.py                   # Base optimizer class
│   │   ├── grid_search.py            # Grid search implementation
│   │   ├── genetic.py                # Genetic algorithm
│   │   ├── walk_forward.py           # Walk-forward analysis
│   │   ├── parallel.py               # Parallel processing
│   │   └── metrics.py                # Optimization metrics
│   │
│   ├── analytics/                     # Performance analysis
│   │   ├── __init__.py
│   │   ├── metrics.py                # Performance metrics
│   │   ├── risk.py                   # Risk analysis
│   │   ├── statistics.py             # Statistical analysis
│   │   └── comparisons.py            # Strategy comparisons
│   │
│   ├── reporting/                     # Reporting system
│   │   ├── __init__.py
│   │   ├── generators.py             # Report generation
│   │   ├── visualizations.py         # Charts and plots
│   │   ├── exporters.py              # Data export
│   │   └── templates/                # Report templates
│   │
│   └── cli/                          # Command line interface
│       ├── __init__.py
│       ├── main.py                   # Main CLI entry point
│       ├── commands.py               # CLI commands
│       └── validators.py             # Input validation
│
├── tests/                            # Test suite
│   ├── unit/                         # Unit tests
│   ├── integration/                  # Integration tests
│   ├── fixtures/                     # Test data
│   └── conftest.py                   # Pytest configuration
│
├── config/                           # Configuration files
│   ├── default.yaml                  # Default configuration
│   ├── strategies/                   # Strategy configs
│   └── optimization/                 # Optimization configs
│
├── docs/                            # Documentation
│   ├── project-brief.md
│   ├── prd/                         # Sharded PRD
│   ├── architecture/                # Sharded architecture docs
│   └── api/                         # API documentation
│
└── data/                            # Data directory (not in git)
    └── MNQ/                         # MNQ tick data
```

## Module Descriptions

### Core Module (`src/core/`)
Foundation utilities used across all other modules.

- **config.py**: Centralized configuration management, YAML loading, validation
- **logging.py**: Structured logging setup, performance logging, error tracking
- **exceptions.py**: Custom exception hierarchy for better error handling
- **utils.py**: Common utilities like date parsing, data type conversions

### Data Module (`src/data/`)
Handles all aspects of data ingestion and preparation.

- **ingestion.py**: Parquet file loading, memory management, batch processing
- **validation.py**: Schema validation, data quality checks, missing data handling
- **orderbook.py**: L2 reconstruction, order book state management, imbalance calculations
- **contracts.py**: Contract month handling, rollover logic, continuous series
- **streaming.py**: Chunked data processing, memory-efficient iterators

### Backtesting Module (`src/backtesting/`)
Core backtesting engine integration with hftbacktest.

- **engine.py**: Main backtesting orchestration, hftbacktest wrapper
- **executor.py**: Order execution simulation, fill logic, slippage modeling
- **market_sim.py**: Market mechanics, trading hours, halt conditions
- **event_handler.py**: Event routing, strategy callbacks, performance monitoring

### Strategies Module (`src/strategies/`)
Pluggable strategy framework and implementations.

- **base.py**: Abstract base class, common strategy functionality
- **registry.py**: Dynamic strategy loading, registration, discovery
- **config_manager.py**: Strategy-specific configuration handling
- **examples/**: Reference implementations demonstrating framework usage
- **utils.py**: Technical indicators, common calculations

### Optimization Module (`src/optimization/`)
Advanced parameter optimization capabilities.

- **base.py**: Common optimization interface, result storage
- **grid_search.py**: Exhaustive parameter search, result ranking
- **genetic.py**: DEAP integration, evolutionary optimization
- **walk_forward.py**: Rolling window optimization, out-of-sample testing
- **parallel.py**: Multiprocessing management, work distribution
- **metrics.py**: Optimization objectives, performance scoring

### Analytics Module (`src/analytics/`)
Comprehensive performance analysis tools.

- **metrics.py**: PnL, Sharpe ratio, win rate, drawdown calculations
- **risk.py**: VaR, CVaR, maximum drawdown, risk-adjusted returns
- **statistics.py**: Trade statistics, distribution analysis, significance tests
- **comparisons.py**: Multi-strategy comparison, benchmarking

### Reporting Module (`src/reporting/`)
Result visualization and export capabilities.

- **generators.py**: Report creation, template filling, formatting
- **visualizations.py**: matplotlib integration, chart generation
- **exporters.py**: CSV, JSON, Excel export functionality
- **templates/**: Jinja2 templates for HTML reports

### CLI Module (`src/cli/`)
User interface and command management.

- **main.py**: Entry point, argument parsing, command routing
- **commands.py**: Command implementations (backtest, optimize, etc.)
- **validators.py**: Input validation, parameter checking

## Module Dependencies

```
cli → all modules (orchestration)
optimization → backtesting, analytics
backtesting → data, strategies, analytics
strategies → data (for market data access)
analytics → (standalone, no dependencies)
reporting → analytics
data → core
all modules → core (for utilities)
```

## Import Guidelines

### Absolute Imports
Always use absolute imports from `src` root:
```python
from src.data.ingestion import ParquetDataLoader
from src.strategies.base import BaseStrategy
```

### Circular Import Prevention
- Core module cannot import from other modules
- Data module only imports from core
- Strategies import from data and core only
- Clear dependency hierarchy prevents circular imports

### Public API Definition
Each module's `__init__.py` defines its public API:
```python
# src/data/__init__.py
from .ingestion import ParquetDataLoader
from .orderbook import OrderBookReconstructor

__all__ = ['ParquetDataLoader', 'OrderBookReconstructor']
```