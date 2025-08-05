#!/usr/bin/env python3
"""
Demonstration: How to run a backtest with Strategy Lab

This shows a working example with minimal data loading.
"""

import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path

print("Strategy Lab Backtest Demo")
print("=" * 50)


# For demonstration, let's create some simple test data instead of loading huge files
def create_test_data():
    """Create simple test tick data for demonstration."""
    print("\nCreating test data...")

    # Create 1000 ticks of test data
    timestamps = pd.date_range(start="2024-01-02 09:30:00", periods=1000, freq="100ms")

    # Simulate price movement
    base_price = 16000
    price_noise = np.random.randn(1000) * 0.25
    prices = base_price + np.cumsum(price_noise)

    # Create L2 data with bid/ask spread
    data = pd.DataFrame(
        {
            "timestamp": timestamps,
            "price": prices,
            "bid": prices - 0.25,  # 1 tick spread
            "ask": prices + 0.25,
            "volume": np.random.randint(1, 20, 1000),
            "level": "L1",
            "mdt": 2,  # Last trade
        }
    )

    # Add some L2 depth data
    l2_data = []
    for i in range(0, 100, 10):  # Every 10th tick
        ts = timestamps[i]
        mid = prices[i]

        # Create 5 levels of depth
        for depth in range(1, 6):
            # Bid side
            l2_data.append(
                {
                    "timestamp": ts,
                    "price": mid - (depth * 0.25),
                    "volume": np.random.randint(10, 50),
                    "level": "L2",
                    "mdt": 1,  # Bid
                    "depth": depth,
                    "operation": 0,  # Add
                    "market_maker": "",
                }
            )

            # Ask side
            l2_data.append(
                {
                    "timestamp": ts,
                    "price": mid + (depth * 0.25),
                    "volume": np.random.randint(10, 50),
                    "level": "L2",
                    "mdt": 0,  # Ask
                    "depth": depth,
                    "operation": 0,  # Add
                    "market_maker": "",
                }
            )

    # Combine L1 and L2 data
    l2_df = pd.DataFrame(l2_data)
    combined = pd.concat([data, l2_df], ignore_index=True)
    combined.sort_values("timestamp", inplace=True)
    combined.set_index("timestamp", inplace=True)

    print(f"Created {len(combined)} ticks of test data")
    return combined


def run_demo_backtest():
    """Run a demonstration backtest."""
    from src.strategy_lab.strategies.implementations.order_book_imbalance import (
        OrderBookImbalanceStrategy,
    )
    from src.strategy_lab.backtesting.engine.portfolio import Portfolio
    from src.strategy_lab.backtesting.metrics import MetricsAggregator
    from decimal import Decimal

    # Create test data
    data = create_test_data()

    # Initialize components
    print("\nInitializing backtest components...")

    # 1. Create strategy
    strategy = OrderBookImbalanceStrategy(
        positive_threshold=0.3,
        negative_threshold=-0.3,
        position_size=1,
        stop_loss_pct=0.5,
    )
    print(f"Strategy: {strategy.name}")

    # 2. Create portfolio
    portfolio = Portfolio(
        initial_capital=Decimal("100000"), commission_per_trade=Decimal("2.0")
    )
    print(f"Initial capital: ${portfolio.cash:,.2f}")

    # 3. Create metrics tracker
    metrics = MetricsAggregator()

    # 4. Initialize strategy
    strategy.initialize()

    # Run backtest
    print("\nRunning backtest...")
    trades = 0

    # Process first 100 ticks as a demo
    for i, (timestamp, row) in enumerate(data.head(100).iterrows()):
        # Update portfolio prices
        prices = {"MNQ": Decimal(str(row["price"]))}
        portfolio.update_prices(prices, timestamp)

        # Get L2 data for this timestamp (simplified)
        l2_at_time = data[data.index == timestamp]
        bid_data = l2_at_time[l2_at_time["mdt"] == 1]
        ask_data = l2_at_time[l2_at_time["mdt"] == 0]

        # Create order book snapshot
        order_book = {
            "bids": [
                (float(r["price"]), int(r["volume"])) for _, r in bid_data.iterrows()
            ],
            "asks": [
                (float(r["price"]), int(r["volume"])) for _, r in ask_data.iterrows()
            ],
        }

        # Process tick through strategy
        try:
            signal = strategy.process_tick(
                {
                    "timestamp": timestamp,
                    "price": float(row["price"]),
                    "volume": int(row.get("volume", 0)),
                    "bid": float(row.get("bid", row["price"])),
                    "ask": float(row.get("ask", row["price"])),
                    "order_book": order_book,
                }
            )

            # Simple order execution based on signal
            if signal and signal.get("action"):
                action = signal["action"]
                size = signal.get("size", 1)

                if action == "BUY" and portfolio.current_position == 0:
                    # Open long position
                    portfolio.open_position(
                        symbol="MNQ",
                        side="LONG",
                        quantity=size,
                        price=Decimal(str(row["ask"])),  # Buy at ask
                        timestamp=timestamp,
                    )
                    trades += 1
                    print(f"  Trade {trades}: BUY {size} @ ${row['ask']:.2f}")

                elif action == "SELL" and portfolio.current_position > 0:
                    # Close long position
                    portfolio.close_position(
                        symbol="MNQ",
                        price=Decimal(str(row["bid"])),  # Sell at bid
                        timestamp=timestamp,
                    )
                    print(f"  Trade {trades}: SELL @ ${row['bid']:.2f}")

        except Exception as e:
            print(f"  Error processing tick {i}: {e}")

        # Update metrics
        if i % 10 == 0:
            metrics.update_portfolio_metrics(portfolio)

    # Finalize
    print("\nBacktest complete!")

    # Get final metrics
    perf_metrics = metrics.get_performance_metrics()

    print(f"\n=== Results ===")
    print(f"Total trades: {len(portfolio.closed_positions)}")
    print(f"Final cash: ${portfolio.cash:,.2f}")
    print(f"Final value: ${portfolio.total_value:,.2f}")

    if perf_metrics:
        print(f"Total PnL: ${perf_metrics.total_pnl:,.2f}")
        print(f"Return: {perf_metrics.total_return:.2%}")

        if len(portfolio.closed_positions) > 0:
            wins = sum(1 for p in portfolio.closed_positions if p.pnl > 0)
            print(f"Win rate: {wins/len(portfolio.closed_positions):.1%}")


if __name__ == "__main__":
    run_demo_backtest()
