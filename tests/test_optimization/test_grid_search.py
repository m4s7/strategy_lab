"""Tests for grid search optimization."""

import time
from unittest.mock import Mock, patch

import pytest

from strategy_lab.optimization.algorithms.grid_search import (
    GridSearchConfig,
    GridSearchOptimizer,
    ProgressTracker,
    _evaluate_combination,
)
from strategy_lab.optimization.core.parameter_space import (
    ContinuousParameter,
    DiscreteParameter,
    ParameterSpace,
)
from strategy_lab.optimization.core.results import OptimizationResultSet


class TestProgressTracker:
    """Test ProgressTracker class."""

    def test_basic_tracking(self):
        """Test basic progress tracking."""
        tracker = ProgressTracker(100, show_progress=False)

        assert tracker.total == 100
        assert tracker.completed == 0
        assert tracker.failed == 0

        # Update progress
        tracker.update(10)
        assert tracker.completed == 10

        tracker.update(5, failed=2)
        assert tracker.completed == 15
        assert tracker.failed == 2

    def test_stats_calculation(self):
        """Test statistics calculation."""
        tracker = ProgressTracker(100, show_progress=False)

        # Simulate some progress
        time.sleep(0.1)
        tracker.update(20)

        stats = tracker.get_stats()
        assert stats["total"] == 100
        assert stats["completed"] == 20
        assert stats["failed"] == 0
        assert stats["progress_pct"] == 20.0
        assert stats["elapsed_time"] > 0
        assert stats["rate"] > 0
        assert stats["eta"] > 0


class TestEvaluateCombination:
    """Test _evaluate_combination function."""

    def test_successful_evaluation(self):
        """Test successful evaluation."""

        def objective(alpha, beta):
            return {"score": alpha + beta}

        params, metrics, exec_time, error = _evaluate_combination(
            {"alpha": 0.5, "beta": 0.3}, objective
        )

        assert params == {"alpha": 0.5, "beta": 0.3}
        assert metrics == {"score": 0.8}
        assert exec_time > 0
        assert error is None

    def test_numeric_return(self):
        """Test numeric return value conversion."""

        def objective(x):
            return x * 2

        params, metrics, exec_time, error = _evaluate_combination({"x": 5}, objective)

        assert metrics == {"objective": 10.0}

    def test_evaluation_error(self):
        """Test evaluation error handling."""

        def failing_objective(**kwargs):
            raise ValueError("Test error")

        params, metrics, exec_time, error = _evaluate_combination(
            {"x": 1}, failing_objective
        )

        assert params == {"x": 1}
        assert metrics is None
        assert exec_time > 0
        assert error == "Test error"


class TestGridSearchOptimizer:
    """Test GridSearchOptimizer class."""

    @pytest.fixture
    def simple_space(self):
        """Create simple parameter space."""
        return ParameterSpace(
            [
                ContinuousParameter("alpha", 0.1, 0.3, 0.1),
                DiscreteParameter("window", 5, 10, 5),
            ]
        )

    @pytest.fixture
    def simple_objective(self):
        """Create simple objective function."""

        def objective(alpha, window):
            return {"score": alpha * window, "time": window / 10.0}

        return objective

    def test_initialization(self):
        """Test optimizer initialization."""
        # Default config
        optimizer = GridSearchOptimizer()
        assert optimizer.config.n_workers > 0
        assert optimizer.config.show_progress is True

        # Custom config
        config = GridSearchConfig(n_workers=2, show_progress=False)
        optimizer = GridSearchOptimizer(config)
        assert optimizer.config.n_workers == 2
        assert optimizer.config.show_progress is False

    def test_serial_optimization(self, simple_space, simple_objective):
        """Test serial optimization execution."""
        config = GridSearchConfig(n_workers=1, show_progress=False)
        optimizer = GridSearchOptimizer(config)

        results = optimizer.optimize(simple_objective, simple_space)

        # Check results
        assert results.size == 6  # 3 alpha * 2 window values

        # Verify all combinations were evaluated
        df = results.to_dataframe()
        assert set(df["param_alpha"].unique()) == {0.1, 0.2, 0.3}
        assert set(df["param_window"].unique()) == {5, 10}

        # Check metrics
        best = results.get_best_results("score", n=1)[0]
        assert best.parameters["alpha"] == 0.3
        assert best.parameters["window"] == 10
        assert best.metrics["score"] == 3.0

    @patch("strategy_lab.optimization.algorithms.grid_search.ProcessPoolExecutor")
    def test_parallel_optimization(self, mock_executor, simple_space, simple_objective):
        """Test parallel optimization execution."""
        # Mock the executor to avoid actual multiprocessing in tests
        mock_future = Mock()
        mock_future.result.return_value = (
            {"alpha": 0.2, "window": 10},
            {"score": 2.0, "time": 1.0},
            0.1,
            None,
        )

        mock_executor_instance = Mock()
        mock_executor_instance.submit.return_value = mock_future
        mock_executor_instance.__enter__.return_value = mock_executor_instance
        mock_executor_instance.__exit__.return_value = None
        mock_executor.return_value = mock_executor_instance

        # Import as_completed and mock it
        from concurrent.futures import as_completed

        with patch(
            "strategy_lab.optimization.algorithms.grid_search.as_completed"
        ) as mock_as_completed:
            mock_as_completed.return_value = [mock_future]

            config = GridSearchConfig(n_workers=2, show_progress=False)
            optimizer = GridSearchOptimizer(config)

            results = optimizer.optimize(simple_objective, simple_space)

            # Should have called executor
            assert mock_executor.called
            assert mock_executor_instance.submit.called

    def test_resume_optimization(self, simple_space, simple_objective):
        """Test resuming optimization from previous results."""
        config = GridSearchConfig(n_workers=1, show_progress=False)
        optimizer = GridSearchOptimizer(config)

        # Run partial optimization
        partial_results = OptimizationResultSet()
        from strategy_lab.optimization.core.results import OptimizationResult

        # Add some completed results
        for alpha in [0.1, 0.2]:
            for window in [5, 10]:
                result = OptimizationResult(
                    parameters={"alpha": alpha, "window": window},
                    metrics=simple_objective(alpha, window),
                    execution_time=0.1,
                )
                partial_results.add_result(result)

        # Resume optimization
        results = optimizer.optimize(
            simple_objective, simple_space, resume_from=partial_results
        )

        # Should have all 6 results (4 existing + 2 new)
        assert results.size == 6

        # Check that only missing combinations were evaluated
        new_results = [r for r in results.results if r.parameters["alpha"] == 0.3]
        assert len(new_results) == 2

    def test_error_handling(self, simple_space):
        """Test error handling during optimization."""

        def failing_objective(alpha, window):
            if alpha > 0.2:
                raise ValueError("Test failure")
            return {"score": alpha * window}

        config = GridSearchConfig(n_workers=1, show_progress=False, retry_failed=False)
        optimizer = GridSearchOptimizer(config)

        results = optimizer.optimize(failing_objective, simple_space)

        # Should have partial results
        assert results.size == 4  # Only alpha <= 0.2 succeed

        # Check no failed parameters in results
        df = results.to_dataframe()
        assert all(df["param_alpha"] <= 0.2)

    def test_empty_parameter_space(self):
        """Test with empty parameter space."""
        empty_space = ParameterSpace([])
        optimizer = GridSearchOptimizer(GridSearchConfig(show_progress=False))

        def objective():
            return {"value": 1.0}

        results = optimizer.optimize(objective, empty_space)

        # Should have one result with no parameters
        assert results.size == 1
        assert results.results[0].parameters == {}
        assert results.results[0].metrics == {"value": 1.0}
