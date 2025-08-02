# Strategy Lab Technical Architecture - Configuration & Deployment

## Configuration Management Architecture

The configuration system provides hierarchical, type-safe configuration management with environment-specific overrides and validation.

### Hierarchical Configuration System

```python
class ConfigurationManager:
    """Hierarchical configuration management"""
    
    def __init__(self, config_dirs: List[str]):
        self.config_dirs = [Path(d) for d in config_dirs]
        self.configs = {}
        self.watchers = {}
        self._load_all_configs()
    
    def get_config(self, 
                   config_name: str,
                   environment: str = 'default') -> Configuration:
        """Get configuration with environment overrides"""
        base_config = self._load_base_config(config_name)
        env_config = self._load_env_config(config_name, environment)
        
        # Merge configurations
        merged = self._deep_merge(base_config, env_config)
        
        # Validate
        validated = self._validate_config(merged, config_name)
        
        return Configuration(validated)
    
    def _load_base_config(self, config_name: str) -> Dict[str, Any]:
        """Load base configuration file"""
        for config_dir in self.config_dirs:
            config_file = config_dir / f"{config_name}.yaml"
            if config_file.exists():
                return self._load_yaml(config_file)
        
        raise ConfigurationError(f"Configuration not found: {config_name}")
    
    def _load_env_config(self, 
                        config_name: str, 
                        environment: str) -> Dict[str, Any]:
        """Load environment-specific overrides"""
        for config_dir in self.config_dirs:
            env_file = config_dir / f"{config_name}.{environment}.yaml"
            if env_file.exists():
                return self._load_yaml(env_file)
        
        return {}  # No environment overrides
    
    def watch_config(self, 
                    config_name: str,
                    callback: Callable[[Configuration], None]):
        """Watch configuration file for changes"""
        # Implementation would use file system watching
        pass
```

### Configuration Schema Validation

```python
from pydantic import BaseModel, Field
from typing import Optional, Union

class SystemConfiguration(BaseModel):
    """System-level configuration schema"""
    
    class LoggingConfig(BaseModel):
        level: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
        file: Optional[str] = None
        max_size_mb: int = Field(default=100, gt=0)
        backup_count: int = Field(default=5, ge=0)
    
    class ResourceConfig(BaseModel):
        max_memory_gb: int = Field(default=32, gt=0)
        max_cpu_cores: int = Field(default=16, gt=0)
        chunk_size: int = Field(default=1_000_000, gt=0)
    
    logging: LoggingConfig = LoggingConfig()
    resources: ResourceConfig = ResourceConfig()
    debug_mode: bool = False

class DataConfiguration(BaseModel):
    """Data processing configuration schema"""
    
    class ValidationConfig(BaseModel):
        strict_mode: bool = True
        max_missing_ratio: float = Field(default=0.01, ge=0, le=1)
        timestamp_tolerance_ns: int = Field(default=1000, ge=0)
    
    class CacheConfig(BaseModel):
        enabled: bool = True
        size_limit_gb: int = Field(default=10, gt=0)
        memory_cache_size: int = Field(default=128, gt=0)
    
    base_path: str = Field(default="./data/MNQ")
    validation: ValidationConfig = ValidationConfig()
    cache: CacheConfig = CacheConfig()

class BacktestConfiguration(BaseModel):
    """Backtesting configuration schema"""
    
    initial_balance: float = Field(default=100_000, gt=0)
    commission: float = Field(default=2.50, ge=0)
    slippage_ticks: float = Field(default=0.0, ge=0)
    
    class LatencyConfig(BaseModel):
        order_latency_ns: int = Field(default=1_000_000, ge=0)
        market_data_latency_ns: int = Field(default=500_000, ge=0)
        jitter_ns: int = Field(default=100_000, ge=0)
    
    latency: LatencyConfig = LatencyConfig()
```

### Configuration File Examples

