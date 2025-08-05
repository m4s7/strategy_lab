#!/usr/bin/env python3
"""
Practical backtest script that handles large MNQ data files properly

Usage:
    python practical_backtest.py --strategy order_book_imbalance --minutes 5
    python practical_backtest.py --strategy bid_ask_bounce --minutes 10 --start-time "2024-01-02 14:30"
"""

import argparse
import pandas as pd
import pyarrow.parquet as pq
from datetime import datetime, timedelta
from pathlib import Path
import time


def load_time_slice(file_path, start_time, duration_minutes=5):
    """Load a specific time slice from the large parquet file."""
    print(f"Loading {duration_minutes} minutes of data starting at {start_time}...")

    start_load = time.time()

    # Load just timestamp column first
    parquet_file = pq.ParquetFile(file_path)
    timestamps = parquet_file.read(["timestamp"]).to_pandas()
    timestamps["timestamp"] = pd.to_datetime(timestamps["timestamp"])

    # Find our time range
    start_dt = pd.Timestamp(start_time)
    end_dt = start_dt + timedelta(minutes=duration_minutes)

    mask = (timestamps["timestamp"] >= start_dt) & (timestamps["timestamp"] <= end_dt)
    indices = timestamps[mask].index

    if len(indices) == 0:
        raise ValueError(f"No data found for time range {start_dt} to {end_dt}")

    # Load full data
    df = parquet_file.read().to_pandas()
    df = df.iloc[indices[0] : indices[-1] + 1]

    # Prepare data
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df.set_index("timestamp", inplace=True)
    df["price"] = pd.to_numeric(df["price"])

    print(f"Loaded {len(df):,} ticks in {time.time()-start_load:.2f}s")
    return df


def run_strategy_backtest(data, strategy_name):
    """Run backtest with specified strategy."""
    print(f"\nRunning {strategy_name} strategy...")

    if strategy_name == "order_book_imbalance":
        from src.strategy_lab.strategies.implementations.order_book_imbalance import (
            OrderBookImbalanceStrategy,
        )

        strategy = OrderBookImbalanceStrategy(
            positive_threshold=0.3,
            negative_threshold=-0.3,
            position_size=1,
            stop_loss_pct=0.5,
            max_holding_seconds=300,
        )
    elif strategy_name == "bid_ask_bounce":
        from src.strategy_lab.strategies.implementations.bid_ask_bounce import (
            BidAskBounceStrategy,
        )

        strategy = BidAskBounceStrategy(
            bounce_sensitivity=0.7,
            min_bounce_strength=0.5,
            profit_target_ticks=2,
            stop_loss_ticks=1,
            max_holding_seconds=120,
        )
    else:
        raise ValueError(f"Unknown strategy: {strategy_name}")

    strategy.initialize()

    # Portfolio tracking
    initial_capital = 100000
    cash = initial_capital
    position = 0
    entry_price = 0
    trades = []

    print(f"Initial capital: ${cash:,.2f}")
    print("Processing ticks...")

    # Process data in chunks for memory efficiency
    chunk_size = 10000
    total_processed = 0

    for i in range(0, len(data), chunk_size):
        chunk = data.iloc[i : i + chunk_size]

        for timestamp, row in chunk.iterrows():
            try:
                # Create tick data
                tick_data = {
                    "timestamp": timestamp,
                    "price": float(row["price"]),
                    "volume": int(row.get("volume", 0)),
                    "bid": float(row["price"]) - 0.25,
                    "ask": float(row["price"]) + 0.25,
                }

                # Get signal
                signal = strategy.process_tick(
                    timestamp=timestamp,
                    price=tick_data["price"],
                    volume=tick_data["volume"],
                    bid=tick_data["bid"],
                    ask=tick_data["ask"],
                )

                # Execute trades
                if signal and "action" in signal:
                    if signal["action"] == "BUY" and position == 0:
                        position = 1
                        entry_price = tick_data["ask"]
                        cash -= 2.0  # Commission

                        trades.append(
                            {
                                "time": timestamp,
                                "action": "BUY",
                                "price": entry_price,
                                "position": position,
                            }
                        )

                        if len(trades) <= 10:
                            print(f"  Trade {len(trades)}: BUY @ ${entry_price:.2f}")

                    elif signal["action"] == "SELL" and position > 0:
                        exit_price = tick_data["bid"]
                        pnl = (
                            (exit_price - entry_price) * position * 2
                        )  # $2 per tick for MNQ
                        cash += pnl - 2.0  # PnL minus commission
                        position = 0

                        trades.append(
                            {
                                "time": timestamp,
                                "action": "SELL",
                                "price": exit_price,
                                "pnl": pnl,
                            }
                        )

                        if len(trades) <= 10:
                            print(
                                f"  Trade {len(trades)}: SELL @ ${exit_price:.2f} (PnL: ${pnl:.2f})"
                            )

            except Exception:
                pass  # Skip errors for demo

        total_processed += len(chunk)

        # Progress update
        if total_processed % 50000 == 0:
            print(f"  Processed {total_processed:,} ticks...")

    # Results
    total_trades = len(trades)
    total_pnl = cash - initial_capital

    if total_trades > 0:
        winning_trades = sum(1 for t in trades if t.get("pnl", 0) > 0)
        win_rate = winning_trades / (total_trades // 2) if total_trades > 1 else 0

        print(f"\n=== RESULTS ===")
        print(f"Processed: {total_processed:,} ticks")
        print(f"Total trades: {total_trades // 2} round trips")
        print(f"Win rate: {win_rate:.1%}")
        print(f"Total PnL: ${total_pnl:.2f}")
        print(f"Return: {total_pnl/initial_capital:.2%}")
        print(f"Final balance: ${cash:.2f}")
    else:
        print(f"\n=== RESULTS ===")
        print(f"Processed: {total_processed:,} ticks")
        print("No trades executed")


def main():
    parser = argparse.ArgumentParser(description="Practical MNQ Backtest")
    parser.add_argument(
        "--strategy",
        choices=["order_book_imbalance", "bid_ask_bounce"],
        default="order_book_imbalance",
        help="Strategy to test",
    )
    parser.add_argument(
        "--minutes", type=int, default=5, help="Duration in minutes (default: 5)"
    )
    parser.add_argument(
        "--start-time",
        default="2024-01-02 09:30:00",
        help="Start time (default: 2024-01-02 09:30:00)",
    )
    parser.add_argument(
        "--date", default="2024-01-02", help="Date to test (default: 2024-01-02)"
    )

    args = parser.parse_args()

    print("Practical MNQ Backtest")
    print("=" * 50)
    print(f"Strategy: {args.strategy}")
    print(f"Date: {args.date}")
    print(f"Start: {args.start_time}")
    print(f"Duration: {args.minutes} minutes")
    print("=" * 50)

    # Determine data file
    file_path = Path(f"data/MNQ/03-24/{args.date.replace('-', '')}.parquet")

    if not file_path.exists():
        print(f"Error: Data file not found: {file_path}")
        return 1

    try:
        # Load time slice
        data = load_time_slice(file_path, args.start_time, args.minutes)

        # Run backtest
        run_strategy_backtest(data, args.strategy)

        return 0

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
