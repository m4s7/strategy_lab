# Strategy Lab Source Tree Structure

## Overview

This document defines the complete source code organization for the Strategy Lab futures trading backtesting framework. The structure is designed for clarity, maintainability, and efficient development workflow.

## Repository Root Structure

```
strategy_lab/
├── README.md                           # Project overview and quick start
├── pyproject.toml                      # Project configuration and dependencies
├── .gitignore                          # Git ignore patterns
├── .pre-commit-config.yaml            # Pre-commit hook configuration
├── CLAUDE.md                           # Claude Code assistant instructions
├── LICENSE                             # Project license
├── CHANGELOG.md                        # Version history and changes
├── 
├── src/                                # Main source code directory
│   └── strategy_lab/                   # Python package root
├── tests/                              # Test suite
├── docs/                               # Documentation
├── data/                               # Data files (gitignored)
├── configs/                            # Configuration templates
├── scripts/                            # Utility and automation scripts
├── notebooks/                          # Jupyter notebooks for analysis
├── logs/                               # Application logs (gitignored)
├── results/                            # Backtest results (gitignored)
├── .bmad-core/                         # BMad framework files
└── knowledge-base/                     # Project knowledge documentation
```

## Source Code Structure (`src/strategy_lab/`)

### Main Package Organization

```
src/strategy_lab/
├── __init__.py                         # Package initialization
├── __version__.py                      # Version information
├── cli/                                # Command-line interface
├── core/                               # Core framework components
├── data/                               # Data processing and ingestion
├── strategies/                         # Trading strategy implementations
├── backtesting/                        # Backtesting engine integration
├── optimization/                       # Parameter optimization algorithms
├── analysis/                           # Performance analysis and metrics
├── utils/                              # Utility functions and helpers
└── api/                                # API interfaces (future)
```

### Command Line Interface (`cli/`)

```
cli/
├── __init__.py
├── main.py                             # Main CLI entry point
├── commands/
│   ├── __init__.py
│   ├── backtest.py                     # Backtest execution commands
│   ├── optimize.py                     # Optimization commands
│   ├── data.py                         # Data management commands
│   ├── config.py                       # Configuration management
│   └── analyze.py                      # Analysis and reporting commands
├── utils/
│   ├── __init__.py
│   ├── output.py                       # CLI output formatting
│   ├── progress.py                     # Progress bar and status
│   └── validation.py                   # Input validation helpers
└── templates/                          # CLI output templates
    ├── backtest_summary.txt
    ├── optimization_report.txt
    └── strategy_config.yaml
```

### Core Framework (`core/`)

```
core/
├── __init__.py
├── config/
│   ├── __init__.py
│   ├── manager.py                      # Configuration management
│   ├── models.py                       # Pydantic configuration models
│   ├── validation.py                   # Configuration validation
│   └── defaults.py                     # Default configuration values
├── logging/
│   ├── __init__.py
│   ├── setup.py                        # Logging configuration
│   ├── formatters.py                   # Log formatting
│   └── handlers.py                     # Custom log handlers
├── exceptions/
│   ├── __init__.py
│   ├── base.py                         # Base exception classes
│   ├── data.py                         # Data-related exceptions
│   ├── strategy.py                     # Strategy-related exceptions
│   └── backtest.py                     # Backtest-related exceptions
├── types/
│   ├── __init__.py
│   ├── market_data.py                  # Market data type definitions
│   ├── strategy.py                     # Strategy type definitions
│   ├── backtest.py                     # Backtest type definitions
│   └── common.py                       # Common type definitions
├── registry/
│   ├── __init__.py
│   ├── strategy.py                     # Strategy registry
│   ├── optimizer.py                    # Optimizer registry
│   └── base.py                         # Base registry functionality
└── events/
    ├── __init__.py
    ├── dispatcher.py                   # Event dispatcher
    ├── handlers.py                     # Event handlers
    └── types.py                        # Event type definitions
```

### Data Processing (`data/`)

