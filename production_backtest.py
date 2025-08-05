#!/usr/bin/env python3
"""
Production-ready backtest with better progress reporting and trade summary

This version provides:
1. Better progress reporting during long backtests
2. Running P&L updates
3. Trade summaries at intervals
4. Final detailed analysis
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
    print(f"Memory usage: {df.memory_usage(deep=True).sum()/1024**2:.1f} MB")

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


def run_production_backtest(order_book_data, strategy_name, debug=False):
    """Run backtest with production-level reporting."""
    print(f"\nRunning {strategy_name} strategy...")

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

    # Portfolio tracking
    initial_capital = 100000
    cash = initial_capital
    position = 0
    entry_price = 0
    trades = []
    signals_generated = 0

    print(f"Initial capital: ${cash:,.2f}")
    print("Processing order book snapshots...")

    # Progress tracking
    last_progress_time = time.time()
    last_progress_trades = 0
    last_progress_pnl = 0

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
                bid_levels=bid_levels,
                ask_levels=ask_levels,
            )

            if signal is not None and signal != 0:
                signals_generated += 1

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

                    # Show first few and recent trades
                    if len(trades) <= 5 or len(trades) % 50 == 0:
                        print(
                            f"  Trade {len(trades)}: BUY @ ${entry_price:.2f} at {timestamp.strftime('%H:%M:%S')}"
                        )

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

                    # Show first few and milestone trades
                    if len(trades) <= 5 or len(trades) % 50 == 0:
                        print(
                            f"  Trade {len(trades)}: SELL @ ${exit_price:.2f} (PnL: ${pnl:.2f}) at {timestamp.strftime('%H:%M:%S')}"
                        )

        except Exception as e:
            if debug and i < 10:
                print(f"  Error at snapshot {i}: {e}")

        # Progress reporting every 30 seconds of processing time
        current_time = time.time()
        if current_time - last_progress_time > 30:
            current_pnl = cash - initial_capital
            new_trades = len(trades) - last_progress_trades
            pnl_change = current_pnl - last_progress_pnl

            progress_pct = (i + 1) / len(order_book_data) * 100
            print(
                f"\n  📊 Progress: {progress_pct:.1f}% | Snapshots: {i+1:,}/{len(order_book_data):,} | "
                f"Signals: {signals_generated:,} | Trades: {len(trades):,} | "
                f"P&L: ${current_pnl:,.2f} | Time: {timestamp.strftime('%H:%M:%S')}"
            )

            if new_trades > 0:
                print(
                    f"     📈 Last 30s: {new_trades} new trades, P&L change: ${pnl_change:+.2f}"
                )

            last_progress_time = current_time
            last_progress_trades = len(trades)
            last_progress_pnl = current_pnl

    # Final comprehensive results
    total_trades = len(trades)
    round_trips = sum(1 for t in trades if t["action"] == "SELL")
    total_pnl = cash - initial_capital

    print(f"\n{'='*80}")
    print(f"BACKTEST COMPLETE - {strategy_name.upper()}")
    print(f"{'='*80}")

    print(f"\n📈 EXECUTION SUMMARY:")
    print(f"   Order book snapshots processed: {len(order_book_data):,}")
    print(f"   Signals generated: {signals_generated:,}")
    print(f"   Total trade actions: {total_trades:,}")
    print(f"   Round trip trades: {round_trips:,}")

    print(f"\n💰 PERFORMANCE SUMMARY:")
    print(f"   Initial capital: ${initial_capital:,.2f}")
    print(f"   Final balance: ${cash:,.2f}")
    print(f"   Total PnL: ${total_pnl:,.2f}")
    print(f"   Return: {total_pnl/initial_capital:.2%}")

    if round_trips > 0:
        wins = [t for t in trades if t.get("pnl", 0) > 0]
        losses = [t for t in trades if t.get("pnl", 0) < 0]

        print(f"\n📊 TRADE ANALYSIS:")
        print(f"   Winning trades: {len(wins):,}")
        print(f"   Losing trades: {len(losses):,}")
        print(f"   Win rate: {len(wins)/round_trips:.1%}")

        if wins:
            win_pnls = [t["pnl"] for t in wins]
            print(f"   Average win: ${np.mean(win_pnls):.2f}")
            print(f"   Largest win: ${max(win_pnls):.2f}")

        if losses:
            loss_pnls = [t["pnl"] for t in losses]
            print(f"   Average loss: ${np.mean(loss_pnls):.2f}")
            print(f"   Largest loss: ${min(loss_pnls):.2f}")

        if wins and losses:
            total_wins = sum(win_pnls)
            total_losses = abs(sum(loss_pnls))
            profit_factor = (
                total_wins / total_losses if total_losses > 0 else float("inf")
            )
            print(f"   Profit factor: {profit_factor:.2f}")

        # Time analysis
        if len(trades) >= 2:
            trade_times = [t["time"] for t in trades if t["action"] == "SELL"]
            if len(trade_times) >= 2:
                duration = trade_times[-1] - trade_times[0]
                trades_per_hour = round_trips / (duration.total_seconds() / 3600)
                print(f"   Trading frequency: {trades_per_hour:.1f} trades/hour")

    print(f"\n{'='*80}")

    return {
        "total_pnl": total_pnl,
        "return_pct": total_pnl / initial_capital,
        "trades": round_trips,
        "win_rate": len(wins) / round_trips if round_trips > 0 else 0,
        "signals": signals_generated,
    }


def main():
    parser = argparse.ArgumentParser(description="Production MNQ Backtest")
    parser.add_argument(
        "--strategy",
        choices=["order_book_imbalance", "bid_ask_bounce"],
        default="bid_ask_bounce",
        help="Strategy to test",
    )
    parser.add_argument("--minutes", type=int, default=30, help="Duration in minutes")
    parser.add_argument(
        "--hours", type=float, help="Duration in hours (alternative to minutes)"
    )
    parser.add_argument(
        "--start-time", default="2024-01-02 09:30:00", help="Start time"
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug output")

    args = parser.parse_args()

    # Determine duration
    if args.hours:
        duration_minutes = int(args.hours * 60)
    else:
        duration_minutes = args.minutes

    print("Production MNQ Backtest")
    print("=" * 50)
    print(f"Strategy: {args.strategy}")
    print(f"Duration: {duration_minutes} minutes ({duration_minutes/60:.1f} hours)")
    print(f"Start: {args.start_time}")
    print("=" * 50)

    file_path = Path("data/MNQ/03-24/20240102.parquet")

    try:
        # Load and process data
        order_book_data = load_and_process_data(
            file_path, args.start_time, duration_minutes
        )

        # Run backtest
        results = run_production_backtest(order_book_data, args.strategy, args.debug)

        return 0

    except Exception as e:
        print(f"Error: {e}")
        if args.debug:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
