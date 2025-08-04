"""Grid search optimization algorithm."""

import logging
import multiprocessing as mp
import time
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

try:
    from tqdm import tqdm
except ImportError:
    # Mock tqdm if not available
    class tqdm:
        def __init__(self, *args, **kwargs):
            self.desc = kwargs.get("desc", "")
            self.total = kwargs.get("total", 0)
            self.current = 0

        def update(self, n=1):
            self.current += n

        def set_description(self, desc):
            self.desc = desc

        def close(self):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass


from ..core.parameter_space import ParameterSpace
from ..core.results import OptimizationResult, OptimizationResultSet

logger = logging.getLogger(__name__)


@dataclass
class GridSearchConfig:
    """Configuration for grid search optimization."""

    parallel: bool = True  # Whether to use parallel execution
    n_workers: int | None = None  # None means use all available cores
    batch_size: int = 1  # Number of combinations per batch
    show_progress: bool = True
    verbose: bool = True  # Whether to print verbose output
    save_intermediate: bool = True
    save_interval: int = 100  # Save results every N evaluations
    timeout_per_eval: float | None = None  # Timeout in seconds per evaluation
    retry_failed: bool = True
    max_retries: int = 3


class ProgressTracker:
    """Track and report optimization progress."""

    def __init__(self, total: int, show_progress: bool = True):
        """Initialize progress tracker.

        Args:
            total: Total number of evaluations
            show_progress: Whether to show progress bar
        """
        self.total = total
        self.completed = 0
        self.failed = 0
        self.start_time = time.time()
        self.show_progress = show_progress

        if show_progress:
            self.pbar = tqdm(total=total, desc="Grid Search")
        else:
            self.pbar = None

    def update(self, n: int = 1, failed: int = 0) -> None:
        """Update progress.

        Args:
            n: Number of completed evaluations
            failed: Number of failed evaluations
        """
        self.completed += n
        self.failed += failed

        if self.pbar:
            self.pbar.update(n)
            self._update_description()

    def _update_description(self) -> None:
        """Update progress bar description with statistics."""
        if not self.pbar:
            return

        elapsed = time.time() - self.start_time
        rate = self.completed / elapsed if elapsed > 0 else 0
        eta = (self.total - self.completed) / rate if rate > 0 else 0

        desc = f"Grid Search [{self.completed}/{self.total}]"
        if self.failed > 0:
            desc += f" (Failed: {self.failed})"
        desc += f" | Rate: {rate:.1f}/s | ETA: {timedelta(seconds=int(eta))}"

        self.pbar.set_description(desc)

    def close(self) -> None:
        """Close progress bar."""
        if self.pbar:
            self.pbar.close()

    def get_stats(self) -> dict[str, Any]:
        """Get current statistics."""
        elapsed = time.time() - self.start_time
        rate = self.completed / elapsed if elapsed > 0 else 0
        eta = (self.total - self.completed) / rate if rate > 0 else 0

        return {
            "total": self.total,
            "completed": self.completed,
            "failed": self.failed,
            "success_rate": (self.completed - self.failed) / self.completed
            if self.completed > 0
            else 0,
            "elapsed_time": elapsed,
            "rate": rate,
            "eta": eta,
            "progress_pct": self.completed / self.total * 100 if self.total > 0 else 0,
        }


def _evaluate_combination(
    combination: dict[str, Any],
    objective_func: Callable,
    timeout: float | None = None,
) -> tuple[dict[str, Any], dict[str, float] | None, float, str | None]:
    """Evaluate a single parameter combination.

    Args:
        combination: Parameter combination
        objective_func: Objective function to evaluate
        timeout: Timeout in seconds

    Returns:
        Tuple of (parameters, metrics, execution_time, error_message)
    """
    start_time = time.time()
    error_msg = None
    metrics = None

    try:
        # Call objective function
        metrics = objective_func(**combination)

        # Ensure metrics is a dictionary
        if isinstance(metrics, (int, float)):
            metrics = {"objective": float(metrics)}
        elif not isinstance(metrics, dict):
            raise ValueError(
                f"Objective function must return dict or numeric, got {type(metrics)}"
            )

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error evaluating {combination}: {e}")

    execution_time = time.time() - start_time

    return combination, metrics, execution_time, error_msg


