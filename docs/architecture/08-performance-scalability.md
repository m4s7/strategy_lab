# Strategy Lab Technical Architecture - Performance & Scalability

## Performance Architecture Overview

The performance architecture focuses on achieving the target of processing 100K-500K ticks per second while maintaining memory efficiency for datasets with millions of rows.

## Memory Management Strategy

### Memory-Efficient Data Processing

```python
class MemoryEfficientDataProcessor:
    """Memory-efficient processing for large datasets"""
    
    def __init__(self, 
                 chunk_size: int = 1_000_000,
                 memory_limit_gb: int = 32):
        self.chunk_size = chunk_size
        self.memory_limit = memory_limit_gb * 1024 * 1024 * 1024
        self.cache = LRUCache(maxsize=128)
        self.memory_monitor = MemoryMonitor()
        
    def process_large_dataset(self, 
                            data_path: str,
                            processor: Callable) -> Iterator[ProcessedChunk]:
        """Process large Parquet files in chunks"""
        parquet_file = pq.ParquetFile(data_path)
        total_rows = parquet_file.metadata.num_rows
        
        logger.info(f"Processing {total_rows:,} rows in chunks of {self.chunk_size:,}")
        
        for i, batch in enumerate(parquet_file.iter_batches(batch_size=self.chunk_size)):
            # Check memory before processing
            if self._memory_pressure_high():
                self._release_memory()
                gc.collect()
            
            # Convert to pandas with optimization
            df = batch.to_pandas()
            df = self._optimize_dtypes(df)
            
            # Process chunk
            processed = processor(df)
            
            # Cache if beneficial
            if self._should_cache(processed):
                self.cache.put(f"chunk_{i}", processed)
            
            yield ProcessedChunk(
                data=processed,
                chunk_id=i,
                total_chunks=total_rows // self.chunk_size + 1
            )
    
    def _optimize_dtypes(self, df: pd.DataFrame) -> pd.DataFrame:
        """Optimize data types to reduce memory usage"""
        optimized = df.copy()
        
        # Optimize integers
        for col in optimized.select_dtypes(include=['int64']).columns:
            optimized[col] = pd.to_numeric(optimized[col], downcast='integer')
        
        # Optimize floats
        for col in optimized.select_dtypes(include=['float64']).columns:
            max_val = optimized[col].max()
            if max_val < np.finfo(np.float32).max:
                optimized[col] = optimized[col].astype(np.float32)
        
        # Use categorical for repeated strings
        for col in optimized.select_dtypes(include=['object']).columns:
            if optimized[col].nunique() / len(optimized) < 0.5:
                optimized[col] = optimized[col].astype('category')
        
        # Log memory savings
        original_memory = df.memory_usage(deep=True).sum()
        optimized_memory = optimized.memory_usage(deep=True).sum()
        reduction = (1 - optimized_memory / original_memory) * 100
        
        logger.debug(f"Memory optimization: {reduction:.1f}% reduction")
        
        return optimized
    
    def _memory_pressure_high(self) -> bool:
        """Check if memory pressure is high"""
        memory_info = self.memory_monitor.get_current_usage()
        return memory_info['percent'] > 80 or memory_info['available'] < 4 * 1024 * 1024 * 1024
```

### Data Type Optimization Matrix

