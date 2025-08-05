#!/usr/bin/env python3
"""
Enhanced backtest script that leverages the server's 64GB RAM properly

This version:
1. Fixes the bid-ask bounce strategy divide by zero issue
2. Can handle larger time windows efficiently
3. Provides better debugging and error handling
4. Shows more detailed results

Usage:
    python enhanced_backtest.py --strategy bid_ask_bounce --hours 1
    python enhanced_backtest.py --strategy order_book_imbalance --minutes 30
"""

import argparse
import pandas as pd
import pyarrow.parquet as pq
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import time


def load_time_range(file_path, start_time, duration_minutes=30):
    """Load a time range efficiently, leveraging available RAM."""
    print(f"Loading {duration_minutes} minutes of data starting at {start_time}...")

    start_load = time.time()

    # With 64GB RAM, we can afford to load more data at once
    parquet_file = pq.ParquetFile(file_path)

    # Load timestamp column first to find our range
    timestamps = parquet_file.read(["timestamp"]).to_pandas()
    timestamps["timestamp"] = pd.to_datetime(timestamps["timestamp"])

    # Find our time range
    start_dt = pd.Timestamp(start_time)
    end_dt = start_dt + timedelta(minutes=duration_minutes)

    mask = (timestamps["timestamp"] >= start_dt) & (timestamps["timestamp"] <= end_dt)
    indices = timestamps[mask].index

    if len(indices) == 0:
        raise ValueError(f"No data found for time range {start_dt} to {end_dt}")

    print(f"Found {len(indices):,} ticks in time range")

    # Load the full data for our range
    first_idx, last_idx = indices[0], indices[-1]
    df = parquet_file.read().to_pandas()
    df = df.iloc[first_idx : last_idx + 1]

    # Prepare data
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df.set_index("timestamp", inplace=True)
    df["price"] = pd.to_numeric(df["price"])

    print(f"Loaded {len(df):,} ticks in {time.time()-start_load:.2f}s")
    print(f"Memory usage: {df.memory_usage(deep=True).sum()/1024**2:.1f} MB")

    return df


