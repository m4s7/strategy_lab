"""Data loader module for efficient MNQ tick data loading."""

from collections.abc import Iterator
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow.parquet as pq


class DataLoader:
    """Efficient loader for MNQ tick data with streaming and batching support."""

    def __init__(
        self,
        cache_size_mb: int = 1000,
        chunk_size: int = 100_000,
    ):
        """
        Initialize the data loader.

        Args:
            cache_size_mb: Maximum cache size in MB
            chunk_size: Default chunk size for batch operations
        """
        self.cache_size_mb = cache_size_mb
        self.chunk_size = chunk_size
        self._cache: dict[tuple[Path, tuple[str, ...] | None], pd.DataFrame] = {}
        self._cache_usage_mb = 0

    def load_file(
        self,
        file_path: Path,
        columns: list[str] | None = None,
        filters: list[tuple[str, str, Any]] | None = None,
        use_cache: bool = True,
    ) -> pd.DataFrame:
        """
        Load a single Parquet file into memory.

        Args:
            file_path: Path to the Parquet file
            columns: Specific columns to load (None for all)
            filters: List of (column, operator, value) tuples for filtering
            use_cache: Whether to use caching

        Returns:
            DataFrame with loaded data
        """
        # Check cache first
        cache_key = (file_path, tuple(columns) if columns else None)
        if use_cache and cache_key in self._cache:
            df = self._cache[cache_key]
            if filters:
                return self._apply_filters(df, filters)
            return df

        # Load from file
        df = pd.read_parquet(
            file_path,
            columns=columns,
            filters=filters if filters else None,
        )

        # Cache if enabled and size permits
        if use_cache:
            df_size_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
            if self._cache_usage_mb + df_size_mb <= self.cache_size_mb:
                self._cache[cache_key] = df
                self._cache_usage_mb += df_size_mb
            else:
                # Evict oldest entries if needed
                self._evict_cache(df_size_mb)
                self._cache[cache_key] = df
                self._cache_usage_mb += df_size_mb

        return df

    def stream_file(
        self,
        file_path: Path,
        columns: list[str] | None = None,
        chunk_size: int | None = None,
    ) -> Iterator[pd.DataFrame]:
        """
        Stream a Parquet file in chunks.

        Args:
            file_path: Path to the Parquet file
            columns: Specific columns to load
            chunk_size: Size of each chunk (uses default if None)

        Yields:
            DataFrame chunks
        """
        chunk_size = chunk_size or self.chunk_size

        parquet_file = pq.ParquetFile(file_path)

        for batch in parquet_file.iter_batches(
            batch_size=chunk_size,
            columns=columns,
        ):
            yield batch.to_pandas()

    def load_time_range(
        self,
        file_paths: list[Path],
        start_time: datetime,
        end_time: datetime,
        columns: list[str] | None = None,
    ) -> pd.DataFrame:
        """
        Load data within a specific time range from multiple files.

        Args:
            file_paths: List of file paths to load from
            start_time: Start of time range
            end_time: End of time range
            columns: Specific columns to load

        Returns:
            Combined DataFrame with data in time range
        """
        # Convert datetime to nanoseconds
        start_ns = int(start_time.timestamp() * 1e9)
        end_ns = int(end_time.timestamp() * 1e9)

        dfs = []
        for file_path in file_paths:
            # Use Parquet predicate pushdown for efficient filtering
            filters = [
                ("timestamp", ">=", start_ns),
                ("timestamp", "<=", end_ns),
            ]

            df = self.load_file(
                file_path,
                columns=columns,
                filters=filters,
                use_cache=False,  # Don't cache filtered data
            )

            if not df.empty:
                dfs.append(df)

        if dfs:
            return pd.concat(dfs, ignore_index=True).sort_values("timestamp")
        # Return empty DataFrame with expected columns
        return pd.DataFrame(columns=columns if columns else [])

    def stream_time_range(
        self,
        file_paths: list[Path],
        start_time: datetime,
        end_time: datetime,
        columns: list[str] | None = None,
        chunk_size: int | None = None,
    ) -> Iterator[pd.DataFrame]:
        """
        Stream data within a time range from multiple files.

        Args:
            file_paths: List of file paths to stream from
            start_time: Start of time range
            end_time: End of time range
            columns: Specific columns to load
            chunk_size: Size of each chunk

        Yields:
            DataFrame chunks in chronological order
        """
        # Convert datetime to nanoseconds
        start_ns = int(start_time.timestamp() * 1e9)
        end_ns = int(end_time.timestamp() * 1e9)

        # Process files in order
        for file_path in file_paths:
            for chunk in self.stream_file(file_path, columns, chunk_size):
                # Filter chunk by time range
                if "timestamp" in chunk.columns:
                    mask = (chunk["timestamp"] >= start_ns) & (
                        chunk["timestamp"] <= end_ns
                    )
                    filtered_chunk = chunk[mask]

                    if not filtered_chunk.empty:
                        yield filtered_chunk

    def load_by_mdt(
        self,
        file_paths: list[Path],
        mdt_types: list[int],
        columns: list[str] | None = None,
    ) -> dict[int, pd.DataFrame]:
        """
        Load data grouped by MDT (Market Data Type).

        Args:
            file_paths: List of file paths to load from
            mdt_types: List of MDT values to load
            columns: Specific columns to load

        Returns:
            Dictionary mapping MDT values to DataFrames
        """
        result: dict[int, list[pd.DataFrame]] = {mdt: [] for mdt in mdt_types}

        for file_path in file_paths:
            df = self.load_file(file_path, columns=columns)

            if "mdt" in df.columns:
                for mdt in mdt_types:
                    mdt_data = df[df["mdt"] == mdt]
                    if not mdt_data.empty:
                        result[mdt].append(mdt_data)

        # Concatenate results for each MDT
        for mdt in mdt_types:
            if result[mdt]:
                result[mdt] = pd.concat(result[mdt], ignore_index=True)
            else:
                result[mdt] = pd.DataFrame(columns=columns if columns else [])

        return result

    def load_level2_book(
        self,
        file_path: Path,
        timestamp: int | None = None,
        max_depth: int = 10,
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Load Level 2 order book data at a specific timestamp.

        Args:
            file_path: Path to Level 2 data file
            timestamp: Specific timestamp to reconstruct book at
            max_depth: Maximum book depth to return

        Returns:
            Tuple of (bid_book, ask_book) DataFrames
        """
        # Load Level 2 data
        filters: list[tuple[str, str, Any]] = [("level", "==", "2")]
        if timestamp:
            # Load all data up to the timestamp to reconstruct book
            filters.append(("timestamp", "<=", timestamp))

        df = self.load_file(file_path, filters=filters, use_cache=False)

        if df.empty:
            empty_book = pd.DataFrame(columns=["price", "volume", "depth"])
            return empty_book, empty_book

        # Separate bids and asks
        bids = df[df["mdt"] == 1].copy()
        asks = df[df["mdt"] == 0].copy()

        # Reconstruct order books
        bid_book = self._reconstruct_book(bids, max_depth)
        ask_book = self._reconstruct_book(asks, max_depth)

        return bid_book, ask_book

    def aggregate_bars(
        self,
        file_paths: list[Path],
        bar_type: str = "time",
        bar_size: int | pd.Timedelta = pd.Timedelta(minutes=1),
        columns: list[str] | None = None,
    ) -> pd.DataFrame:
        """
        Aggregate tick data into bars (OHLCV).

        Args:
            file_paths: List of file paths to load from
            bar_type: Type of bars ("time", "tick", "volume")
            bar_size: Size of each bar
            columns: Specific columns to load

        Returns:
            DataFrame with aggregated bars
        """
        # Ensure we have necessary columns
        required_cols = ["timestamp", "price", "volume", "mdt"]
        if columns:
            columns = list(set(columns) | set(required_cols))

        # Load trade data only (mdt=2 for Last)
        all_trades = []
        for file_path in file_paths:
            df = self.load_file(
                file_path,
                columns=columns,
                filters=[("mdt", "==", 2)],
            )
            if not df.empty:
                all_trades.append(df)

        if not all_trades:
            return pd.DataFrame(
                columns=["timestamp", "open", "high", "low", "close", "volume"]
            )

        trades = pd.concat(all_trades, ignore_index=True).sort_values("timestamp")

        if bar_type == "time":
            return self._aggregate_time_bars(trades, bar_size)
        if bar_type == "tick":
            return self._aggregate_tick_bars(trades, bar_size)
        if bar_type == "volume":
            return self._aggregate_volume_bars(trades, bar_size)
        raise ValueError(f"Unknown bar type: {bar_type}")

    def _apply_filters(
        self, df: pd.DataFrame, filters: list[tuple[str, str, Any]]
    ) -> pd.DataFrame:
        """Apply filters to a DataFrame."""
        result = df

        for col, op, value in filters:
            if col not in result.columns:
                continue

            if op == "==":
                result = result[result[col] == value]
            elif op == "!=":
                result = result[result[col] != value]
            elif op == "<":
                result = result[result[col] < value]
            elif op == "<=":
                result = result[result[col] <= value]
            elif op == ">":
                result = result[result[col] > value]
            elif op == ">=":
                result = result[result[col] >= value]
            elif op == "in":
                result = result[result[col].isin(value)]
            elif op == "not in":
                result = result[~result[col].isin(value)]

        return result

    def _evict_cache(self, required_mb: float) -> None:
        """Evict cache entries to make room for new data."""
        # Simple FIFO eviction for now
        while self._cache and self._cache_usage_mb + required_mb > self.cache_size_mb:
            # Remove first entry
            key = next(iter(self._cache))
            df = self._cache.pop(key)
            self._cache_usage_mb -= df.memory_usage(deep=True).sum() / (1024 * 1024)

    def _reconstruct_book(self, updates: pd.DataFrame, max_depth: int) -> pd.DataFrame:
        """Reconstruct order book from update messages."""
        if updates.empty:
            return pd.DataFrame(columns=["price", "volume", "depth"])

        # Sort by timestamp to apply updates in order
        updates = updates.sort_values("timestamp")

        # Build book state
        book_state = {}

        for _, row in updates.iterrows():
            price = row["price"]
            volume = row["volume"]
            operation = row.get("operation", 0)
            depth = row.get("depth", 0)

            if operation == 0:  # Add
                book_state[price] = {"volume": volume, "depth": depth}
            elif operation == 1:  # Update
                if price in book_state:
                    book_state[price]["volume"] = volume
            elif operation == 2:  # Remove
                book_state.pop(price, None)

        # Convert to DataFrame
        if not book_state:
            return pd.DataFrame(columns=["price", "volume", "depth"])

        book_df = pd.DataFrame.from_dict(book_state, orient="index").reset_index()
        book_df.columns = ["price", "volume", "depth"]

        # Sort and limit depth
        book_df = book_df.sort_values("price", ascending=False)[:max_depth]

        return book_df

    def _aggregate_time_bars(
        self, trades: pd.DataFrame, bar_size: pd.Timedelta
    ) -> pd.DataFrame:
        """Aggregate trades into time-based bars."""
        # Convert timestamp to datetime
        trades["datetime"] = pd.to_datetime(trades["timestamp"], unit="ns")

        # Group by time intervals
        trades.set_index("datetime", inplace=True)

        bars = trades.groupby(pd.Grouper(freq=bar_size)).agg(
            {
                "price": ["first", "max", "min", "last"],
                "volume": "sum",
                "timestamp": "first",
            }
        )

        # Flatten column names
        bars.columns = ["open", "high", "low", "close", "volume", "timestamp"]

        # Remove empty bars
        bars = bars.dropna(subset=["open"])

        return bars.reset_index(drop=True)

    def _aggregate_tick_bars(self, trades: pd.DataFrame, bar_size: int) -> pd.DataFrame:
        """Aggregate trades into tick-count bars."""
        num_bars = len(trades) // bar_size

        bars = []
        for i in range(num_bars):
            start_idx = i * bar_size
            end_idx = (i + 1) * bar_size
            bar_trades = trades.iloc[start_idx:end_idx]

            bar = {
                "timestamp": bar_trades.iloc[0]["timestamp"],
                "open": bar_trades.iloc[0]["price"],
                "high": bar_trades["price"].max(),
                "low": bar_trades["price"].min(),
                "close": bar_trades.iloc[-1]["price"],
                "volume": bar_trades["volume"].sum(),
            }
            bars.append(bar)

        return pd.DataFrame(bars)

    def _aggregate_volume_bars(
        self, trades: pd.DataFrame, bar_size: int
    ) -> pd.DataFrame:
        """Aggregate trades into volume bars."""
        trades["cum_volume"] = trades["volume"].cumsum()
        trades["bar_num"] = trades["cum_volume"] // bar_size

        bars = trades.groupby("bar_num").agg(
            {
                "timestamp": "first",
                "price": ["first", "max", "min", "last"],
                "volume": "sum",
            }
        )

        # Flatten column names
        bars.columns = ["timestamp", "open", "high", "low", "close", "volume"]

        return bars.reset_index(drop=True)

    def clear_cache(self) -> None:
        """Clear the internal cache."""
        self._cache.clear()
        self._cache_usage_mb = 0
