"""HftBacktest adapter and unified data pipeline for MNQ futures data."""

import gc
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

import pandas as pd
import psutil
from decimal import Decimal

from ..ingestion.data_loader import DataLoader
from ..ingestion.file_discovery import ParquetFileDiscovery
from ..processing.order_book import OrderBook, OrderBookReconstructor

logger = logging.getLogger(__name__)


@dataclass
class PipelineConfig:
    """Configuration for data pipeline processing."""
    
    chunk_size: int = 100_000  # Records per chunk
    memory_limit_mb: int = 4_000  # Memory limit in MB
    gc_threshold: float = 0.8  # Trigger GC at 80% memory
    max_retries: int = 3  # Max retry attempts
    retry_delay: float = 1.0  # Delay between retries
    progress_interval: int = 50_000  # Progress report interval
    enable_l2_processing: bool = True  # Process Level 2 data
    order_book_depth: int = 10  # Order book depth levels


@dataclass
class ProcessingStats:
    """Statistics for pipeline processing."""
    
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    files_processed: int = 0
    records_processed: int = 0
    errors_encountered: int = 0
    memory_peak_mb: float = 0.0
    l1_records: int = 0
    l2_records: int = 0
    
    @property
    def duration(self) -> float:
        """Get processing duration in seconds."""
        end = self.end_time or time.time()
        return end - self.start_time
    
    @property
    def records_per_second(self) -> float:
        """Get processing rate in records per second."""
        duration = self.duration
        return self.records_processed / duration if duration > 0 else 0.0


class MemoryMonitor:
    """Monitor and manage memory usage during pipeline execution."""
    
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.process = psutil.Process()
        self.peak_memory = 0.0
    
    def get_memory_usage_mb(self) -> float:
        """Get current memory usage in MB."""
        memory_info = self.process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024
        self.peak_memory = max(self.peak_memory, memory_mb)
        return memory_mb
    
    def should_trigger_gc(self) -> bool:
        """Check if garbage collection should be triggered."""
        current_memory = self.get_memory_usage_mb()
        return current_memory > (self.config.memory_limit_mb * self.config.gc_threshold)
    
    def trigger_gc(self) -> float:
        """Trigger garbage collection and return memory freed."""
        memory_before = self.get_memory_usage_mb()
        gc.collect()
        memory_after = self.get_memory_usage_mb()
        freed = memory_before - memory_after
        
        if freed > 100:  # Only log if significant memory freed
            logger.info(f"GC freed {freed:.1f} MB, current usage: {memory_after:.1f} MB")
        
        return freed


