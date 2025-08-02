# Strategy Lab Technical Architecture - Testing & Security

## Testing Architecture

The testing strategy follows the test pyramid approach with comprehensive unit tests, integration tests, and end-to-end validation of the complete backtesting workflow.

### Test Structure and Organization

```
tests/
├── unit/                          # Unit tests
│   ├── test_data_ingestion.py    # Data layer tests
│   ├── test_order_book.py        # Order book reconstruction
│   ├── test_strategies.py        # Strategy framework tests
│   ├── test_optimization.py      # Optimization algorithms
│   └── test_analytics.py         # Performance metrics
├── integration/                   # Integration tests
│   ├── test_backtest_engine.py   # Full engine integration
│   ├── test_data_pipeline.py     # End-to-end data flow
│   └── test_strategy_execution.py # Strategy + engine
├── performance/                   # Performance tests
│   ├── test_throughput.py        # Tick processing performance
│   ├── test_memory_usage.py      # Memory efficiency
│   └── test_optimization_speed.py # Optimization performance
├── fixtures/                      # Test data and utilities
│   ├── sample_data/              # Sample tick data
│   ├── test_strategies.py        # Test strategy implementations
│   └── mock_data_generator.py    # Synthetic data generation
└── conftest.py                   # Pytest configuration
```

### Unit Testing Framework

```python
import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from src.data.ingestion import ParquetDataLoader
from src.data.orderbook import OrderBookReconstructor
from src.strategies.base import BaseStrategy

class TestParquetDataLoader:
    """Unit tests for data loading functionality"""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample tick data for testing"""
        return pd.DataFrame({
            'timestamp': range(1000),
            'mdt': [0, 1, 2] * 333 + [0],
            'price': [100.0 + i * 0.25 for i in range(1000)],
            'volume': [10] * 1000,
            'operation': [0] * 1000,
            'depth': [1] * 1000
        })
    
    @pytest.fixture
    def data_loader(self, tmp_path):
        """Create data loader with temporary directory"""
        return ParquetDataLoader(str(tmp_path))
    
    def test_load_valid_data(self, data_loader, sample_data, tmp_path):
        """Test loading valid Parquet data"""
        # Save sample data
        data_file = tmp_path / "test_data.parquet"
        sample_data.to_parquet(data_file)
        
        # Load and verify
        loaded_data = list(data_loader.load_date_range("2024-01-01", "2024-01-01"))
        
        assert len(loaded_data) == 1
        assert len(loaded_data[0]) == 1000
        pd.testing.assert_frame_equal(loaded_data[0], sample_data)
    
    def test_memory_optimization(self, data_loader, sample_data):
        """Test data type optimization reduces memory usage"""
        original_memory = sample_data.memory_usage(deep=True).sum()
        optimized = data_loader._optimize_dtypes(sample_data)
        optimized_memory = optimized.memory_usage(deep=True).sum()
        
        assert optimized_memory < original_memory
        # Verify data integrity
        assert len(optimized) == len(sample_data)
    
    def test_invalid_data_handling(self, data_loader):
        """Test graceful handling of invalid data files"""
        with pytest.raises(FileNotFoundError):
            list(data_loader.load_date_range("2024-01-01", "2024-01-01"))
    
    def test_chunk_size_configuration(self, tmp_path):
        """Test configurable chunk sizes"""
        loader_small = ParquetDataLoader(str(tmp_path), chunk_size=100)
        loader_large = ParquetDataLoader(str(tmp_path), chunk_size=1000)
        
        assert loader_small.chunk_size == 100
        assert loader_large.chunk_size == 1000

class TestOrderBookReconstructor:
    """Unit tests for order book reconstruction"""
    
    @pytest.fixture
    def order_book(self):
        """Create order book reconstructor"""
        return OrderBookReconstructor(max_depth=5)
    
    def test_add_order(self, order_book):
        """Test adding new order to book"""
        from src.data.orderbook import L2Event, Operation
        
        event = L2Event(
            timestamp=1000,
            operation=Operation.ADD,
            side='bid',
            price=100.0,
            volume=10,
            depth=1
        )
        
        state = order_book.process_l2_event(event)
        
        assert state.best_bid == 100.0
        assert state.bid_volume_at_level(1) == 10
    
    def test_order_book_imbalance(self, order_book):
        """Test order book imbalance calculation"""
        # Add bids and asks
        bid_events = [
            L2Event(1000, Operation.ADD, 'bid', 100.0, 50, 1),
            L2Event(1001, Operation.ADD, 'bid', 99.75, 30, 2)
        ]
        ask_events = [
            L2Event(1002, Operation.ADD, 'ask', 100.25, 20, 1),
            L2Event(1003, Operation.ADD, 'ask', 100.50, 15, 2)
        ]
        
        for event in bid_events + ask_events:
            order_book.process_l2_event(event)
        
        imbalance = order_book.get_imbalance()
        
        # More bid volume (80) than ask volume (35)
        expected_imbalance = (80 - 35) / (80 + 35)
        assert abs(imbalance - expected_imbalance) < 0.001

class TestStrategyFramework:
    """Unit tests for strategy framework"""
    
    @pytest.fixture
    def test_strategy(self):
        """Create test strategy instance"""
        class TestStrategy(BaseStrategy):
            def generate_signal(self, market_data):
                if market_data.bid > 100:
                    return Signal('BUY', 1)
                return Signal('HOLD', 0)
            
            def get_parameters(self):
                return {'threshold': {'min': 50, 'max': 150, 'step': 1}}
        
        return TestStrategy({'threshold': 100})
    
    def test_signal_generation(self, test_strategy):
        """Test strategy signal generation"""
        from src.strategies.base import MarketData, Signal
        
        # Test buy signal
        market_data = MarketData(
            timestamp=1000,
            bid=101.0,
            ask=101.25,
            last=101.0,
            volume=10
        )
        
        signal = test_strategy.generate_signal(market_data)
        assert signal.action == 'BUY'
        assert signal.quantity == 1
        
        # Test hold signal
        market_data.bid = 99.0
        signal = test_strategy.generate_signal(market_data)
        assert signal.action == 'HOLD'
    
    def test_parameter_validation(self, test_strategy):
        """Test parameter validation"""
        valid_params = {'threshold': 120}
        test_strategy.update_parameters(valid_params)
        assert test_strategy.config['threshold'] == 120
        
        # Test invalid parameters would require validation implementation
    
    def test_state_reset(self, test_strategy):
        """Test strategy state reset"""
        test_strategy.position = 5
        test_strategy.state = {'some_data': 'value'}
        
        test_strategy.reset_state()
        
        assert test_strategy.position == 0
        assert test_strategy.state == {}
```