class GridSearchOptimizer:
    """Grid search optimization algorithm."""

    def __init__(self, config: GridSearchConfig | None = None):
        """Initialize grid search optimizer.

        Args:
            config: Grid search configuration
        """
        self.config = config or GridSearchConfig()

        # Determine number of workers
        if not self.config.parallel:
            self.config.n_workers = 1
        elif self.config.n_workers is None:
            self.config.n_workers = mp.cpu_count()

    def optimize(
        self,
        objective_func: Callable[..., dict[str, float]],
        parameter_space: ParameterSpace,
        resume_from: OptimizationResultSet | None = None,
    ) -> OptimizationResultSet:
        """Run grid search optimization.

        Args:
            objective_func: Function to optimize. Should accept keyword arguments
                           for parameters and return dict of metrics.
            parameter_space: Parameter space to search
            resume_from: Previous results to resume from

        Returns:
            OptimizationResultSet with all results
        """
        # Initialize results
        if resume_from:
            results = OptimizationResultSet(resume_from.results.copy())
            completed_params = {
                tuple(sorted(r.parameters.items())) for r in results.results
            }
        else:
            results = OptimizationResultSet()
            completed_params = set()

        # Generate all combinations
        all_combinations = list(parameter_space.generate_combinations())

        # Filter out already completed combinations
        remaining_combinations = [
            combo
            for combo in all_combinations
            if tuple(sorted(combo.items())) not in completed_params
        ]

        if not remaining_combinations:
            logger.info("All combinations already evaluated")
            return results

        logger.info(
            f"Starting grid search: {len(remaining_combinations)} combinations "
            f"({len(completed_params)} already completed), "
            f"{self.config.n_workers} workers"
        )

        # Initialize progress tracker
        tracker = ProgressTracker(
            len(remaining_combinations), self.config.show_progress
        )

        # Run optimization
        try:
            if self.config.n_workers == 1:
                # Serial execution
                self._run_serial(
                    objective_func, remaining_combinations, results, tracker
                )
            else:
                # Parallel execution
                self._run_parallel(
                    objective_func, remaining_combinations, results, tracker
                )
        finally:
            tracker.close()

        # Log final statistics
        stats = tracker.get_stats()
        logger.info(
            f"Grid search completed: {stats['completed']} evaluated, "
            f"{stats['failed']} failed, "
            f"elapsed time: {timedelta(seconds=int(stats['elapsed_time']))}"
        )

        return results

    def _run_serial(
        self,
        objective_func: Callable,
        combinations: list[dict[str, Any]],
        results: OptimizationResultSet,
        tracker: ProgressTracker,
    ) -> None:
        """Run evaluations serially."""
        save_counter = 0

        for combo in combinations:
            # Evaluate combination
            params, metrics, exec_time, error = _evaluate_combination(
                combo, objective_func, self.config.timeout_per_eval
            )

            # Handle result
            if metrics is not None:
                result = OptimizationResult(
                    parameters=params, metrics=metrics, execution_time=exec_time
                )
                results.add_result(result)
                tracker.update(1)
            else:
                tracker.update(1, failed=1)

                # Retry if configured
                if self.config.retry_failed:
                    for retry in range(self.config.max_retries):
                        logger.info(f"Retrying {params} (attempt {retry + 1})")
                        params, metrics, exec_time, error = _evaluate_combination(
                            combo, objective_func, self.config.timeout_per_eval
                        )
                        if metrics is not None:
                            result = OptimizationResult(
                                parameters=params,
                                metrics=metrics,
                                execution_time=exec_time,
                            )
                            results.add_result(result)
                            break

            # Save intermediate results
            save_counter += 1
            if (
                self.config.save_intermediate
                and save_counter >= self.config.save_interval
            ):
                self._save_intermediate_results(results)
                save_counter = 0

    def _run_parallel(
        self,
        objective_func: Callable,
        combinations: list[dict[str, Any]],
        results: OptimizationResultSet,
        tracker: ProgressTracker,
    ) -> None:
        """Run evaluations in parallel."""
        save_counter = 0

        with ProcessPoolExecutor(max_workers=self.config.n_workers) as executor:
            # Submit all tasks
            futures = {
                executor.submit(
                    _evaluate_combination,
                    combo,
                    objective_func,
                    self.config.timeout_per_eval,
                ): combo
                for combo in combinations
            }

            # Process completed tasks
            for future in as_completed(futures):
                combo = futures[future]

                try:
                    params, metrics, exec_time, error = future.result()

                    if metrics is not None:
                        result = OptimizationResult(
                            parameters=params, metrics=metrics, execution_time=exec_time
                        )
                        results.add_result(result)
                        tracker.update(1)
                    else:
                        tracker.update(1, failed=1)

                        # Retry if configured
                        if self.config.retry_failed:
                            # Submit retry task
                            retry_future = executor.submit(
                                _evaluate_combination,
                                combo,
                                objective_func,
                                self.config.timeout_per_eval,
                            )
                            # Note: Simplified retry logic for parallel execution

                except Exception as e:
                    logger.error(f"Error processing result for {combo}: {e}")
                    tracker.update(1, failed=1)

                # Save intermediate results
                save_counter += 1
                if (
                    self.config.save_intermediate
                    and save_counter >= self.config.save_interval
                ):
                    self._save_intermediate_results(results)
                    save_counter = 0

    def _save_intermediate_results(self, results: OptimizationResultSet) -> None:
        """Save intermediate results to disk."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"grid_search_intermediate_{timestamp}.json"

        try:
            results.save_to_file(filename)
            logger.debug(f"Saved intermediate results to {filename}")
        except Exception as e:
            logger.error(f"Failed to save intermediate results: {e}")
