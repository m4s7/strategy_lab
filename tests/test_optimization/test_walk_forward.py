"""Tests for walk-forward analysis."""

import random
from datetime import datetime, timedelta

import numpy as np
import pytest

from strategy_lab.optimization.core.parameter_space import (
    ContinuousParameter,
    DiscreteParameter,
    ParameterSpace,
)
from strategy_lab.optimization.walk_forward import (
    PerformanceValidator,
    WalkForwardAnalyzer,
    WalkForwardConfig,
    WalkForwardResult,
    WalkForwardResultSet,
    WalkForwardScheduler,
    WindowDefinition,
)


class TestWindowDefinition:
    """Test WindowDefinition class."""

    def test_window_creation(self):
        """Test window definition creation."""
        window = WindowDefinition(
            in_sample_start=datetime(2024, 1, 1),
            in_sample_end=datetime(2024, 3, 31),
            out_of_sample_start=datetime(2024, 4, 1),
            out_of_sample_end=datetime(2024, 4, 30),
            window_id=0,
        )

        assert window.window_id == 0
        assert window.in_sample_days == 90
        assert window.out_of_sample_days == 29
        assert window.in_sample_period == (datetime(2024, 1, 1), datetime(2024, 3, 31))
        assert window.out_of_sample_period == (
            datetime(2024, 4, 1),
            datetime(2024, 4, 30),
        )

    def test_contains_date(self):
        """Test date containment checking."""
        window = WindowDefinition(
            in_sample_start=datetime(2024, 1, 1),
            in_sample_end=datetime(2024, 1, 31),
            out_of_sample_start=datetime(2024, 2, 1),
            out_of_sample_end=datetime(2024, 2, 15),
            window_id=0,
        )

        assert window.contains_date(datetime(2024, 1, 15)) == "in_sample"
        assert window.contains_date(datetime(2024, 2, 10)) == "out_of_sample"
        assert window.contains_date(datetime(2023, 12, 31)) == "none"
        assert window.contains_date(datetime(2024, 3, 1)) == "none"


class TestWalkForwardScheduler:
    """Test WalkForwardScheduler class."""

    def test_scheduler_creation(self):
        """Test scheduler initialization."""
        scheduler = WalkForwardScheduler(
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31),
            in_sample_days=90,
            out_of_sample_days=30,
            step_days=30,
            overlap=True,
        )

        assert len(scheduler) > 0
        assert scheduler.in_sample_days == 90
        assert scheduler.out_of_sample_days == 30
        assert scheduler.overlap is True

    def test_non_overlapping_windows(self):
        """Test non-overlapping window generation."""
        scheduler = WalkForwardScheduler(
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31),
            in_sample_days=60,
            out_of_sample_days=30,
            step_days=30,  # Ignored for non-overlapping
            overlap=False,
        )

        windows = list(scheduler)

        # Check no overlap
        for i in range(len(windows) - 1):
            assert windows[i].out_of_sample_end < windows[i + 1].in_sample_start

    def test_overlapping_windows(self):
        """Test overlapping window generation."""
        scheduler = WalkForwardScheduler(
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 6, 30),
            in_sample_days=60,
            out_of_sample_days=30,
            step_days=15,
            overlap=True,
        )

        windows = list(scheduler)

        # Check overlap exists
        overlap_found = False
        for i in range(len(windows) - 1):
            if windows[i].out_of_sample_end >= windows[i + 1].in_sample_start:
                overlap_found = True
                break

        assert overlap_found

    def test_gap_between_periods(self):
        """Test gap between in-sample and out-of-sample."""
        scheduler = WalkForwardScheduler(
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31),
            in_sample_days=60,
            out_of_sample_days=30,
            step_days=30,
            gap_days=5,
        )

        window = scheduler.get_window(0)
        gap = (window.out_of_sample_start - window.in_sample_end).days - 1
        assert gap == 5

    def test_insufficient_data_error(self):
        """Test error when insufficient data."""
        with pytest.raises(ValueError, match="Insufficient data"):
            WalkForwardScheduler(
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 1, 31),
                in_sample_days=60,
                out_of_sample_days=30,
                step_days=30,
            )

    def test_get_windows_for_date(self):
        """Test finding windows containing a date."""
        scheduler = WalkForwardScheduler(
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31),
            in_sample_days=60,
            out_of_sample_days=30,
            step_days=30,
            overlap=True,
        )

        # Test date in multiple windows
        test_date = datetime(2024, 3, 15)
        windows = scheduler.get_windows_for_date(test_date)

        assert len(windows) > 0
        for window, period_type in windows:
            assert window.contains_date(test_date) == period_type

    def test_coverage_analysis(self):
        """Test coverage analysis."""
        scheduler = WalkForwardScheduler(
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 6, 30),
            in_sample_days=60,
            out_of_sample_days=30,
            step_days=30,
            overlap=True,
        )

        coverage_df = scheduler.get_coverage_analysis()

        assert len(coverage_df) == 182  # Jan 1 to Jun 30 inclusive
        assert "date" in coverage_df.columns
        assert "is_covered" in coverage_df.columns
        assert coverage_df["is_covered"].any()  # At least some dates covered


