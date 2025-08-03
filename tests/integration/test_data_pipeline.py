"""Integration tests for data pipeline and hftbacktest adapter."""

import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from strategy_lab.data.adapters.hftbacktest import (
    DataPipeline,
    HftBacktestAdapter,
    HftBacktestDataFormatter,
    MemoryMonitor,
    PipelineConfig,
    ProcessingStats,
)


class TestHftBacktestDataFormatter:
    """Test data formatting for hftbacktest."""

    def test_format_l1_data_empty(self):
        """Test formatting empty L1 data."""
        empty_df = pd.DataFrame()
        result = HftBacktestDataFormatter.format_l1_data(empty_df)

        assert result.empty
        assert list(result.columns) == ["timestamp", "price", "qty", "side"]

    def test_format_l1_data_valid(self):
        """Test formatting valid L1 data."""
        # Create sample L1 data
        l1_data = pd.DataFrame(
            {
                "level": ["1", "1", "1"],
                "timestamp": [
                    1609459200000000000,
                    1609459200000000001,
                    1609459200000000002,
                ],
                "mdt": [0, 1, 2],  # Ask, Bid, Trade
                "price": [100.25, 100.0, 100.125],
                "volume": [1000, 1500, 500],
                "operation": [0, 0, 0],
            }
        )

        result = HftBacktestDataFormatter.format_l1_data(l1_data)

        assert len(result) == 3
        assert list(result.columns) == ["timestamp", "price", "qty", "side"]
        assert result["side"].tolist() == [-1, 1, 0]  # Ask=Sell, Bid=Buy, Trade=Unknown
        assert result["price"].tolist() == [100.25, 100.0, 100.125]
        assert result["qty"].tolist() == [1000.0, 1500.0, 500.0]

    def test_format_l2_data_empty(self):
        """Test formatting empty L2 data."""
        empty_df = pd.DataFrame()
        result = HftBacktestDataFormatter.format_l2_data(empty_df)

        assert result.empty
        assert list(result.columns) == ["timestamp", "price", "qty", "side", "op"]

    def test_format_l2_data_valid(self):
        """Test formatting valid L2 data."""
        # Create sample L2 data
        l2_data = pd.DataFrame(
            {
                "level": ["2", "2", "2"],
                "timestamp": [
                    1609459200000000000,
                    1609459200000000001,
                    1609459200000000002,
                ],
                "mdt": [0, 1, 0],  # Ask, Bid, Ask
                "price": [100.25, 100.0, 100.5],
                "volume": [1000, 1500, 0],
                "operation": [0, 0, 2],  # Add, Add, Remove
            }
        )

        result = HftBacktestDataFormatter.format_l2_data(l2_data)

        assert len(result) == 3
        assert list(result.columns) == ["timestamp", "price", "qty", "side", "op"]
        assert result["side"].tolist() == [-1, 1, -1]  # Ask=Sell, Bid=Buy
        assert result["op"].tolist() == [0, 0, 2]  # Operations preserved

    def test_mixed_level_data_filtering(self):
        """Test that formatter correctly filters L1/L2 data."""
        mixed_data = pd.DataFrame(
            {
                "level": ["1", "2", "1", "2"],
                "timestamp": [
                    1609459200000000000,
                    1609459200000000001,
                    1609459200000000002,
                    1609459200000000003,
                ],
                "mdt": [0, 1, 2, 0],
                "price": [100.25, 100.0, 100.125, 100.5],
                "volume": [1000, 1500, 500, 800],
                "operation": [0, 0, 0, 1],
            }
        )

        l1_result = HftBacktestDataFormatter.format_l1_data(mixed_data)
        l2_result = HftBacktestDataFormatter.format_l2_data(mixed_data)

        assert len(l1_result) == 2  # Only L1 records
        assert len(l2_result) == 2  # Only L2 records