```yaml
# config/default.yaml
system:
  logging:
    level: INFO
    file: logs/strategy_lab.log
    max_size_mb: 100
    backup_count: 5
  
  resources:
    max_memory_gb: 32
    max_cpu_cores: 16
    chunk_size: 1000000
  
  debug_mode: false

data:
  base_path: "./data/MNQ"
  
  validation:
    strict_mode: true
    max_missing_ratio: 0.01
    timestamp_tolerance_ns: 1000
  
  cache:
    enabled: true
    size_limit_gb: 10
    memory_cache_size: 128

backtesting:
  initial_balance: 100000
  commission: 2.50
  slippage_ticks: 0.0
  
  latency:
    order_latency_ns: 1000000
    market_data_latency_ns: 500000
    jitter_ns: 100000

optimization:
  default_algorithm: grid_search
  max_parallel_jobs: 16
  timeout_hours: 24
  
  grid_search:
    max_combinations: 10000
    adaptive_refinement: true
  
  genetic:
    population_size: 50
    generations: 100
    mutation_rate: 0.1
    crossover_rate: 0.8
    elite_size: 5
  
  walk_forward:
    in_sample_days: 252
    out_sample_days: 63
    step_days: 21
```

```yaml
# config/strategies/orderbook_imbalance.yaml
strategy:
  name: orderbook_imbalance
  description: "Order book imbalance-based scalping strategy"
  requires_l2_data: true
  
parameters:
  imbalance_threshold:
    default: 0.6
    min: 0.3
    max: 0.8
    step: 0.05
    description: "Minimum imbalance ratio to trigger trade"
  
  min_spread:
    default: 0.25
    min: 0.1
    max: 1.0
    step: 0.05
    description: "Minimum spread required for trade"
  
  position_size:
    default: 1
    min: 1
    max: 5
    step: 1
    description: "Number of contracts per trade"

risk_management:
  max_position: 3
  stop_loss_ticks: 4
  profit_target_ticks: 2
  max_daily_loss: 1000

execution:
  order_type: "LIMIT"
  urgency: "normal"  # passive, normal, aggressive
  timeout_seconds: 30

optimization:
  preferred_metrics: ["sharpe_ratio", "calmar_ratio"]
  include_parameters: ["imbalance_threshold", "min_spread"]
  exclude_parameters: ["position_size"]
```

## Environment Management

### Environment Configuration

```python
class EnvironmentManager:
    """Manages different deployment environments"""
    
    ENVIRONMENTS = {
        'development': {
            'debug_mode': True,
            'logging_level': 'DEBUG',
            'data_validation': 'strict',
            'cache_enabled': True
        },
        'testing': {
            'debug_mode': True,
            'logging_level': 'INFO',
            'data_validation': 'strict',
            'cache_enabled': False
        },
        'production': {
            'debug_mode': False,
            'logging_level': 'INFO',
            'data_validation': 'normal',
            'cache_enabled': True
        }
    }
    
    def __init__(self, environment: str = None):
        self.environment = environment or os.getenv('STRATEGY_LAB_ENV', 'development')
        self.config = self._build_environment_config()
    
    def _build_environment_config(self) -> Dict[str, Any]:
        """Build configuration for current environment"""
        if self.environment not in self.ENVIRONMENTS:
            raise ValueError(f"Unknown environment: {self.environment}")
        
        env_config = self.ENVIRONMENTS[self.environment].copy()
        
        # Add environment-specific overrides from environment variables
        env_overrides = self._get_env_overrides()
        env_config.update(env_overrides)
        
        return env_config
    
    def _get_env_overrides(self) -> Dict[str, Any]:
        """Get configuration overrides from environment variables"""
        overrides = {}
        
        # Map environment variables to config keys
        env_map = {
            'STRATEGY_LAB_DEBUG': ('debug_mode', lambda x: x.lower() == 'true'),
            'STRATEGY_LAB_LOG_LEVEL': ('logging_level', str),
            'STRATEGY_LAB_DATA_PATH': ('data_path', str),
            'STRATEGY_LAB_MAX_MEMORY_GB': ('max_memory_gb', int),
            'STRATEGY_LAB_MAX_CORES': ('max_cpu_cores', int)
        }
        
        for env_var, (config_key, converter) in env_map.items():
            value = os.getenv(env_var)
            if value is not None:
                try:
                    overrides[config_key] = converter(value)
                except ValueError as e:
                    logger.warning(f"Invalid environment variable {env_var}={value}: {e}")
        
        return overrides
```