### Integration Testing

```python
class TestBacktestEngineIntegration:
    """Integration tests for complete backtesting workflow"""
    
    @pytest.fixture
    def sample_strategy(self):
        """Simple strategy for integration testing"""
        from src.strategies.examples.bid_ask_bounce import BidAskBounceStrategy
        
        config = {
            'bounce_threshold': 2,
            'min_bounce_size': 0.5,
            'hold_periods': 5
        }
        return BidAskBounceStrategy(config)
    
    @pytest.fixture
    def sample_data_file(self, tmp_path, sample_tick_data):
        """Create sample data file for testing"""
        data_file = tmp_path / "sample_data.parquet"
        sample_tick_data.to_parquet(data_file)
        return str(data_file)
    
    def test_complete_backtest_workflow(self, sample_strategy, sample_data_file):
        """Test end-to-end backtesting workflow"""
        from src.backtesting.engine import BacktestingEngine
        
        config = {
            'initial_balance': 100_000,
            'commission': 2.50
        }
        
        engine = BacktestingEngine(config)
        engine.setup_engine(sample_data_file, sample_strategy)
        
        results = engine.run_backtest()
        
        # Verify results structure
        assert hasattr(results, 'performance_metrics')
        assert hasattr(results, 'trades')
        assert hasattr(results, 'equity_curve')
        
        # Verify basic metrics
        assert isinstance(results.performance_metrics.total_pnl, (int, float))
        assert 0 <= results.performance_metrics.win_rate <= 1
        assert results.performance_metrics.total_trades >= 0
    
    def test_data_pipeline_integration(self, sample_data_file):
        """Test complete data processing pipeline"""
        from src.data.ingestion import ParquetDataLoader
        from src.data.validation import DataValidator
        from src.data.orderbook import OrderBookReconstructor
        
        # Load data
        loader = ParquetDataLoader('.')
        data_chunks = list(loader.load_date_range("2024-01-01", "2024-01-01"))
        
        assert len(data_chunks) > 0
        
        # Validate data
        validator = DataValidator()
        for chunk in data_chunks:
            validation_result = validator.validate_dataframe(chunk)
            assert validation_result.is_valid
        
        # Process through order book
        order_book = OrderBookReconstructor()
        for chunk in data_chunks:
            for _, row in chunk.iterrows():
                if row['mdt'] in [0, 1]:  # Bid/Ask updates
                    # Process L2 event
                    pass
    
    @pytest.mark.slow
    def test_optimization_integration(self, sample_strategy):
        """Test optimization workflow integration"""
        from src.optimization.grid_search import GridSearchOptimizer
        
        parameter_space = {
            'bounce_threshold': {'min': 1, 'max': 5, 'step': 1},
            'min_bounce_size': {'min': 0.25, 'max': 1.0, 'step': 0.25}
        }
        
        optimizer = GridSearchOptimizer(n_cores=2)  # Limited cores for testing
        
        # Mock objective function for testing
        def mock_objective(params):
            return sum(params.values())  # Simple test function
        
        config = Mock()
        config.data_path = "test_path"
        config.strategy_name = "test_strategy"
        config.timeout_seconds = 30
        
        with patch.object(optimizer, '_worker_function', return_value=({'test': 1}, 0.5)):
            results = optimizer.optimize(mock_objective, parameter_space, config)
            
            assert results.best_params is not None
            assert isinstance(results.best_score, (int, float))
```