class TestHftBacktestAdapter:
    """Test hftbacktest adapter functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = PipelineConfig(chunk_size=1000, enable_l2_processing=True)
        self.adapter = HftBacktestAdapter(self.config)

        # Create sample data
        self.sample_data = pd.DataFrame(
            {
                "level": ["1", "1", "2", "2"],
                "timestamp": [
                    1609459200000000000,
                    1609459200000000001,
                    1609459200000000002,
                    1609459200000000003,
                ],
                "mdt": [0, 1, 0, 1],
                "price": [100.25, 100.0, 100.5, 99.75],
                "volume": [1000, 1500, 800, 1200],
                "operation": [0, 0, 0, 0],
            }
        )

    @patch("strategy_lab.data.adapters.hftbacktest.DataLoader")
    def test_prepare_data_success(self, mock_loader_class):
        """Test successful data preparation."""
        mock_loader = MagicMock()
        mock_loader.load_file.return_value = self.sample_data
        mock_loader_class.return_value = mock_loader

        adapter = HftBacktestAdapter(self.config)
        adapter.data_loader = mock_loader

        result = adapter.prepare_data(Path("test.parquet"))

        assert "l1" in result
        assert "l2" in result
        assert len(result["l1"]) == 2  # Two L1 records
        assert len(result["l2"]) == 2  # Two L2 records

        mock_loader.load_file.assert_called_once()

    @patch("strategy_lab.data.adapters.hftbacktest.DataLoader")
    def test_prepare_data_with_time_filter(self, mock_loader_class):
        """Test data preparation with time filtering."""
        mock_loader = MagicMock()
        mock_loader.load_file.return_value = self.sample_data
        mock_loader_class.return_value = mock_loader

        adapter = HftBacktestAdapter(self.config)
        adapter.data_loader = mock_loader

        # Filter to include only first two records
        start_time = 1609459200000000000
        end_time = 1609459200000000001

        result = adapter.prepare_data(Path("test.parquet"), start_time, end_time)

        # Should only get L1 data (first two records are L1)
        assert len(result["l1"]) == 2
        assert len(result["l2"]) == 0  # No L2 in time range

    def test_get_contract_specs(self):
        """Test contract specifications retrieval."""
        specs = self.adapter.get_contract_specs()

        assert specs["tick_size"] == 0.25
        assert specs["lot_size"] == 20
        assert specs["contract"] == "MNQ"
        assert specs["currency"] == "USD"
        assert specs["exchange"] == "CME"
        assert specs["asset_type"] == "future"


class TestMemoryMonitor:
    """Test memory monitoring functionality."""

    def test_memory_monitor_initialization(self):
        """Test memory monitor initialization."""
        config = PipelineConfig(memory_limit_mb=1000, gc_threshold=0.8)
        monitor = MemoryMonitor(config)

        assert monitor.config == config
        assert monitor.peak_memory == 0.0
        assert monitor.process is not None

    def test_memory_usage_tracking(self):
        """Test memory usage tracking."""
        config = PipelineConfig()
        monitor = MemoryMonitor(config)

        # Get memory usage (should be > 0)
        memory_mb = monitor.get_memory_usage_mb()
        assert memory_mb > 0
        assert monitor.peak_memory >= memory_mb

    def test_gc_threshold_check(self):
        """Test garbage collection threshold check."""
        config = PipelineConfig(memory_limit_mb=100, gc_threshold=0.8)  # Very low limit
        monitor = MemoryMonitor(config)

        # With such a low limit, should trigger GC
        should_gc = monitor.should_trigger_gc()
        # This may or may not trigger depending on actual memory usage
        assert isinstance(should_gc, bool)

    def test_trigger_gc(self):
        """Test garbage collection triggering."""
        config = PipelineConfig()
        monitor = MemoryMonitor(config)

        # Trigger GC and get freed memory
        freed = monitor.trigger_gc()
        assert isinstance(freed, float)
        # Freed memory could be negative if memory increased during GC


class TestProcessingStats:
    """Test processing statistics tracking."""

    def test_stats_initialization(self):
        """Test stats initialization."""
        stats = ProcessingStats()

        assert stats.files_processed == 0
        assert stats.records_processed == 0
        assert stats.errors_encountered == 0
        assert stats.start_time > 0
        assert stats.end_time is None

    def test_duration_calculation(self):
        """Test duration calculation."""
        stats = ProcessingStats()
        stats.start_time = 1000.0

        # Without end time, should use current time
        duration = stats.duration
        assert duration > 0

        # With end time
        stats.end_time = 1010.0
        assert stats.duration == 10.0

    def test_records_per_second(self):
        """Test records per second calculation."""
        stats = ProcessingStats()
        stats.start_time = 1000.0
        stats.end_time = 1010.0  # 10 second duration
        stats.records_processed = 1000

        assert stats.records_per_second == 100.0

        # Test zero duration
        stats.start_time = stats.end_time
        assert stats.records_per_second == 0.0


class TestDataPipeline:
    """Test complete data pipeline functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = PipelineConfig(
            chunk_size=100, memory_limit_mb=1000, enable_l2_processing=True
        )
        self.pipeline = DataPipeline(self.config)

    def create_test_data_file(self, tmp_dir: Path, data: pd.DataFrame) -> Path:
        """Create a temporary test data file."""
        file_path = tmp_dir / "test_data.parquet"
        data.to_parquet(file_path)
        return file_path

    @patch("strategy_lab.data.adapters.hftbacktest.ParquetFileDiscovery")
    def test_process_date_range_no_files(self, mock_discovery_class):
        """Test processing when no files are found."""
        mock_discovery = MagicMock()
        mock_discovery.discover_files.return_value = []
        mock_discovery_class.return_value = mock_discovery

        pipeline = DataPipeline(self.config)
        pipeline.file_discovery = mock_discovery

        start_date = datetime(2020, 1, 1)
        end_date = datetime(2020, 1, 2)

        results = list(pipeline.process_date_range(start_date, end_date))
        assert len(results) == 0

    def test_create_data_chunk_empty(self):
        """Test creating data chunk with empty data."""
        empty_l1 = pd.DataFrame()
        empty_l2 = pd.DataFrame()

        result = self.pipeline._create_data_chunk(empty_l1, empty_l2)
        assert result is None

    def test_create_data_chunk_valid(self):
        """Test creating data chunk with valid data."""
        l1_data = pd.DataFrame(
            {
                "timestamp": [1609459200000000000, 1609459200000000001],
                "price": [100.0, 100.25],
                "qty": [1000, 500],
                "side": [1, -1],
            }
        )

        l2_data = pd.DataFrame(
            {
                "timestamp": [1609459200000000002],
                "price": [100.5],
                "qty": [800],
                "side": [-1],
                "op": [0],
            }
        )

        result = self.pipeline._create_data_chunk(l1_data, l2_data)

        assert result is not None
        assert "l1_data" in result
        assert "l2_data" in result
        assert "contract_specs" in result
        assert "timestamp_range" in result

        assert len(result["l1_data"]) == 2
        assert len(result["l2_data"]) == 1
        assert result["timestamp_range"]["start"] == 1609459200000000000
        assert result["timestamp_range"]["end"] == 1609459200000000001

    def test_convert_l2_to_original_format(self):
        """Test conversion from hftbacktest L2 format to original format."""
        hft_l2_data = pd.DataFrame(
            {
                "timestamp": [1609459200000000000, 1609459200000000001],
                "price": [100.0, 100.25],
                "qty": [1000, 500],
                "side": [1, -1],  # Buy, Sell
                "op": [0, 1],  # Add, Update
            }
        )

        original = self.pipeline._convert_l2_to_original_format(hft_l2_data)

        assert len(original) == 2
        assert list(original.columns) == [
            "level",
            "timestamp",
            "mdt",
            "price",
            "volume",
            "operation",
        ]
        assert (original["level"] == "2").all()
        assert original["mdt"].tolist() == [1, 0]  # Buy->Bid, Sell->Ask
        assert original["operation"].tolist() == [0, 1]

    def test_get_stats(self):
        """Test statistics retrieval."""
        stats = self.pipeline.get_stats()
        assert isinstance(stats, ProcessingStats)
        assert stats.files_processed == 0
        assert stats.records_processed == 0

    def test_cleanup(self):
        """Test pipeline cleanup."""
        # Should not raise any exceptions
        self.pipeline.cleanup()


