"""Walk-forward analysis implementation."""

import logging
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

import pandas as pd

from ..algorithms.grid_search import GridSearchOptimizer
from ..algorithms.genetic_algorithm import GeneticAlgorithmOptimizer
from ..core.parameter_space import ParameterSpace
from .results import WalkForwardResult, WalkForwardResultSet
from .scheduler import WalkForwardScheduler, WindowDefinition
from .validator import PerformanceValidator

logger = logging.getLogger(__name__)


@dataclass
class WalkForwardConfig:
    """Configuration for walk-forward analysis."""

    # Time window configuration
    in_sample_days: int
    out_of_sample_days: int
    step_days: int
    overlap: bool = False
    gap_days: int = 0

    # Optimization configuration
    optimization_method: str = "grid_search"  # or "genetic_algorithm"
    optimization_config: Optional[Dict[str, Any]] = None

    # Validation configuration
    primary_metric: str = "sharpe_ratio"
    minimize_metric: bool = False
    min_trades_per_window: int = 50

    # Statistical validation
    enable_statistical_tests: bool = True
    significance_level: float = 0.05
    bootstrap_samples: int = 1000

    # Parameter stability
    track_parameter_stability: bool = True
    stability_lookback_windows: int = 3

    # Performance thresholds
    min_in_sample_performance: Optional[float] = None
    max_acceptable_degradation: float = 0.5

    # Execution
    parallel: bool = True
    n_workers: Optional[int] = None
    verbose: bool = True
    save_intermediate: bool = True
    results_dir: Optional[Path] = None