### Performance Testing

```python
class TestPerformanceBenchmarks:
    """Performance and scalability tests"""
    
    @pytest.mark.performance
    def test_data_loading_throughput(self, large_sample_data):
        """Test data loading meets performance targets"""
        from src.data.ingestion import ParquetDataLoader
        
        loader = ParquetDataLoader('.')
        
        start_time = time.perf_counter()
        
        total_rows = 0
        for chunk in loader.process_large_dataset(large_sample_data):
            total_rows += len(chunk.data)
        
        duration = time.perf_counter() - start_time
        throughput = total_rows / duration
        
        # Target: 1M+ rows per second
        assert throughput > 1_000_000, f"Throughput {throughput:,.0f} rows/s below target"
    
    @pytest.mark.performance
    def test_strategy_execution_speed(self, sample_strategy):
        """Test strategy execution meets performance targets"""
        from src.strategies.base import MarketData
        
        # Generate test market data
        market_data_list = []
        for i in range(100_000):
            data = MarketData(
                timestamp=i,
                bid=100.0 + (i % 100) * 0.25,
                ask=100.25 + (i % 100) * 0.25,
                last=100.0 + (i % 100) * 0.25,
                volume=10
            )
            market_data_list.append(data)
        
        # Time signal generation
        start_time = time.perf_counter()
        
        signals = []
        for data in market_data_list:
            signal = sample_strategy.generate_signal(data)
            signals.append(signal)
        
        duration = time.perf_counter() - start_time
        signals_per_second = len(signals) / duration
        
        # Target: 100K+ signals per second
        assert signals_per_second > 100_000, \
            f"Signal generation {signals_per_second:,.0f} signals/s below target"
    
    @pytest.mark.performance
    def test_memory_usage_efficiency(self, large_sample_data):
        """Test memory usage stays within limits"""
        import psutil
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        # Load and process large dataset
        from src.data.ingestion import ParquetDataLoader
        loader = ParquetDataLoader('.', chunk_size=1_000_000)
        
        max_memory = initial_memory
        for chunk in loader.process_large_dataset(large_sample_data):
            current_memory = process.memory_info().rss
            max_memory = max(max_memory, current_memory)
        
        memory_increase_gb = (max_memory - initial_memory) / (1024 * 1024 * 1024)
        
        # Should not exceed 4GB increase for processing
        assert memory_increase_gb < 4, \
            f"Memory usage increased by {memory_increase_gb:.2f}GB, exceeds 4GB limit"
```

### Test Configuration

