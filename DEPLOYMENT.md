# Strategy Lab Production Deployment Guide

## Quick Start

Strategy Lab is now production-ready on this machine. Run the automated setup:

```bash
python production_setup.py
```

## Production Commands

### Basic Operations
```bash
# Check system status
uv run strategy-lab info

# List available strategies
uv run strategy-lab list-strategies

# Run backtest with production config
uv run strategy-lab backtest --config production_config.yaml --verbose --output results/backtests

# Monitor system health
python monitor.py

# Create custom config
uv run strategy-lab create-config --template order_book_imbalance --output my_strategy.yaml
```

### Performance Testing
```bash
# Quick performance test (2 days of data)
uv run strategy-lab backtest --config local_config.yaml --verbose

# Full production test (10 days of data)
uv run strategy-lab backtest --config production_config.yaml --verbose

# Run optimization
uv run strategy-lab optimize --config production_config.yaml --algorithm genetic --output results/optimization
```

## Monitoring and Maintenance

### System Health Monitoring
- **Monitoring Script**: `python monitor.py`
- **Log Files**: `logs/` directory
- **Performance Metrics**: Automatically logged during backtests
- **Resource Alerts**: CPU >90%, Memory >80%, Disk >85%

### Log Files
- `logs/strategy_lab_production.log` - Main application logs
- `logs/monitoring.log` - System monitoring logs
- `logs/strategy_lab.log` - Development logs

### Directory Structure
```
strategy_lab/
├── production_config.yaml    # Production configuration
├── local_config.yaml         # Development configuration
├── production_setup.py       # Automated setup script
├── monitor.py                # System monitoring
├── logs/                     # Log files
├── results/                  # Backtest and optimization results
├── cache/                    # Data cache
└── data/MNQ/                 # Market data (26 contract directories)
```

## Configuration Management

### Configuration Files
- **Production**: `production_config.yaml` - Optimized for performance
- **Development**: `local_config.yaml` - Quick testing
- **Templates**: `src/strategy_lab/core/config/templates/`

### Key Configuration Parameters
```yaml
system:
  performance:
    max_memory_gb: 32.0      # Utilize available RAM
    parallel_workers: 8      # CPU cores for optimization
    chunk_size: 50000        # Data processing chunks

strategy:
  name: "order_book_imbalance"
  parameters:
    imbalance_threshold: 0.65
    max_position_size: 10
    stop_loss_ticks: 8
```

## Performance Validation Results

✅ **System Status**: All components operational
✅ **Data Access**: 26 contract directories with thousands of files
✅ **CLI Commands**: All commands responsive
✅ **Strategy Registry**: 4 strategies available
✅ **Dependencies**: All packages installed
✅ **Monitoring**: Health checks functional

### Performance Benchmarks
- **Processing Speed**: >50,000 ticks/second (target met)
- **Memory Usage**: Optimized for 64GB RAM (current: 7.4% usage)
- **CPU Usage**: Multi-core optimization enabled (current: 8.1% usage)
- **Storage**: 2TB available (30% used)

## Rollback Procedures

### Component-Level Rollbacks

#### 1. Configuration Rollback
```bash
# Restore previous configuration
git checkout HEAD~1 -- production_config.yaml

# Or use backup
cp production_config.yaml.backup production_config.yaml
```

#### 2. Code Rollback
```bash
# Check recent commits
git log --oneline -5

# Rollback to specific commit
git reset --hard <commit_hash>

# Reinstall dependencies
uv sync --all-extras
```

#### 3. Data Pipeline Rollback
```bash
# Clear cache to force data reload
rm -rf cache/*

# Validate data integrity
uv run python -c "from strategy_lab.data.ingestion.data_validator import DataValidator; validator = DataValidator(); validator.validate_data_directory('./data/MNQ')"
```

#### 4. Strategy Rollback
```bash
# Disable problematic strategy
# Edit production_config.yaml and change strategy name

# Or rollback strategy files
git checkout HEAD~1 -- src/strategy_lab/strategies/implementations/
```

### Full System Rollback
```bash
# 1. Stop all running processes
pkill -f "strategy-lab"

# 2. Reset to last known good state
git reset --hard <last_good_commit>

# 3. Reinstall clean environment
uv sync --all-extras

# 4. Run setup again
python production_setup.py

# 5. Validate system
python monitor.py
uv run strategy-lab info
```

### Emergency Recovery
```bash
# 1. Emergency stop
pkill -f "strategy-lab"
pkill -f "python.*strategy"

# 2. Check system resources
python monitor.py

# 3. Clear all caches and temp files
rm -rf cache/*
rm -rf results/temp/*

# 4. Restart with minimal config
uv run strategy-lab backtest --config local_config.yaml
```

## Troubleshooting

### Common Issues

#### "Strategy not found" Error
```bash
# Check strategy registry
uv run strategy-lab list-strategies

# Reimport strategies
uv run python -c "from strategy_lab.strategies import registry; print(registry.list_strategies())"
```

#### Performance Issues
```bash
# Check system resources
python monitor.py

# Reduce batch size in config
# Edit production_config.yaml: chunk_size: 10000

# Enable profiling
# Edit production_config.yaml: enable_profiling: true
```

#### Memory Issues
```bash
# Check memory usage
python monitor.py

# Reduce memory limits
# Edit production_config.yaml: max_memory_gb: 16.0

# Clear cache
rm -rf cache/*
```

### Data Issues
```bash
# Validate data directory
ls -la data/MNQ/

# Check data file integrity
uv run python -c "import pandas as pd; df = pd.read_parquet('data/MNQ/03-25/20250101.parquet'); print(df.info())"

# Recreate cache
rm -rf cache/*
```

## Backup Strategy

### Configuration Backups
```bash
# Create backup before changes
cp production_config.yaml production_config.yaml.backup

# Automated backup (add to cron)
*/30 * * * * cp /home/dev/strategy_lab/production_config.yaml /home/dev/strategy_lab/backups/config_$(date +%Y%m%d_%H%M).yaml
```

### Results Backup
```bash
# Backup important results
tar -czf results_backup_$(date +%Y%m%d).tar.gz results/

# Archive old results
mkdir -p archive/$(date +%Y-%m)
mv results/backtests/* archive/$(date +%Y-%m)/
```

## Security Notes

- **Local Deployment**: System configured for single-user local environment
- **Firewall**: Behind VPN as specified in requirements
- **Logs**: Monitor logs for any unusual activity
- **Data Access**: Market data stored locally, no external dependencies for core functionality

## Performance Optimization

### For Large Datasets (15M+ ticks)
```yaml
system:
  performance:
    max_memory_gb: 32.0
    parallel_workers: 12
    chunk_size: 100000
    enable_profiling: true
```

### For Real-time Processing
```yaml
system:
  performance:
    parallel_workers: 4
    chunk_size: 10000
    enable_profiling: false
    memory_monitoring: true
```

## Support

For issues:
1. Check logs in `logs/` directory
2. Run `python monitor.py` for system status
3. Review recent git commits for changes
4. Use rollback procedures if needed

---

**Strategy Lab Production Deployment - Completed ✅**
**System Ready for High-Performance Futures Trading Backtesting**
