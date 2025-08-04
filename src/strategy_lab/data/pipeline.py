"""Data pipeline integration for MNQ tick data streaming."""

import logging
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from .ingestion.data_loader import DataLoader
from .ingestion.data_validator import DataValidator
from .ingestion.file_discovery import ParquetFileDiscovery, ParquetFileInfo

logger = logging.getLogger(__name__)


class TickDataStream:
    """Streaming interface for MNQ tick data."""

    def __init__(
        self,
        data_path: Path,
        contracts: list[str] | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        chunk_size: int = 100_000,
        memory_limit_mb: int = 1000,
        validate_data: bool = True,
    ):
        """Initialize tick data stream.

        Args:
            data_path: Path to MNQ data directory
            contracts: List of contract months to include (e.g., ["03-24", "06-24"])
            start_date: Start date for filtering
            end_date: End date for filtering
            chunk_size: Size of data chunks for streaming
            memory_limit_mb: Memory limit for data loading
            validate_data: Whether to validate data integrity
        """
        self.data_path = Path(data_path)
        self.contracts = contracts
        self.start_date = start_date
        self.end_date = end_date
        self.chunk_size = chunk_size
        self.memory_limit_mb = memory_limit_mb
        self.validate_data = validate_data

        # Initialize components
        self.file_discovery = ParquetFileDiscovery(self.data_path)
        self.data_loader = DataLoader(
            cache_size_mb=memory_limit_mb // 2,  # Use half for cache
            chunk_size=chunk_size,
        )
        self.validator = DataValidator() if validate_data else None

        # Discovered files cache
        self._discovered_files: list[ParquetFileInfo] | None = None
        self._validation_results: dict[Path, Any] | None = None

    def discover_files(self) -> list[ParquetFileInfo]:
        """Discover available data files matching criteria.

        Returns:
            List of ParquetFileInfo objects for matching files

        Raises:
            FileNotFoundError: If data directory doesn't exist
            ValueError: If no matching files found
        """
        if self._discovered_files is not None:
            return self._discovered_files

        logger.info(f"Discovering files in {self.data_path}")

        if not self.data_path.exists():
            raise FileNotFoundError(
                f"Data directory not found: {self.data_path}. "
                "Please ensure MNQ data is available."
            )

        try:
            files = self.file_discovery.discover_files(
                contract_months=self.contracts,
                start_date=self.start_date,
                end_date=self.end_date,
            )
        except Exception as e:
            raise RuntimeError(f"Failed to discover data files: {e}") from e

        if not files:
            error_msg = "No data files found matching criteria"
            if self.contracts:
                error_msg += f" (contracts: {self.contracts})"
            if self.start_date or self.end_date:
                error_msg += f" (date range: {self.start_date} to {self.end_date})"
            raise ValueError(error_msg)

        logger.info(f"Discovered {len(files)} data files")
        self._discovered_files = files
        return files

    def validate_files(self) -> dict[Path, Any]:
        """Validate discovered data files.

        Returns:
            Dictionary mapping file paths to validation results

        Raises:
            RuntimeError: If validation fails for critical files
        """
        if not self.validate_data or self.validator is None:
            return {}

        if self._validation_results is not None:
            return self._validation_results

        files = self.discover_files()
        logger.info(f"Validating {len(files)} data files...")

        file_paths = [f.path for f in files]
        results = self.validator.validate_batch(file_paths)

        # Check for critical validation failures
        failed_files = [path for path, result in results.items() if not result.is_valid]
        if failed_files:
            logger.warning(f"Validation failed for {len(failed_files)} files")
            for path in failed_files[:5]:  # Log first 5 failures
                result = results[path]
                logger.warning(f"  {path.name}: {', '.join(result.errors[:3])}")

            # If more than 50% of files fail, raise error
            failure_rate = len(failed_files) / len(results)
            if failure_rate > 0.5:
                raise RuntimeError(
                    f"High validation failure rate ({failure_rate:.1%}). "
                    "Please check data integrity."
                )

        logger.info(
            f"Validation completed: {len(results) - len(failed_files)} valid files"
        )
        self._validation_results = results
        return results

    def stream_ticks(
        self,
        columns: list[str] | None = None,
        chunk_size: int | None = None,
    ) -> Iterator[pd.DataFrame]:
        """Stream tick data chronologically across all files.

        Args:
            columns: Specific columns to include (None for all)
            chunk_size: Override default chunk size

        Yields:
            DataFrames containing tick data in chronological order

        Raises:
            RuntimeError: If streaming fails
        """
        files = self.discover_files()

        if self.validate_data:
            self.validate_files()

        chunk_size = chunk_size or self.chunk_size
        logger.info(
            f"Starting tick stream: {len(files)} files, chunk_size={chunk_size}"
        )

        total_chunks = 0
        total_records = 0

        try:
            for file_info in files:
                logger.debug(f"Processing file: {file_info.path.name}")

                try:
                    # Stream chunks from file
                    for chunk in self.data_loader.stream_file(
                        file_info.path,
                        columns=columns,
                        chunk_size=chunk_size,
                    ):
                        if chunk.empty:
                            continue

                        # Apply time filtering if needed
                        if self.start_date or self.end_date:
                            chunk = self._filter_chunk_by_time(chunk)
                            if chunk.empty:
                                continue

                        # Ensure chronological ordering within chunk
                        if "timestamp" in chunk.columns:
                            chunk = chunk.sort_values("timestamp").reset_index(
                                drop=True
                            )

                        total_chunks += 1
                        total_records += len(chunk)

                        logger.debug(
                            f"Yielding chunk {total_chunks}: {len(chunk)} records"
                        )
                        yield chunk

                except Exception as e:
                    logger.error(f"Failed to process file {file_info.path}: {e}")
                    if "corrupted" in str(e).lower() or "invalid" in str(e).lower():
                        continue  # Skip corrupted files
                    raise

        except Exception as e:
            raise RuntimeError(f"Tick streaming failed: {e}") from e

        logger.info(
            f"Stream completed: {total_chunks} chunks, {total_records} total records"
        )

    def get_date_range(self) -> tuple[datetime, datetime]:
        """Get the actual date range of discovered files.

        Returns:
            Tuple of (earliest_date, latest_date)
        """
        files = self.discover_files()
        dates = [f.date for f in files]
        return min(dates), max(dates)

    def get_available_contracts(self) -> list[str]:
        """Get list of available contract months.

        Returns:
            Sorted list of contract month strings
        """
        return self.file_discovery.get_contract_months()

    def get_stats(self) -> dict[str, Any]:
        """Get statistics about the data stream.

        Returns:
            Dictionary with stream statistics
        """
        try:
            files = self.discover_files()
            file_stats = self.file_discovery.get_file_stats()

            date_range = self.get_date_range()

            return {
                "total_files": len(files),
                "date_range": date_range,
                "total_size_gb": file_stats.get("total_size_gb", 0),
                "available_contracts": self.get_available_contracts(),
                "filter_contracts": self.contracts,
                "filter_date_range": (self.start_date, self.end_date),
                "chunk_size": self.chunk_size,
                "memory_limit_mb": self.memory_limit_mb,
            }
        except Exception as e:
            logger.error(f"Failed to get stream stats: {e}")
            return {"error": str(e)}

    def _filter_chunk_by_time(self, chunk: pd.DataFrame) -> pd.DataFrame:
        """Apply time filtering to a data chunk."""
        if "timestamp" not in chunk.columns:
            return chunk

        mask = pd.Series([True] * len(chunk))

        if self.start_date:
            start_ns = int(self.start_date.timestamp() * 1e9)
            mask &= chunk["timestamp"] >= start_ns

        if self.end_date:
            end_ns = int(self.end_date.timestamp() * 1e9)
            mask &= chunk["timestamp"] <= end_ns

        return chunk[mask].reset_index(drop=True)


class DataPipelineError(Exception):
    """Base exception for data pipeline errors."""


class DataValidationError(DataPipelineError):
    """Exception raised when data validation fails."""


class DataDiscoveryError(DataPipelineError):
    """Exception raised when file discovery fails."""


class DataStreamingError(DataPipelineError):
    """Exception raised during data streaming."""