class HftBacktestDataFormatter:
    """Format MNQ data for hftbacktest consumption."""
    
    # hftbacktest data format constants
    BUY = 1
    SELL = -1
    
    # MNQ contract specifications
    MNQ_TICK_SIZE = 0.25  # $0.25 per tick
    MNQ_LOT_SIZE = 20  # $20 per index point
    
    @staticmethod
    def format_l1_data(df: pd.DataFrame) -> pd.DataFrame:
        """
        Format Level 1 data for hftbacktest.
        
        Expected hftbacktest format:
        - timestamp: int64 nanoseconds
        - price: float64 
        - qty: float64
        - side: int (1=buy, -1=sell, 0=unknown)
        - order_id: int64 (optional)
        """
        if df.empty:
            return pd.DataFrame(columns=['timestamp', 'price', 'qty', 'side'])
        
        # Filter for Level 1 data only
        l1_data = df[df['level'] == '1'].copy()
        
        if l1_data.empty:
            return pd.DataFrame(columns=['timestamp', 'price', 'qty', 'side'])
        
        # Convert to hftbacktest format
        formatted = pd.DataFrame()
        formatted['timestamp'] = l1_data['timestamp'].astype('int64')
        formatted['price'] = l1_data['price'].astype('float64')
        formatted['qty'] = l1_data['volume'].astype('float64')
        
        # Map MDT to side (simplified mapping)
        # MDT: 0=Ask, 1=Bid, 2=Last/Trade
        formatted['side'] = l1_data['mdt'].map({
            0: HftBacktestDataFormatter.SELL,  # Ask = Sell
            1: HftBacktestDataFormatter.BUY,   # Bid = Buy  
            2: 0,  # Trade = Unknown side
        }).fillna(0).astype('int')
        
        # Sort by timestamp
        formatted = formatted.sort_values('timestamp').reset_index(drop=True)
        
        logger.debug(f"Formatted {len(formatted)} L1 records for hftbacktest")
        return formatted
    
    @staticmethod
    def format_l2_data(df: pd.DataFrame) -> pd.DataFrame:
        """
        Format Level 2 data for hftbacktest order book.
        
        For hftbacktest, L2 data typically represents order book updates
        which can be processed through the order book reconstructor.
        """
        if df.empty:
            return pd.DataFrame(columns=['timestamp', 'price', 'qty', 'side', 'op'])
        
        # Filter for Level 2 data only
        l2_data = df[df['level'] == '2'].copy()
        
        if l2_data.empty:
            return pd.DataFrame(columns=['timestamp', 'price', 'qty', 'side', 'op'])
        
        # Convert to hftbacktest L2 format
        formatted = pd.DataFrame()
        formatted['timestamp'] = l2_data['timestamp'].astype('int64')
        formatted['price'] = l2_data['price'].astype('float64')
        formatted['qty'] = l2_data['volume'].astype('float64')
        
        # Map MDT to side
        formatted['side'] = l2_data['mdt'].map({
            0: HftBacktestDataFormatter.SELL,  # Ask = Sell
            1: HftBacktestDataFormatter.BUY,   # Bid = Buy
        }).fillna(0).astype('int')
        
        # Map operation type (0=Add, 1=Update, 2=Remove)
        formatted['op'] = l2_data['operation'].astype('int')
        
        # Sort by timestamp
        formatted = formatted.sort_values('timestamp').reset_index(drop=True)
        
        logger.debug(f"Formatted {len(formatted)} L2 records for hftbacktest")
        return formatted


class HftBacktestAdapter:
    """Adapter for integrating MNQ data with hftbacktest engine."""
    
    def __init__(self, config: Optional[PipelineConfig] = None):
        """Initialize the hftbacktest adapter."""
        self.config = config or PipelineConfig()
        self.formatter = HftBacktestDataFormatter()
        self.data_loader = DataLoader()
        
    def prepare_data(
        self, 
        file_path: Path, 
        start_time: Optional[int] = None,
        end_time: Optional[int] = None
    ) -> Dict[str, pd.DataFrame]:
        """
        Prepare MNQ data for hftbacktest consumption.
        
        Args:
            file_path: Path to MNQ Parquet file
            start_time: Start timestamp filter (nanoseconds)
            end_time: End timestamp filter (nanoseconds)
            
        Returns:
            Dictionary with 'l1' and 'l2' formatted DataFrames
        """
        logger.info(f"Preparing data from {file_path}")
        
        # Load raw data
        raw_data = self.data_loader.load_file(file_path)
        
        # Apply time filters if specified
        if start_time or end_time:
            if start_time:
                raw_data = raw_data[raw_data['timestamp'] >= start_time]
            if end_time:
                raw_data = raw_data[raw_data['timestamp'] <= end_time]
        
        # Format data for hftbacktest
        l1_data = self.formatter.format_l1_data(raw_data)
        l2_data = self.formatter.format_l2_data(raw_data) if self.config.enable_l2_processing else pd.DataFrame()
        
        logger.info(f"Prepared {len(l1_data)} L1 and {len(l2_data)} L2 records")
        
        return {
            'l1': l1_data,
            'l2': l2_data
        }
    
    def get_contract_specs(self) -> Dict[str, Any]:
        """Get MNQ contract specifications for hftbacktest."""
        return {
            'tick_size': self.formatter.MNQ_TICK_SIZE,
            'lot_size': self.formatter.MNQ_LOT_SIZE,
            'contract': 'MNQ',
            'currency': 'USD',
            'exchange': 'CME',
            'asset_type': 'future'
        }


