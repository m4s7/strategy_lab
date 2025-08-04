# Getting Started with Strategy Lab

This guide will help you quickly get up and running with Strategy Lab, a high-performance futures trading backtesting framework for MNQ (Micro E-mini NASDAQ-100) strategies.

## Prerequisites

Before starting, ensure you have:

- **Python 3.12+** installed
- **uv package manager** (recommended) or pip
- **64GB RAM** recommended for large datasets
- **Ubuntu/Linux environment** (preferred)
- **MNQ tick data** in Parquet format (optional for initial testing)

## Installation

### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd strategy_lab

# Create virtual environment with uv
uv venv
source .venv/bin/activate

# Install dependencies
uv sync
```

### 2. Verify Installation

Run the quick start script to verify everything is working:

```bash
uv run python quick_start.py
```

You should see:
```
🚀 Strategy Lab Quick Start
==================================================
Testing component imports...
✓ Backtesting Engine
✓ Simple MA Strategy
✓ Grid Search Optimizer
✓ Genetic Algorithm Optimizer
✓ Configuration Loader

✅ All core components loaded successfully!
```

## Using the Command Line Interface

Strategy Lab provides a comprehensive CLI for all operations.

### Basic Commands

```bash
# Show help and available commands
uv run strategy-lab --help

# Display system information
uv run strategy-lab info

# List all available strategies
uv run strategy-lab list-strategies
```

### Configuration Management

#### Create a New Configuration

```bash
# Create from base template
uv run strategy-lab create-config --template base --output my_strategy.yaml

# Available templates:
# - base: Basic configuration template
# - production: Production-ready setup
# - bid_ask_bounce: Bid-ask bounce strategy
# - order_book_imbalance: Order book imbalance strategy
```

#### Configuration Structure

A typical configuration file includes:

```yaml
# Strategy configuration
strategy:
  name: "SimpleMAStrategy"
  parameters:
    fast_period: 10
    slow_period: 30
    position_size: 1

# Data configuration
data:
  source: "parquet"
  path: "./data/MNQ/"
  contracts: ["03-20", "06-20"]

# Backtesting parameters
backtest:
  start_date: "2023-01-01"
  end_date: "2023-12-31"
  initial_capital: 100000
```

### Running Backtests

#### Basic Backtest

```bash
# Run a backtest with your configuration
uv run strategy-lab backtest --config my_strategy.yaml

# With verbose output
uv run strategy-lab backtest --config my_strategy.yaml --verbose

# Save results to specific directory
uv run strategy-lab backtest --config my_strategy.yaml --output ./results/
```

#### Example Backtest Workflow

1. **Create Configuration:**
   ```bash
   uv run strategy-lab create-config --template base --output ma_strategy.yaml
   ```

2. **Edit Configuration:** Modify `ma_strategy.yaml` to set your parameters

3. **Run Backtest:**
   ```bash
   uv run strategy-lab backtest --config ma_strategy.yaml --verbose
   ```

### Parameter Optimization

Strategy Lab supports two optimization algorithms:

#### Grid Search Optimization

```bash
# Run grid search optimization
uv run strategy-lab optimize --config optimization_config.yaml --algorithm grid

# Example optimization config
```

Create an optimization configuration:

```yaml
# optimization_config.yaml
strategy:
  name: "SimpleMAStrategy"

optimization:
  algorithm: "grid_search"
  parameters:
    fast_period:
      type: "range"
      min: 5
      max: 20
      step: 5
    slow_period:
      type: "range"
      min: 20
      max: 50
      step: 10

  parallel: true
  n_workers: 8
```

#### Genetic Algorithm Optimization

```bash
# Run genetic algorithm optimization
uv run strategy-lab optimize --config genetic_config.yaml --algorithm genetic
```

Example genetic algorithm config:

```yaml
# genetic_config.yaml
strategy:
  name: "SimpleMAStrategy"

optimization:
  algorithm: "genetic"
  population_size: 100
  generations: 50
  crossover_prob: 0.8
  mutation_prob: 0.2

  parameters:
    fast_period:
      type: "continuous"
      min: 5.0
      max: 20.0
    slow_period:
      type: "continuous"
      min: 20.0
      max: 50.0
```

## Data Setup

### MNQ Data Structure

Strategy Lab expects MNQ tick data in Parquet format organized by contract month:

```
data/
└── MNQ/
    ├── 03-20/          # March 2020 contract
    │   ├── file1.parquet
    │   └── file2.parquet
    ├── 06-20/          # June 2020 contract
    └── 09-20/          # September 2020 contract
