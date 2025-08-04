#!/usr/bin/env python3
"""
Production Setup Script for Strategy Lab
Configures the system for production use on this machine.
"""

import os
import sys
from pathlib import Path
import subprocess
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ProductionSetup:
    """Handles production setup for Strategy Lab"""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.logs_dir = self.project_root / "logs"
        self.results_dir = self.project_root / "results"
        self.cache_dir = self.project_root / "cache"

    def setup_directories(self):
        """Create necessary directories"""
        logger.info("Setting up directory structure...")

        directories = [
            self.logs_dir,
            self.results_dir,
            self.cache_dir,
            self.results_dir / "backtests",
            self.results_dir / "optimization",
            self.results_dir / "reports",
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"✓ Created directory: {directory}")

    def check_dependencies(self):
        """Verify all dependencies are installed"""
        logger.info("Checking dependencies...")

        try:
            import strategy_lab

            logger.info("✓ Strategy Lab package available")
        except ImportError:
            logger.error("❌ Strategy Lab package not installed")
            return False

        try:
            result = subprocess.run(["uv", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"✓ uv package manager: {result.stdout.strip()}")
            else:
                logger.error("❌ uv package manager not available")
                return False
        except FileNotFoundError:
            logger.error("❌ uv package manager not found")
            return False

        return True

    def validate_data_access(self):
        """Check data directory accessibility"""
        logger.info("Validating data access...")

        data_path = self.project_root / "data" / "MNQ"
        if not data_path.exists():
            logger.warning(f"⚠️  Data directory not found: {data_path}")
            logger.info("Creating placeholder data structure...")
            data_path.mkdir(parents=True, exist_ok=True)
            return False

        # Check for contract data
        contracts_found = list(data_path.glob("*-*"))
        if contracts_found:
            logger.info(f"✓ Found {len(contracts_found)} contract directories")
            for contract in contracts_found[:3]:  # Show first 3
                files = list(contract.glob("*.parquet"))
                logger.info(f"  {contract.name}: {len(files)} files")
        else:
            logger.warning("⚠️  No contract data found")
            return False

        return True

    def create_production_config(self):
        """Create production configuration file"""
        logger.info("Creating production configuration...")

        config_content = """# Production Configuration for Strategy Lab
# Optimized for local deployment

system:
  version: "1.0.0"
  environment: "production"

  logging:
    level: "INFO"
    file: "logs/strategy_lab_production.log"
    console: true
    format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    max_size_mb: 100
    backup_count: 5

  performance:
    max_memory_gb: 32.0  # Utilize available RAM
    parallel_workers: 8  # Use more CPU cores
    chunk_size: 50000    # Larger chunks for efficiency
    enable_profiling: true
    memory_monitoring: true

  data:
    data_path: "./data/MNQ"
    cache_enabled: true
    cache_path: "./cache"
    preload_data: true
    validation_enabled: true

# Default strategy for production testing
strategy:
  name: "order_book_imbalance"
  parameters:
    imbalance_threshold: 0.65
    min_spread: 0.25
    max_position_size: 10
    stop_loss_ticks: 8
    take_profit_ticks: 4
    hold_time_seconds: 45

# Production backtesting configuration
backtesting:
  start_date: "2025-01-01T00:00:00"
  end_date: "2025-01-10T23:59:59"  # 10 days for comprehensive testing
  initial_capital: 100000
  commission: 2.00
  slippage: 0.25
  contracts: ["03-25"]

  engine:
    commission_rate: 0.001
    slippage_model: "linear"
    slippage_factor: 0.0001
    enable_shorting: true
    margin_requirement: 0.5

# Optimization configuration
optimization:
  method: "genetic"  # More efficient for production
  metric: "sharpe_ratio"
  direction: "maximize"
  max_iterations: 500
  parallel: true
  random_seed: 42

  # Performance constraints
  max_drawdown_limit: 0.15  # 15% max drawdown
  min_win_rate: 0.45        # 45% minimum win rate
  min_profit_factor: 1.2    # 1.2 minimum profit factor

# Monitoring and alerting
monitoring:
  enabled: true
  performance_tracking: true
  memory_alerts: true
  error_reporting: true

  alerts:
    max_memory_percent: 80
    max_cpu_percent: 90
    min_processing_speed: 50000  # ticks per second
"""

        config_path = self.project_root / "production_config.yaml"
        config_path.write_text(config_content)
        logger.info(f"✓ Production config created: {config_path}")

        return config_path

    def setup_monitoring(self):
        """Set up basic monitoring script"""
        logger.info("Setting up monitoring capabilities...")

        monitoring_script = """#!/usr/bin/env python3
'''
Basic monitoring script for Strategy Lab production deployment
'''

import psutil
import logging
import time
from pathlib import Path
from datetime import datetime

class StrategyLabMonitor:
    def __init__(self):
        self.log_file = Path("logs/monitoring.log")
        self.log_file.parent.mkdir(exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - MONITOR - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def check_system_resources(self):
        '''Monitor system resources'''
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        self.logger.info(f"CPU Usage: {cpu_percent:.1f}%")
        self.logger.info(f"Memory Usage: {memory.percent:.1f}% ({memory.used/1024**3:.1f}GB/{memory.total/1024**3:.1f}GB)")
        self.logger.info(f"Disk Usage: {disk.percent:.1f}% ({disk.used/1024**3:.1f}GB/{disk.total/1024**3:.1f}GB)")

        # Check for alerts
        if cpu_percent > 90:
            self.logger.warning(f"HIGH CPU USAGE: {cpu_percent:.1f}%")
        if memory.percent > 80:
            self.logger.warning(f"HIGH MEMORY USAGE: {memory.percent:.1f}%")
        if disk.percent > 85:
            self.logger.warning(f"HIGH DISK USAGE: {disk.percent:.1f}%")

    def check_strategy_lab_processes(self):
        '''Check for running Strategy Lab processes'''
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if 'strategy-lab' in ' '.join(proc.info['cmdline'] or []):
                    processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        if processes:
            self.logger.info(f"Found {len(processes)} Strategy Lab processes running")
        else:
            self.logger.info("No Strategy Lab processes currently running")

    def run_health_check(self):
        '''Run complete health check'''
        self.logger.info("=== Strategy Lab Health Check ===")
        self.check_system_resources()
        self.check_strategy_lab_processes()
        self.logger.info("=== Health Check Complete ===\\n")

if __name__ == "__main__":
    monitor = StrategyLabMonitor()
    monitor.run_health_check()
"""

        monitor_path = self.project_root / "monitor.py"
        monitor_path.write_text(monitoring_script)
        monitor_path.chmod(0o755)
        logger.info(f"✓ Monitoring script created: {monitor_path}")

        return monitor_path

    def run_performance_validation(self):
        """Run basic performance validation"""
        logger.info("Running performance validation...")

        try:
            # Test CLI accessibility
            result = subprocess.run(
                ["uv", "run", "strategy-lab", "info"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                logger.info("✓ CLI commands accessible")
            else:
                logger.warning("⚠️  CLI command issues detected")

            # Test strategy listing
            result = subprocess.run(
                ["uv", "run", "strategy-lab", "list-strategies"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0 and "order_book_imbalance" in result.stdout:
                logger.info("✓ Strategy registry functional")
            else:
                logger.warning("⚠️  Strategy registry issues detected")

        except subprocess.TimeoutExpired:
            logger.warning("⚠️  Commands taking longer than expected")
        except Exception as e:
            logger.error(f"❌ Performance validation failed: {e}")
            return False

        return True

    def run_setup(self):
        """Run complete production setup"""
        logger.info("Starting Strategy Lab Production Setup...")
        logger.info("=" * 60)

        steps = [
            ("Setting up directories", self.setup_directories),
            ("Checking dependencies", self.check_dependencies),
            ("Validating data access", self.validate_data_access),
            ("Creating production config", self.create_production_config),
            ("Setting up monitoring", self.setup_monitoring),
            ("Running performance validation", self.run_performance_validation),
        ]

        results = {}
        for step_name, step_func in steps:
            logger.info(f"\\n📋 {step_name}...")
            try:
                result = step_func()
                results[step_name] = result
                if result is not False:
                    logger.info(f"✅ {step_name} completed successfully")
                else:
                    logger.warning(f"⚠️  {step_name} completed with warnings")
            except Exception as e:
                logger.error(f"❌ {step_name} failed: {e}")
                results[step_name] = False

        # Summary
        logger.info("\\n" + "=" * 60)
        logger.info("PRODUCTION SETUP SUMMARY")
        logger.info("=" * 60)

        success_count = sum(1 for r in results.values() if r is not False)
        total_count = len(results)

        logger.info(f"Steps completed: {success_count}/{total_count}")

        for step, result in results.items():
            status = (
                "✅ PASS"
                if result is not False
                else ("⚠️  WARN" if result is False else "❌ FAIL")
            )
            logger.info(f"  {step}: {status}")

        if success_count == total_count:
            logger.info("\\n🎉 Strategy Lab is ready for production use!")
            logger.info("\\nNext steps:")
            logger.info(
                "  1. Run: uv run strategy-lab backtest --config production_config.yaml"
            )
            logger.info("  2. Monitor with: python monitor.py")
            logger.info("  3. Check logs in: logs/")
        elif success_count >= total_count - 1:
            logger.info("\\n✅ Strategy Lab is mostly ready - review warnings above")
        else:
            logger.warning(
                "\\n⚠️  Several issues detected - review and resolve before production use"
            )

        logger.info("=" * 60)


if __name__ == "__main__":
    setup = ProductionSetup()
    setup.run_setup()
