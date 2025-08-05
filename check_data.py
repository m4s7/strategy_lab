#!/usr/bin/env python3
"""Check what data files exist"""

import os
from pathlib import Path

data_dir = Path("data/MNQ")

# List contract directories
print("Contract directories:")
contracts = sorted([d for d in data_dir.iterdir() if d.is_dir()])
for contract in contracts[:5]:  # Show first 5
    files = list(contract.glob("*.parquet"))
    print(f"  {contract.name}: {len(files)} files")
    if files:
        # Show first file size
        first_file = files[0]
        size_mb = first_file.stat().st_size / (1024 * 1024)
        print(f"    First file: {first_file.name} ({size_mb:.1f} MB)")

# Check for index file
index_file = data_dir.parent / "MNQ_parquet_files.json"
if index_file.exists():
    print(f"\nIndex file exists: {index_file}")
    print(f"Size: {index_file.stat().st_size / 1024:.1f} KB")
else:
    print("\nNo index file found")
