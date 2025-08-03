"""Data validation module for MNQ tick data integrity."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow.parquet as pq


@dataclass
class ValidationResult:
    """Result of data validation checks."""

    file_path: Path
    is_valid: bool
    errors: list[str]
    warnings: list[str]
    stats: dict[str, Any]
    validation_time: datetime


class DataValidator:
    """Validates MNQ tick data files for integrity and consistency."""

    # Expected schema columns
    REQUIRED_COLUMNS = {
        "level", "mdt", "timestamp", "price", "volume"
    }

    LEVEL2_COLUMNS = {
        "operation", "depth", "market_maker"
    }

    # Valid MDT values
    VALID_MDT_VALUES = {
        0,  # Ask
        1,  # Bid
        2,  # Last
        3,  # DailyHigh
        4,  # DailyLow
        5,  # DailyVolume
        6,  # LastClose
        7,  # Opening
        8,  # OpenInterest
        9,  # Settlement
    }

    # Valid operation values for Level 2
    VALID_OPERATIONS = {0, 1, 2}  # Add, Update, Remove

    def __init__(self) -> None:
        """Initialize the data validator."""
        self.validation_cache: dict[Path, ValidationResult] = {}

    def validate_file(
        self,
        file_path: Path,
        check_data_integrity: bool = True,
        check_timestamps: bool = True,
        check_prices: bool = True,
        cache_results: bool = True,
    ) -> ValidationResult:
        """
        Validate a single Parquet file.
        
        Args:
            file_path: Path to the Parquet file
            check_data_integrity: Whether to check data integrity
            check_timestamps: Whether to validate timestamps
            check_prices: Whether to validate price data
            cache_results: Whether to cache validation results
            
        Returns:
            ValidationResult with validation details
        """
        # Check cache first
        if cache_results and file_path in self.validation_cache:
            return self.validation_cache[file_path]

        errors = []
        warnings = []
        stats = {}

        try:
            # Read file metadata
            parquet_file = pq.ParquetFile(file_path)
            metadata = parquet_file.metadata

            # Basic file checks
            stats["num_rows"] = metadata.num_rows
            stats["num_columns"] = len(parquet_file.schema)
            stats["file_size_mb"] = file_path.stat().st_size / (1024 * 1024)

            # Read data for detailed validation
            df = pd.read_parquet(file_path)

            # Schema validation
            schema_errors = self._validate_schema(df)
            errors.extend(schema_errors)

            if not schema_errors and check_data_integrity:
                # Data integrity checks
                integrity_errors, integrity_warnings = self._validate_data_integrity(df)
                errors.extend(integrity_errors)
                warnings.extend(integrity_warnings)

            if not schema_errors and check_timestamps:
                # Timestamp validation
                ts_errors, ts_stats = self._validate_timestamps(df)
                errors.extend(ts_errors)
                stats.update(ts_stats)

            if not schema_errors and check_prices:
                # Price validation
                price_errors, price_stats = self._validate_prices(df)
                errors.extend(price_errors)
                stats.update(price_stats)

            # Collect general statistics
            stats["unique_levels"] = df["level"].nunique() if "level" in df.columns else 0
            stats["unique_mdts"] = df["mdt"].nunique() if "mdt" in df.columns else 0

        except Exception as e:
            errors.append(f"Failed to read file: {e!s}")

        result = ValidationResult(
            file_path=file_path,
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            stats=stats,
            validation_time=datetime.now(),
        )

        if cache_results:
            self.validation_cache[file_path] = result

        return result

    def _validate_schema(self, df: pd.DataFrame) -> list[str]:
        """Validate dataframe schema."""
        errors = []

        # Check required columns
        missing_columns = self.REQUIRED_COLUMNS - set(df.columns)
        if missing_columns:
            errors.append(f"Missing required columns: {missing_columns}")

        # Check Level 2 specific columns if applicable
        if "level" in df.columns and any(df["level"] == "2"):
            missing_level2 = self.LEVEL2_COLUMNS - set(df.columns)
            if missing_level2:
                errors.append(f"Missing Level 2 columns: {missing_level2}")

        # Check data types
        if "timestamp" in df.columns and not pd.api.types.is_integer_dtype(df["timestamp"]):
            errors.append("Timestamp column must be integer type (nanoseconds)")

        if "price" in df.columns and not pd.api.types.is_numeric_dtype(df["price"]):
            errors.append("Price column must be numeric type")

        if "volume" in df.columns and not pd.api.types.is_integer_dtype(df["volume"]):
            errors.append("Volume column must be integer type")

        return errors

    def _validate_data_integrity(
        self, df: pd.DataFrame
    ) -> tuple[list[str], list[str]]:
        """Validate data integrity and consistency."""
        errors = []
        warnings = []

        # Check for null values
        null_counts = df.isnull().sum()
        critical_nulls = null_counts[null_counts > 0]
        if not critical_nulls.empty:
            for col, count in critical_nulls.items():
                if col in self.REQUIRED_COLUMNS:
                    errors.append(f"Found {count} null values in required column '{col}'")
                else:
                    warnings.append(f"Found {count} null values in column '{col}'")

        # Validate MDT values
        if "mdt" in df.columns:
            invalid_mdt = ~df["mdt"].isin(self.VALID_MDT_VALUES)
            if invalid_mdt.any():
                invalid_count = invalid_mdt.sum()
                unique_invalid = df.loc[invalid_mdt, "mdt"].unique()
                errors.append(
                    f"Found {invalid_count} rows with invalid MDT values: {unique_invalid}"
                )

        # Validate Level 2 operations (exclude NaN values)
        if "operation" in df.columns:
            non_null_ops = df["operation"].dropna()
            if not non_null_ops.empty:
                invalid_ops = ~non_null_ops.isin(self.VALID_OPERATIONS)
                if invalid_ops.any():
                    invalid_count = invalid_ops.sum()
                    unique_invalid = non_null_ops[invalid_ops].unique()
                    errors.append(
                        f"Found {invalid_count} rows with invalid operations: {unique_invalid}"
                    )

        # Check volume values
        if "volume" in df.columns:
            negative_volumes = df["volume"] < 0
            if negative_volumes.any():
                count = negative_volumes.sum()
                errors.append(f"Found {count} rows with negative volume")

        return errors, warnings

    def _validate_timestamps(self, df: pd.DataFrame) -> tuple[list[str], dict[str, Any]]:
        """Validate timestamp data."""
        errors: list[str] = []
        stats: dict[str, Any] = {}

        if "timestamp" not in df.columns:
            return errors, stats

        # Convert timestamps to datetime for analysis
        try:
            df["datetime"] = pd.to_datetime(df["timestamp"], unit="ns")
        except Exception as e:
            errors.append(f"Failed to convert timestamps: {e!s}")
            return errors, stats

        # Check timestamp range
        min_ts = df["datetime"].min()
        max_ts = df["datetime"].max()
        stats["timestamp_range"] = (min_ts, max_ts)

        # Check for timestamps in the future
        now = pd.Timestamp.now()
        future_timestamps = df["datetime"] > now
        if future_timestamps.any():
            count = future_timestamps.sum()
            errors.append(f"Found {count} timestamps in the future")

        # Check for very old timestamps (before 2019)
        cutoff_date = pd.Timestamp("2019-01-01")
        old_timestamps = df["datetime"] < cutoff_date
        if old_timestamps.any():
            count = old_timestamps.sum()
            errors.append(f"Found {count} timestamps before 2019")

        # Check timestamp ordering
        if not df["timestamp"].is_monotonic_increasing:
            # Count out-of-order timestamps
            diffs = df["timestamp"].diff()
            out_of_order = (diffs < 0).sum()
            errors.append(f"Timestamps are not monotonically increasing ({out_of_order} reversals)")

        # Calculate timestamp statistics
        if len(df) > 1:
            time_diffs = df["timestamp"].diff().dropna()
            stats["avg_time_diff_ns"] = time_diffs.mean()
            stats["max_time_gap_ns"] = time_diffs.max()
            stats["min_time_gap_ns"] = time_diffs[time_diffs > 0].min() if (time_diffs > 0).any() else 0

        return errors, stats

    def _validate_prices(self, df: pd.DataFrame) -> tuple[list[str], dict[str, Any]]:
        """Validate price data."""
        errors: list[str] = []
        stats: dict[str, Any] = {}

        if "price" not in df.columns:
            return errors, stats

        # Check for negative prices
        negative_prices = df["price"] < 0
        if negative_prices.any():
            count = negative_prices.sum()
            errors.append(f"Found {count} rows with negative prices")

        # Check for zero prices (might be valid for some MDT types)
        zero_prices = df["price"] == 0
        if zero_prices.any():
            # Only warn for bid/ask/last prices
            if "mdt" in df.columns:
                critical_zero = zero_prices & df["mdt"].isin([0, 1, 2])
                if critical_zero.any():
                    count = critical_zero.sum()
                    errors.append(f"Found {count} bid/ask/last prices with zero value")

        # Calculate price statistics
        price_data = df["price"][df["price"] > 0]  # Exclude zeros
        if not price_data.empty:
            stats["min_price"] = float(price_data.min())
            stats["max_price"] = float(price_data.max())
            stats["avg_price"] = float(price_data.mean())
            stats["price_std"] = float(price_data.std())

            # Check for extreme price outliers (more than 10 std devs)
            if stats["price_std"] > 0:
                z_scores = abs((price_data - stats["avg_price"]) / stats["price_std"])
                extreme_outliers = z_scores > 10
                if extreme_outliers.any():
                    count = extreme_outliers.sum()
                    errors.append(f"Found {count} extreme price outliers (>10 std devs)")

        return errors, stats

    def validate_batch(
        self,
        file_paths: list[Path],
        parallel: bool = True,
        **kwargs: Any
    ) -> dict[Path, ValidationResult]:
        """
        Validate multiple files.
        
        Args:
            file_paths: List of file paths to validate
            parallel: Whether to process files in parallel
            **kwargs: Additional arguments for validate_file
            
        Returns:
            Dictionary mapping file paths to validation results
        """
        results = {}

        if parallel:
            # TODO: Implement parallel processing with multiprocessing
            # For now, fall back to sequential
            pass

        # Sequential processing
        for file_path in file_paths:
            results[file_path] = self.validate_file(file_path, **kwargs)

        return results

    def generate_validation_report(
        self, results: dict[Path, ValidationResult]
    ) -> str:
        """
        Generate a summary report from validation results.
        
        Args:
            results: Dictionary of validation results
            
        Returns:
            Formatted report string
        """
        report = ["Data Validation Report", "=" * 50, ""]

        total_files = len(results)
        valid_files = sum(1 for r in results.values() if r.is_valid)
        invalid_files = total_files - valid_files

        report.append(f"Total files validated: {total_files}")
        report.append(f"Valid files: {valid_files}")
        report.append(f"Invalid files: {invalid_files}")
        report.append("")

        if invalid_files > 0:
            report.append("Invalid Files:")
            report.append("-" * 30)
            for path, result in results.items():
                if not result.is_valid:
                    report.append(f"\n{path.name}:")
                    for error in result.errors:
                        report.append(f"  ERROR: {error}")
                    for warning in result.warnings:
                        report.append(f"  WARNING: {warning}")

        # Summary statistics
        report.append("\nValidation Statistics:")
        report.append("-" * 30)

        total_rows = sum(r.stats.get("num_rows", 0) for r in results.values())
        total_size = sum(r.stats.get("file_size_mb", 0) for r in results.values())

        report.append(f"Total rows processed: {total_rows:,}")
        report.append(f"Total data size: {total_size:.2f} MB")

        return "\n".join(report)