```
data/
├── __init__.py
├── ingestion/
│   ├── __init__.py
│   ├── parquet_loader.py               # Parquet file loading
│   ├── data_validator.py               # Data quality validation
│   ├── schema_manager.py               # Data schema management
│   └── file_discovery.py               # Data file discovery
├── processing/
│   ├── __init__.py
│   ├── tick_processor.py               # Tick data processing
│   ├── order_book.py                   # Order book reconstruction
│   ├── market_data.py                  # Market data transformations
│   └── filters.py                      # Data filtering and cleaning
├── storage/
│   ├── __init__.py
│   ├── cache_manager.py                # Data caching
│   ├── result_store.py                 # Result persistence
│   └── metadata.py                     # Metadata management
├── adapters/
│   ├── __init__.py
│   ├── hftbacktest.py                  # hftbacktest data adapter
│   ├── pandas.py                       # Pandas data adapter
│   └── base.py                         # Base adapter interface
└── models/
    ├── __init__.py
    ├── tick_data.py                    # Tick data models
    ├── order_book.py                   # Order book models
    └── market_state.py                 # Market state models
```

### Strategy Framework (`strategies/`)

```
strategies/
├── __init__.py
├── base/
│   ├── __init__.py
│   ├── strategy.py                     # Base strategy interface
│   ├── signal_generator.py             # Signal generation base
│   ├── position_manager.py             # Position management base
│   └── risk_manager.py                 # Risk management base
├── implementations/
│   ├── __init__.py
│   ├── order_book_imbalance.py         # Order book imbalance strategy
│   ├── bid_ask_bounce.py               # Bid-ask bounce strategy
│   ├── momentum_scalper.py             # Momentum scalping strategy
│   └── mean_reversion.py               # Mean reversion strategy
├── components/
│   ├── __init__.py
│   ├── indicators/
│   │   ├── __init__.py
│   │   ├── technical.py                # Technical indicators
│   │   ├── order_book.py               # Order book indicators
│   │   └── custom.py                   # Custom indicators
│   ├── signals/
│   │   ├── __init__.py
│   │   ├── entry.py                    # Entry signal logic
│   │   ├── exit.py                     # Exit signal logic
│   │   └── filters.py                  # Signal filters
│   └── rules/
│       ├── __init__.py
│       ├── entry_rules.py              # Entry rule definitions
│       ├── exit_rules.py               # Exit rule definitions
│       └── risk_rules.py               # Risk management rules
├── factory/
│   ├── __init__.py
│   ├── strategy_factory.py             # Strategy creation factory
│   └── component_factory.py            # Component creation factory
└── templates/
    ├── __init__.py
    ├── scalping_template.py             # Scalping strategy template
    ├── arbitrage_template.py            # Arbitrage strategy template
    └── basic_template.py                # Basic strategy template
```

### Backtesting Engine (`backtesting/`)

```
backtesting/
├── __init__.py
├── engine/
│   ├── __init__.py
│   ├── backtest_engine.py              # Main backtesting engine
│   ├── simulation.py                   # Market simulation
│   ├── execution.py                    # Order execution logic
│   └── portfolio.py                    # Portfolio management
├── hft_integration/
│   ├── __init__.py
│   ├── adapter.py                      # hftbacktest adapter
│   ├── data_feed.py                    # Data feed integration
│   └── event_processor.py              # Event processing
├── metrics/
│   ├── __init__.py
│   ├── performance.py                  # Performance metrics
│   ├── risk.py                         # Risk metrics
│   ├── trade_analysis.py               # Trade analysis
│   └── drawdown.py                     # Drawdown analysis
├── reports/
│   ├── __init__.py
│   ├── generator.py                    # Report generation
│   ├── formatters.py                   # Output formatting
│   └── templates/                      # Report templates
│       ├── html_report.html
│       ├── text_summary.txt
│       └── csv_trades.csv
└── validators/
    ├── __init__.py
    ├── config_validator.py             # Configuration validation
    ├── data_validator.py               # Data validation
    └── result_validator.py             # Result validation
```

### Optimization Framework (`optimization/`)

