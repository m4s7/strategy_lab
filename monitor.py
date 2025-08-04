#!/usr/bin/env python3
"""
Basic monitoring script for Strategy Lab production deployment
"""

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
            format="%(asctime)s - MONITOR - %(levelname)s - %(message)s",
            handlers=[logging.FileHandler(self.log_file), logging.StreamHandler()],
        )
        self.logger = logging.getLogger(__name__)

    def check_system_resources(self):
        """Monitor system resources"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        self.logger.info(f"CPU Usage: {cpu_percent:.1f}%")
        self.logger.info(
            f"Memory Usage: {memory.percent:.1f}% ({memory.used/1024**3:.1f}GB/{memory.total/1024**3:.1f}GB)"
        )
        self.logger.info(
            f"Disk Usage: {disk.percent:.1f}% ({disk.used/1024**3:.1f}GB/{disk.total/1024**3:.1f}GB)"
        )

        # Check for alerts
        if cpu_percent > 90:
            self.logger.warning(f"HIGH CPU USAGE: {cpu_percent:.1f}%")
        if memory.percent > 80:
            self.logger.warning(f"HIGH MEMORY USAGE: {memory.percent:.1f}%")
        if disk.percent > 85:
            self.logger.warning(f"HIGH DISK USAGE: {disk.percent:.1f}%")

    def check_strategy_lab_processes(self):
        """Check for running Strategy Lab processes"""
        processes = []
        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                if "strategy-lab" in " ".join(proc.info["cmdline"] or []):
                    processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        if processes:
            self.logger.info(f"Found {len(processes)} Strategy Lab processes running")
        else:
            self.logger.info("No Strategy Lab processes currently running")

    def run_health_check(self):
        """Run complete health check"""
        self.logger.info("=== Strategy Lab Health Check ===")
        self.check_system_resources()
        self.check_strategy_lab_processes()
        self.logger.info("=== Health Check Complete ===\n")


if __name__ == "__main__":
    monitor = StrategyLabMonitor()
    monitor.run_health_check()
