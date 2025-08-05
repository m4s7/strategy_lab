# Strategy Lab Examples

This directory contains example scripts showing how to use the Strategy Lab backtesting framework.

## Prerequisites

1. Make sure you have MNQ tick data in the `data/MNQ/` directory
2. Install dependencies: `uv sync`
3. Ensure you're in the project root directory when running examples

## Available Examples

### 1. Basic Backtest (`run_backtest.py`)

Shows how to run a simple backtest with either strategy:

```bash
# Run from project root
python examples/run_backtest.py
```

This example demonstrates:
- Running Order Book Imbalance strategy
- Running Bid-Ask Bounce strategy
- Loading configuration from YAML files
- Displaying and saving results

### 2. Parallel Backtesting (`run_parallel_backtest.py`)

Shows advanced features like parameter optimization and strategy comparison:

```bash
# Run from project root
python examples/run_parallel_backtest.py
```

This example demonstrates:
- Parameter grid search optimization
- Running multiple backtests in parallel
- Comparing different strategies
- Finding optimal parameters

### 3. Command Line Interface (`backtest.py`)

Simple CLI for quick backtesting:

```bash
# Show help
python backtest.py --help

# Run Order Book Imbalance strategy
python backtest.py order_book_imbalance --start 2024-01-01 --end 2024-01-31

# Run Bid-Ask Bounce strategy with custom capital
python backtest.py bid_ask_bounce --start 2024-01-01 --end 2024-03-31 --capital 50000

# Specify contract months manually
python backtest.py order_book_imbalance --start 2024-01-01 --end 2024-06-30 --contracts 03-24 06-24
```

## Strategy Parameters

### Order Book Imbalance Strategy

```python
{
    "positive_threshold": 0.3,      # Long entry threshold
    "negative_threshold": -0.3,     # Short entry threshold
    "smoothing_window": 5,          # EMA window for smoothing
    "position_size": 1,             # Number of contracts
    "stop_loss_pct": 0.5,          # Stop loss percentage
    "max_holding_seconds": 300      # Maximum holding time
}
```

### Bid-Ask Bounce Strategy

```python
{
    "bounce_sensitivity": 0.7,      # Bounce detection sensitivity
    "min_bounce_strength": 0.5,     # Minimum bounce strength
    "profit_target_ticks": 2,       # Profit target in ticks
    "stop_loss_ticks": 1,          # Stop loss in ticks
    "max_spread_ticks": 2,         # Maximum spread filter
    "min_volume": 10,              # Minimum volume requirement
    "max_holding_seconds": 120      # Maximum holding time
}
```

## Data Requirements

The examples expect MNQ tick data organized as:
```
data/
  MNQ/
    03-24/  # March 2024 contract
      *.parquet
    06-24/  # June 2024 contract
      *.parquet
    ...
```

## Results

Backtest results are saved to the `results/` directory as JSON files containing:
- Performance metrics (PnL, Sharpe ratio, drawdown, etc.)
- Trade history
- Strategy parameters used
- Execution metadata

## Custom Strategies

To backtest your own strategy:

1. Create a strategy class inheriting from `PluggableStrategy`
2. Register it with `@register_strategy` decorator
3. Update the examples to use your strategy module and class

Example:
```python
from src.strategy_lab.strategies.registry import register_strategy
from src.strategy_lab.strategies.base import PluggableStrategy

@register_strategy("my_strategy")
class MyStrategy(PluggableStrategy):
    def process_tick(self, tick_data):
        # Your strategy logic here
        pass
```

## Troubleshooting

1. **Import errors**: Make sure you're running from the project root directory
2. **No data found**: Check that MNQ data exists in `data/MNQ/` for the specified dates
3. **Memory errors**: Reduce date range or use fewer contract months
4. **Slow performance**: Enable parallel processing with `max_workers` parameter

## Performance Tips

- Use parallel backtesting for parameter optimization
- Start with smaller date ranges for testing
- Monitor memory usage with large datasets
- Use the progress bar to track execution

For more information, see the main project documentation.
