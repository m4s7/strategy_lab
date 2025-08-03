"""Tests for data ingestion module."""

from datetime import UTC, datetime
from unittest.mock import patch

import pandas as pd
import pytest

from strategy_lab.data.ingestion import (
    DataLoader,
    DataValidator,
    ParquetFileDiscovery,
    ParquetFileInfo,
    ValidationResult,
)


@pytest.fixture
def sample_tick_data():
    """Create sample tick data for testing."""
    return pd.DataFrame(
        {
            "level": ["1", "1", "2", "2", "1"],
            "mdt": [0, 1, 0, 1, 2],  # Ask, Bid, Ask (L2), Bid (L2), Last
            "timestamp": [
                1609459200000000000,  # 2021-01-01 00:00:00
                1609459200100000000,
                1609459200200000000,
                1609459200300000000,
                1609459200400000000,
            ],
            "price": [100.50, 100.25, 100.75, 100.00, 100.30],
            "volume": [10, 15, 20, 25, 5],
            "operation": [pd.NA, pd.NA, 0, 0, pd.NA],  # Add operations for L2 only
            "depth": [pd.NA, pd.NA, 1, 1, pd.NA],
            "market_maker": [None, None, "MM1", "MM2", None],
        }
    )


@pytest.fixture
def temp_parquet_file(tmp_path, sample_tick_data):
    """Create a temporary Parquet file."""
    file_path = tmp_path / "test_data.parquet"
    sample_tick_data.to_parquet(file_path)
    return file_path


class TestParquetFileDiscovery:
    """Test ParquetFileDiscovery class."""

    def test_initialization(self, tmp_path):
        """Test discovery initialization."""
        discovery = ParquetFileDiscovery(data_dir=tmp_path)
        assert discovery.data_dir == tmp_path
        assert discovery.cache_file == tmp_path.parent / "MNQ_parquet_files.json"

    def test_parse_filename(self):
        """Test filename parsing."""
        discovery = ParquetFileDiscovery()

        # Valid filename
        info = discovery._parse_filename("MNQ_03-20_2020-01-15.parquet")
        assert info is not None
        assert info["contract_month"] == "03-20"
        assert info["date"] == datetime(2020, 1, 15)

        # Invalid filename
        info = discovery._parse_filename("invalid_file.parquet")
        assert info is None

    def test_discover_files(self, tmp_path):
        """Test file discovery."""
        # Create test directory structure
        contract_dir = tmp_path / "03-20"
        contract_dir.mkdir(parents=True)

        # Create test files with simple date format
        test_file = contract_dir / "20200115.parquet"
        test_file.write_text("")

        discovery = ParquetFileDiscovery(data_dir=tmp_path)
        files = discovery.discover_files()

        assert len(files) == 1
        assert files[0].contract_month == "03-20"
        assert files[0].date == datetime(2020, 1, 15)

    def test_discover_files_with_filters(self, tmp_path):
        """Test file discovery with filters."""
        # Create multiple contract months
        for month in ["03-20", "06-20"]:
            contract_dir = tmp_path / month
            contract_dir.mkdir(parents=True)

            # Create files for different dates
            for day in [15, 16]:
                test_file = contract_dir / f"202001{day}.parquet"
                test_file.write_text("")

        discovery = ParquetFileDiscovery(data_dir=tmp_path)

        # Filter by contract month
        files = discovery.discover_files(contract_months=["03-20"])
        assert len(files) == 2
        assert all(f.contract_month == "03-20" for f in files)

        # Filter by date range
        start_date = datetime(2020, 1, 16)
        files = discovery.discover_files(start_date=start_date)
        assert len(files) == 2
        assert all(f.date >= start_date for f in files)

    @patch("json.dump")
    @patch("json.load")
    def test_cache_operations(self, mock_load, mock_dump, tmp_path):
        """Test cache save and load operations."""
        discovery = ParquetFileDiscovery(data_dir=tmp_path)

        # Test save cache
        files = [
            ParquetFileInfo(
                path=tmp_path / "test.parquet",
                contract_month="03-20",
                date=datetime(2020, 1, 15),
                size_bytes=11010048,  # ~10.5 MB
                file_name="test.parquet",
            )
        ]
        discovery.save_cache(files)
        assert mock_dump.called

        # Test load cache
        mock_load.return_value = [
            {
                "path": str(tmp_path / "test.parquet"),
                "contract_month": "03-20",
                "date": "2020-01-15T00:00:00",
                "size_mb": 10.5,
                "row_count": 1000000,
            }
        ]

        loaded_files = discovery.load_cache()
        assert len(loaded_files) == 1
        assert loaded_files[0].contract_month == "03-20"