class TestIntegrationScenarios:
    """Integration test scenarios."""

    def test_end_to_end_small_dataset(self):
        """Test end-to-end processing with small dataset."""
        # Create test data
        test_data = pd.DataFrame(
            {
                "level": ["1", "1", "2", "2", "1"],
                "timestamp": [
                    1609459200000000000,
                    1609459200000000001,
                    1609459200000000002,
                    1609459200000000003,
                    1609459200000000004,
                ],
                "mdt": [0, 1, 0, 1, 2],  # Ask, Bid, Ask, Bid, Trade
                "price": [100.25, 100.0, 100.5, 99.75, 100.125],
                "volume": [1000, 1500, 800, 1200, 500],
                "operation": [0, 0, 0, 0, 0],
            }
        )

        config = PipelineConfig(chunk_size=2, enable_l2_processing=False)
        adapter = HftBacktestAdapter(config)

        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create test file
            test_file = Path(tmp_dir) / "test.parquet"
            test_data.to_parquet(test_file)

            # Process data
            result = adapter.prepare_data(test_file)

            # Verify results
            assert "l1" in result
            assert "l2" in result
            assert len(result["l1"]) == 3  # Three L1 records
            assert len(result["l2"]) == 0  # L2 processing disabled

            # Verify data format
            l1_data = result["l1"]
            assert list(l1_data.columns) == ["timestamp", "price", "qty", "side"]
            assert l1_data["side"].tolist() == [-1, 1, 0]  # Ask, Bid, Trade

    def test_memory_management_simulation(self):
        """Test memory management with simulated large dataset."""
        config = PipelineConfig(
            chunk_size=10,
            memory_limit_mb=50,  # Very low limit for testing
            gc_threshold=0.1,  # Trigger GC early
        )

        pipeline = DataPipeline(config)

        # Create larger dataset
        large_data = pd.DataFrame(
            {
                "timestamp": range(1609459200000000000, 1609459200000000000 + 100),
                "price": [100.0 + (i % 10) * 0.25 for i in range(100)],
                "qty": [1000] * 100,
                "side": [1 if i % 2 == 0 else -1 for i in range(100)],
            }
        )

        # Test chunk processing
        chunks = list(pipeline._process_chunks(large_data, pd.DataFrame()))

        # Should create multiple chunks
        assert len(chunks) > 1

        # Verify total records processed
        total_records = sum(len(chunk["l1_data"]) for chunk in chunks if chunk)
        assert total_records == 100

    def test_error_recovery_simulation(self):
        """Test error recovery mechanisms."""
        config = PipelineConfig(max_retries=2, retry_delay=0.1)

        # Mock file discovery to return a non-existent file
        with patch(
            "strategy_lab.data.adapters.hftbacktest.ParquetFileDiscovery"
        ) as mock_discovery_class:
            mock_discovery = MagicMock()
            mock_file_info = MagicMock()
            mock_file_info.file_path = Path("nonexistent.parquet")
            mock_discovery.discover_files.return_value = [mock_file_info]
            mock_discovery_class.return_value = mock_discovery

            pipeline = DataPipeline(config)
            pipeline.file_discovery = mock_discovery

            start_date = datetime(2020, 1, 1)
            end_date = datetime(2020, 1, 2)

            # Should handle errors gracefully
            results = list(pipeline.process_date_range(start_date, end_date))
            assert len(results) == 0

            # Should have recorded errors
            stats = pipeline.get_stats()
            assert stats.errors_encountered > 0

    def test_mixed_l1_l2_synchronization(self):
        """Test L1/L2 data synchronization."""
        # Create mixed data with overlapping timestamps
        mixed_data = pd.DataFrame(
            {
                "level": ["1", "2", "1", "2", "1", "2"],
                "timestamp": [
                    1609459200000000000,  # L1
                    1609459200000000000,  # L2 - same timestamp
                    1609459200000000001,  # L1
                    1609459200000000001,  # L2 - same timestamp
                    1609459200000000002,  # L1
                    1609459200000000003,  # L2
                ],
                "mdt": [2, 0, 2, 1, 2, 0],  # Trade, Ask, Trade, Bid, Trade, Ask
                "price": [100.0, 100.25, 100.125, 99.75, 100.25, 100.5],
                "volume": [1000, 500, 800, 1200, 600, 400],
                "operation": [0, 0, 0, 0, 0, 1],
            }
        )

        formatter = HftBacktestDataFormatter()

        l1_result = formatter.format_l1_data(mixed_data)
        l2_result = formatter.format_l2_data(mixed_data)

        # Verify separation
        assert len(l1_result) == 3  # Three L1 records
        assert len(l2_result) == 3  # Three L2 records

        # Verify timestamp ordering is maintained
        assert l1_result["timestamp"].is_monotonic_increasing
        assert l2_result["timestamp"].is_monotonic_increasing

        # Verify overlapping timestamps are handled
        l1_timestamps = set(l1_result["timestamp"])
        l2_timestamps = set(l2_result["timestamp"])
        overlap = l1_timestamps.intersection(l2_timestamps)
        assert len(overlap) >= 1  # Should have at least one overlapping timestamp


