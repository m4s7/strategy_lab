"""Data adapter for backtesting engine."""

from datetime import datetime
from pathlib import Path
import pandas as pd
from typing import List, Optional

from ...data.ingestion.data_loader import DataLoader
from ...data.ingestion.file_discovery import ParquetFileDiscovery


class BacktestDataLoader:
    """Adapter class to provide data loading for backtesting."""

    def __init__(self, data_path: Path):
        """Initialize with data path."""
        self.data_path = data_path
        self.data_loader = DataLoader()
        self.file_discovery = ParquetFileDiscovery(data_path)

    def load_data(
        self,
        start_date: Optional[pd.Timestamp] = None,
        end_date: Optional[pd.Timestamp] = None,
        columns: Optional[List[str]] = None,
        contracts: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """Load data for specified date range and contracts.

        Args:
            start_date: Start date for data
            end_date: End date for data
            columns: Columns to load
            contracts: Contract months to include

        Returns:
            Combined DataFrame with all data
        """
        # Discover files
        files = self.file_discovery.discover_files()

        # Filter by contracts if specified
        if contracts:
            files = [f for f in files if f.contract_month in contracts]

        if not files:
            raise ValueError("No data files found for specified contracts")

        # Load and combine data
        dfs = []
        for file in files:
            try:
                df = self.data_loader.load_file(file.path, columns=columns)

                # Filter by date range if specified
                if start_date or end_date:
                    if "timestamp" in df.columns:
                        df["timestamp"] = pd.to_datetime(df["timestamp"])
                        df.set_index("timestamp", inplace=True)

                    if start_date and end_date:
                        df = df[start_date:end_date]
                    elif start_date:
                        df = df[start_date:]
                    elif end_date:
                        df = df[:end_date]

                if not df.empty:
                    dfs.append(df)

            except Exception as e:
                print(f"Warning: Failed to load {file}: {e}")
                continue

        if not dfs:
            raise ValueError("No data loaded for specified date range")

        # Combine all data
        combined = pd.concat(dfs, ignore_index=False)

        # Sort by timestamp
        if "timestamp" in combined.columns:
            combined.sort_values("timestamp", inplace=True)
        else:
            combined.sort_index(inplace=True)

        return combined