class DataPipeline:
    """Unified data pipeline for processing MNQ data for backtesting."""
    
    def __init__(self, config: Optional[PipelineConfig] = None):
        """Initialize the data pipeline."""
        self.config = config or PipelineConfig()
        self.memory_monitor = MemoryMonitor(self.config)
        self.file_discovery = ParquetFileDiscovery()
        self.adapter = HftBacktestAdapter(self.config)
        self.order_book_reconstructor = OrderBookReconstructor(
            max_depth=self.config.order_book_depth
        ) if self.config.enable_l2_processing else None
        
        self.stats = ProcessingStats()
    
    def process_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        contract_months: Optional[List[str]] = None
    ) -> Iterator[Dict[str, Any]]:
        """
        Process data over a date range in chunks.
        
        Args:
            start_date: Start date for processing
            end_date: End date for processing  
            contract_months: Contract months to include (e.g., ['03-20', '06-20'])
            
        Yields:
            Processed data chunks ready for backtesting
        """
        logger.info(f"Starting pipeline processing from {start_date} to {end_date}")
        self.stats = ProcessingStats()
        
        # Discover files in date range
        files = self.file_discovery.discover_files(
            contract_months=contract_months,
            start_date=start_date,
            end_date=end_date
        )
        
        if not files:
            logger.warning("No files found for the specified date range")
            return
        
        logger.info(f"Found {len(files)} files to process")
        
        retry_count = 0
        
        for file_info in files:
            try:
                # Memory check before processing
                if self.memory_monitor.should_trigger_gc():
                    self.memory_monitor.trigger_gc()
                
                # Process file
                yield from self._process_file(file_info.file_path)
                
                self.stats.files_processed += 1
                retry_count = 0  # Reset retry count on success
                
            except Exception as e:
                self.stats.errors_encountered += 1
                retry_count += 1
                
                logger.error(f"Error processing {file_info.file_path}: {e}")
                
                if retry_count <= self.config.max_retries:
                    logger.info(f"Retrying in {self.config.retry_delay}s (attempt {retry_count})")
                    time.sleep(self.config.retry_delay)
                    continue
                else:
                    logger.error(f"Max retries exceeded for {file_info.file_path}, skipping")
                    retry_count = 0
                    continue
        
        # Final stats
        self.stats.end_time = time.time()
        self.stats.memory_peak_mb = self.memory_monitor.peak_memory
        
        logger.info(f"Pipeline completed: {self.stats.files_processed} files, "
                   f"{self.stats.records_processed} records in {self.stats.duration:.1f}s "
                   f"({self.stats.records_per_second:.0f} records/s)")
    
    def _process_file(self, file_path: Path) -> Iterator[Dict[str, Any]]:
        """Process a single file in chunks."""
        logger.debug(f"Processing file: {file_path}")
        
        try:
            # Load and prepare data
            prepared_data = self.adapter.prepare_data(file_path)
            
            l1_data = prepared_data['l1']
            l2_data = prepared_data['l2']
            
            self.stats.l1_records += len(l1_data)
            self.stats.l2_records += len(l2_data)
            
            # Process in chunks if data is large
            if len(l1_data) > self.config.chunk_size:
                yield from self._process_chunks(l1_data, l2_data)
            else:
                # Process entire dataset
                result = self._create_data_chunk(l1_data, l2_data)
                if result:
                    yield result
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            raise
    
    def _process_chunks(
        self, 
        l1_data: pd.DataFrame, 
        l2_data: pd.DataFrame
    ) -> Iterator[Dict[str, Any]]:
        """Process large datasets in chunks."""
        
        chunk_count = 0
        l1_chunks = [l1_data[i:i + self.config.chunk_size] 
                     for i in range(0, len(l1_data), self.config.chunk_size)]
        
        # For L2 data, we need to be more careful about chunking
        # to maintain order book state consistency
        for l1_chunk in l1_chunks:
            chunk_start_time = l1_chunk['timestamp'].min()
            chunk_end_time = l1_chunk['timestamp'].max()
            
            # Get corresponding L2 data for this time range
            l2_chunk = l2_data[
                (l2_data['timestamp'] >= chunk_start_time) &
                (l2_data['timestamp'] <= chunk_end_time)
            ] if not l2_data.empty else pd.DataFrame()
            
            result = self._create_data_chunk(l1_chunk, l2_chunk)
            if result:
                yield result
            
            chunk_count += 1
            self.stats.records_processed += len(l1_chunk) + len(l2_chunk)
            
            # Progress reporting
            if chunk_count % 10 == 0:
                memory_mb = self.memory_monitor.get_memory_usage_mb()
                logger.info(f"Processed {chunk_count} chunks, "
                           f"{self.stats.records_processed} total records, "
                           f"memory: {memory_mb:.1f} MB")
    
    def _create_data_chunk(
        self, 
        l1_data: pd.DataFrame, 
        l2_data: pd.DataFrame
    ) -> Optional[Dict[str, Any]]:
        """Create a processed data chunk ready for backtesting."""
        
        if l1_data.empty and l2_data.empty:
            return None
        
        result = {
            'l1_data': l1_data,
            'l2_data': l2_data,
            'contract_specs': self.adapter.get_contract_specs(),
            'timestamp_range': {
                'start': int(l1_data['timestamp'].min()) if not l1_data.empty else None,
                'end': int(l1_data['timestamp'].max()) if not l1_data.empty else None,
            }
        }
        
        # Add order book snapshot if L2 processing is enabled
        if self.config.enable_l2_processing and not l2_data.empty and self.order_book_reconstructor:
            try:
                # Create temporary file for order book reconstruction
                import tempfile
                with tempfile.NamedTemporaryFile(suffix='.parquet', delete=True) as tmp_file:
                    # Convert back to original format for order book processing
                    l2_original_format = self._convert_l2_to_original_format(l2_data)
                    l2_original_format.to_parquet(tmp_file.name)
                    
                    # Reconstruct order book
                    end_timestamp = int(l2_data['timestamp'].max())
                    snapshot = self.order_book_reconstructor.reconstruct_from_file(
                        tmp_file.name, end_timestamp
                    )
                    
                    result['order_book_snapshot'] = {
                        'timestamp': snapshot.timestamp,
                        'best_bid': float(snapshot.best_bid.price) if snapshot.best_bid else None,
                        'best_ask': float(snapshot.best_ask.price) if snapshot.best_ask else None,
                        'spread': float(snapshot.spread) if snapshot.spread else None,
                        'mid_price': float(snapshot.mid_price) if snapshot.mid_price else None,
                        'bid_levels': len(snapshot.bid_levels),
                        'ask_levels': len(snapshot.ask_levels)
                    }
                    
            except Exception as e:
                logger.warning(f"Failed to create order book snapshot: {e}")
        
        return result
    
    def _convert_l2_to_original_format(self, l2_data: pd.DataFrame) -> pd.DataFrame:
        """Convert hftbacktest L2 format back to original MNQ format for order book processing."""
        
        if l2_data.empty:
            return pd.DataFrame(columns=['level', 'timestamp', 'mdt', 'price', 'volume', 'operation'])
        
        original_format = pd.DataFrame({
            'level': ['2'] * len(l2_data),
            'timestamp': l2_data['timestamp'],
            'mdt': l2_data['side'].map({
                1: 1,   # Buy -> Bid
                -1: 0,  # Sell -> Ask
            }).fillna(0),
            'price': l2_data['price'],
            'volume': l2_data['qty'],
            'operation': l2_data['op']
        })
        
        return original_format
    
    def get_stats(self) -> ProcessingStats:
        """Get current processing statistics."""
        return self.stats
    
    def cleanup(self):
        """Perform cleanup operations."""
        self.memory_monitor.trigger_gc()
        logger.info("Pipeline cleanup completed")


class PipelineError(Exception):
    """Base exception for pipeline errors."""
    pass


class DataValidationError(PipelineError):
    """Raised when data validation fails."""
    pass


class MemoryLimitExceededError(PipelineError):
    """Raised when memory limit is exceeded."""
    pass