class TestWalkForwardResult:
    """Test WalkForwardResult class."""

    def test_result_creation(self):
        """Test result object creation."""
        result = WalkForwardResult(
            window_id=0,
            in_sample_start=datetime(2024, 1, 1),
            in_sample_end=datetime(2024, 3, 31),
            out_of_sample_start=datetime(2024, 4, 1),
            out_of_sample_end=datetime(2024, 4, 30),
            optimal_parameters={"alpha": 0.5, "beta": 10},
            in_sample_metrics={"sharpe_ratio": 2.0, "profit": 1000},
            out_of_sample_metrics={"sharpe_ratio": 1.5, "profit": 500},
            optimization_time=10.5,
            backtest_time=2.3,
            n_parameter_combinations=100,
        )

        assert result.window_id == 0
        assert result.optimal_parameters["alpha"] == 0.5
        assert result.in_sample_metrics["sharpe_ratio"] == 2.0

    def test_performance_ratio(self):
        """Test performance ratio calculation."""
        result = WalkForwardResult(
            window_id=0,
            in_sample_start=datetime(2024, 1, 1),
            in_sample_end=datetime(2024, 3, 31),
            out_of_sample_start=datetime(2024, 4, 1),
            out_of_sample_end=datetime(2024, 4, 30),
            optimal_parameters={},
            in_sample_metrics={"sharpe_ratio": 2.0, "profit": 1000, "zero_metric": 0},
            out_of_sample_metrics={
                "sharpe_ratio": 1.5,
                "profit": 750,
                "zero_metric": 100,
            },
            optimization_time=10.5,
            backtest_time=2.3,
            n_parameter_combinations=100,
        )

        ratios = result.performance_ratio
        assert ratios["sharpe_ratio"] == 0.75
        assert ratios["profit"] == 0.75
        assert ratios["zero_metric"] == np.inf

    def test_degradation_score(self):
        """Test degradation score calculation."""
        # Good performance
        result1 = WalkForwardResult(
            window_id=0,
            in_sample_start=datetime(2024, 1, 1),
            in_sample_end=datetime(2024, 3, 31),
            out_of_sample_start=datetime(2024, 4, 1),
            out_of_sample_end=datetime(2024, 4, 30),
            optimal_parameters={},
            in_sample_metrics={"sharpe_ratio": 2.0},
            out_of_sample_metrics={"sharpe_ratio": 1.8},
            optimization_time=10.5,
            backtest_time=2.3,
            n_parameter_combinations=100,
        )

        assert result1.get_degradation_score() == 0.9

        # Severe degradation
        result2 = WalkForwardResult(
            window_id=1,
            in_sample_start=datetime(2024, 1, 1),
            in_sample_end=datetime(2024, 3, 31),
            out_of_sample_start=datetime(2024, 4, 1),
            out_of_sample_end=datetime(2024, 4, 30),
            optimal_parameters={},
            in_sample_metrics={"sharpe_ratio": 2.0},
            out_of_sample_metrics={"sharpe_ratio": 0.5},
            optimization_time=10.5,
            backtest_time=2.3,
            n_parameter_combinations=100,
        )

        assert result2.get_degradation_score() == 0.25