```

### Data Schema

The expected Parquet schema includes:

- **timestamp**: Nanosecond precision timestamps
- **price**: Decimal128 with 2 decimal places
- **volume**: Int32 trade/quote volume
- **mdt**: Market Data Type (0=Ask, 1=Bid, 2=Last, etc.)
- **level**: Data level indicator
- **operation**: Order book operations (0=Add, 1=Update, 2=Remove)
- **depth**: Order book depth level

### Sample Data

If you don't have MNQ data yet, you can:

1. **Use Demo Mode:** Some strategies can run in demo mode with synthetic data
2. **Contact Data Providers:** CME Group, IEX, or other market data vendors
3. **Use Sample Files:** Check if sample data is available in the repository

## Available Strategies

### Built-in Strategies

1. **SimpleMAStrategy**: Moving average crossover strategy
   - Parameters: `fast_period`, `slow_period`
   - Good for: Trend following

2. **BidAskBounceStrategy**: Scalping strategy based on bid-ask spread
   - Parameters: `threshold`, `position_size`
   - Good for: High-frequency scalping

3. **OrderBookImbalanceStrategy**: Strategy based on order book imbalance
   - Parameters: `imbalance_threshold`, `window_size`
   - Good for: Microstructure-based trading

### Creating Custom Strategies

Extend the base strategy class:

```python
from strategy_lab.strategies.base.pluggable_strategy import PluggableStrategy

class MyCustomStrategy(PluggableStrategy):
    def _initialize_strategy(self):
        # Initialize your strategy
        pass

    def _generate_signal(self, timestamp, price, volume, bid, ask, **kwargs):
        # Generate trading signals
        return signal  # 1=buy, -1=sell, 0=flat
```

## Development and Testing

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src

# Run specific test file
uv run pytest tests/test_strategies/test_examples/test_simple_ma_strategy.py
```

### Code Quality

```bash
# Format code
uv run black src tests

# Lint code
uv run ruff check src tests

# Type checking
uv run mypy src
```

## Monitoring and Analysis

### Performance Metrics

Strategy Lab provides comprehensive performance analysis:

- **Returns**: Total return, annualized return, excess return
- **Risk Metrics**: Sharpe ratio, Sortino ratio, maximum drawdown
- **Trade Analysis**: Win rate, average trade, profit factor
- **Risk Management**: VaR, CVaR, volatility metrics

### Visualization

Results include:

- **Equity Curves**: Portfolio value over time
- **Drawdown Charts**: Risk visualization
- **Trade Distribution**: P&L analysis
- **Parameter Sensitivity**: Optimization heatmaps

## Production Deployment

### Configuration for Production

Use the production template:

```bash
uv run strategy-lab create-config --template production --output prod_config.yaml
```

### Key Production Settings

- **Risk Management**: Position sizing, stop losses
- **Data Quality**: Validation and filtering
- **Performance Monitoring**: Real-time metrics
- **Logging**: Comprehensive trade and system logs

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure you're using `uv run` or have activated the virtual environment
2. **Data Not Found**: Check data path and file structure
3. **Memory Issues**: Reduce dataset size or increase system RAM
4. **Performance**: Enable parallel processing for optimization

### Getting Help

- **Documentation**: Check `docs/` directory for detailed guides
- **Examples**: Review `configs/` for example configurations
- **Logs**: Enable verbose/debug mode for detailed output
- **Tests**: Run tests to verify system integrity

### Support Commands

```bash
# System information
uv run strategy-lab info

# Verify installation
uv run python quick_start.py

# Test specific components
uv run pytest tests/test_strategies/ -v
```

## Next Steps

1. **Create Your First Strategy**: Start with a simple moving average strategy
2. **Prepare Your Data**: Set up MNQ tick data in the required format
3. **Run Backtests**: Test your strategy with historical data
4. **Optimize Parameters**: Use grid search or genetic algorithms
5. **Analyze Results**: Review performance metrics and visualizations
6. **Deploy**: Move to production with proper risk management

## Quick Reference

### Essential Commands

```bash
# Setup
uv run python quick_start.py          # Verify installation
uv run strategy-lab info               # System status

# Configuration
uv run strategy-lab create-config      # Create config
uv run strategy-lab list-strategies    # List strategies

# Execution
uv run strategy-lab backtest -c config.yaml    # Run backtest
uv run strategy-lab optimize -c config.yaml    # Optimize parameters

# Development
uv run pytest                         # Run tests
uv run black src tests               # Format code
```

### File Locations

- **Configurations**: `./configs/` or current directory
- **Data**: `./data/MNQ/`
- **Results**: `./results/` (configurable)
- **Logs**: Standard output or log files
- **Templates**: `./src/strategy_lab/core/config/templates/`

Strategy Lab is now ready for professional quantitative trading strategy development and backtesting. Start with simple strategies and gradually build complexity as you become familiar with the framework.