class WalkForwardAnalyzer:
    """Performs walk-forward analysis for strategy validation."""

    def __init__(self, config: WalkForwardConfig):
        """Initialize analyzer.

        Args:
            config: Walk-forward configuration
        """
        self.config = config
        self.validator = PerformanceValidator(
            significance_level=config.significance_level,
            bootstrap_samples=config.bootstrap_samples,
        )

        # Setup results directory
        if config.save_intermediate and config.results_dir:
            config.results_dir.mkdir(parents=True, exist_ok=True)

        # Track previous parameters for stability analysis
        self.parameter_history: List[Dict[str, Any]] = []

    def analyze(
        self,
        objective_func: Callable[..., Union[float, Dict[str, float]]],
        parameter_space: ParameterSpace,
        start_date: datetime,
        end_date: datetime,
        data_getter: Optional[Callable[[datetime, datetime], pd.DataFrame]] = None,
    ) -> WalkForwardResultSet:
        """Run walk-forward analysis.

        Args:
            objective_func: Objective function to optimize
            parameter_space: Parameter space for optimization
            start_date: Start date for analysis
            end_date: End date for analysis
            data_getter: Optional function to get data for specific date range

        Returns:
            WalkForwardResultSet with all results
        """
        # Create scheduler
        scheduler = WalkForwardScheduler(
            start_date=start_date,
            end_date=end_date,
            in_sample_days=self.config.in_sample_days,
            out_of_sample_days=self.config.out_of_sample_days,
            step_days=self.config.step_days,
            overlap=self.config.overlap,
            gap_days=self.config.gap_days,
        )

        if self.config.verbose:
            logger.info(f"Starting walk-forward analysis with {len(scheduler)} windows")
            logger.info(scheduler.visualize_schedule())

        # Initialize results
        results = WalkForwardResultSet()

        # Process each window
        for window in scheduler:
            if self.config.verbose:
                logger.info(
                    f"\nProcessing window {window.window_id + 1}/{len(scheduler)}"
                )

            try:
                result = self._process_window(
                    window=window,
                    objective_func=objective_func,
                    parameter_space=parameter_space,
                    data_getter=data_getter,
                )

                results.add_result(result)

                # Save intermediate results
                if self.config.save_intermediate and self.config.results_dir:
                    self._save_intermediate_results(results, window.window_id)

            except Exception as e:
                logger.error(f"Error processing window {window.window_id}: {e}")
                continue

        # Final analysis
        if self.config.verbose:
            self._log_final_summary(results)

        return results

    def _process_window(
        self,
        window: WindowDefinition,
        objective_func: Callable,
        parameter_space: ParameterSpace,
        data_getter: Optional[Callable] = None,
    ) -> WalkForwardResult:
        """Process a single walk-forward window."""
        start_time = time.time()

        # Create window-specific objective functions if data_getter provided
        if data_getter:
            in_sample_data = data_getter(window.in_sample_start, window.in_sample_end)
            out_of_sample_data = data_getter(
                window.out_of_sample_start, window.out_of_sample_end
            )

            def in_sample_objective(**params):
                return objective_func(data=in_sample_data, **params)

            def out_of_sample_objective(**params):
                return objective_func(data=out_of_sample_data, **params)

        else:
            # Use date parameters directly
            def in_sample_objective(**params):
                return objective_func(
                    start_date=window.in_sample_start,
                    end_date=window.in_sample_end,
                    **params,
                )

            def out_of_sample_objective(**params):
                return objective_func(
                    start_date=window.out_of_sample_start,
                    end_date=window.out_of_sample_end,
                    **params,
                )

        # Run in-sample optimization
        optimization_start = time.time()
        optimal_params, in_sample_metrics, n_combinations = self._optimize_parameters(
            objective_func=in_sample_objective, parameter_space=parameter_space
        )
        optimization_time = time.time() - optimization_start

        if self.config.verbose:
            logger.info(f"  Optimization completed in {optimization_time:.1f}s")
            logger.info(f"  Optimal parameters: {optimal_params}")
            logger.info(
                f"  In-sample {self.config.primary_metric}: {in_sample_metrics.get(self.config.primary_metric, 'N/A')}"
            )

        # Check minimum performance threshold
        if self.config.min_in_sample_performance is not None:
            primary_value = in_sample_metrics.get(
                self.config.primary_metric, float("-inf")
            )
            if primary_value < self.config.min_in_sample_performance:
                logger.warning(
                    f"  In-sample performance {primary_value:.4f} below threshold "
                    f"{self.config.min_in_sample_performance}"
                )

        # Run out-of-sample backtest
        backtest_start = time.time()
        out_of_sample_result = out_of_sample_objective(**optimal_params)
        backtest_time = time.time() - backtest_start

        # Extract metrics
        if isinstance(out_of_sample_result, dict):
            out_of_sample_metrics = out_of_sample_result
        else:
            out_of_sample_metrics = {
                self.config.primary_metric: float(out_of_sample_result)
            }

        if self.config.verbose:
            logger.info(
                f"  Out-of-sample {self.config.primary_metric}: {out_of_sample_metrics.get(self.config.primary_metric, 'N/A')}"
            )

        # Calculate parameter changes
        parameter_changes = None
        parameter_stability_score = None

        if self.config.track_parameter_stability:
            parameter_changes = self._calculate_parameter_changes(optimal_params)
            if len(self.parameter_history) >= self.config.stability_lookback_windows:
                parameter_stability_score = self._calculate_stability_score()

        # Update parameter history
        self.parameter_history.append(optimal_params)

        # Statistical validation
        statistical_tests = None
        is_significant = None

        if self.config.enable_statistical_tests and window.window_id >= 5:
            statistical_tests, is_significant = self._run_statistical_tests(
                window_id=window.window_id
            )

        # Create result
        result = WalkForwardResult(
            window_id=window.window_id,
            in_sample_start=window.in_sample_start,
            in_sample_end=window.in_sample_end,
            out_of_sample_start=window.out_of_sample_start,
            out_of_sample_end=window.out_of_sample_end,
            optimal_parameters=optimal_params,
            in_sample_metrics=in_sample_metrics,
            out_of_sample_metrics=out_of_sample_metrics,
            optimization_time=optimization_time,
            backtest_time=backtest_time,
            n_parameter_combinations=n_combinations,
            parameter_changes=parameter_changes,
            parameter_stability_score=parameter_stability_score,
            statistical_tests=statistical_tests,
            is_significant=is_significant,
        )

        # Check for performance degradation
        degradation_score = result.get_degradation_score(self.config.primary_metric)
        if degradation_score < self.config.max_acceptable_degradation:
            logger.warning(
                f"  Severe performance degradation detected: {degradation_score:.2f}"
            )

        return result

    def _optimize_parameters(
        self, objective_func: Callable, parameter_space: ParameterSpace
    ) -> tuple[Dict[str, Any], Dict[str, float], int]:
        """Run parameter optimization."""
        if self.config.optimization_method == "grid_search":
            from ..algorithms.grid_search import GridSearchConfig, GridSearchOptimizer

            # Create optimizer config
            opt_config = GridSearchConfig(
                parallel=self.config.parallel,
                n_workers=self.config.n_workers,
                verbose=False,  # Suppress optimizer verbosity
                **(self.config.optimization_config or {}),
            )

            optimizer = GridSearchOptimizer(opt_config)
            result_set = optimizer.optimize(objective_func, parameter_space)

        elif self.config.optimization_method == "genetic_algorithm":
            from ..algorithms.genetic_algorithm import (
                GeneticAlgorithmConfig,
                GeneticAlgorithmOptimizer,
            )

            # Create optimizer config
            opt_config = GeneticAlgorithmConfig(
                parallel=self.config.parallel,
                n_workers=self.config.n_workers,
                verbose=False,
                **(self.config.optimization_config or {}),
            )

            optimizer = GeneticAlgorithmOptimizer(opt_config)
            result_set = optimizer.optimize(objective_func, parameter_space)

        else:
            raise ValueError(
                f"Unknown optimization method: {self.config.optimization_method}"
            )

        # Get best result
        best_results = result_set.get_best_results(
            metric=self.config.primary_metric, minimize=self.config.minimize_metric, n=1
        )

        if not best_results:
            raise RuntimeError("Optimization failed to produce results")

        best_result = best_results[0]

        return (best_result.parameters, best_result.metrics, result_set.size)

    def _calculate_parameter_changes(
        self, current_params: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate parameter changes from previous window."""
        if not self.parameter_history:
            return {}

        previous_params = self.parameter_history[-1]
        changes = {}

        for param_name, current_value in current_params.items():
            if param_name in previous_params:
                prev_value = previous_params[param_name]

                if isinstance(current_value, (int, float)) and isinstance(
                    prev_value, (int, float)
                ):
                    # Calculate relative change
                    if prev_value != 0:
                        change = abs(current_value - prev_value) / abs(prev_value)
                    else:
                        change = abs(current_value)
                    changes[param_name] = change
                elif current_value != prev_value:
                    # Categorical parameter changed
                    changes[param_name] = 1.0
                else:
                    changes[param_name] = 0.0

        return changes

    def _calculate_stability_score(self) -> float:
        """Calculate overall parameter stability score."""
        if len(self.parameter_history) < self.config.stability_lookback_windows:
            return 1.0

        # Get recent parameter values
        recent_params = self.parameter_history[
            -self.config.stability_lookback_windows :
        ]

        # Extract parameter values by name
        param_values = {}
        for params in recent_params:
            for name, value in params.items():
                if name not in param_values:
                    param_values[name] = []
                param_values[name].append(value)

        # Calculate stability scores
        stability_scores = self.validator.calculate_parameter_stability(param_values)

        # Return average stability
        if stability_scores:
            return sum(stability_scores.values()) / len(stability_scores)
        else:
            return 1.0

    def _run_statistical_tests(self, window_id: int) -> tuple[Dict[str, float], bool]:
        """Run statistical tests on accumulated results."""
        # This would need access to previous results
        # For now, return placeholder
        return {}, False

    def _save_intermediate_results(
        self, results: WalkForwardResultSet, window_id: int
    ) -> None:
        """Save intermediate results to disk."""
        if not self.config.results_dir:
            return

        filepath = self.config.results_dir / f"walk_forward_window_{window_id:03d}.json"
        results.save(filepath)

    def _log_final_summary(self, results: WalkForwardResultSet) -> None:
        """Log final analysis summary."""
        aggregate = results.calculate_aggregate_metrics()

        logger.info("\n" + "=" * 80)
        logger.info("Walk-Forward Analysis Summary")
        logger.info("=" * 80)

        logger.info(f"Total windows analyzed: {aggregate['n_windows']}")
        logger.info(
            f"Total optimization time: {aggregate['total_optimization_time']:.1f}s"
        )
        logger.info(f"Total backtest time: {aggregate['total_backtest_time']:.1f}s")

        # Performance summary
        metric = self.config.primary_metric
        if f"mean_out_of_sample_{metric}" in aggregate:
            logger.info(f"\nPerformance ({metric}):")
            logger.info(
                f"  Mean in-sample: {aggregate.get(f'mean_in_sample_{metric}', 'N/A'):.4f}"
            )
            logger.info(
                f"  Mean out-of-sample: {aggregate.get(f'mean_out_of_sample_{metric}', 'N/A'):.4f}"
            )
            logger.info(
                f"  Mean performance ratio: {aggregate.get(f'mean_ratio_{metric}', 'N/A'):.4f}"
            )

        # Overfitting analysis
        if "overfitting_indicators" in aggregate:
            indicators = aggregate["overfitting_indicators"]
            logger.info("\nOverfitting Analysis:")
            logger.info(
                f"  Windows with degradation: {indicators['windows_with_degradation']}"
            )
            logger.info(
                f"  Windows with severe degradation: {indicators['windows_with_severe_degradation']}"
            )
            logger.info(f"  Consistency score: {indicators['consistency_score']:.3f}")

        # Parameter stability
        if "parameter_stability" in aggregate:
            logger.info("\nParameter Stability:")
            for param, stability in aggregate["parameter_stability"].items():
                logger.info(
                    f"  {param}: CV={stability['cv']:.3f}, drift={stability['drift']:.3f}"
                )

        # Breakdown periods
        breakdowns = results.identify_breakdown_periods(
            metric=self.config.primary_metric,
            threshold=self.config.max_acceptable_degradation,
        )

        if breakdowns:
            logger.info(f"\nPerformance Breakdown Periods: {len(breakdowns)}")
            for breakdown in breakdowns[:3]:  # Show first 3
                period = breakdown["out_of_sample_period"]
                logger.info(
                    f"  Window {breakdown['window_id']}: "
                    f"{period[0].date()} to {period[1].date()} "
                    f"(ratio={breakdown['performance_ratio']:.2f})"
                )