class TestWalkForwardResultSet:
    """Test WalkForwardResultSet class."""

    @pytest.fixture
    def sample_results(self):
        """Create sample results."""
        results = []
        for i in range(5):
            result = WalkForwardResult(
                window_id=i,
                in_sample_start=datetime(2024, 1, 1) + timedelta(days=i * 30),
                in_sample_end=datetime(2024, 1, 31) + timedelta(days=i * 30),
                out_of_sample_start=datetime(2024, 2, 1) + timedelta(days=i * 30),
                out_of_sample_end=datetime(2024, 2, 15) + timedelta(days=i * 30),
                optimal_parameters={"alpha": 0.5 + i * 0.1, "beta": 10 + i},
                in_sample_metrics={
                    "sharpe_ratio": 2.0 - i * 0.1,
                    "profit": 1000 - i * 50,
                },
                out_of_sample_metrics={
                    "sharpe_ratio": 1.5 - i * 0.2,
                    "profit": 800 - i * 100,
                },
                optimization_time=10.0 + i,
                backtest_time=2.0,
                n_parameter_combinations=100,
            )
            results.append(result)
        return results

    def test_result_set_operations(self, sample_results):
        """Test result set basic operations."""
        result_set = WalkForwardResultSet()

        for result in sample_results:
            result_set.add_result(result)

        assert result_set.size == 5
        assert result_set.get_result(2) == sample_results[2]
        assert result_set.get_result(10) is None

    def test_to_dataframe(self, sample_results):
        """Test DataFrame conversion."""
        result_set = WalkForwardResultSet()
        for result in sample_results:
            result_set.add_result(result)

        df = result_set.to_dataframe()

        assert len(df) == 5
        assert "window_id" in df.columns
        assert "param_alpha" in df.columns
        assert "in_sample_sharpe_ratio" in df.columns
        assert "out_of_sample_sharpe_ratio" in df.columns
        assert "ratio_sharpe_ratio" in df.columns

    def test_parameter_evolution(self, sample_results):
        """Test parameter evolution tracking."""
        result_set = WalkForwardResultSet()
        for result in sample_results:
            result_set.add_result(result)

        evolution_df = result_set.get_parameter_evolution()

        assert len(evolution_df) == 5
        assert "alpha" in evolution_df.columns
        assert "beta" in evolution_df.columns

        # Check parameter drift
        alpha_values = evolution_df["alpha"].values
        assert alpha_values[0] < alpha_values[-1]  # Increasing trend

    def test_aggregate_metrics(self, sample_results):
        """Test aggregate metrics calculation."""
        result_set = WalkForwardResultSet()
        for result in sample_results:
            result_set.add_result(result)

        aggregate = result_set.calculate_aggregate_metrics()

        assert aggregate["n_windows"] == 5
        assert "mean_in_sample_sharpe_ratio" in aggregate
        assert "mean_out_of_sample_sharpe_ratio" in aggregate
        assert "overfitting_indicators" in aggregate

        # Check overfitting detection
        indicators = aggregate["overfitting_indicators"]
        assert indicators["windows_with_degradation"] >= 0

    def test_breakdown_detection(self, sample_results):
        """Test breakdown period detection."""
        result_set = WalkForwardResultSet()
        for result in sample_results:
            result_set.add_result(result)

        breakdowns = result_set.identify_breakdown_periods(threshold=0.7)

        # Later windows have worse performance ratios
        assert len(breakdowns) > 0
        # First breakdown should be in later windows (but could be window 1)
        assert breakdowns[0]["window_id"] >= 1


class TestPerformanceValidator:
    """Test PerformanceValidator class."""

    def test_paired_t_test(self):
        """Test paired t-test for performance validation."""
        validator = PerformanceValidator()

        # No degradation case
        in_sample = [2.0, 2.1, 1.9, 2.0, 2.2]
        out_of_sample = [1.9, 2.0, 1.8, 2.1, 2.0]

        tests = validator.validate_performance(in_sample, out_of_sample)

        assert isinstance(tests.t_statistic, float)
        assert isinstance(tests.t_p_value, float)
        assert isinstance(tests.t_significant, (bool, np.bool_))

    def test_bootstrap_analysis(self):
        """Test bootstrap confidence intervals."""
        validator = PerformanceValidator(bootstrap_samples=100)

        # Generate synthetic data with known degradation
        np.random.seed(42)
        in_sample = np.random.normal(2.0, 0.2, 20)
        out_of_sample = np.random.normal(1.5, 0.3, 20)  # Lower performance

        tests = validator.validate_performance(
            in_sample.tolist(), out_of_sample.tolist()
        )

        assert tests.bootstrap_mean is not None
        assert tests.bootstrap_ci_lower is not None
        assert tests.bootstrap_ci_upper is not None
        assert tests.bootstrap_ci_lower < tests.bootstrap_ci_upper

    def test_parameter_stability(self):
        """Test parameter stability calculation."""
        validator = PerformanceValidator()

        # Stable parameter
        stable_values = {"alpha": [0.5, 0.51, 0.49, 0.50, 0.52]}

        # Unstable parameter
        unstable_values = {"beta": [10, 15, 8, 20, 5]}

        stable_scores = validator.calculate_parameter_stability(stable_values)
        unstable_scores = validator.calculate_parameter_stability(unstable_values)

        assert stable_scores["alpha"] > unstable_scores["beta"]
        assert 0 <= stable_scores["alpha"] <= 1
        assert 0 <= unstable_scores["beta"] <= 1

    def test_overfitting_detection(self):
        """Test overfitting detection."""
        validator = PerformanceValidator()

        # Clear overfitting case
        performance_ratios = [0.5, 0.4, 0.3, 0.45, 0.35]  # Poor out-of-sample
        parameter_changes = [0.4, 0.5, 0.3, 0.6, 0.4]  # High changes

        indicators = validator.detect_overfitting(performance_ratios, parameter_changes)

        assert indicators["likely_overfitted"] is True
        assert indicators["confidence"] > 0.5
        assert len(indicators["reasons"]) > 0


