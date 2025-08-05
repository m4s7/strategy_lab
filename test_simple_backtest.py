#!/usr/bin/env python3
"""
Simple test to check backtest functionality
"""

import logging
from datetime import datetime
from pathlib import Path

from src.strategy_lab.backtesting.engine import BacktestEngine
from src.strategy_lab.backtesting.engine.config import BacktestConfig

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def test_simple_backtest():
    """Run a minimal backtest to test the setup."""

    print("Creating backtest configuration...")

    # Create minimal configuration
    config = BacktestConfig(
        name="test_backtest",
        description="Simple test backtest",
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
            "contracts": ["03-24"],  # Only one contract
            "validate_data": False,  # Skip validation for speed
            "chunk_size": 10000,  # Smaller chunks
        },
        execution={
            "start_date": datetime(2024, 1, 1),
            "end_date": datetime(2024, 1, 2),  # Just 2 days
            "initial_capital": 100000.0,
            "commission": 2.0,
            "slippage": 0.25,
            "progress_interval": 100,  # More frequent updates
        },
        output_dir=Path("test_results"),
    )

    print("Configuration created successfully!")
    print(f"Strategy: {config.strategy.name}")
    print(f"Date range: {config.execution.start_date} to {config.execution.end_date}")

    # Initialize engine
    print("\nInitializing backtest engine...")
    engine = BacktestEngine(output_dir=Path("test_results"))

    # Create job
    print("Creating backtest job...")
    try:
        job_id = engine.create_backtest(config, validate=False)
        print(f"Job created: {job_id}")
    except Exception as e:
        print(f"Error creating job: {e}")
        return

    # Check job status
    status = engine.get_job_status(job_id)
    print(f"Job status: {status}")

    # Try to run the backtest
    print("\nAttempting to run backtest...")
    try:
        result = engine.run_backtest(job_id)

        if result:
            print("\n=== Backtest completed successfully! ===")
            print(f"Total PnL: ${result.total_pnl:,.2f}")
            print(f"Total trades: {result.total_trades}")
            print(f"Execution time: {result.execution_time:.2f} seconds")
        else:
            print("Backtest returned no result")

    except Exception as e:
        print(f"Error running backtest: {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_simple_backtest()
