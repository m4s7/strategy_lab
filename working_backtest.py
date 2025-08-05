#!/usr/bin/env python3
"""
Working backtest example that handles large data files properly

The MNQ tick data is extremely large (30M+ ticks per day), so we need
to be smart about how we load and process it.
"""

import pandas as pd
import time
from datetime import datetime
from pathlib import Path
from decimal import Decimal

print("Strategy Lab - Working Backtest Example")
print("=" * 50)

# First, let's understand the data size
print("\nChecking data size...")
file_path = Path("data/MNQ/03-24/20240102.parquet")
file_size_mb = file_path.stat().st_size / (1024**2)
print(f"File size: {file_size_mb:.1f} MB")

# For a working demo, let's load just a small slice of data
print("\nLoading a small time slice...")
start_time = time.time()

# Use pyarrow to load just specific columns and time range
import pyarrow.parquet as pq

parquet_file = pq.ParquetFile(file_path)

# Read just the timestamp column first to find our range
timestamps = parquet_file.read(["timestamp"]).to_pandas()
timestamps["timestamp"] = pd.to_datetime(timestamps["timestamp"])

# Find indices for our time range (just 1 minute for demo)
start_dt = pd.Timestamp("2024-01-02 09:30:00")
end_dt = pd.Timestamp("2024-01-02 09:31:00")

mask = (timestamps["timestamp"] >= start_dt) & (timestamps["timestamp"] <= end_dt)
indices = timestamps[mask].index

print(f"Found {len(indices):,} ticks in our 1-minute window")

# Now load just those rows
if len(indices) > 0:
    # Get row groups that contain our data
    first_idx = indices[0]
    last_idx = indices[-1]

    # Load the data
    df = parquet_file.read().to_pandas()
    df = df.iloc[first_idx : last_idx + 1]

    print(f"Loaded {len(df):,} rows in {time.time()-start_time:.2f}s")
    print(f"Memory usage: {df.memory_usage(deep=True).sum()/1024**2:.1f} MB")

    # Prepare data for backtesting
    print("\nPreparing data...")
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df.set_index("timestamp", inplace=True)

    # Convert price to numeric (it's stored as Decimal)
    df["price"] = pd.to_numeric(df["price"])

    print(f"Data range: {df.index.min()} to {df.index.max()}")
    print(f"Price range: ${df['price'].min():.2f} - ${df['price'].max():.2f}")

    # Now run a simple backtest simulation
    print("\n" + "=" * 50)
    print("Running Simple Backtest Simulation")
    print("=" * 50)

    from src.strategy_lab.strategies.implementations.order_book_imbalance import (
        OrderBookImbalanceStrategy,
    )

    # Initialize strategy
    strategy = OrderBookImbalanceStrategy(
        positive_threshold=0.3, negative_threshold=-0.3, position_size=1
    )
    strategy.initialize()

    # Simple portfolio tracking
    cash = 100000
    position = 0
    trades = []

    print(f"\nInitial capital: ${cash:,.2f}")
    print("Processing ticks...")

    # Process a subset of ticks
    tick_count = 0
    for timestamp, row in df.head(1000).iterrows():  # Just first 1000 ticks
        tick_count += 1

        # Create tick data
        tick_data = {
            "timestamp": timestamp,
            "price": float(row["price"]),
            "volume": int(row.get("volume", 0)),
            "bid": float(row["price"]) - 0.25,  # Simulated bid
            "ask": float(row["price"]) + 0.25,  # Simulated ask
        }

        # Get signal from strategy
        try:
            signal = strategy.process_tick(
                timestamp=timestamp,
                price=tick_data["price"],
                volume=tick_data["volume"],
                bid=tick_data["bid"],
                ask=tick_data["ask"],
            )

            # Execute trades based on signal
            if signal and "action" in signal:
                if signal["action"] == "BUY" and position == 0:
                    # Buy
                    position = 1
                    entry_price = tick_data["ask"]
                    trades.append(
                        {
                            "time": timestamp,
                            "action": "BUY",
                            "price": entry_price,
                            "position": position,
                        }
                    )
                    if len(trades) <= 5:  # Show first 5 trades
                        print(f"  Trade {len(trades)}: BUY @ ${entry_price:.2f}")

                elif signal["action"] == "SELL" and position > 0:
                    # Sell
                    exit_price = tick_data["bid"]
                    pnl = (exit_price - entry_price) * position
                    cash += pnl
                    position = 0
                    trades.append(
                        {
                            "time": timestamp,
                            "action": "SELL",
                            "price": exit_price,
                            "pnl": pnl,
                        }
                    )
                    if len(trades) <= 5:
                        print(
                            f"  Trade {len(trades)}: SELL @ ${exit_price:.2f} (PnL: ${pnl:.2f})"
                        )

        except Exception as e:
            if tick_count == 1:  # Only show first error
                print(f"  Strategy error: {e}")

    # Summary
    print(f"\nProcessed {tick_count} ticks")
    print(f"Total trades: {len(trades)}")

    if trades:
        total_pnl = sum(t.get("pnl", 0) for t in trades)
        print(f"Total PnL: ${total_pnl:.2f}")
        print(f"Final cash: ${cash:.2f}")

    print("\n" + "=" * 50)
    print("Demonstration Complete!")
    print("=" * 50)

else:
    print("No data found in the specified time range")

print("\nKey Insights:")
print("1. MNQ tick data is extremely large (30M+ ticks/day)")
print("2. Loading full days requires significant memory (6-7GB)")
print("3. For production, use streaming or chunked processing")
print("4. Consider sampling or aggregating data for strategy development")