class TestWalkForwardAnalyzer:
    """Test WalkForwardAnalyzer class."""

    @pytest.fixture
    def simple_objective(self):
        """Create simple objective function."""

        def objective(alpha=0.5, beta=10, start_date=None, end_date=None, **kwargs):
            # Simulate performance that degrades over time
            base_performance = alpha * 2 + beta / 10

            # Add time-based degradation
            if start_date:
                days_from_start = (start_date - datetime(2024, 1, 1)).days
                degradation = days_from_start / 1000
                base_performance -= degradation

            # Add some noise
            noise = random.gauss(0, 0.1)

            return {
                "sharpe_ratio": max(0, base_performance + noise),
                "profit": max(0, (base_performance + noise) * 1000),
                "max_drawdown": -abs(noise) * 0.1,
            }

        return objective

    @pytest.fixture
    def parameter_space(self):
        """Create parameter space."""
        return ParameterSpace(
            [
                ContinuousParameter("alpha", 0.1, 1.0, 0.1),
                DiscreteParameter("beta", 5, 15, 5),
            ]
        )

    def test_analyzer_initialization(self):
        """Test analyzer initialization."""
        config = WalkForwardConfig(
            in_sample_days=60,
            out_of_sample_days=30,
            step_days=30,
            primary_metric="sharpe_ratio",
        )

        analyzer = WalkForwardAnalyzer(config)

        assert analyzer.config.in_sample_days == 60
        assert analyzer.config.primary_metric == "sharpe_ratio"
        assert analyzer.validator is not None

    def test_walk_forward_analysis(self, simple_objective, parameter_space, tmp_path):
        """Test complete walk-forward analysis."""
        config = WalkForwardConfig(
            in_sample_days=30,
            out_of_sample_days=15,
            step_days=15,
            overlap=True,
            optimization_method="grid_search",
            primary_metric="sharpe_ratio",
            verbose=False,
            parallel=False,  # Disable parallel execution for test
            save_intermediate=True,
            results_dir=tmp_path / "results",
        )

        analyzer = WalkForwardAnalyzer(config)

        # Run analysis
        results = analyzer.analyze(
            objective_func=simple_objective,
            parameter_space=parameter_space,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 4, 30),
        )

        assert results.size > 0

        # Check results
        df = results.to_dataframe()
        assert "param_alpha" in df.columns
        assert "in_sample_sharpe_ratio" in df.columns
        assert "out_of_sample_sharpe_ratio" in df.columns

        # Check intermediate saves
        saved_files = list((tmp_path / "results").glob("*.json"))
        assert len(saved_files) > 0

    def test_optimization_methods(self, simple_objective, parameter_space):
        """Test different optimization methods."""
        # Test with genetic algorithm
        config = WalkForwardConfig(
            in_sample_days=30,
            out_of_sample_days=15,
            step_days=30,
            optimization_method="genetic_algorithm",
            optimization_config={"population_size": 10, "generations": 5},
            verbose=False,
            parallel=False,  # Disable parallel execution for test
        )

        analyzer = WalkForwardAnalyzer(config)

        results = analyzer.analyze(
            objective_func=simple_objective,
            parameter_space=parameter_space,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 3, 31),
        )

        assert results.size >= 1