## Command Line Interface

### CLI Application Structure

```python
import click
from src.core.config import ConfigurationManager
from src.backtesting.engine import BacktestingEngine
from src.strategies.registry import strategy_registry

@click.group()
@click.option('--config-dir', default='config', help='Configuration directory')
@click.option('--env', default='development', help='Environment (development/testing/production)')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.pass_context
def cli(ctx, config_dir, env, verbose):
    """Strategy Lab - Futures Trading Backtesting Framework"""
    ctx.ensure_object(dict)
    
    # Initialize configuration
    config_manager = ConfigurationManager([config_dir])
    ctx.obj['config_manager'] = config_manager
    ctx.obj['environment'] = env
    ctx.obj['verbose'] = verbose
    
    # Setup logging
    setup_logging(verbose)

@cli.command()
@click.option('--strategy', required=True, help='Strategy name')
@click.option('--start-date', required=True, help='Start date (YYYY-MM-DD)')
@click.option('--end-date', required=True, help='End date (YYYY-MM-DD)')
@click.option('--config-file', help='Strategy configuration file')
@click.option('--output-dir', default='results', help='Output directory')
@click.pass_context
def backtest(ctx, strategy, start_date, end_date, config_file, output_dir):
    """Run single strategy backtest"""
    try:
        # Load configuration
        config_manager = ctx.obj['config_manager']
        backtest_config = config_manager.get_config('backtest', ctx.obj['environment'])
        
        # Load strategy configuration
        if config_file:
            strategy_config = config_manager.load_file(config_file)
        else:
            strategy_config = config_manager.get_config(f'strategies/{strategy}')
        
        # Run backtest
        engine = BacktestingEngine(backtest_config)
        strategy_instance = strategy_registry.get_strategy(strategy, strategy_config)
        
        engine.setup_engine(data_path, strategy_instance, start_date, end_date)
        results = engine.run_backtest()
        
        # Save results
        output_path = Path(output_dir) / f"{strategy}_{start_date}_{end_date}.json"
        results.save(output_path)
        
        click.echo(f"Backtest completed. Results saved to {output_path}")
        click.echo(f"Total PnL: ${results.performance_metrics.total_pnl:,.2f}")
        click.echo(f"Win Rate: {results.performance_metrics.win_rate:.1%}")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()

@cli.command()
@click.option('--strategy', required=True, help='Strategy name')
@click.option('--algorithm', type=click.Choice(['grid_search', 'genetic', 'adaptive']), 
              default='grid_search', help='Optimization algorithm')
@click.option('--metric', default='sharpe_ratio', help='Optimization metric')
@click.option('--max-jobs', type=int, help='Maximum parallel jobs')
@click.pass_context
def optimize(ctx, strategy, algorithm, metric, max_jobs):
    """Run strategy parameter optimization"""
    # Implementation for optimization command
    pass

@cli.command()
@click.option('--strategy', required=True, help='Strategy name')
@click.option('--in-sample-days', default=252, help='In-sample period (days)')
@click.option('--out-sample-days', default=63, help='Out-of-sample period (days)')
@click.option('--step-days', default=21, help='Step size (days)')
@click.pass_context
def walk_forward(ctx, strategy, in_sample_days, out_sample_days, step_days):
    """Run walk-forward analysis"""
    # Implementation for walk-forward analysis
    pass

@cli.group()
def config():
    """Configuration management commands"""
    pass

@config.command('validate')
@click.argument('config_file')
def validate_config(config_file):
    """Validate configuration file"""
    try:
        config_manager = ConfigurationManager(['config'])
        config_data = config_manager.load_file(config_file)
        
        # Validate based on file type
        if 'strategy' in config_data:
            # Validate strategy config
            result = validate_strategy_config(config_data)
        else:
            # Validate system config
            result = validate_system_config(config_data)
        
        if result.is_valid:
            click.echo("✅ Configuration is valid")
        else:
            click.echo("❌ Configuration validation failed:")
            for error in result.errors:
                click.echo(f"  - {error}")
                
    except Exception as e:
        click.echo(f"Error validating configuration: {e}", err=True)

if __name__ == '__main__':
    cli()
```

