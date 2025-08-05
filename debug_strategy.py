#!/usr/bin/env python3
"""
Debug strategy execution to understand why no trades are happening
"""

import pandas as pd
import pyarrow.parquet as pq
from datetime import datetime, timedelta
from pathlib import Path
import time


def debug_strategy_execution():
    """Debug what the strategies are seeing and why they're not trading."""

    print("Debug Strategy Execution")
    print("=" * 50)

    # Load small amount of data
    file_path = Path("data/MNQ/03-24/20240102.parquet")
    print("Loading 5 minutes of data...")

    start_load = time.time()
    parquet_file = pq.ParquetFile(file_path)
    timestamps = parquet_file.read(["timestamp"]).to_pandas()
    timestamps["timestamp"] = pd.to_datetime(timestamps["timestamp"])

    start_dt = pd.Timestamp("2024-01-02 09:30:00")
    end_dt = start_dt + timedelta(minutes=5)

    mask = (timestamps["timestamp"] >= start_dt) & (timestamps["timestamp"] <= end_dt)
    indices = timestamps[mask].index

    df = parquet_file.read().to_pandas()
    df = df.iloc[indices[0] : indices[-1] + 1]

    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df.set_index("timestamp", inplace=True)
    df["price"] = pd.to_numeric(df["price"])

    print(f"Loaded {len(df):,} ticks in {time.time()-start_load:.2f}s")

    # Analyze the data structure
    print(f"\nData structure:")
    print(f"Columns: {list(df.columns)}")
    print(f"Level types: {df['level'].value_counts()}")
    print(f"MDT types: {df['mdt'].value_counts()}")
    print(f"Price range: ${df['price'].min():.2f} - ${df['price'].max():.2f}")

    # Show sample data
    print(f"\nSample data:")
    print(df.head(10))

    # Check for L2 data
    l2_data = df[df["level"] == "L2"]
    print(f"\nL2 data: {len(l2_data):,} rows")
    if len(l2_data) > 0:
        print("L2 sample:")
        print(l2_data.head())

        # Check bid/ask data
        bids = l2_data[l2_data["mdt"] == 1]  # Bid
        asks = l2_data[l2_data["mdt"] == 0]  # Ask
        print(f"Bids: {len(bids):,}, Asks: {len(asks):,}")

    # Test strategy initialization
    print(f"\n" + "=" * 50)
    print("Testing Order Book Imbalance Strategy")
    print("=" * 50)

    from src.strategy_lab.strategies.implementations.order_book_imbalance import (
        OrderBookImbalanceStrategy,
    )

    strategy = OrderBookImbalanceStrategy(
        positive_threshold=0.1,  # Lower threshold for testing
        negative_threshold=-0.1,
        position_size=1,
    )
    strategy.initialize()

    print(f"Strategy initialized: {strategy.name}")
    print(f"Thresholds: +{strategy.positive_threshold}, {strategy.negative_threshold}")

    # Process first 100 ticks and see what happens
    signals = []
    for i, (timestamp, row) in enumerate(df.head(100).iterrows()):
        try:
            price = float(row["price"])
            volume = int(row.get("volume", 0))
            bid = price - 0.125  # Half tick
            ask = price + 0.125

            signal = strategy.process_tick(
                timestamp=timestamp, price=price, volume=volume, bid=bid, ask=ask
            )

            if signal:
                signals.append((i, timestamp, signal))
                if len(signals) <= 5:
                    print(f"Signal {len(signals)} at tick {i}: {signal}")

        except Exception as e:
            if i < 5:  # Show first few errors
                print(f"Error at tick {i}: {e}")

    print(f"\nGenerated {len(signals)} signals from 100 ticks")

    # Test with actual L2 data if available
    if len(l2_data) > 100:
        print(f"\n" + "=" * 50)
        print("Testing with L2 Order Book Data")
        print("=" * 50)

        # Group L2 data by timestamp to reconstruct order book
        l2_by_time = l2_data.groupby(level=0)

        ob_signals = []
        for timestamp, group in list(l2_by_time)[:20]:  # First 20 timestamps
            try:
                # Get bids and asks
                bids = group[group["mdt"] == 1].sort_values("price", ascending=False)
                asks = group[group["mdt"] == 0].sort_values("price", ascending=True)

                if len(bids) > 0 and len(asks) > 0:
                    best_bid = float(bids.iloc[0]["price"])
                    best_ask = float(asks.iloc[0]["price"])
                    mid_price = (best_bid + best_ask) / 2

                    # Create order book data
                    order_book = {
                        "bids": [
                            (float(r["price"]), int(r["volume"]))
                            for _, r in bids.head(5).iterrows()
                        ],
                        "asks": [
                            (float(r["price"]), int(r["volume"]))
                            for _, r in asks.head(5).iterrows()
                        ],
                    }

                    signal = strategy.process_tick(
                        timestamp=timestamp,
                        price=mid_price,
                        volume=100,
                        bid=best_bid,
                        ask=best_ask,
                        order_book=order_book,
                    )

                    if signal:
                        ob_signals.append((timestamp, signal))
                        print(f"L2 Signal: {signal} at {timestamp}")

            except Exception as e:
                print(f"Error processing L2 data: {e}")
                break

        print(f"Generated {len(ob_signals)} signals from L2 data")

    print(f"\n" + "=" * 50)
    print("DEBUGGING COMPLETE")
    print("=" * 50)

    if len(signals) == 0 and len(l2_data) == 0:
        print("Recommendation: The data may not contain proper L2 order book data")
        print("Try adjusting strategy parameters (lower thresholds)")
    elif len(signals) > 0:
        print("Strategy is generating signals - check trade execution logic")
    else:
        print("Strategy may need different market conditions or parameter tuning")


if __name__ == "__main__":
    debug_strategy_execution()
