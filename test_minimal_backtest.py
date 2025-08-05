#!/usr/bin/env python3
"""
Minimal test to check if backtesting works at all
"""

import logging
from datetime import datetime
from pathlib import Path
import pandas as pd

# Set up logging to see what's happening
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def test_data_loading():
    """Test if we can load any data at all."""
    from src.strategy_lab.data.ingestion.file_discovery import ParquetFileDiscovery
    from src.strategy_lab.data.ingestion.data_loader import DataLoader

    print("Step 1: Discovering files...")
    discovery = ParquetFileDiscovery(Path("data/MNQ"))
    files = discovery.discover_files(contract_months=["03-24"])
    print(f"Found {len(files)} files for contract 03-24")

    if not files:
        print("No files found!")
        return

    # Just load the first file
    print(f"\nStep 2: Loading first file: {files[0].path}")
    loader = DataLoader()
    df = loader.load_file(files[0].path)
    print(f"Loaded {len(df)} rows")
    print(f"Columns: {list(df.columns)}")
    print(f"Date range: {df.index.min()} to {df.index.max()}")

    # Show sample data
    print("\nSample data:")
    print(df.head())


def test_simple_strategy():
    """Test if we can create a strategy."""
    from src.strategy_lab.strategies.implementations.order_book_imbalance import (
        OrderBookImbalanceStrategy,
    )

    print("\nStep 3: Creating strategy...")
    strategy = OrderBookImbalanceStrategy()
    print(f"Strategy created: {strategy.name}")
    print(f"Strategy description: {strategy.description}")


def test_minimal_backtest():
    """Test minimal backtest with just one day of data."""
    from src.strategy_lab.backtesting.engine.data_adapter import BacktestDataLoader

    print("\nStep 4: Testing data adapter...")
    loader = BacktestDataLoader(Path("data/MNQ"))

    # Load just one hour of data
    start = pd.Timestamp("2024-01-02 09:00:00")
    end = pd.Timestamp("2024-01-02 10:00:00")

    print(f"Loading data from {start} to {end}...")
    try:
        data = loader.load_data(start_date=start, end_date=end, contracts=["03-24"])
        print(f"Loaded {len(data)} ticks")

        # Show some info
        if not data.empty:
            print(f"Columns: {list(data.columns)}")
            print(f"First tick: {data.index[0]}")
            print(f"Last tick: {data.index[-1]}")
            print("\nFirst few rows:")
            print(data.head())

    except Exception as e:
        print(f"Error loading data: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    print("=== Minimal Backtest Test ===\n")

    # Test each component separately
    test_data_loading()
    test_simple_strategy()
    test_minimal_backtest()
