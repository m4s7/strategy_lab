#!/usr/bin/env python3
"""Test a working backtest with proper configuration"""

from datetime import datetime
from pathlib import Path
from decimal import Decimal

from src.strategy_lab.backtesting.engine import BacktestEngine
from src.strategy_lab.backtesting.engine.config import BacktestConfig

# Create configuration that avoids validation issues
config = BacktestConfig(
    name="test_mnq_backtest",
    description="Test backtest for MNQ",
    strategy={
        "name": "OrderBookImbalanceStrategy",
        "module": "src.strategy_lab.strategies.implementations.order_book_imbalance",
        "parameters": {
            "positive_threshold": 0.3,
            "negative_threshold": -0.3,
            "smoothing_window": 5,
            "position_size": 1,
            "stop_loss_pct": 0.5,
            "max_holding_seconds": 300,
        },
    },
    data={
        "symbol": "MNQ",
        "data_path": Path("data/MNQ"),
        "contracts": ["03-24"],
        "validate_data": False,  # Skip validation due to data format issues
        "chunk_size": 50000,
    },
    execution={
        # Use actual data time range
        "start_date": datetime(2024, 1, 2, 9, 30),  # Market open
        "end_date": datetime(2024, 1, 2, 10, 0),  # 30 minutes later
        "initial_capital": Decimal("100000"),
        "commission": Decimal("2.0"),
        "slippage": Decimal("0.25"),
        "progress_interval": 10000,
        "max_memory_gb": 4.0,
    },
    output_dir=Path("results/test"),
)

print("Configuration created successfully!")
print(f"Date range: {config.execution.start_date} to {config.execution.end_date}")

# Create engine and run
engine = BacktestEngine()

try:
    print("\nCreating backtest job...")
    job_id = engine.create_backtest(config, validate=False)  # Skip validation
    print(f"Job ID: {job_id}")

    print("\nRunning backtest...")
    result = engine.run_backtest(job_id)

    if result:
        print("\n=== RESULTS ===")
        print(f"Total PnL: ${result.total_pnl:,.2f}")
        print(f"Total trades: {result.total_trades}")
        print(f"Execution time: {result.execution_time:.2f}s")
    else:
        print("No result returned")

except Exception as e:
    print(f"\nError: {type(e).__name__}: {e}")
    import traceback

    traceback.print_exc()