```
optimization/
├── __init__.py
├── algorithms/
│   ├── __init__.py
│   ├── grid_search.py                  # Grid search optimization
│   ├── genetic_algorithm.py            # Genetic algorithm optimization
│   ├── random_search.py                # Random search optimization
│   ├── bayesian.py                     # Bayesian optimization
│   └── base.py                         # Base optimizer interface
├── objectives/
│   ├── __init__.py
│   ├── single_objective.py             # Single objective functions
│   ├── multi_objective.py              # Multi-objective functions
│   └── custom.py                       # Custom objective functions
├── constraints/
│   ├── __init__.py
│   ├── parameter_bounds.py             # Parameter bound constraints
│   ├── risk_constraints.py             # Risk-based constraints
│   └── business_rules.py               # Business rule constraints
├── parallel/
│   ├── __init__.py
│   ├── executor.py                     # Parallel execution manager
│   ├── worker.py                       # Worker process implementation
│   └── scheduler.py                    # Task scheduling
├── analysis/
│   ├── __init__.py
│   ├── convergence.py                  # Convergence analysis
│   ├── sensitivity.py                  # Sensitivity analysis
│   └── visualization.py                # Optimization visualization
└── walk_forward/
    ├── __init__.py
    ├── analyzer.py                     # Walk-forward analysis
    ├── scheduler.py                    # Time window scheduling
    └── validator.py                    # Out-of-sample validation
```

### Analysis and Reporting (`analysis/`)

```
analysis/
├── __init__.py
├── performance/
│   ├── __init__.py
│   ├── returns.py                      # Return analysis
│   ├── ratios.py                       # Performance ratios
│   ├── attribution.py                  # Performance attribution
│   └── benchmarking.py                 # Benchmark comparison
├── risk/
│   ├── __init__.py
│   ├── value_at_risk.py                # VaR calculations
│   ├── stress_testing.py               # Stress testing
│   ├── correlation.py                  # Correlation analysis
│   └── exposure.py                     # Risk exposure analysis
├── trade/
│   ├── __init__.py
│   ├── trade_analysis.py               # Individual trade analysis
│   ├── holding_periods.py              # Holding period analysis
│   ├── patterns.py                     # Trading pattern analysis
│   └── clustering.py                   # Trade clustering
├── visualization/
│   ├── __init__.py
│   ├── charts.py                       # Chart generation
│   ├── plots.py                        # Statistical plots
│   ├── dashboards.py                   # Dashboard creation
│   └── interactive.py                  # Interactive visualizations
└── statistics/
    ├── __init__.py
    ├── descriptive.py                  # Descriptive statistics
    ├── hypothesis_testing.py           # Statistical tests
    └── time_series.py                  # Time series analysis
```

### Utilities (`utils/`)

```
utils/
├── __init__.py
├── math/
│   ├── __init__.py
│   ├── statistics.py                   # Statistical functions
│   ├── financial.py                    # Financial calculations
│   └── optimization.py                 # Optimization utilities
├── data/
│   ├── __init__.py
│   ├── transformations.py              # Data transformations
│   ├── validation.py                   # Data validation utilities
│   └── formatting.py                   # Data formatting
├── time/
│   ├── __init__.py
│   ├── datetime_utils.py               # DateTime utilities
│   ├── business_calendar.py            # Business day calculations
│   └── timezone_handling.py            # Timezone management
├── io/
│   ├── __init__.py
│   ├── file_utils.py                   # File I/O utilities
│   ├── compression.py                  # Compression utilities
│   └── serialization.py                # Object serialization
├── memory/
│   ├── __init__.py
│   ├── profiler.py                     # Memory profiling
│   ├── cache.py                        # Caching utilities
│   └── optimization.py                 # Memory optimization
└── system/
    ├── __init__.py
    ├── resources.py                    # System resource monitoring
    ├── platform.py                     # Platform-specific utilities
    └── environment.py                  # Environment detection
```

## Test Structure (`tests/`)