class TestDataValidator:
    """Test DataValidator class."""

    def test_initialization(self):
        """Test validator initialization."""
        validator = DataValidator()
        assert isinstance(validator.validation_cache, dict)
        assert len(validator.validation_cache) == 0

    def test_validate_schema(self, sample_tick_data):
        """Test schema validation."""
        validator = DataValidator()

        # Valid schema
        errors = validator._validate_schema(sample_tick_data)
        assert len(errors) == 0

        # Missing required column
        df_missing = sample_tick_data.drop(columns=["timestamp"])
        errors = validator._validate_schema(df_missing)
        assert len(errors) == 1
        assert "timestamp" in errors[0]

    def test_validate_data_integrity(self, sample_tick_data):
        """Test data integrity validation."""
        validator = DataValidator()

        # Valid data
        errors, warnings = validator._validate_data_integrity(sample_tick_data)
        assert len(errors) == 0

        # Invalid MDT values
        df_invalid = sample_tick_data.copy()
        df_invalid.loc[0, "mdt"] = 99
        errors, warnings = validator._validate_data_integrity(df_invalid)
        assert len(errors) == 1
        assert "invalid MDT" in errors[0]

    def test_validate_timestamps(self, sample_tick_data):
        """Test timestamp validation."""
        validator = DataValidator()

        # Valid timestamps
        errors, stats = validator._validate_timestamps(sample_tick_data)
        assert len(errors) == 0
        assert "timestamp_range" in stats

        # Future timestamps
        df_future = sample_tick_data.copy()
        future_time = int(datetime(2030, 1, 1).timestamp() * 1e9)  # Year 2030
        df_future["timestamp"] = future_time
        errors, stats = validator._validate_timestamps(df_future)
        assert len(errors) > 0
        assert "future" in errors[0]

    def test_validate_prices(self, sample_tick_data):
        """Test price validation."""
        validator = DataValidator()

        # Valid prices
        errors, stats = validator._validate_prices(sample_tick_data)
        assert len(errors) == 0
        assert "avg_price" in stats

        # Negative prices
        df_negative = sample_tick_data.copy()
        df_negative.loc[0, "price"] = -100
        errors, stats = validator._validate_prices(df_negative)
        assert len(errors) == 1
        assert "negative" in errors[0]

    def test_validate_file(self, temp_parquet_file):
        """Test full file validation."""
        validator = DataValidator()

        result = validator.validate_file(temp_parquet_file)
        assert isinstance(result, ValidationResult)
        assert result.file_path == temp_parquet_file
        assert isinstance(result.is_valid, bool)
        assert isinstance(result.errors, list)
        assert isinstance(result.warnings, list)
        assert isinstance(result.stats, dict)

    def test_validation_caching(self, temp_parquet_file):
        """Test validation result caching."""
        validator = DataValidator()

        # First validation
        result1 = validator.validate_file(temp_parquet_file, cache_results=True)
        assert temp_parquet_file in validator.validation_cache

        # Second validation should use cache
        with patch.object(validator, "_validate_schema") as mock_validate:
            result2 = validator.validate_file(temp_parquet_file, cache_results=True)
            mock_validate.assert_not_called()

        assert result1.validation_time == result2.validation_time

    def test_generate_validation_report(self, temp_parquet_file):
        """Test validation report generation."""
        validator = DataValidator()

        # Create some validation results
        results = {
            temp_parquet_file: ValidationResult(
                file_path=temp_parquet_file,
                is_valid=True,
                errors=[],
                warnings=["Test warning"],
                stats={"num_rows": 1000, "file_size_mb": 10.5},
                validation_time=datetime.now(),
            )
        }

        report = validator.generate_validation_report(results)
        assert isinstance(report, str)
        assert "Total files validated: 1" in report
        assert "Valid files: 1" in report