class TestPerformance:
    """Performance and benchmarking tests."""

    @pytest.mark.slow
    def test_large_dataset_processing(self):
        """Test processing of large dataset (marked as slow test)."""
        # Create a larger test dataset
        n_records = 10000
        large_data = pd.DataFrame(
            {
                "level": ["1" if i % 3 != 2 else "2" for i in range(n_records)],
                "timestamp": range(
                    1609459200000000000, 1609459200000000000 + n_records
                ),
                "mdt": [i % 3 for i in range(n_records)],
                "price": [100.0 + (i % 100) * 0.25 for i in range(n_records)],
                "volume": [1000 + (i % 500) for i in range(n_records)],
                "operation": [0] * n_records,
            }
        )

        config = PipelineConfig(chunk_size=1000)
        adapter = HftBacktestAdapter(config)

        import time

        start_time = time.time()

        with tempfile.TemporaryDirectory() as tmp_dir:
            test_file = Path(tmp_dir) / "large_test.parquet"
            large_data.to_parquet(test_file)

            result = adapter.prepare_data(test_file)

            processing_time = time.time() - start_time

            # Verify results
            assert len(result["l1"]) > 0
            assert len(result["l2"]) > 0

            # Performance assertion (should process 10k records in reasonable time)
            records_per_second = n_records / processing_time
            assert (
                records_per_second > 1000
            )  # Should process at least 1k records/second

            print(
                f"Processed {n_records} records in {processing_time:.2f}s "
                f"({records_per_second:.0f} records/second)"
            )


# Fixtures for integration tests
@pytest.fixture
def sample_mnq_data():
    """Fixture providing sample MNQ data for testing."""
    return pd.DataFrame(
        {
            "level": ["1", "1", "2", "2", "1", "2"],
            "timestamp": [
                1609459200000000000,
                1609459200000000001,
                1609459200000000002,
                1609459200000000003,
                1609459200000000004,
                1609459200000000005,
            ],
            "mdt": [0, 1, 0, 1, 2, 0],  # Ask, Bid, Ask, Bid, Trade, Ask
            "price": [100.25, 100.0, 100.5, 99.75, 100.125, 100.75],
            "volume": [1000, 1500, 800, 1200, 500, 600],
            "operation": [0, 0, 0, 0, 0, 1],
        }
    )


@pytest.fixture
def pipeline_config():
    """Fixture providing pipeline configuration for testing."""
    return PipelineConfig(
        chunk_size=100,
        memory_limit_mb=1000,
        gc_threshold=0.8,
        max_retries=2,
        retry_delay=0.1,
        enable_l2_processing=True,
        order_book_depth=5,
    )