```python
class DataTypeOptimizer:
    """Intelligent data type optimization"""
    
    # Optimization rules for MNQ data
    TYPE_RULES = {
        'timestamp': 'int64',  # Keep nanosecond precision
        'mdt': 'int8',       # Market data type (0-10)
        'operation': 'int8',  # Operations (0-2)
        'depth': 'int8',     # Depth levels (1-10)
        'volume': 'int32',   # Volume fits in int32
        'price': 'float32',  # Price precision sufficient
        'market_maker': 'category'  # Repeated values
    }
    
    @classmethod
    def optimize_dataframe(cls, df: pd.DataFrame) -> pd.DataFrame:
        """Apply optimization rules to dataframe"""
        optimized = df.copy()
        
        for col, target_type in cls.TYPE_RULES.items():
            if col in optimized.columns:
                if target_type == 'category':
                    optimized[col] = optimized[col].astype('category')
                else:
                    optimized[col] = optimized[col].astype(target_type)
        
        return optimized
    
    @classmethod
    def estimate_memory_usage(cls, num_rows: int) -> Dict[str, float]:
        """Estimate memory usage for given number of rows"""
        # Bytes per row for each data type
        bytes_per_row = {
            'int8': 1,
            'int32': 4,
            'int64': 8,
            'float32': 4,
            'category': 2  # Approximate for category
        }
        
        total_bytes = 0
        for col, dtype in cls.TYPE_RULES.items():
            if dtype in bytes_per_row:
                total_bytes += bytes_per_row[dtype]
        
        total_mb = (total_bytes * num_rows) / (1024 * 1024)
        
        return {
            'bytes_per_row': total_bytes,
            'total_mb': total_mb,
            'total_gb': total_mb / 1024
        }
```

## Resource Monitoring

### System Resource Monitor

```python
import psutil
import threading
from collections import deque
from contextlib import contextmanager

class ResourceMonitor:
    """Monitor system resources during backtesting"""
    
    def __init__(self, sampling_interval: float = 1.0):
        self.sampling_interval = sampling_interval
        self.monitoring = False
        self.stats_history = deque(maxlen=3600)  # 1 hour at 1s intervals
        self.alerts = []
        
    @contextmanager
    def monitor_operation(self, operation_name: str):
        """Context manager for monitoring specific operations"""
        start_stats = self._get_current_stats()
        start_time = time.time()
        
        try:
            yield self
        finally:
            end_stats = self._get_current_stats()
            duration = time.time() - start_time
            
            # Log operation metrics
            operation_metrics = {
                'operation': operation_name,
                'duration': duration,
                'cpu_usage': end_stats['cpu_percent'] - start_stats['cpu_percent'],
                'memory_delta': end_stats['memory_mb'] - start_stats['memory_mb'],
                'peak_memory': max(s['memory_mb'] for s in self.stats_history 
                                  if s['timestamp'] >= start_time)
            }
            
            logger.info(f"Operation metrics: {operation_metrics}")
    
    def start_monitoring(self):
        """Start resource monitoring thread"""
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def _monitor_loop(self):
        """Background monitoring loop"""
        while self.monitoring:
            stats = self._get_current_stats()
            self.stats_history.append(stats)
            
            # Check for alerts
            self._check_alerts(stats)
            
            time.sleep(self.sampling_interval)
    
    def _get_current_stats(self) -> Dict[str, Any]:
        """Get current system statistics"""
        memory = psutil.virtual_memory()
        disk_io = psutil.disk_io_counters()
        
        return {
            'timestamp': time.time(),
            'cpu_percent': psutil.cpu_percent(interval=0.1),
            'cpu_count': psutil.cpu_count(),
            'memory_mb': memory.used / (1024 * 1024),
            'memory_percent': memory.percent,
            'memory_available_mb': memory.available / (1024 * 1024),
            'disk_read_mb': disk_io.read_bytes / (1024 * 1024),
            'disk_write_mb': disk_io.write_bytes / (1024 * 1024)
        }
    
    def _check_alerts(self, stats: Dict[str, Any]):
        """Check for resource alerts"""
        alerts = []
        
        if stats['cpu_percent'] > 90:
            alerts.append(('HIGH_CPU', f"CPU usage: {stats['cpu_percent']}%"))
        
        if stats['memory_percent'] > 85:
            alerts.append(('HIGH_MEMORY', f"Memory usage: {stats['memory_percent']}%"))
        
        if stats['memory_available_mb'] < 2048:
            alerts.append(('LOW_MEMORY', f"Available memory: {stats['memory_available_mb']}MB"))
        
        for alert_type, message in alerts:
            logger.warning(f"Resource alert [{alert_type}]: {message}")
            self.alerts.append({
                'type': alert_type,
                'message': message,
                'timestamp': stats['timestamp']
            })
```