class TestDataLoader:
    """Test DataLoader class."""

    def test_initialization(self):
        """Test loader initialization."""
        loader = DataLoader(cache_size_mb=500, chunk_size=50000)
        assert loader.cache_size_mb == 500
        assert loader.chunk_size == 50000
        assert loader._cache_usage_mb == 0

    def test_load_file(self, temp_parquet_file):
        """Test file loading."""
        loader = DataLoader()

        df = loader.load_file(temp_parquet_file)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 5
        assert all(col in df.columns for col in ["timestamp", "price", "volume"])

    def test_load_file_with_columns(self, temp_parquet_file):
        """Test loading specific columns."""
        loader = DataLoader()

        df = loader.load_file(temp_parquet_file, columns=["timestamp", "price"])
        assert list(df.columns) == ["timestamp", "price"]

    def test_load_file_caching(self, temp_parquet_file):
        """Test file caching."""
        loader = DataLoader()

        # First load
        df1 = loader.load_file(temp_parquet_file, use_cache=True)
        cache_key = (temp_parquet_file, None)
        assert cache_key in loader._cache

        # Second load should use cache
        with patch("pandas.read_parquet") as mock_read:
            df2 = loader.load_file(temp_parquet_file, use_cache=True)
            mock_read.assert_not_called()

        assert df1.equals(df2)

    def test_stream_file(self, temp_parquet_file):
        """Test file streaming."""
        loader = DataLoader(chunk_size=2)

        chunks = list(loader.stream_file(temp_parquet_file, chunk_size=2))
        assert len(chunks) == 3  # 5 rows with chunk size 2
        assert all(isinstance(chunk, pd.DataFrame) for chunk in chunks)

    def test_load_time_range(self, tmp_path, sample_tick_data):
        """Test loading data within time range."""
        # Create multiple files with different timestamps
        file1 = tmp_path / "file1.parquet"
        file2 = tmp_path / "file2.parquet"

        df1 = sample_tick_data.copy()
        df2 = sample_tick_data.copy()
        df2["timestamp"] = df2["timestamp"] + 1000000000  # Add 1 second

        df1.to_parquet(file1)
        df2.to_parquet(file2)

        loader = DataLoader()

        # Load time range
        start_time = datetime(2021, 1, 1, 0, 0, 0, tzinfo=UTC)
        end_time = datetime(2021, 1, 1, 0, 0, 0, 500000, tzinfo=UTC)

        result = loader.load_time_range([file1, file2], start_time, end_time)
        assert len(result) > 0
        assert all(result["timestamp"] <= int(end_time.timestamp() * 1e9))

    def test_load_by_mdt(self, tmp_path, sample_tick_data):
        """Test loading data grouped by MDT."""
        file_path = tmp_path / "test.parquet"
        sample_tick_data.to_parquet(file_path)

        loader = DataLoader()

        result = loader.load_by_mdt([file_path], mdt_types=[0, 1, 2])
        assert len(result) == 3
        assert len(result[0]) == 2  # 2 asks
        assert len(result[1]) == 2  # 2 bids
        assert len(result[2]) == 1  # 1 last

    def test_aggregate_bars(self, tmp_path):
        """Test bar aggregation."""
        # Create trade data
        trades = pd.DataFrame(
            {
                "timestamp": [
                    1609459200000000000 + i * 1000000000  # 1 second intervals
                    for i in range(10)
                ],
                "price": [100 + i * 0.1 for i in range(10)],
                "volume": [10] * 10,
                "mdt": [2] * 10,  # All trades
                "level": ["1"] * 10,
            }
        )

        file_path = tmp_path / "trades.parquet"
        trades.to_parquet(file_path)

        loader = DataLoader()

        # Test time bars
        bars = loader.aggregate_bars(
            [file_path],
            bar_type="time",
            bar_size=pd.Timedelta(seconds=5),
        )
        assert len(bars) == 2  # 10 seconds / 5 second bars
        assert all(
            col in bars.columns for col in ["open", "high", "low", "close", "volume"]
        )

    def test_clear_cache(self):
        """Test cache clearing."""
        loader = DataLoader()
        loader._cache = {"test": pd.DataFrame()}
        loader._cache_usage_mb = 100

        loader.clear_cache()
        assert len(loader._cache) == 0
        assert loader._cache_usage_mb == 0