```python
# conftest.py
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

@pytest.fixture(scope="session")
def sample_tick_data():
    """Generate realistic sample tick data"""
    np.random.seed(42)
    
    n_rows = 10_000
    timestamps = range(n_rows)
    
    # Generate realistic price movements
    base_price = 100.0
    price_changes = np.random.normal(0, 0.1, n_rows)
    prices = base_price + np.cumsum(price_changes) * 0.25
    
    data = pd.DataFrame({
        'timestamp': timestamps,
        'mdt': np.random.choice([0, 1, 2], n_rows, p=[0.4, 0.4, 0.2]),
        'price': prices,
        'volume': np.random.randint(1, 100, n_rows),
        'operation': np.random.choice([0, 1, 2], n_rows, p=[0.3, 0.6, 0.1]),
        'depth': np.random.randint(1, 11, n_rows)
    })
    
    return data

@pytest.fixture(scope="session")
def large_sample_data(tmp_path_factory):
    """Generate large sample dataset for performance testing"""
    tmp_dir = tmp_path_factory.mktemp("large_data")
    data_file = tmp_dir / "large_sample.parquet"
    
    # Generate 1M rows of data
    n_rows = 1_000_000
    np.random.seed(42)
    
    data = pd.DataFrame({
        'timestamp': range(n_rows),
        'mdt': np.random.choice([0, 1, 2], n_rows),
        'price': 100.0 + np.random.normal(0, 10, n_rows),
        'volume': np.random.randint(1, 1000, n_rows),
        'operation': np.random.choice([0, 1, 2], n_rows),
        'depth': np.random.randint(1, 11, n_rows)
    })
    
    data.to_parquet(data_file)
    return str(data_file)

# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )

def pytest_collection_modifyitems(config, items):
    """Automatically mark slow tests"""
    for item in items:
        if "test_optimization" in item.nodeid:
            item.add_marker(pytest.mark.slow)
        if "test_large_dataset" in item.nodeid:
            item.add_marker(pytest.mark.slow)
```

## Security Architecture

### Data Security Measures

```python
class SecurityManager:
    """Manages security aspects of the application"""
    
    def __init__(self):
        self.data_validator = DataSecurityValidator()
        self.access_controller = AccessController()
        self.audit_logger = AuditLogger()
    
    def validate_data_access(self, user_id: str, data_path: str) -> bool:
        """Validate user access to data files"""
        # Check if path is within allowed directories
        allowed_paths = ['/data/MNQ', './data/MNQ']
        normalized_path = os.path.normpath(data_path)
        
        for allowed in allowed_paths:
            if normalized_path.startswith(os.path.normpath(allowed)):
                self.audit_logger.log_access(user_id, data_path, 'ALLOWED')
                return True
        
        self.audit_logger.log_access(user_id, data_path, 'DENIED')
        return False
    
    def sanitize_file_path(self, file_path: str) -> str:
        """Sanitize file paths to prevent directory traversal"""
        # Remove any path traversal attempts
        sanitized = os.path.normpath(file_path)
        
        # Remove leading directory separators
        sanitized = sanitized.lstrip(os.sep)
        
        # Validate no parent directory access
        if '..' in sanitized:
            raise SecurityError("Parent directory access not allowed")
        
        return sanitized

class DataSecurityValidator:
    """Validates data for security issues"""
    
    def scan_data_file(self, file_path: str) -> SecurityScanResult:
        """Scan data file for security issues"""
        issues = []
        
        # Check file size (prevent DoS through large files)
        file_size = os.path.getsize(file_path)
        max_size = 10 * 1024 * 1024 * 1024  # 10GB limit
        
        if file_size > max_size:
            issues.append(f"File size {file_size} exceeds limit {max_size}")
        
        # Check file type
        if not file_path.endswith('.parquet'):
            issues.append("Only Parquet files are allowed")
        
        # Validate file structure
        try:
            import pyarrow.parquet as pq
            pq.ParquetFile(file_path)
        except Exception as e:
            issues.append(f"Invalid Parquet file: {e}")
        
        return SecurityScanResult(
            is_safe=len(issues) == 0,
            issues=issues
        )

class AuditLogger:
    """Comprehensive audit logging"""
    
    def __init__(self, log_file: str = 'logs/audit.log'):
        self.log_file = log_file
        self.logger = self._setup_logger()
    
    def log_access(self, user_id: str, resource: str, result: str):
        """Log data access attempts"""
        self.logger.info(f"ACCESS|{user_id}|{resource}|{result}")
    
    def log_operation(self, user_id: str, operation: str, details: Dict[str, Any]):
        """Log system operations"""
        details_str = json.dumps(details)
        self.logger.info(f"OPERATION|{user_id}|{operation}|{details_str}")
    
    def log_security_event(self, event_type: str, details: str):
        """Log security-related events"""
        self.logger.warning(f"SECURITY|{event_type}|{details}")
```

### Configuration Security

