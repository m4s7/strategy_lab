# How to Run Backtests with Strategy Lab

Strategy Lab provides multiple ways to run backtests with your MNQ tick data. This guide shows you the practical approaches that work with the large data files.

## ⚠️ Important: Data Size Considerations

MNQ tick data is extremely large:
- **31+ million ticks per day**
- **6-8 GB memory per day when loaded**
- **Takes 15-20 seconds just to load one day**

For practical backtesting, you should:
1. Test on small time windows first (minutes, not hours)
2. Use the streaming/chunked approaches below
3. Consider data sampling for strategy development

## 🚀 Quick Start: Practical Backtest (Recommended)

The easiest way to run a backtest:

```bash
# Test order book imbalance strategy for 5 minutes
python practical_backtest.py --strategy order_book_imbalance --minutes 5

# Test bid-ask bounce strategy for 10 minutes at a specific time
python practical_backtest.py --strategy bid_ask_bounce --minutes 10 --start-time "2024-01-02 14:30"

# Options:
# --strategy: order_book_imbalance or bid_ask_bounce
# --minutes: Duration in minutes (default: 5)
# --start-time: Start time (default: "2024-01-02 09:30:00")
# --date: Date to test (default: "2024-01-02")
```

### What this does:
- Loads only the specified time window from the large data file
- Runs the strategy on real tick data
- Shows trade execution and results
- Handles memory efficiently

## 📊 Example Output

```
Practical MNQ Backtest
==================================================
Strategy: order_book_imbalance
Date: 2024-01-02
Start: 2024-01-02 09:30:00
Duration: 5 minutes
==================================================
Loading 5 minutes of data starting at 2024-01-02 09:30:00...
Loaded 35,129 ticks in 23.14s

Running order_book_imbalance strategy...
Initial capital: $100,000.00
Processing ticks...
  Trade 1: BUY @ $17005.25
  Trade 2: SELL @ $17007.75 (PnL: $5.00)

=== RESULTS ===
Processed: 35,129 ticks
Total trades: 3 round trips
Win rate: 66.7%
Total PnL: $8.50
Return: 0.01%
Final balance: $100,008.50
```

## 🏗️ Framework Integration (Advanced)

For integration with the full framework:

```python
from datetime import datetime
from pathlib import Path
from decimal import Decimal

from src.strategy_lab.backtesting.engine import BacktestEngine
from src.strategy_lab.backtesting.engine.config import BacktestConfig

# Configure backtest (use SHORT time ranges!)
config = BacktestConfig(
    name="my_backtest",
    description="Test backtest",

    strategy={
        "name": "OrderBookImbalanceStrategy",
        "module": "src.strategy_lab.strategies.implementations.order_book_imbalance",
        "parameters": {
            "positive_threshold": 0.3,
            "negative_threshold": -0.3,
            "position_size": 1,
        }
    },

    data={
        "symbol": "MNQ",
        "data_path": Path("data/MNQ"),
        "contracts": ["03-24"],
        "validate_data": False,  # Skip validation due to data format
    },

    execution={
        # IMPORTANT: Use short time ranges!
        "start_date": datetime(2024, 1, 2, 9, 30),
        "end_date": datetime(2024, 1, 2, 9, 35),  # Just 5 minutes
        "initial_capital": Decimal("100000"),
        "commission": Decimal("2.0"),
        "slippage": Decimal("0.25"),
    }
)

# Run backtest
engine = BacktestEngine()
job_id = engine.create_backtest(config, validate=False)
result = engine.run_backtest(job_id)

print(f"Total PnL: ${result.total_pnl:.2f}")
```

## 📋 Available Strategies

### 1. Order Book Imbalance Strategy
- **Module**: `order_book_imbalance`
- **Description**: Uses Level 2 market depth data to detect imbalances
- **Parameters**:
  - `positive_threshold`: Long entry threshold (default: 0.3)
  - `negative_threshold`: Short entry threshold (default: -0.3)
  - `smoothing_window`: EMA smoothing window (default: 5)
  - `position_size`: Contracts per trade (default: 1)
  - `stop_loss_pct`: Stop loss percentage (default: 0.5)

### 2. Bid-Ask Bounce Strategy
- **Module**: `bid_ask_bounce`
- **Description**: Detects price bounces off bid/ask levels
- **Parameters**:
  - `bounce_sensitivity`: Detection sensitivity (default: 0.7)
  - `min_bounce_strength`: Minimum bounce strength (default: 0.5)
  - `profit_target_ticks`: Profit target in ticks (default: 2)
  - `stop_loss_ticks`: Stop loss in ticks (default: 1)
  - `max_holding_seconds`: Max hold time (default: 120)

## 📈 Data Analysis

The MNQ data contains:
- **Level 1**: Best bid/ask and trades
- **Level 2**: Full order book depth (5+ levels)
- **Timestamp**: Nanosecond precision
- **Price**: Decimal precision (stored as string)
- **Volume**: Trade/quote volume

### Data Schema:
```
level: 'L1' or 'L2'
mdt: Market Data Type (0=Ask, 1=Bid, 2=Last, etc.)
timestamp: Nanosecond timestamps
price: Decimal price (as string)
volume: Integer volume
operation: Order book operations (0=Add, 1=Update, 2=Remove)
depth: Order book depth level
market_maker: Market maker ID
```

## 🔧 Troubleshooting

### "Validation Error: End date must be after start date"
- **Fix**: The CLI automatically handles same-day backtests now
- **Manual fix**: Set end_date to later in the day

### "Memory Error" or "Process Killed"
- **Cause**: Trying to load too much data at once
- **Fix**: Use shorter time windows (minutes instead of hours)
- **Fix**: Use the `practical_backtest.py` script instead

### "No trades executed"
- **Normal**: Strategies may not trigger in short time windows
- **Try**: Longer time windows or different market hours
- **Try**: Adjust strategy parameters (lower thresholds)

### "Data validation failed"
- **Fix**: Use `validate_data: False` in configuration
- **Cause**: Data format differs from expected schema

## 💡 Best Practices

1. **Start Small**: Begin with 1-5 minute windows
2. **Use Market Hours**: 9:30 AM - 4:00 PM ET for active trading
3. **Monitor Memory**: Each minute ≈ 7,000 ticks ≈ 1.5 MB
4. **Test Parameters**: Start with default strategy parameters
5. **Check Results**: Verify trades make sense given market conditions

## 📝 Next Steps

After running basic backtests:

1. **Parameter Optimization**: Test different strategy parameters
2. **Longer Time Periods**: Gradually increase backtest duration
3. **Multiple Days**: Test across different market conditions
4. **Custom Strategies**: Develop your own trading strategies
5. **Performance Analysis**: Use the analytics framework for detailed analysis

## 🔗 Related Files

- `practical_backtest.py` - Main backtest script (recommended)
- `backtest.py` - Original CLI (needs data size fixes)
- `working_backtest.py` - Educational example
- `examples/` - Additional examples and documentation