## Performance Profiling

### Backtest Performance Profiler

```python
import cProfile
import pstats
from line_profiler import LineProfiler
from memory_profiler import profile

class PerformanceProfiler:
    """Performance profiling and optimization tools"""
    
    def __init__(self):
        self.timers = defaultdict(list)
        self.counters = defaultdict(int)
        self.profiler = cProfile.Profile()
        
    @contextmanager
    def time_operation(self, operation_name: str):
        """Time specific operations"""
        start_time = time.perf_counter()
        self.counters[operation_name] += 1
        
        try:
            yield
        finally:
            duration = time.perf_counter() - start_time
            self.timers[operation_name].append(duration)
            
            # Log slow operations
            if duration > 1.0:
                logger.warning(f"Slow operation [{operation_name}]: {duration:.2f}s")
    
    def profile_function(self, func: Callable) -> Callable:
        """Decorator for detailed function profiling"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            self.profiler.enable()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                self.profiler.disable()
        
        return wrapper
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        report = {
            'operation_timings': {},
            'operation_counts': dict(self.counters),
            'bottlenecks': []
        }
        
        # Calculate timing statistics
        for operation, times in self.timers.items():
            if times:
                report['operation_timings'][operation] = {
                    'count': len(times),
                    'total': sum(times),
                    'average': sum(times) / len(times),
                    'min': min(times),
                    'max': max(times),
                    'median': sorted(times)[len(times) // 2]
                }
        
        # Identify bottlenecks
        total_time = sum(sum(times) for times in self.timers.values())
        for operation, times in self.timers.items():
            operation_time = sum(times)
            percentage = (operation_time / total_time * 100) if total_time > 0 else 0
            
            if percentage > 10:  # Operations taking >10% of total time
                report['bottlenecks'].append({
                    'operation': operation,
                    'percentage': percentage,
                    'total_time': operation_time
                })
        
        return report
    
    def save_profile_stats(self, filename: str):
        """Save detailed profiling statistics"""
        stats = pstats.Stats(self.profiler)
        stats.sort_stats('cumulative')
        stats.dump_stats(filename)
```

## Caching Strategy

### Multi-Level Cache System

```python
from functools import lru_cache
from diskcache import Cache

class MultiLevelCache:
    """Multi-level caching for performance optimization"""
    
    def __init__(self, 
                 memory_cache_size: int = 128,
                 disk_cache_dir: str = '.cache'):
        # L1: In-memory LRU cache
        self.memory_cache = LRUCache(maxsize=memory_cache_size)
        
        # L2: Disk-based cache
        self.disk_cache = Cache(disk_cache_dir, size_limit=10 * 1024 * 1024 * 1024)  # 10GB
        
        # Cache statistics
        self.stats = {
            'memory_hits': 0,
            'memory_misses': 0,
            'disk_hits': 0,
            'disk_misses': 0
        }
    
    def get(self, key: str) -> Optional[Any]:
        """Retrieve from cache with fallback"""
        # Try memory cache first
        value = self.memory_cache.get(key)
        if value is not None:
            self.stats['memory_hits'] += 1
            return value
        
        self.stats['memory_misses'] += 1
        
        # Try disk cache
        value = self.disk_cache.get(key)
        if value is not None:
            self.stats['disk_hits'] += 1
            # Promote to memory cache
            self.memory_cache.put(key, value)
            return value
        
        self.stats['disk_misses'] += 1
        return None
    
    def put(self, key: str, value: Any, cache_level: str = 'both'):
        """Store in cache"""
        if cache_level in ['memory', 'both']:
            self.memory_cache.put(key, value)
        
        if cache_level in ['disk', 'both']:
            self.disk_cache.set(key, value)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        total_requests = (self.stats['memory_hits'] + self.stats['memory_misses'])
        
        return {
            'memory_hit_rate': self.stats['memory_hits'] / total_requests if total_requests > 0 else 0,
            'disk_hit_rate': self.stats['disk_hits'] / self.stats['disk_misses'] if self.stats['disk_misses'] > 0 else 0,
            'total_requests': total_requests,
            **self.stats
        }
```

