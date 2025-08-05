#!/usr/bin/env python3
"""Debug data loading to find the bottleneck"""

import time
from pathlib import Path
import pandas as pd
from datetime import datetime

print("=== Data Loading Debug ===\n")

# Step 1: File discovery
print("1. Testing file discovery...")
start = time.time()

from src.strategy_lab.data.ingestion.file_discovery import ParquetFileDiscovery

discovery = ParquetFileDiscovery(Path("data/MNQ"))
files = discovery.discover_files(contract_months=["03-24"])

print(f"   Found {len(files)} files in {time.time() - start:.2f}s")

# Step 2: Load one file directly
print("\n2. Loading single file directly...")
start = time.time()

file_path = Path("data/MNQ/03-24/20240102.parquet")
df = pd.read_parquet(file_path)

print(f"   Loaded {len(df):,} rows in {time.time() - start:.2f}s")
print(f"   Memory usage: {df.memory_usage(deep=True).sum() / 1024**2:.1f} MB")

# Step 3: Filter by time
print("\n3. Filtering by time range...")
start = time.time()

# Convert timestamp to datetime index
df["timestamp"] = pd.to_datetime(df["timestamp"])
df.set_index("timestamp", inplace=True)

# Filter to 30 minutes
start_time = pd.Timestamp("2024-01-02 09:30:00")
end_time = pd.Timestamp("2024-01-02 10:00:00")
filtered = df[start_time:end_time]

print(f"   Filtered to {len(filtered):,} rows in {time.time() - start:.2f}s")
print(f"   Time range: {filtered.index.min()} to {filtered.index.max()}")

# Step 4: Test BacktestDataLoader
print("\n4. Testing BacktestDataLoader...")
start = time.time()

try:
    from src.strategy_lab.backtesting.engine.data_adapter import BacktestDataLoader

    loader = BacktestDataLoader(Path("data/MNQ"))

    # Load small time range
    data = loader.load_data(
        start_date=start_time, end_date=end_time, contracts=["03-24"]
    )

    print(
        f"   BacktestDataLoader loaded {len(data):,} rows in {time.time() - start:.2f}s"
    )

except Exception as e:
    print(f"   Error: {e}")
    import traceback

    traceback.print_exc()

# Step 5: Check data types
print("\n5. Data types:")
print(filtered.dtypes)
