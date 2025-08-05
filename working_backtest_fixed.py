#!/usr/bin/env python3
"""
Fixed working backtest that properly formats L2 order book data for strategies

This version correctly constructs order book levels from the MNQ tick data
and passes them to strategies in the expected format.
"""

import argparse
import pandas as pd
import pyarrow.parquet as pq
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import time
from collections import defaultdict


def load_and_process_data(file_path, start_time, duration_minutes=30):
    """Load and process MNQ data into proper order book format."""
    print(f"Loading {duration_minutes} minutes of data starting at {start_time}...")

    start_load = time.time()
    parquet_file = pq.ParquetFile(file_path)

    # Load timestamp column first to find our range
    timestamps = parquet_file.read(["timestamp"]).to_pandas()
    timestamps["timestamp"] = pd.to_datetime(timestamps["timestamp"])

    start_dt = pd.Timestamp(start_time)
    end_dt = start_dt + timedelta(minutes=duration_minutes)

    mask = (timestamps["timestamp"] >= start_dt) & (timestamps["timestamp"] <= end_dt)
    indices = timestamps[mask].index

    if len(indices) == 0:
        raise ValueError(f"No data found for time range {start_dt} to {end_dt}")

    # Load the data
    first_idx, last_idx = indices[0], indices[-1]
    df = parquet_file.read().to_pandas()
    df = df.iloc[first_idx : last_idx + 1]

    # Prepare data
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df.set_index("timestamp", inplace=True)
    df["price"] = pd.to_numeric(df["price"])

    print(f"Loaded {len(df):,} ticks in {time.time()-start_load:.2f}s")

    # Process into order book snapshots
    print("Processing order book data...")
    start_process = time.time()

    # Group by timestamp to create order book snapshots
    order_book_data = []

    for timestamp, group in df.groupby(level=0):
        # Get L1 trades for this timestamp
        l1_data = group[group["level"] == "L1"]
        # Get L2 order book updates
        l2_data = group[group["level"] == "L2"]

        if len(l1_data) > 0:
            # Use the last trade price as our reference
            last_trade = l1_data.iloc[-1]
            trade_price = float(last_trade["price"])
            trade_volume = int(last_trade["volume"])

            # Build order book from L2 data
            bids = []
            asks = []

            if len(l2_data) > 0:
                # Group L2 data by price and mdt
                for _, row in l2_data.iterrows():
                    price = float(row["price"])
                    volume = int(row["volume"])
                    mdt = int(row["mdt"])

                    if price > 0 and volume > 0:  # Valid price and volume
                        if mdt == 1:  # Bid
                            bids.append((price, volume))
                        elif mdt == 0:  # Ask
                            asks.append((price, volume))

                # Sort and deduplicate by price
                bids = sorted(list(set(bids)), key=lambda x: x[0], reverse=True)[
                    :5
                ]  # Top 5 bid levels
                asks = sorted(list(set(asks)), key=lambda x: x[0])[
                    :5
                ]  # Top 5 ask levels

            # If no L2 data, create synthetic bid/ask
            if not bids or not asks:
                tick_size = 0.25
                bids = [(trade_price - tick_size, trade_volume)]
                asks = [(trade_price + tick_size, trade_volume)]

            # Create order book snapshot
            order_book_data.append(
                {
                    "timestamp": timestamp,
                    "price": trade_price,
                    "volume": trade_volume,
                    "bid": bids[0][0] if bids else trade_price - 0.25,
                    "ask": asks[0][0] if asks else trade_price + 0.25,
                    "bid_levels": bids,
                    "ask_levels": asks,
                }
            )

    print(
        f"Processed {len(order_book_data):,} order book snapshots in {time.time()-start_process:.2f}s"
    )
    return order_book_data


