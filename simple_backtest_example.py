#!/usr/bin/env python3
"""
Simple working example of running a backtest

This demonstrates the correct way to use the Strategy Lab framework.
"""

from datetime import datetime
from pathlib import Path
from decimal import Decimal

# Import the required components
from src.strategy_lab.backtesting.engine import BacktestEngine
from src.strategy_lab.backtesting.engine.config import BacktestConfig


def run_simple_backtest():
    """Run a simple backtest with minimal configuration."""

    print("Strategy Lab - Simple Backtest Example")
    print("=" * 50)

    # 1. Create backtest configuration
    config = BacktestConfig(
        name="simple_example",
        description="A simple backtest example",
        # Strategy configuration
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
        # Data configuration
        data={
            "symbol": "MNQ",
            "data_path": Path("data/MNQ"),
            "contracts": ["03-24"],  # Just one contract
            "validate_data": False,  # Skip validation for speed
            "chunk_size": 10000,  # Small chunks to avoid memory issues
        },
        # Execution configuration
        execution={
            "start_date": datetime(2024, 1, 2, 9, 30),  # Start at market open
            "end_date": datetime(2024, 1, 2, 10, 0),  # Just 30 minutes
            "initial_capital": Decimal("100000"),
            "commission": Decimal("2.0"),  # $2 per trade
            "slippage": Decimal("0.25"),  # 1 tick slippage
            "progress_interval": 1000,  # Update every 1000 ticks
            "max_memory_gb": 2.0,  # Limit memory usage
        },
        # Output configuration
        output_dir=Path("results/examples"),
        save_trades=True,
        save_equity_curve=True,
    )

    print("\nConfiguration created:")
    print(f"  Strategy: {config.strategy.name}")
    print(f"  Data: {config.data.contracts} contracts")
    print(f"  Period: {config.execution.start_date} to {config.execution.end_date}")
    print(f"  Capital: ${config.execution.initial_capital:,.2f}")

    # 2. Initialize backtest engine
    print("\nInitializing backtest engine...")
    engine = BacktestEngine(output_dir=config.output_dir)

    # 3. Create and run backtest
    try:
        print("\nCreating backtest job...")
        job_id = engine.create_backtest(config, validate=False)
        print(f"  Job ID: {job_id}")

        print("\nRunning backtest...")
        print("  (This may take a moment as it loads and processes tick data)")

        result = engine.run_backtest(job_id)

        if result:
            print("\n" + "=" * 50)
            print("BACKTEST COMPLETE!")
            print("=" * 50)

            # Display results
            print(f"\nPerformance Summary:")
            print(f"  Total PnL: ${result.total_pnl:,.2f}")
            print(f"  Return: {result.total_return:.2%}")
            print(f"  Sharpe Ratio: {result.sharpe_ratio:.2f}")
            print(f"  Max Drawdown: {result.max_drawdown:.2%}")

            print(f"\nTrading Summary:")
            print(f"  Total Trades: {result.total_trades}")
            print(f"  Win Rate: {result.win_rate:.1%}")
            print(f"  Avg Win: ${result.avg_win:.2f}")
            print(f"  Avg Loss: ${result.avg_loss:.2f}")
            print(f"  Profit Factor: {result.profit_factor:.2f}")

            print(f"\nExecution Summary:")
            print(f"  Total Ticks: {result.total_ticks:,}")
            print(f"  Processing Time: {result.execution_time:.1f} seconds")
            print(f"  Ticks/Second: {result.ticks_per_second:,.0f}")

            # Results location
            results_file = (
                config.output_dir / f"{config.name}_{result.backtest_id}.json"
            )
            print(f"\nDetailed results saved to: {results_file}")

        else:
            print("\nBacktest failed - check logs for details")

    except Exception as e:
        print(f"\nError during backtest: {type(e).__name__}: {e}")
        print("\nCommon issues:")
        print("  - No data files for the specified date range")
        print("  - Insufficient memory for the data size")
        print("  - Invalid strategy parameters")

        # For debugging
        import traceback

        print("\nFull traceback:")
        traceback.print_exc()


def main():
    """Main entry point."""
    run_simple_backtest()

    print("\n" + "=" * 50)
    print("Next Steps:")
    print("  1. Try different date ranges and contracts")
    print("  2. Adjust strategy parameters")
    print("  3. Use the bid_ask_bounce strategy instead")
    print("  4. Load results for further analysis")


if __name__ == "__main__":
    main()
