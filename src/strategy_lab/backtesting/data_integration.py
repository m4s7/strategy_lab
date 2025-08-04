"""Data pipeline integration for backtest engine."""

import logging
from typing import Any

from strategy_lab.data.pipeline import TickDataStream

from .engine.config import BacktestConfig

logger = logging.getLogger(__name__)


class BacktestDataProvider:
    """Provides data streaming interface for backtest engine."""

    def __init__(self, config: BacktestConfig):
        """Initialize data provider with backtest configuration.

        Args:
            config: Backtest configuration containing data settings
        """
        self.config = config
        self.data_stream = TickDataStream(
            data_path=config.data.data_path,
            contracts=config.data.contracts,
            start_date=config.execution.start_date,
            end_date=config.execution.end_date,
            chunk_size=config.data.chunk_size,
            memory_limit_mb=config.data.memory_limit_mb,
            validate_data=config.data.validate_data,
        )

    def initialize(self) -> dict[str, Any]:
        """Initialize data provider and validate configuration.

        Returns:
            Dictionary with initialization stats

        Raises:
            RuntimeError: If initialization fails
        """
        logger.info("Initializing backtest data provider...")

        try:
            # Discover and validate files
            files = self.data_stream.discover_files()

            if self.config.data.validate_data:
                validation_results = self.data_stream.validate_files()
                failed_files = [
                    path
                    for path, result in validation_results.items()
                    if not result.is_valid
                ]
                if failed_files:
                    logger.warning(
                        f"Found {len(failed_files)} files with validation issues"
                    )

            # Get data statistics
            stats = self.data_stream.get_stats()

            logger.info(
                f"Data provider initialized: {len(files)} files, "
                f"{stats['total_size_gb']:.2f} GB"
            )

            return {
                "files_discovered": len(files),
                "total_size_gb": stats["total_size_gb"],
                "date_range": stats["date_range"],
                "contracts": stats["available_contracts"],
                "filtered_contracts": stats["filter_contracts"],
            }

        except Exception as e:
            logger.error(f"Failed to initialize data provider: {e}")
            raise RuntimeError(f"Data provider initialization failed: {e}") from e

    def get_data_stream(self) -> TickDataStream:
        """Get the tick data stream for backtesting.

        Returns:
            TickDataStream instance
        """
        return self.data_stream

    def get_data_info(self) -> dict[str, Any]:
        """Get information about available data.

        Returns:
            Dictionary with data information
        """
        stats: dict[str, Any] = self.data_stream.get_stats()
        return stats

    def validate_date_range(self) -> tuple[bool, str]:
        """Validate that requested date range has data available.

        Returns:
            Tuple of (is_valid, message)
        """
        try:
            available_start, available_end = self.data_stream.get_date_range()

            requested_start = self.config.execution.start_date
            requested_end = self.config.execution.end_date

            if requested_start and requested_start < available_start:
                return False, (
                    f"Requested start date {requested_start} is before available data "
                    f"starts at {available_start}"
                )

            if requested_end and requested_end > available_end:
                return False, (
                    f"Requested end date {requested_end} is after available data "
                    f"ends at {available_end}"
                )

            return True, "Date range is valid"

        except Exception as e:
            return False, f"Failed to validate date range: {e}"

    def validate_contracts(self) -> tuple[bool, str]:
        """Validate that requested contracts are available.

        Returns:
            Tuple of (is_valid, message)
        """
        try:
            available_contracts = self.data_stream.get_available_contracts()
            requested_contracts = self.config.data.contracts

            if not requested_contracts:
                return True, f"Using all available contracts: {available_contracts}"

            missing_contracts = set(requested_contracts) - set(available_contracts)
            if missing_contracts:
                return False, (
                    f"Requested contracts not available: {missing_contracts}. "
                    f"Available: {available_contracts}"
                )

            return True, f"All requested contracts are available: {requested_contracts}"

        except Exception as e:
            return False, f"Failed to validate contracts: {e}"