```python
class SecureConfigManager:
    """Secure configuration management with encryption"""
    
    def __init__(self, encryption_key: Optional[str] = None):
        self.encryption_key = encryption_key or self._get_default_key()
        self.fernet = Fernet(self.encryption_key.encode() if isinstance(self.encryption_key, str) else self.encryption_key)
    
    def _get_default_key(self) -> str:
        """Get encryption key from environment or generate"""
        key = os.getenv('STRATEGY_LAB_ENCRYPTION_KEY')
        if not key:
            # Generate and save key for development
            key = Fernet.generate_key().decode()
            logger.warning("Generated new encryption key. Set STRATEGY_LAB_ENCRYPTION_KEY in production")
        return key
    
    def encrypt_sensitive_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt sensitive configuration values"""
        sensitive_keys = ['api_keys', 'passwords', 'tokens', 'connection_strings']
        
        encrypted_config = config.copy()
        
        for key in sensitive_keys:
            if key in config:
                value = json.dumps(config[key])
                encrypted_value = self.fernet.encrypt(value.encode()).decode()
                encrypted_config[key] = f"encrypted:{encrypted_value}"
        
        return encrypted_config
    
    def decrypt_sensitive_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt sensitive configuration values"""
        decrypted_config = config.copy()
        
        for key, value in config.items():
            if isinstance(value, str) and value.startswith('encrypted:'):
                encrypted_data = value[10:]  # Remove 'encrypted:' prefix
                decrypted_data = self.fernet.decrypt(encrypted_data.encode()).decode()
                decrypted_config[key] = json.loads(decrypted_data)
        
        return decrypted_config

class AccessController:
    """Simple access control for application resources"""
    
    def __init__(self):
        self.permissions = {
            'data_read': ['user', 'admin'],
            'data_write': ['admin'],
            'config_read': ['user', 'admin'],
            'config_write': ['admin'],
            'system_admin': ['admin']
        }
    
    def check_permission(self, user_role: str, action: str) -> bool:
        """Check if user role has permission for action"""
        allowed_roles = self.permissions.get(action, [])
        return user_role in allowed_roles
    
    def require_permission(self, user_role: str, action: str):
        """Decorator to require specific permission"""
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                if not self.check_permission(user_role, action):
                    raise PermissionError(f"Role '{user_role}' lacks permission for '{action}'")
                return func(*args, **kwargs)
            return wrapper
        return decorator
```

### Input Validation and Sanitization

```python
class InputValidator:
    """Comprehensive input validation"""
    
    @staticmethod
    def validate_date_string(date_str: str) -> bool:
        """Validate date string format"""
        try:
            pd.Timestamp(date_str)
            return True
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_strategy_name(name: str) -> bool:
        """Validate strategy name for security"""
        # Only allow alphanumeric and underscores
        import re
        pattern = r'^[a-zA-Z0-9_]+$'
        return bool(re.match(pattern, name)) and len(name) <= 50
    
    @staticmethod
    def validate_file_path(path: str) -> bool:
        """Validate file path for security"""
        # Prevent directory traversal
        if '..' in path or path.startswith('/'):
            return False
        
        # Must be within data directory
        normalized = os.path.normpath(path)
        return normalized.startswith('data/') or normalized.startswith('./data/')
    
    @staticmethod
    def sanitize_string_input(input_str: str, max_length: int = 255) -> str:
        """Sanitize string input"""
        if not isinstance(input_str, str):
            raise ValueError("Input must be string")
        
        # Truncate if too long
        sanitized = input_str[:max_length]
        
        # Remove potentially dangerous characters
        dangerous_chars = ['<', '>', '"', "'", '&', '\x00']
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')
        
        return sanitized.strip()
```

### Error Handling Security

```python
class SecureErrorHandler:
    """Secure error handling that doesn't leak sensitive information"""
    
    def __init__(self, debug_mode: bool = False):
        self.debug_mode = debug_mode
        self.audit_logger = AuditLogger()
    
    def handle_error(self, error: Exception, context: str) -> str:
        """Handle errors securely"""
        # Log full error details for debugging
        error_id = str(uuid.uuid4())
        self.audit_logger.log_security_event(
            'ERROR',
            f"ID:{error_id}|Context:{context}|Error:{str(error)}"
        )
        
        # Return sanitized error message
        if self.debug_mode:
            return f"Error {error_id}: {str(error)}"
        else:
            # Generic error message for production
            error_type = type(error).__name__
            return f"An error occurred (ID: {error_id}). Error type: {error_type}"
    
    def safe_file_error(self, file_path: str, error: Exception) -> str:
        """Handle file-related errors without exposing paths"""
        if self.debug_mode:
            return f"File error: {file_path} - {str(error)}"
        else:
            return "File operation failed. Check logs for details."
```