def run_enhanced_backtest(data, strategy_name, debug=False):
    """Run backtest with enhanced error handling and debugging."""
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

    # Initialize strategy
    strategy.initialize()

    # Portfolio tracking
    initial_capital = 100000
    cash = initial_capital
    position = 0
    entry_price = 0
    trades = []
    errors = []

    print(f"Initial capital: ${cash:,.2f}")
    print(f"Data range: {data.index.min()} to {data.index.max()}")
    print("Processing ticks...")

    # Process all data (with 64GB RAM, we can handle this)
    processed = 0
    last_update = time.time()

    for timestamp, row in data.iterrows():
        processed += 1

        try:
            # Create proper tick data
            price = float(row["price"])
            volume = int(row.get("volume", 0))

            # Calculate bid/ask from price (MNQ has 0.25 tick size)
            tick_size = 0.25
            bid = price - tick_size / 2
            ask = price + tick_size / 2

            # Call strategy with proper parameters
            signal = strategy.process_tick(
                timestamp=timestamp, price=price, volume=volume, bid=bid, ask=ask
            )

            # Handle trade signals
            if signal and isinstance(signal, dict) and "action" in signal:
                action = signal["action"]

                if action == "BUY" and position == 0:
                    # Open long position
                    position = 1
                    entry_price = ask  # Buy at ask
                    cash -= 2.0  # Commission

                    trade_info = {
                        "time": timestamp,
                        "action": "BUY",
                        "price": entry_price,
                        "position": position,
                    }
                    trades.append(trade_info)

                    if len(trades) <= 20:  # Show first 20 trades
                        print(
                            f"  Trade {len(trades)}: BUY @ ${entry_price:.2f} at {timestamp}"
                        )

                elif action == "SELL" and position > 0:
                    # Close long position
                    exit_price = bid  # Sell at bid
                    # MNQ: $2 per tick, so (exit - entry) / 0.25 * 2
                    ticks = (exit_price - entry_price) / 0.25
                    pnl = ticks * 2  # $2 per tick for MNQ micro contract
                    cash += pnl - 2.0  # PnL minus commission
                    position = 0

                    trade_info = {
                        "time": timestamp,
                        "action": "SELL",
                        "price": exit_price,
                        "pnl": pnl,
                        "ticks": ticks,
                    }
                    trades.append(trade_info)

                    if len(trades) <= 20:
                        print(
                            f"  Trade {len(trades)}: SELL @ ${exit_price:.2f} (PnL: ${pnl:.2f}, {ticks:.1f} ticks)"
                        )

        except Exception as e:
            errors.append(f"Tick {processed}: {type(e).__name__}: {e}")
            if debug and len(errors) <= 10:  # Show first 10 errors in debug mode
                print(f"  Error at tick {processed}: {e}")

        # Progress updates
        if time.time() - last_update > 5:  # Every 5 seconds
            print(
                f"  Processed {processed:,} / {len(data):,} ticks ({processed/len(data)*100:.1f}%)"
            )
            last_update = time.time()

    # Final results
    print(f"\nProcessed {processed:,} ticks")
    if errors:
        print(f"Encountered {len(errors)} errors")
        if debug:
            print("Sample errors:")
            for error in errors[:5]:
                print(f"  {error}")

    # Calculate results
    total_trades = len(trades)
    round_trips = sum(1 for t in trades if t["action"] == "SELL")
    total_pnl = cash - initial_capital

    print(f"\n=== DETAILED RESULTS ===")
    print(f"Total signals: {total_trades}")
    print(f"Round trip trades: {round_trips}")
    print(f"Total PnL: ${total_pnl:.2f}")
    print(f"Return: {total_pnl/initial_capital:.2%}")
    print(f"Final balance: ${cash:.2f}")

    if round_trips > 0:
        winning_trades = sum(1 for t in trades if t.get("pnl", 0) > 0)
        losing_trades = sum(1 for t in trades if t.get("pnl", 0) < 0)
        win_rate = winning_trades / round_trips

        wins = [t["pnl"] for t in trades if t.get("pnl", 0) > 0]
        losses = [t["pnl"] for t in trades if t.get("pnl", 0) < 0]

        print(f"Win rate: {win_rate:.1%}")
        print(f"Winning trades: {winning_trades}")
        print(f"Losing trades: {losing_trades}")

        if wins:
            print(f"Average win: ${np.mean(wins):.2f}")
            print(f"Largest win: ${max(wins):.2f}")
        if losses:
            print(f"Average loss: ${np.mean(losses):.2f}")
            print(f"Largest loss: ${min(losses):.2f}")

        if wins and losses:
            profit_factor = sum(wins) / abs(sum(losses))
            print(f"Profit factor: {profit_factor:.2f}")

    return {
        "total_pnl": total_pnl,
        "return_pct": total_pnl / initial_capital,
        "trades": round_trips,
        "errors": len(errors),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Enhanced MNQ Backtest (64GB RAM optimized)"
    )
    parser.add_argument(
        "--strategy",
        choices=["order_book_imbalance", "bid_ask_bounce"],
        default="bid_ask_bounce",
        help="Strategy to test",
    )
    parser.add_argument("--minutes", type=int, help="Duration in minutes")
    parser.add_argument(
        "--hours", type=float, help="Duration in hours (alternative to minutes)"
    )
    parser.add_argument(
        "--start-time",
        default="2024-01-02 09:30:00",
        help="Start time (default: 2024-01-02 09:30:00)",
    )
    parser.add_argument(
        "--date", default="2024-01-02", help="Date to test (default: 2024-01-02)"
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug output")

    args = parser.parse_args()

    # Determine duration
    if args.hours:
        duration_minutes = int(args.hours * 60)
    elif args.minutes:
        duration_minutes = args.minutes
    else:
        duration_minutes = 30  # Default to 30 minutes

    print("Enhanced MNQ Backtest (64GB RAM)")
    print("=" * 50)
    print(f"Strategy: {args.strategy}")
    print(f"Date: {args.date}")
    print(f"Start: {args.start_time}")
    print(f"Duration: {duration_minutes} minutes ({duration_minutes/60:.1f} hours)")
    print(f"Debug mode: {'ON' if args.debug else 'OFF'}")
    print("=" * 50)

    # Determine data file
    file_path = Path(f"data/MNQ/03-24/{args.date.replace('-', '')}.parquet")

    if not file_path.exists():
        print(f"Error: Data file not found: {file_path}")
        return 1

    try:
        # Load data
        data = load_time_range(file_path, args.start_time, duration_minutes)

        # Run backtest
        results = run_enhanced_backtest(data, args.strategy, args.debug)

        print(f"\n{'='*50}")
        print("BACKTEST COMPLETE")
        print(f"{'='*50}")

        return 0

    except Exception as e:
        print(f"Error: {e}")
        if args.debug:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