```
tests/
├── __init__.py
├── conftest.py                         # Pytest configuration and fixtures
├── unit/                               # Unit tests
│   ├── __init__.py
│   ├── test_core/
│   │   ├── __init__.py
│   │   ├── test_config.py
│   │   ├── test_logging.py
│   │   └── test_exceptions.py
│   ├── test_data/
│   │   ├── __init__.py
│   │   ├── test_ingestion.py
│   │   ├── test_processing.py
│   │   └── test_order_book.py
│   ├── test_strategies/
│   │   ├── __init__.py
│   │   ├── test_base.py
│   │   ├── test_order_book_imbalance.py
│   │   └── test_bid_ask_bounce.py
│   ├── test_backtesting/
│   │   ├── __init__.py
│   │   ├── test_engine.py
│   │   ├── test_metrics.py
│   │   └── test_reports.py
│   ├── test_optimization/
│   │   ├── __init__.py
│   │   ├── test_grid_search.py
│   │   ├── test_genetic_algorithm.py
│   │   └── test_walk_forward.py
│   └── test_utils/
│       ├── __init__.py
│       ├── test_math.py
│       ├── test_data_utils.py
│       └── test_time_utils.py
├── integration/                        # Integration tests
│   ├── __init__.py
│   ├── test_data_pipeline.py
│   ├── test_backtest_pipeline.py
│   ├── test_optimization_pipeline.py
│   └── test_end_to_end.py
├── performance/                        # Performance tests
│   ├── __init__.py
│   ├── test_data_loading.py
│   ├── test_strategy_execution.py
│   └── test_optimization_speed.py
├── fixtures/                           # Test data and fixtures
│   ├── __init__.py
│   ├── sample_data/
│   │   ├── test_tick_data.parquet
│   │   ├── test_config.yaml
│   │   └── expected_results.json
│   └── mocks/
│       ├── __init__.py
│       ├── mock_data_feed.py
│       └── mock_strategies.py
└── utils/                              # Test utilities
    ├── __init__.py
    ├── data_generators.py              # Test data generation
    ├── assertions.py                   # Custom assertions
    └── helpers.py                      # Test helper functions
```

## Configuration Structure (`configs/`)

```
configs/
├── strategies/                         # Strategy configurations
│   ├── order_book_imbalance.yaml
│   ├── bid_ask_bounce.yaml
│   └── template.yaml
├── optimization/                       # Optimization configurations
│   ├── grid_search.yaml
│   ├── genetic_algorithm.yaml
│   └── walk_forward.yaml
├── backtesting/                        # Backtesting configurations
│   ├── default.yaml
│   ├── high_frequency.yaml
│   └── research.yaml
├── system/                             # System configurations
│   ├── logging.yaml
│   ├── performance.yaml
│   └── development.yaml
└── examples/                           # Example configurations
    ├── quick_start.yaml
    ├── full_backtest.yaml
    └── parameter_sweep.yaml
```

## Documentation Structure (`docs/`)

```
docs/
├── README.md                           # Documentation overview
├── architecture/                       # Architecture documentation
│   ├── README.md
│   ├── 01-overview.md
│   ├── 02-system-architecture.md
│   ├── 03-module-structure.md
│   ├── 04-data-architecture.md
│   ├── 05-strategy-framework.md
│   ├── 06-backtesting-engine.md
│   ├── 07-optimization-architecture.md
│   ├── 08-performance-scalability.md
│   ├── 09-configuration-deployment.md
│   ├── 10-testing-security.md
│   ├── coding-standards.md             # This document
│   ├── tech-stack.md                   # Technology stack
│   └── source-tree.md                  # This document
├── user-guide/                         # User documentation
│   ├── README.md
│   ├── installation.md
│   ├── quick-start.md
│   ├── strategy-development.md
│   ├── backtesting-guide.md
│   ├── optimization-guide.md
│   └── troubleshooting.md
├── api/                                # API documentation
│   ├── README.md
│   ├── core.md
│   ├── strategies.md
│   ├── backtesting.md
│   └── optimization.md
├── tutorials/                          # Step-by-step tutorials
│   ├── README.md
│   ├── first-strategy.md
│   ├── data-analysis.md
│   ├── optimization-tutorial.md
│   └── advanced-techniques.md
└── examples/                           # Code examples
    ├── README.md
    ├── basic_backtest.py
    ├── custom_strategy.py
    ├── optimization_example.py
    └── analysis_examples.py
```