## Deployment Architecture

### Docker Configuration

```dockerfile
# Dockerfile
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libc6-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager
RUN pip install uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install Python dependencies
RUN uv sync --frozen

# Copy source code
COPY src/ src/
COPY config/ config/
COPY docs/ docs/

# Create required directories
RUN mkdir -p data/MNQ logs results cache

# Set environment variables
ENV PYTHONPATH=/app/src
ENV STRATEGY_LAB_ENV=production
ENV STRATEGY_LAB_CONFIG_DIR=/app/config

# Create non-root user
RUN useradd --create-home --shell /bin/bash strategylab
RUN chown -R strategylab:strategylab /app
USER strategylab

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -m src.cli.main config validate config/default.yaml || exit 1

# Default command
ENTRYPOINT ["python", "-m", "src.cli.main"]
CMD ["--help"]
```

### Docker Compose for Development

```yaml
# docker-compose.yml
version: '3.8'

services:
  strategy-lab:
    build: .
    environment:
      - STRATEGY_LAB_ENV=development
      - STRATEGY_LAB_DEBUG=true
      - STRATEGY_LAB_LOG_LEVEL=DEBUG
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./results:/app/results
      - ./config:/app/config
    working_dir: /app
    command: ["--help"]
  
  strategy-lab-notebook:
    build: .
    ports:
      - "8888:8888"
    environment:
      - STRATEGY_LAB_ENV=development
    volumes:
      - ./:/app
      - ./notebooks:/app/notebooks
    working_dir: /app
    command: ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root"]
```

### Systemd Service Configuration

```ini
# /etc/systemd/system/strategy-lab.service
[Unit]
Description=Strategy Lab Backtesting Service
After=network.target

[Service]
Type=simple
User=strategylab
Group=strategylab
WorkingDirectory=/opt/strategy-lab
Environment=STRATEGY_LAB_ENV=production
Environment=STRATEGY_LAB_CONFIG_DIR=/opt/strategy-lab/config
Environment=PYTHONPATH=/opt/strategy-lab/src
ExecStart=/opt/strategy-lab/.venv/bin/python -m src.cli.main daemon
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

## Monitoring and Observability

### Application Metrics

```python
import time
from prometheus_client import Counter, Histogram, Gauge, start_http_server

class MetricsCollector:
    """Collect application metrics for monitoring"""
    
    def __init__(self):
        # Counters
        self.backtests_total = Counter('backtests_total', 'Total number of backtests run')
        self.optimizations_total = Counter('optimizations_total', 'Total optimizations run')
        self.errors_total = Counter('errors_total', 'Total errors', ['error_type'])
        
        # Histograms
        self.backtest_duration = Histogram('backtest_duration_seconds', 'Backtest execution time')
        self.data_load_duration = Histogram('data_load_duration_seconds', 'Data loading time')
        self.optimization_duration = Histogram('optimization_duration_seconds', 'Optimization time')
        
        # Gauges
        self.active_backtests = Gauge('active_backtests', 'Currently running backtests')
        self.memory_usage_bytes = Gauge('memory_usage_bytes', 'Current memory usage')
        self.cpu_usage_percent = Gauge('cpu_usage_percent', 'Current CPU usage')
    
    def start_metrics_server(self, port: int = 8000):
        """Start Prometheus metrics server"""
        start_http_server(port)
        logger.info(f"Metrics server started on port {port}")
    
    @contextmanager
    def time_backtest(self):
        """Context manager for timing backtests"""
        self.active_backtests.inc()
        start_time = time.time()
        
        try:
            with self.backtest_duration.time():
                yield
            self.backtests_total.inc()
        except Exception as e:
            self.errors_total.labels(error_type=type(e).__name__).inc()
            raise
        finally:
            self.active_backtests.dec()
    
    def update_system_metrics(self):
        """Update system resource metrics"""
        import psutil
        
        # Memory usage
        memory = psutil.virtual_memory()
        self.memory_usage_bytes.set(memory.used)
        
        # CPU usage
        cpu_percent = psutil.cpu_percent()
        self.cpu_usage_percent.set(cpu_percent)

# Global metrics instance
metrics = MetricsCollector()
```