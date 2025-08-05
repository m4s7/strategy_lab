#!/usr/bin/env python3
"""
Example: How to run a backtest with Strategy Lab

This script demonstrates running a backtest with the Order Book Imbalance strategy.
"""

import logging
from datetime import datetime
from pathlib import Path

from src.strategy_lab.backtesting.engine import BacktestEngine, BacktestConfig
from src.strategy_lab.core.config import ConfigurationManager

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def run_order_book_imbalance_backtest():
    """Run a backtest with the Order Book Imbalance strategy."""

    # 1. Initialize the backtest engine
    engine = BacktestEngine(output_dir=Path("results"))

    # 2. Create backtest configuration
    config = BacktestConfig(
        # Strategy configuration
        strategy_name="order_book_imbalance",
        strategy_module="src.strategy_lab.strategies.implementations.order_book_imbalance",
        strategy_class="OrderBookImbalanceStrategy",
        # Strategy parameters
        strategy_params={
            "positive_threshold": 0.3,
            "negative_threshold": -0.3,
            "smoothing_window": 5,
            "position_size": 1,
            "stop_loss_pct": 0.5,
            "max_holding_seconds": 300,
        },
        # Data configuration
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 1, 31),
        # MNQ contract months to use
        contract_months=["03-24"],  # March 2024 contract
        # Backtest parameters
        initial_capital=100000.0,
        commission_rate=0.001,  # 0.1%
        slippage_model="linear",
        # Execution settings
        max_workers=1,  # Single-threaded for this example
        enable_progress=True,
    )

    # 3. Run the backtest
    print(f"Starting backtest for {config.strategy_name}")
    print(f"Date range: {config.start_date} to {config.end_date}")
    print(f"Initial capital: ${config.initial_capital:,.2f}")

    result = engine.run_backtest(config)

    # 4. Display results
    if result:
        print("\n=== Backtest Results ===")
        print(f"Total PnL: ${result.total_pnl:,.2f}")
        print(f"Return: {result.total_return:.2%}")
        print(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
        print(f"Max Drawdown: {result.max_drawdown:.2%}")
        print(f"Total Trades: {result.total_trades}")
        print(f"Win Rate: {result.win_rate:.2%}")

        # Save results
        output_file = engine.output_dir / f"{config.strategy_name}_results.json"
        print(f"\nResults saved to: {output_file}")
    else:
        print("Backtest failed!")


def run_bid_ask_bounce_backtest():
    """Run a backtest with the Bid-Ask Bounce strategy."""

    # 1. Initialize the backtest engine
    engine = BacktestEngine(output_dir=Path("results"))

    # 2. Create backtest configuration
    config = BacktestConfig(
        # Strategy configuration
        strategy_name="bid_ask_bounce",
        strategy_module="src.strategy_lab.strategies.implementations.bid_ask_bounce",
        strategy_class="BidAskBounceStrategy",
        # Strategy parameters
        strategy_params={
            "bounce_sensitivity": 0.7,
            "min_bounce_strength": 0.5,
            "profit_target_ticks": 2,
            "stop_loss_ticks": 1,
            "max_spread_ticks": 2,
            "min_volume": 10,
            "max_holding_seconds": 120,
        },
        # Data configuration
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 1, 31),
        # MNQ contract months to use
        contract_months=["03-24"],  # March 2024 contract
        # Backtest parameters
        initial_capital=100000.0,
        commission_rate=0.001,  # 0.1%
        slippage_model="linear",
        # Execution settings
        max_workers=1,  # Single-threaded for this example
        enable_progress=True,
    )

    # 3. Run the backtest
    print(f"Starting backtest for {config.strategy_name}")
    print(f"Date range: {config.start_date} to {config.end_date}")
    print(f"Initial capital: ${config.initial_capital:,.2f}")

    result = engine.run_backtest(config)

    # 4. Display results
    if result:
        print("\n=== Backtest Results ===")
        print(f"Total PnL: ${result.total_pnl:,.2f}")
        print(f"Return: {result.total_return:.2%}")
        print(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
        print(f"Max Drawdown: {result.max_drawdown:.2%}")
        print(f"Total Trades: {result.total_trades}")
        print(f"Win Rate: {result.win_rate:.2%}")

        # Save results
        output_file = engine.output_dir / f"{config.strategy_name}_results.json"
        print(f"\nResults saved to: {output_file}")
    else:
        print("Backtest failed!")


def run_with_config_file():
    """Run a backtest using a YAML configuration file."""

    # 1. Initialize configuration manager
    config_manager = ConfigurationManager()

    # 2. Load configuration from file
    config_file = Path("configs/strategies/order_book_imbalance.yaml")
    config_data = config_manager.load_config(config_file)

    # 3. Create backtest configuration from loaded data
    engine = BacktestEngine()

    # Extract strategy config
    strategy_config = config_data.get("strategies", {}).get("order_book_imbalance", {})

    config = BacktestConfig(
        strategy_name="order_book_imbalance",
        strategy_module="src.strategy_lab.strategies.implementations.order_book_imbalance",
        strategy_class="OrderBookImbalanceStrategy",
        strategy_params=strategy_config.get("parameters", {}),
        # Use backtesting config from file
        **config_data.get("backtesting", {}),
    )

    # 4. Run backtest
    result = engine.run_backtest(config)

    if result:
        print(f"Backtest completed! Total PnL: ${result.total_pnl:,.2f}")


if __name__ == "__main__":
    print("Strategy Lab Backtest Examples\n")

    # Example 1: Run Order Book Imbalance strategy
    print("=== Example 1: Order Book Imbalance Strategy ===")
    run_order_book_imbalance_backtest()

    print("\n" + "=" * 50 + "\n")

    # Example 2: Run Bid-Ask Bounce strategy
    print("=== Example 2: Bid-Ask Bounce Strategy ===")
    run_bid_ask_bounce_backtest()

    # Example 3: Load from config file (commented out by default)
    # print("\n=== Example 3: Load from Config File ===")
    # run_with_config_file()