## Parallel Processing Optimization

### CPU Affinity Management

```python
import os

class CPUAffinityManager:
    """Manage CPU affinity for optimal parallel processing"""
    
    def __init__(self, num_cores: int = 16):
        self.num_cores = num_cores
        self.available_cores = os.cpu_count()
        
    def setup_worker_affinity(self, worker_id: int, workers_per_core: int = 1):
        """Set CPU affinity for worker process"""
        if not hasattr(os, 'sched_setaffinity'):
            return  # Not supported on this platform
        
        # Calculate which core(s) this worker should use
        core_id = worker_id // workers_per_core
        
        # Set affinity
        pid = os.getpid()
        affinity_mask = {core_id % self.available_cores}
        os.sched_setaffinity(pid, affinity_mask)
        
        logger.debug(f"Worker {worker_id} bound to CPU core {core_id}")
    
    def optimize_thread_pool_size(self, task_type: str) -> int:
        """Determine optimal thread pool size for task type"""
        if task_type == 'io_bound':
            # More threads for I/O bound tasks
            return self.available_cores * 2
        elif task_type == 'cpu_bound':
            # One thread per core for CPU bound tasks
            return self.available_cores
        elif task_type == 'mixed':
            # Balance between CPU and I/O
            return int(self.available_cores * 1.5)
        else:
            return self.available_cores
```

## Performance Benchmarks

### Benchmark Suite

```python
class PerformanceBenchmark:
    """Comprehensive performance benchmarking"""
    
    def __init__(self):
        self.results = {}
        
    def benchmark_data_loading(self, data_path: str) -> Dict[str, float]:
        """Benchmark data loading performance"""
        file_size = os.path.getsize(data_path) / (1024 * 1024)  # MB
        
        # Benchmark different loading methods
        results = {}
        
        # Standard pandas loading
        start = time.perf_counter()
        df = pd.read_parquet(data_path)
        results['pandas_load_time'] = time.perf_counter() - start
        results['pandas_throughput_mb_s'] = file_size / results['pandas_load_time']
        
        # Chunked loading
        start = time.perf_counter()
        chunks = []
        for chunk in pd.read_parquet(data_path, chunksize=1_000_000):
            chunks.append(chunk)
        results['chunked_load_time'] = time.perf_counter() - start
        results['chunked_throughput_mb_s'] = file_size / results['chunked_load_time']
        
        # Memory usage
        results['memory_usage_mb'] = df.memory_usage(deep=True).sum() / (1024 * 1024)
        results['rows_per_second'] = len(df) / results['pandas_load_time']
        
        return results
    
    def benchmark_strategy_execution(self, 
                                   strategy: BaseStrategy,
                                   market_data: List[MarketData]) -> Dict[str, float]:
        """Benchmark strategy signal generation"""
        results = {}
        
        # Warm up
        for _ in range(100):
            strategy.generate_signal(market_data[0])
        
        # Benchmark
        start = time.perf_counter()
        signals = []
        for data in market_data:
            signal = strategy.generate_signal(data)
            signals.append(signal)
        
        total_time = time.perf_counter() - start
        
        results['total_signals'] = len(signals)
        results['total_time'] = total_time
        results['signals_per_second'] = len(signals) / total_time
        results['avg_signal_time_us'] = (total_time / len(signals)) * 1_000_000
        
        return results
```