def run_fixed_backtest(order_book_data, strategy_name, debug=False):
    """Run backtest with properly formatted order book data."""
    print(f"\nRunning {strategy_name} strategy with proper L2 data...")

    if strategy_name == "order_book_imbalance":
        from src.strategy_lab.strategies.implementations.order_book_imbalance import (
            OrderBookImbalanceStrategy,
        )

        strategy = OrderBookImbalanceStrategy(
            positive_threshold=0.2,  # Lower threshold to get signals
            negative_threshold=-0.2,
            position_size=1,
            stop_loss_pct=0.5,
            max_holding_seconds=300,
        )
    elif strategy_name == "bid_ask_bounce":
        from src.strategy_lab.strategies.implementations.bid_ask_bounce import (
            BidAskBounceStrategy,
        )

        strategy = BidAskBounceStrategy(
            bounce_sensitivity=0.5,  # Lower sensitivity
            min_bounce_strength=0.3,
            profit_target_ticks=2,
            stop_loss_ticks=1,
            max_holding_seconds=120,
        )
    else:
        raise ValueError(f"Unknown strategy: {strategy_name}")

    # Initialize strategy
    strategy.initialize()

    print(f"Strategy initialized: {strategy.name}")
    if strategy_name == "order_book_imbalance":
        print(
            f"Thresholds: +{strategy.positive_threshold}, {strategy.negative_threshold}"
        )

    # Portfolio tracking
    initial_capital = 100000
    cash = initial_capital
    position = 0
    entry_price = 0
    trades = []
    signals_generated = 0

    print(f"Initial capital: ${cash:,.2f}")
    print("Processing order book snapshots...")

    # Process order book data
    for i, snapshot in enumerate(order_book_data):
        try:
            timestamp = snapshot["timestamp"]
            price = snapshot["price"]
            volume = snapshot["volume"]
            bid = snapshot["bid"]
            ask = snapshot["ask"]
            bid_levels = snapshot["bid_levels"]
            ask_levels = snapshot["ask_levels"]

            # Call strategy with proper L2 data
            signal = strategy.process_tick(
                timestamp=timestamp,
                price=price,
                volume=volume,
                bid=bid,
                ask=ask,
                bid_levels=bid_levels,  # This is what the strategy needs!
                ask_levels=ask_levels,  # This is what the strategy needs!
            )

            if signal is not None and signal != 0:
                signals_generated += 1

                if debug and signals_generated <= 10:
                    print(
                        f"  Signal {signals_generated}: {signal} at {timestamp} (price: ${price:.2f})"
                    )

                # Execute trades
                if signal > 0 and position == 0:  # Buy signal, no position
                    position = 1
                    entry_price = ask  # Buy at ask
                    cash -= 2.0  # Commission

                    trades.append(
                        {
                            "time": timestamp,
                            "action": "BUY",
                            "price": entry_price,
                            "signal_strength": signal,
                        }
                    )

                    if len(trades) <= 20:
                        print(f"  Trade {len(trades)}: BUY @ ${entry_price:.2f}")

                elif signal < 0 and position > 0:  # Sell signal, have position
                    exit_price = bid  # Sell at bid
                    ticks = (exit_price - entry_price) / 0.25
                    pnl = ticks * 2  # $2 per tick for MNQ
                    cash += pnl - 2.0  # PnL minus commission
                    position = 0

                    trades.append(
                        {
                            "time": timestamp,
                            "action": "SELL",
                            "price": exit_price,
                            "pnl": pnl,
                            "ticks": ticks,
                        }
                    )

                    if len(trades) <= 20:
                        print(
                            f"  Trade {len(trades)}: SELL @ ${exit_price:.2f} (PnL: ${pnl:.2f})"
                        )

        except Exception as e:
            if debug and i < 10:
                print(f"  Error at snapshot {i}: {e}")

        # Progress update
        if i > 0 and i % 1000 == 0:
            print(
                f"  Processed {i:,} / {len(order_book_data):,} snapshots ({i/len(order_book_data)*100:.1f}%)"
            )

    # Results
    total_trades = len(trades)
    round_trips = sum(1 for t in trades if t["action"] == "SELL")
    total_pnl = cash - initial_capital

    print(f"\n=== RESULTS ===")
    print(f"Order book snapshots processed: {len(order_book_data):,}")
    print(f"Signals generated: {signals_generated}")
    print(f"Total trade actions: {total_trades}")
    print(f"Round trip trades: {round_trips}")
    print(f"Total PnL: ${total_pnl:.2f}")
    print(f"Return: {total_pnl/initial_capital:.2%}")
    print(f"Final balance: ${cash:.2f}")

    if round_trips > 0:
        wins = [t for t in trades if t.get("pnl", 0) > 0]
        losses = [t for t in trades if t.get("pnl", 0) < 0]

        print(f"Winning trades: {len(wins)}")
        print(f"Losing trades: {len(losses)}")
        print(f"Win rate: {len(wins)/round_trips:.1%}")

        if wins:
            avg_win = np.mean([t["pnl"] for t in wins])
            print(f"Average win: ${avg_win:.2f}")
        if losses:
            avg_loss = np.mean([t["pnl"] for t in losses])
            print(f"Average loss: ${avg_loss:.2f}")


def main():
    parser = argparse.ArgumentParser(
        description="Fixed MNQ Backtest with proper L2 data"
    )
    parser.add_argument(
        "--strategy",
        choices=["order_book_imbalance", "bid_ask_bounce"],
        default="order_book_imbalance",
        help="Strategy to test",
    )
    parser.add_argument("--minutes", type=int, default=15, help="Duration in minutes")
    parser.add_argument(
        "--start-time", default="2024-01-02 09:30:00", help="Start time"
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug output")

    args = parser.parse_args()

    print("Fixed MNQ Backtest with Proper L2 Data")
    print("=" * 50)
    print(f"Strategy: {args.strategy}")
    print(f"Duration: {args.minutes} minutes")
    print(f"Start: {args.start_time}")
    print("=" * 50)

    file_path = Path("data/MNQ/03-24/20240102.parquet")

    try:
        # Load and process data
        order_book_data = load_and_process_data(
            file_path, args.start_time, args.minutes
        )

        # Run backtest
        run_fixed_backtest(order_book_data, args.strategy, args.debug)

        return 0

    except Exception as e:
        print(f"Error: {e}")
        if args.debug:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
