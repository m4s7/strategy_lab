# Strategy Lab Technical Architecture - Data Architecture

## Data Processing Pipeline

The data architecture is designed for high-performance processing of millions of ticks while maintaining memory efficiency and data integrity.

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Parquet   │───▶│   Data      │───▶│   Order     │───▶│ hftbacktest │
│   Files     │    │ Validation  │    │   Book      │    │   Engine    │
│             │    │ & Cleaning  │    │Reconstruction│    │             │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       │                  │                  │                  │
       ▼                  ▼                  ▼                  ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ • Contract  │    │ • Schema    │    │ • L2 Events │    │ • Strategy  │
│   Discovery │    │   Validation│    │ • Book State│    │   Execution │
│ • Date Range│    │ • Missing   │    │ • Imbalance │    │ • Event     │
│   Filtering │    │   Data      │    │   Calc      │    │   Processing│
│ • Memory    │    │ • Quality   │    │ • Bid/Ask   │    │ • Trade     │
│   Management│    │   Checks    │    │   Updates   │    │   Simulation│
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

## Data Ingestion Architecture

### Primary Components

1. **ParquetDataLoader** - Core data loading with memory optimization
2. **DataValidator** - Schema validation and quality checks  
3. **ContractManager** - Multi-contract and rollover handling
4. **StreamingProcessor** - Memory-efficient processing for large datasets

### Key Design Patterns

- **Streaming Processing**: Process data in chunks to manage memory usage
- **Lazy Loading**: Load data on-demand to optimize resource usage
- **Caching Strategy**: Cache frequently accessed data with LRU eviction
- **Error Recovery**: Graceful handling of corrupted or missing data

### ParquetDataLoader Implementation

```python
class ParquetDataLoader:
    """High-performance Parquet data loader with memory optimization"""
    
    def __init__(self, base_path: str, chunk_size: int = 1_000_000):
        self.base_path = Path(base_path)
        self.chunk_size = chunk_size
        self.cache = LRUCache(maxsize=128)
        
    def load_date_range(self, 
                       start_date: str, 
                       end_date: str,
                       contracts: Optional[List[str]] = None) -> Iterator[pd.DataFrame]:
        """Load data for date range with streaming support"""
        files = self._discover_files(start_date, end_date, contracts)
        
        for file_path in files:
            yield from self._load_file_chunked(file_path)
    
    def _load_file_chunked(self, file_path: Path) -> Iterator[pd.DataFrame]:
        """Load Parquet file in memory-efficient chunks"""
        parquet_file = pq.ParquetFile(file_path)
        
        for batch in parquet_file.iter_batches(batch_size=self.chunk_size):
            df = batch.to_pandas()
            yield self._optimize_dtypes(df)
```

## Order Book Reconstruction

### Architecture Overview

The order book reconstruction system maintains real-time book state by processing Level 2 events with operation codes (Add/Update/Remove).

### OrderBookReconstructor Design

```python
class OrderBookReconstructor:
    """
    Reconstructs order book state from Level 2 tick data
    Handles Add/Update/Remove operations efficiently
    """
    
    def __init__(self, max_depth: int = 10):
        self.bids = SortedDict()  # Price -> Volume
        self.asks = SortedDict()  # Price -> Volume
        self.max_depth = max_depth
        self.last_update = None
    
    def process_l2_event(self, event: L2Event) -> OrderBookState:
        """Process single L2 event and return updated book state"""
        if event.operation == Operation.ADD:
            self._add_level(event)
        elif event.operation == Operation.UPDATE:
            self._update_level(event)
        elif event.operation == Operation.REMOVE:
            self._remove_level(event)
        
        return self._create_snapshot()
    
    def get_imbalance(self) -> float:
        """Calculate order book imbalance ratio"""
        bid_volume = sum(self.bids.values()[:self.max_depth])
        ask_volume = sum(self.asks.values()[:self.max_depth])
        
        if bid_volume + ask_volume == 0:
            return 0.0
        
        return (bid_volume - ask_volume) / (bid_volume + ask_volume)
```

### Performance Optimizations

1. **SortedDict for Efficient Operations**
   - O(log n) insertions and deletions
   - O(1) best bid/ask access
   - Memory-efficient for sparse books

2. **Incremental Updates**
   - Only process changed levels
   - Maintain running statistics
   - Avoid full book rebuilds

