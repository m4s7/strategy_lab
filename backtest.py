#!/usr/bin/env python3
"""
Strategy Lab Backtest CLI

Simple command-line interface for running backtests.

Usage:
    python backtest.py order_book_imbalance --start 2024-01-01 --end 2024-01-31
    python backtest.py bid_ask_bounce --start 2024-01-01 --end 2024-01-31 --capital 50000
    python backtest.py --help
"""

import argparse
import logging
from datetime import datetime
from pathlib import Path

from src.strategy_lab.backtesting.engine import BacktestEngine
from src.strategy_lab.backtesting.engine.config import BacktestConfig

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Strategy configurations
STRATEGIES = {
    "order_book_imbalance": {
        "module": "src.strategy_lab.strategies.implementations.order_book_imbalance",
        "class_name": "OrderBookImbalanceStrategy",
        "default_params": {
            "positive_threshold": 0.3,
            "negative_threshold": -0.3,
            "smoothing_window": 5,
            "position_size": 1,
            "stop_loss_pct": 0.5,
            "max_holding_seconds": 300,
        },
        "description": "Order book imbalance strategy using L2 market depth data",
    },
    "bid_ask_bounce": {
        "module": "src.strategy_lab.strategies.implementations.bid_ask_bounce",
        "class_name": "BidAskBounceStrategy",
        "default_params": {
            "bounce_sensitivity": 0.7,
            "min_bounce_strength": 0.5,
            "profit_target_ticks": 2,
            "stop_loss_ticks": 1,
            "max_spread_ticks": 2,
            "min_volume": 10,
            "max_holding_seconds": 120,
        },
        "description": "Bid-ask bounce strategy using L1 tick data",
    },
}


def parse_date(date_str):
    """Parse date string to datetime object."""
    return datetime.strptime(date_str, "%Y-%m-%d")


def get_contract_months(start_date, end_date):
    """Determine which MNQ contract months to use based on date range."""
    contracts = []

    # Map months to contract codes
    contract_months = {3: "03", 6: "06", 9: "09", 12: "12"}

    current = start_date
    while current <= end_date:
        # Find next contract month
        for month in [3, 6, 9, 12]:
            if current.month <= month:
                year_suffix = str(current.year)[-2:]
                contract = f"{contract_months[month]}-{year_suffix}"
                if contract not in contracts:
                    contracts.append(contract)
                break

        # Move to next quarter
        if current.month >= 10:
            current = current.replace(year=current.year + 1, month=1)
        else:
            current = current.replace(month=min(current.month + 3, 12))

    return contracts


def main():
    parser = argparse.ArgumentParser(
        description="Strategy Lab Backtest CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Strategy selection
    parser.add_argument(
        "strategy", choices=list(STRATEGIES.keys()), help="Strategy to backtest"
    )

    # Date range
    parser.add_argument(
        "--start", type=str, required=True, help="Start date (YYYY-MM-DD)"
    )

    parser.add_argument("--end", type=str, required=True, help="End date (YYYY-MM-DD)")

    # Optional parameters
    parser.add_argument(
        "--capital",
        type=float,
        default=100000.0,
        help="Initial capital (default: 100000)",
    )

    parser.add_argument(
        "--commission",
        type=float,
        default=0.001,
        help="Commission rate (default: 0.001 = 0.1%%)",
    )

    parser.add_argument(
        "--contracts",
        type=str,
        nargs="+",
        help="Contract months to use (e.g., 03-24 06-24). Auto-detected if not specified.",
    )

    parser.add_argument(
        "--output",
        type=str,
        default="results",
        help="Output directory for results (default: results)",
    )

    parser.add_argument(
        "--no-progress", action="store_true", help="Disable progress bar"
    )

    # Parse arguments
    args = parser.parse_args()

    # Parse dates
    start_date = parse_date(args.start)
    end_date = parse_date(args.end)

    # If same day, set end time to end of day
    if start_date.date() == end_date.date():
        end_date = end_date.replace(hour=23, minute=59, second=59)

    # Get contract months
    if args.contracts:
        contract_months = args.contracts
    else:
        contract_months = get_contract_months(start_date, end_date)

    # Get strategy configuration
    strategy_info = STRATEGIES[args.strategy]

    # Print backtest information
    print(f"\n{'='*60}")
    print(f"Strategy Lab Backtest")
    print(f"{'='*60}")
    print(f"Strategy: {args.strategy}")
    print(f"Description: {strategy_info['description']}")
    print(f"Date Range: {args.start} to {args.end}")
    print(f"Contracts: {', '.join(contract_months)}")
    print(f"Initial Capital: ${args.capital:,.2f}")
    print(f"Commission Rate: {args.commission:.3%}")
    print(f"{'='*60}\n")

    # Create backtest configuration with nested structure
    config = BacktestConfig(
        name=f"{args.strategy}_backtest",
        description=f"Backtest of {strategy_info['description']}",
        strategy={
            "name": strategy_info["class_name"],
            "module": strategy_info["module"],
            "parameters": strategy_info["default_params"],
        },
        data={
            "symbol": "MNQ",
            "data_path": Path("data/MNQ"),
            "contracts": contract_months,
            "validate_data": True,
        },
        execution={
            "start_date": start_date,
            "end_date": end_date,
            "initial_capital": args.capital,
            "commission": args.commission * 1000,  # Convert rate to dollar amount
            "slippage": 0.25,  # Default slippage in ticks
        },
        output_dir=Path(args.output),
    )

    # Initialize engine
    engine = BacktestEngine(output_dir=Path(args.output))

    # Create and run backtest job
    print("Running backtest...")
    job_id = engine.create_backtest(config)
    result = engine.run_backtest(job_id)

    # Display results
    if result:
        print(f"\n{'='*60}")
        print(f"Backtest Results")
        print(f"{'='*60}")
        print(f"Total PnL:        ${result.total_pnl:,.2f}")
        print(f"Total Return:     {result.total_return:.2%}")
        print(f"Sharpe Ratio:     {result.sharpe_ratio:.2f}")
        print(f"Max Drawdown:     {result.max_drawdown:.2%}")
        print(f"Total Trades:     {result.total_trades}")
        print(f"Win Rate:         {result.win_rate:.2%}")

        if result.total_trades > 0:
            print(f"Avg Win:          ${result.avg_win:.2f}")
            print(f"Avg Loss:         ${result.avg_loss:.2f}")
            print(f"Profit Factor:    {result.profit_factor:.2f}")

        # Save results
        output_file = (
            engine.output_dir / f"{args.strategy}_{args.start}_{args.end}_results.json"
        )
        print(f"\nResults saved to: {output_file}")
        print(f"{'='*60}\n")
    else:
        print("\nBacktest failed! Check logs for details.")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