## Utility Scripts (`scripts/`)

```
scripts/
├── development/                        # Development utilities
│   ├── setup_environment.py
│   ├── generate_test_data.py
│   ├── run_quality_checks.py
│   └── profile_performance.py
├── data/                               # Data management scripts
│   ├── validate_parquet_files.py
│   ├── convert_data_format.py
│   ├── clean_data_directory.py
│   └── generate_metadata.py
├── deployment/                         # Deployment scripts
│   ├── build_package.py
│   ├── run_tests.py
│   └── deploy.sh
└── maintenance/                        # Maintenance scripts
    ├── cleanup_logs.py
    ├── backup_results.py
    └── update_dependencies.py
```

## Analysis Notebooks (`notebooks/`)

```
notebooks/
├── README.md                           # Notebook overview
├── exploratory/                        # Exploratory data analysis
│   ├── data_exploration.ipynb
│   ├── market_microstructure.ipynb
│   └── order_book_analysis.ipynb
├── strategy_development/               # Strategy development notebooks
│   ├── strategy_research.ipynb
│   ├── signal_analysis.ipynb
│   └── parameter_sensitivity.ipynb
├── backtesting/                        # Backtesting analysis
│   ├── performance_analysis.ipynb
│   ├── risk_analysis.ipynb
│   └── trade_analysis.ipynb
├── optimization/                       # Optimization analysis
│   ├── parameter_optimization.ipynb
│   ├── walk_forward_analysis.ipynb
│   └── multi_objective_optimization.ipynb
└── templates/                          # Notebook templates
    ├── strategy_template.ipynb
    ├── analysis_template.ipynb
    └── optimization_template.ipynb
```

## File Naming Conventions

### Python Files
- **Modules**: Use snake_case (e.g., `order_book_processor.py`)
- **Classes**: Use PascalCase (e.g., `OrderBookProcessor`)
- **Functions**: Use snake_case (e.g., `calculate_imbalance`)
- **Constants**: Use UPPER_SNAKE_CASE (e.g., `DEFAULT_TIMEOUT`)

### Configuration Files
- **Strategy configs**: `{strategy_name}.yaml`
- **System configs**: `{component}.yaml`
- **Environment configs**: `{environment}.yaml`

### Test Files
- **Unit tests**: `test_{module_name}.py`
- **Integration tests**: `test_{feature}_integration.py`
- **Performance tests**: `test_{component}_performance.py`

### Documentation Files
- **Architecture docs**: `{nn}-{topic}.md` (numbered)
- **User guides**: `{topic}-guide.md`
- **API docs**: `{module}.md`

## Import Path Guidelines

### Absolute Imports
```python
# Preferred: Absolute imports from package root
from strategy_lab.core.config import ConfigManager
from strategy_lab.strategies.base import StrategyBase
from strategy_lab.data.processing import TickProcessor
```

### Relative Imports
```python
# Within same package only
from .base import StrategyBase
from ..core.config import ConfigManager
```

### External Dependencies
```python
# Group external imports
import pandas as pd
import numpy as np
from hftbacktest import BacktestEngine

# Then internal imports
from strategy_lab.core.config import ConfigManager
```

## Version and Release Management

### Version Numbering
- **Format**: Semantic versioning (MAJOR.MINOR.PATCH)
- **Location**: `src/strategy_lab/__version__.py`
- **Automation**: Automated version bumping with release scripts

### Release Structure
```
releases/
├── v0.1.0/
│   ├── release_notes.md
│   ├── migration_guide.md
│   └── changelog.md
└── v0.2.0/
    ├── release_notes.md
    ├── migration_guide.md
    └── changelog.md
```

This source tree structure provides a solid foundation for the Strategy Lab project, ensuring clear organization, maintainability, and scalability as the codebase grows. The structure supports both the immediate development needs and future expansion of the framework.