3. **Snapshot Caching**
   - Cache recent book states
   - Fast state queries for strategies
   - Configurable cache size

## Data Schema and Validation

### MNQ Tick Data Schema

```python
@dataclass
class TickSchema:
    """Expected schema for MNQ tick data"""
    level: str              # Data level indicator
    mdt: int               # Market Data Type (0-10)
    timestamp: int         # Nanosecond precision
    operation: Optional[int]  # L2 operations (0=Add, 1=Update, 2=Remove)
    depth: Optional[int]      # Order book depth level
    market_maker: Optional[str]  # Market maker ID
    price: Decimal         # Price with 13,2 precision
    volume: int            # Trade/quote volume
```

### Validation Pipeline

```python
class DataValidator:
    """Comprehensive data validation for tick data integrity"""
    
    def validate_dataframe(self, df: pd.DataFrame) -> ValidationResult:
        """Run all validation checks on dataframe"""
        checks = [
            self._validate_schema,
            self._validate_timestamps,
            self._validate_prices,
            self._validate_volumes,
            self._validate_operations
        ]
        
        results = []
        for check in checks:
            result = check(df)
            results.append(result)
            if result.is_critical and not result.passed:
                break
                
        return ValidationResult(results)
    
    def _validate_timestamps(self, df: pd.DataFrame) -> CheckResult:
        """Ensure timestamps are monotonic and valid"""
        # Check for monotonic increasing timestamps
        # Detect and report time gaps
        # Validate nanosecond precision
        pass
```

## Memory Management Strategy

### Chunk Processing

```python
class MemoryEfficientDataProcessor:
    """Memory-efficient processing for large datasets"""
    
    def __init__(self, chunk_size: int = 1_000_000):
        self.chunk_size = chunk_size
        self.memory_limit = 32 * 1024 * 1024 * 1024  # 32GB
        
    def process_large_dataset(self, data_path: str) -> Iterator[pd.DataFrame]:
        """Process large Parquet files in chunks"""
        with self._monitor_memory():
            parquet_file = pq.ParquetFile(data_path)
            
            for batch in parquet_file.iter_batches(batch_size=self.chunk_size):
                df = batch.to_pandas()
                
                # Optimize memory usage
                df = self._optimize_dtypes(df)
                
                # Check memory pressure
                if self._memory_pressure_high():
                    self._release_memory()
                
                yield df
```

### Data Type Optimization

```python
def _optimize_dtypes(self, df: pd.DataFrame) -> pd.DataFrame:
    """Optimize data types to reduce memory usage"""
    # Convert int64 to smallest possible int type
    for col in df.select_dtypes(include=['int64']).columns:
        df[col] = pd.to_numeric(df[col], downcast='integer')
    
    # Convert float64 to float32 where possible
    for col in df.select_dtypes(include=['float64']).columns:
        if df[col].max() < np.finfo(np.float32).max:
            df[col] = df[col].astype(np.float32)
    
    # Use categorical for repeated strings
    if 'market_maker' in df.columns:
        df['market_maker'] = df['market_maker'].astype('category')
    
    return df
```

## Contract Management

### Multi-Contract Handling

```python
class ContractManager:
    """Manages multiple futures contracts and rollover logic"""
    
    def __init__(self, contract_specs: Dict[str, Any]):
        self.contract_specs = contract_specs
        self.active_contracts = {}
        
    def get_continuous_series(self, 
                            start_date: str,
                            end_date: str,
                            rollover_days: int = 5) -> pd.DataFrame:
        """Create continuous contract series with rollover handling"""
        # Identify relevant contracts for date range
        contracts = self._identify_contracts(start_date, end_date)
        
        # Load data for each contract
        contract_data = {}
        for contract in contracts:
            contract_data[contract] = self._load_contract_data(contract)
        
        # Apply rollover logic
        continuous = self._apply_rollover(contract_data, rollover_days)
        
        return continuous
```

## Data Pipeline Configuration

### Pipeline Configuration Schema

```yaml
data_pipeline:
  ingestion:
    chunk_size: 1000000
    max_memory_gb: 32
    cache_size: 128
    
  validation:
    strict_mode: true
    max_missing_ratio: 0.01
    timestamp_tolerance_ns: 1000
    
  order_book:
    max_depth: 10
    snapshot_frequency: 1000
    imbalance_calculation: true
    
  contracts:
    rollover_days: 5
    adjustment_method: "ratio"
    front_month_only: false
```