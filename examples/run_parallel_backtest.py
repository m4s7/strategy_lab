#!/usr/bin/env python3
"""
Example: Parallel backtesting with parameter optimization

This script demonstrates running multiple backtests in parallel with different parameters.
"""

import logging
from datetime import datetime
from pathlib import Path
from itertools import product

from src.strategy_lab.backtesting.engine import (
    BacktestEngine,
    BacktestConfig,
    execute_backtest_parallel,
)

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def create_parameter_grid():
    """Create a grid of parameters to test."""

    # Define parameter ranges for Order Book Imbalance strategy
    param_grid = {
        "positive_threshold": [0.2, 0.3, 0.4],
        "negative_threshold": [-0.2, -0.3, -0.4],
        "smoothing_window": [3, 5, 7],
        "stop_loss_pct": [0.3, 0.5, 0.7],
    }

    # Generate all combinations
    keys = param_grid.keys()
    values = param_grid.values()

    parameter_sets = []
    for combination in product(*values):
        params = dict(zip(keys, combination))
        # Add fixed parameters
        params.update({"position_size": 1, "max_holding_seconds": 300})
        parameter_sets.append(params)

    return parameter_sets


def run_parameter_optimization():
    """Run parallel backtests with different parameter combinations."""

    # 1. Generate parameter combinations
    parameter_sets = create_parameter_grid()
    print(f"Testing {len(parameter_sets)} parameter combinations")

    # 2. Create backtest configurations
    configs = []
    for i, params in enumerate(parameter_sets):
        config = BacktestConfig(
            # Unique job ID for each backtest
            job_id=f"optimization_{i:03d}",
            # Strategy configuration
            strategy_name="order_book_imbalance",
            strategy_module="src.strategy_lab.strategies.implementations.order_book_imbalance",
            strategy_class="OrderBookImbalanceStrategy",
            strategy_params=params,
            # Data configuration
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 3, 31),  # 3 months
            contract_months=["03-24", "06-24"],  # Multiple contracts
            # Backtest parameters
            initial_capital=100000.0,
            commission_rate=0.001,
            slippage_model="linear",
        )
        configs.append(config)

    # 3. Run backtests in parallel
    print("\nRunning backtests in parallel...")
    results = execute_backtest_parallel(
        configs,
        max_workers=4,  # Use 4 CPU cores
        output_dir=Path("results/optimization"),
    )

    # 4. Analyze results
    print("\n=== Optimization Results ===")

    # Sort by Sharpe ratio
    sorted_results = sorted(
        [(cfg, res) for cfg, res in zip(configs, results) if res is not None],
        key=lambda x: x[1].sharpe_ratio if x[1].sharpe_ratio else -float("inf"),
        reverse=True,
    )

    # Display top 5 results
    print("\nTop 5 parameter combinations by Sharpe Ratio:")
    print("-" * 80)

    for i, (config, result) in enumerate(sorted_results[:5]):
        print(f"\nRank {i+1}:")
        print(f"  Parameters: {config.strategy_params}")
        print(f"  Total PnL: ${result.total_pnl:,.2f}")
        print(f"  Return: {result.total_return:.2%}")
        print(f"  Sharpe Ratio: {result.sharpe_ratio:.2f}")
        print(f"  Max Drawdown: {result.max_drawdown:.2%}")
        print(f"  Win Rate: {result.win_rate:.2%}")
        print(f"  Total Trades: {result.total_trades}")

    # Find best parameters
    if sorted_results:
        best_config, best_result = sorted_results[0]
        print(f"\n{'='*80}")
        print(f"BEST PARAMETERS:")
        print(f"{'='*80}")
        for key, value in best_config.strategy_params.items():
            print(f"  {key}: {value}")

        # Save best configuration
        output_file = Path("results/optimization/best_parameters.yaml")
        print(f"\nBest parameters saved to: {output_file}")


def run_strategy_comparison():
    """Compare different strategies on the same data."""

    strategies = [
        {
            "name": "order_book_imbalance",
            "module": "src.strategy_lab.strategies.implementations.order_book_imbalance",
            "class": "OrderBookImbalanceStrategy",
            "params": {
                "positive_threshold": 0.3,
                "negative_threshold": -0.3,
                "smoothing_window": 5,
                "position_size": 1,
                "stop_loss_pct": 0.5,
                "max_holding_seconds": 300,
            },
        },
        {
            "name": "bid_ask_bounce",
            "module": "src.strategy_lab.strategies.implementations.bid_ask_bounce",
            "class": "BidAskBounceStrategy",
            "params": {
                "bounce_sensitivity": 0.7,
                "min_bounce_strength": 0.5,
                "profit_target_ticks": 2,
                "stop_loss_ticks": 1,
                "max_spread_ticks": 2,
                "min_volume": 10,
                "max_holding_seconds": 120,
            },
        },
    ]

    # Common configuration
    common_config = {
        "start_date": datetime(2024, 1, 1),
        "end_date": datetime(2024, 6, 30),  # 6 months
        "contract_months": ["03-24", "06-24", "09-24"],
        "initial_capital": 100000.0,
        "commission_rate": 0.001,
        "slippage_model": "linear",
    }

    # Create configurations
    configs = []
    for strategy in strategies:
        config = BacktestConfig(
            job_id=f"compare_{strategy['name']}",
            strategy_name=strategy["name"],
            strategy_module=strategy["module"],
            strategy_class=strategy["class"],
            strategy_params=strategy["params"],
            **common_config,
        )
        configs.append(config)

    # Run backtests
    print("Comparing strategies...")
    results = execute_backtest_parallel(
        configs, max_workers=2, output_dir=Path("results/comparison")
    )

    # Display comparison
    print("\n=== Strategy Comparison ===")
    print("-" * 80)
    print(
        f"{'Strategy':<25} {'Total PnL':>15} {'Return':>10} {'Sharpe':>10} {'Max DD':>10} {'Win Rate':>10}"
    )
    print("-" * 80)

    for config, result in zip(configs, results):
        if result:
            print(
                f"{config.strategy_name:<25} "
                f"${result.total_pnl:>14,.2f} "
                f"{result.total_return:>9.2%} "
                f"{result.sharpe_ratio:>10.2f} "
                f"{result.max_drawdown:>9.2%} "
                f"{result.win_rate:>9.2%}"
            )


if __name__ == "__main__":
    print("Strategy Lab Parallel Backtest Examples\n")

    # Example 1: Parameter optimization
    print("=== Example 1: Parameter Optimization ===")
    run_parameter_optimization()

    print("\n" + "=" * 80 + "\n")

    # Example 2: Strategy comparison
    print("=== Example 2: Strategy Comparison ===")
    run_strategy_comparison()
