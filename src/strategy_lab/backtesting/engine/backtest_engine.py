"""Main backtest engine coordinating all components."""

import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from .config import BacktestConfig, ConfigTemplate
from .execution import BacktestExecutor, execute_backtest_parallel
from .execution_enhanced import EnhancedBacktestExecutor
from .results import BacktestResult, query_results, save_results

logger = logging.getLogger(__name__)


class BacktestStatus(Enum):
    """Backtest execution status."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass
class BacktestJob:
    """Represents a backtest job."""

    job_id: str
    config: BacktestConfig
    status: BacktestStatus = BacktestStatus.PENDING
    result: BacktestResult | None = None
    error: str | None = None


class BacktestEngine:
    """Main engine for managing backtest execution."""

    def __init__(self, output_dir: Path = Path("results")):
        """Initialize backtest engine.

        Args:
            output_dir: Default output directory for results
        """
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Job tracking
        self.jobs: dict[str, BacktestJob] = {}
        self._job_counter = 0

    def create_backtest(
        self, config: BacktestConfig | dict, validate: bool = True
    ) -> str:
        """Create a new backtest job.

        Args:
            config: Backtest configuration
            validate: Whether to validate configuration

        Returns:
            Job ID for the created backtest
        """
        # Convert dict to config if needed
        if isinstance(config, dict):
            config = BacktestConfig.from_dict(config)

        # Validate configuration
        if validate:
            errors = config.validate()
            if errors:
                raise ValueError(f"Invalid configuration: {', '.join(errors)}")

            # Validate data availability
            data_errors = self._validate_data_availability(config)
            if data_errors:
                raise ValueError(f"Data validation failed: {', '.join(data_errors)}")

        # Create job
        self._job_counter += 1
        job_id = f"job_{self._job_counter:05d}"

        job = BacktestJob(job_id=job_id, config=config, status=BacktestStatus.PENDING)

        self.jobs[job_id] = job
        logger.info(f"Created backtest job {job_id}")

        return job_id

    def run_backtest(self, job_id: str) -> BacktestResult:
        """Run a single backtest job.

        Args:
            job_id: Job ID to run

        Returns:
            BacktestResult
        """
        if job_id not in self.jobs:
            raise ValueError(f"Job {job_id} not found")

        job = self.jobs[job_id]

        if job.status != BacktestStatus.PENDING:
            raise ValueError(f"Job {job_id} is not pending (status: {job.status})")

        # Update status
        job.status = BacktestStatus.RUNNING
        logger.info(f"Running backtest job {job_id}")

        try:
            # Execute backtest
            executor = BacktestExecutor(job.config)
            result = executor.execute()

            # Save results
            if job.config.output_dir:
                save_results(result, job.config.output_dir)

            # Update job
            job.status = BacktestStatus.COMPLETED
            job.result = result

            logger.info(f"Completed backtest job {job_id}")
            return result

        except Exception as e:
            # Handle failure
            job.status = BacktestStatus.FAILED
            job.error = str(e)
            logger.error(f"Failed backtest job {job_id}: {e}")
            raise

    def run_parallel(
        self, configs: list[BacktestConfig], max_workers: int | None = None
    ) -> list[BacktestResult]:
        """Run multiple backtests in parallel.

        Args:
            configs: List of backtest configurations
            max_workers: Maximum parallel workers

        Returns:
            List of BacktestResult objects
        """
        # Create jobs for all configs
        job_ids = []
        for config in configs:
            job_id = self.create_backtest(config)
            job_ids.append(job_id)

        logger.info(f"Running {len(configs)} backtests in parallel")

        # Execute in parallel
        results = execute_backtest_parallel(configs, max_workers)

        # Update jobs with results
        for job_id, result in zip(job_ids, results, strict=False):
            job = self.jobs[job_id]
            job.status = BacktestStatus.COMPLETED
            job.result = result

            # Save results
            if job.config.output_dir:
                save_results(result, job.config.output_dir)

        logger.info(f"Completed {len(results)} parallel backtests")
        return results

    def get_job_status(self, job_id: str) -> BacktestStatus:
        """Get the status of a backtest job.

        Args:
            job_id: Job ID to check

        Returns:
            BacktestStatus
        """
        if job_id not in self.jobs:
            raise ValueError(f"Job {job_id} not found")

        return self.jobs[job_id].status

    def get_result(self, job_id: str) -> BacktestResult | None:
        """Get the result of a completed backtest.

        Args:
            job_id: Job ID

        Returns:
            BacktestResult or None if not completed
        """
        if job_id not in self.jobs:
            raise ValueError(f"Job {job_id} not found")

        return self.jobs[job_id].result

    def cancel_job(self, job_id: str) -> None:
        """Cancel a pending backtest job.

        Args:
            job_id: Job ID to cancel
        """
        if job_id not in self.jobs:
            raise ValueError(f"Job {job_id} not found")

        job = self.jobs[job_id]

        if job.status != BacktestStatus.PENDING:
            raise ValueError(f"Can only cancel pending jobs (status: {job.status})")

        job.status = BacktestStatus.CANCELLED
        logger.info(f"Cancelled backtest job {job_id}")

    def list_jobs(self, status: BacktestStatus | None = None) -> list[str]:
        """List all job IDs, optionally filtered by status.

        Args:
            status: Optional status filter

        Returns:
            List of job IDs
        """
        if status is None:
            return list(self.jobs.keys())

        return [job_id for job_id, job in self.jobs.items() if job.status == status]

    def load_historical_results(
        self, strategy_name: str | None = None, min_sharpe: float | None = None
    ) -> list[BacktestResult]:
        """Load historical backtest results.

        Args:
            strategy_name: Filter by strategy name
            min_sharpe: Minimum Sharpe ratio filter

        Returns:
            List of BacktestResult objects
        """
        return query_results(
            output_dir=self.output_dir,
            strategy_name=strategy_name,
            min_sharpe=min_sharpe,
        )

    def create_optimization_batch(
        self,
        strategy_name: str,
        strategy_module: str,
        param_grid: dict[str, list],
        base_config: BacktestConfig | None = None,
    ) -> list[str]:
        """Create a batch of backtests for parameter optimization.

        Args:
            strategy_name: Strategy name
            strategy_module: Strategy module path
            param_grid: Parameter grid for optimization
            base_config: Base configuration to use

        Returns:
            List of created job IDs
        """
        # Generate all parameter combinations
        import itertools

        param_names = list(param_grid.keys())
        param_values = list(param_grid.values())
        param_combinations = list(itertools.product(*param_values))

        job_ids = []

        for combination in param_combinations:
            # Create parameter dict
            params = dict(zip(param_names, combination, strict=False))

            # Create config
            if base_config:
                config = base_config.copy(deep=True)
                config.strategy.parameters.update(params)
            else:
                config = ConfigTemplate.optimization_config(
                    strategy_name=strategy_name,
                    strategy_module=strategy_module,
                    param_ranges=param_grid,
                )
                config.strategy.parameters = params

            # Add parameter info to name
            param_str = "_".join(f"{k}={v}" for k, v in params.items())
            config.name = f"{strategy_name}_opt_{param_str}"

            # Create job
            job_id = self.create_backtest(config)
            job_ids.append(job_id)

        logger.info(f"Created {len(job_ids)} optimization jobs")
        return job_ids

    def get_best_result(
        self, job_ids: list[str], metric: str = "sharpe_ratio"
    ) -> BacktestResult | None:
        """Get the best result from a list of jobs.

        Args:
            job_ids: List of job IDs to compare
            metric: Metric to optimize (default: sharpe_ratio)

        Returns:
            Best BacktestResult or None
        """
        best_result = None
        best_value = float("-inf")

        for job_id in job_ids:
            if job_id not in self.jobs:
                continue

            job = self.jobs[job_id]
            if job.status != BacktestStatus.COMPLETED or job.result is None:
                continue

            # Get metric value
            if hasattr(job.result, metric):
                value = getattr(job.result, metric)
            elif metric in job.result.custom_metrics:
                value = job.result.custom_metrics[metric]
            else:
                continue

            # Update best
            if value > best_value:
                best_value = value
                best_result = job.result

        return best_result

    def _validate_data_availability(self, config: BacktestConfig) -> list[str]:
        """Validate that data is available for the given configuration.

        Args:
            config: Backtest configuration to validate

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        try:
            from ..data_integration import BacktestDataProvider

            data_provider = BacktestDataProvider(config)

            # Validate date range
            date_valid, date_msg = data_provider.validate_date_range()
            if not date_valid:
                errors.append(date_msg)

            # Validate contracts
            contracts_valid, contracts_msg = data_provider.validate_contracts()
            if not contracts_valid:
                errors.append(contracts_msg)

            # Try to discover files to ensure data exists
            try:
                data_provider.initialize()
            except Exception as e:
                errors.append(f"Data initialization failed: {e}")

        except Exception as e:
            errors.append(f"Data validation error: {e}")

        return errors

    def get_data_info(self, config: BacktestConfig) -> dict[str, Any]:
        """Get information about available data for a configuration.

        Args:
            config: Backtest configuration

        Returns:
            Dictionary with data information
        """
        try:
            from ..data_integration import BacktestDataProvider

            data_provider = BacktestDataProvider(config)
            return data_provider.get_data_info()
        except Exception as e:
            logger.error(f"Failed to get data info: {e}")
            return {"error": str(e)}

    def create_backtest_with_data_stream(
        self, config: BacktestConfig
    ) -> tuple[str, Any]:
        """Create backtest with initialized data stream.

        Args:
            config: Backtest configuration

        Returns:
            Tuple of (job_id, data_provider)
        """
        from ..data_integration import BacktestDataProvider

        # Create the backtest job
        job_id = self.create_backtest(config, validate=True)

        # Initialize data provider
        data_provider = BacktestDataProvider(config)
        data_provider.initialize()

        return job_id, data_provider

    def run_enhanced_backtest(self, job_id: str) -> BacktestResult:
        """Run a backtest using the enhanced executor with data pipeline integration.

        Args:
            job_id: Job ID to run

        Returns:
            BacktestResult from enhanced execution
        """
        if job_id not in self.jobs:
            raise ValueError(f"Job {job_id} not found")

        job = self.jobs[job_id]

        if job.status != BacktestStatus.PENDING:
            raise ValueError(f"Job {job_id} is not pending (status: {job.status})")

        # Update status
        job.status = BacktestStatus.RUNNING
        logger.info(f"Running enhanced backtest job {job_id}")

        try:
            # Execute backtest with enhanced executor
            enhanced_executor = EnhancedBacktestExecutor(job.config)
            result = enhanced_executor.execute()

            # Save results
            if job.config.output_dir:
                save_results(result, job.config.output_dir)

            # Update job
            job.status = BacktestStatus.COMPLETED
            job.result = result

            logger.info(f"Completed enhanced backtest job {job_id}")
            return result

        except Exception as e:
            # Handle failure
            job.status = BacktestStatus.FAILED
            job.error = str(e)
            logger.error(f"Failed enhanced backtest job {job_id}: {e}")
            raise

    def run_backtest_with_data_pipeline(
        self, config: BacktestConfig, use_enhanced: bool = True
    ) -> BacktestResult:
        """Convenience method to run backtest with data pipeline integration.

        Args:
            config: Backtest configuration
            use_enhanced: Whether to use enhanced executor (default: True)

        Returns:
            BacktestResult
        """
        # Create and run job
        job_id = self.create_backtest(config, validate=True)

        if use_enhanced:
            return self.run_enhanced_backtest(job_id)
        return self.run_backtest(job_id)
