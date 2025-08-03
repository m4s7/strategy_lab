"""Tests for optimization results."""

import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from strategy_lab.optimization.core.results import (
    OptimizationResult,
    OptimizationResultSet,
)


class TestOptimizationResult:
    """Test OptimizationResult class."""

    def test_basic_result(self):
        """Test basic result creation."""
        result = OptimizationResult(
            parameters={"alpha": 0.5, "beta": 0.3},
            metrics={"sharpe": 1.5, "returns": 0.08},
            execution_time=2.5,
        )

        assert result.parameters["alpha"] == 0.5
        assert result.metrics["sharpe"] == 1.5
        assert result.execution_time == 2.5
        assert isinstance(result.timestamp, datetime)

    def test_primary_metric(self):
        """Test primary metric access."""
        result = OptimizationResult(
            parameters={}, metrics={"sharpe": 1.5, "returns": 0.08}, execution_time=1.0
        )

        assert result.primary_metric == 1.5  # First metric

        # Empty metrics
        empty_result = OptimizationResult(parameters={}, metrics={}, execution_time=1.0)
        assert empty_result.primary_metric is None

    def test_get_metric(self):
        """Test getting specific metric."""
        result = OptimizationResult(
            parameters={}, metrics={"sharpe": 1.5, "returns": 0.08}, execution_time=1.0
        )

        assert result.get_metric("sharpe") == 1.5
        assert result.get_metric("returns") == 0.08
        assert result.get_metric("nonexistent") is None

    def test_serialization(self):
        """Test result serialization."""
        result = OptimizationResult(
            parameters={"alpha": 0.5},
            metrics={"sharpe": 1.5},
            execution_time=2.5,
            metadata={"strategy": "test"},
        )

        # To dict
        data = result.to_dict()
        assert data["parameters"]["alpha"] == 0.5
        assert data["metrics"]["sharpe"] == 1.5
        assert data["execution_time"] == 2.5
        assert data["metadata"]["strategy"] == "test"
        assert "timestamp" in data

        # From dict
        restored = OptimizationResult.from_dict(data)
        assert restored.parameters == result.parameters
        assert restored.metrics == result.metrics
        assert restored.execution_time == result.execution_time
        assert restored.metadata == result.metadata


class TestOptimizationResultSet:
    """Test OptimizationResultSet class."""

    @pytest.fixture
    def sample_results(self):
        """Create sample results."""
        results = []
        for i in range(10):
            result = OptimizationResult(
                parameters={
                    "alpha": 0.1 * (i + 1),
                    "beta": 0.5 + 0.05 * i,
                    "method": "fast" if i < 5 else "slow",
                },
                metrics={
                    "sharpe": 1.0 + 0.1 * i,
                    "returns": 0.05 + 0.01 * i,
                    "max_dd": -0.1 - 0.01 * i,
                },
                execution_time=1.0 + 0.1 * i,
            )
            results.append(result)
        return OptimizationResultSet(results)

    def test_basic_operations(self, sample_results):
        """Test basic result set operations."""
        assert sample_results.size == 10

        # Add result
        new_result = OptimizationResult(
            parameters={"alpha": 1.5}, metrics={"sharpe": 2.0}, execution_time=1.0
        )
        sample_results.add_result(new_result)
        assert sample_results.size == 11

        # Add multiple results
        more_results = [
            OptimizationResult(
                parameters={"alpha": 2.0}, metrics={"sharpe": 2.5}, execution_time=1.0
            )
        ]
        sample_results.add_results(more_results)
        assert sample_results.size == 12

    def test_to_dataframe(self, sample_results):
        """Test DataFrame conversion."""
        df = sample_results.to_dataframe()

        assert len(df) == 10
        assert "param_alpha" in df.columns
        assert "param_beta" in df.columns
        assert "param_method" in df.columns
        assert "metric_sharpe" in df.columns
        assert "metric_returns" in df.columns
        assert "execution_time" in df.columns

        # Check caching
        df2 = sample_results.to_dataframe()
        assert df is df2  # Should return cached version

    def test_get_best_results(self, sample_results):
        """Test getting best results."""
        # Maximize sharpe
        best = sample_results.get_best_results("sharpe", n=3, minimize=False)
        assert len(best) == 3
        assert best[0].metrics["sharpe"] == 1.9  # Highest sharpe
        assert best[1].metrics["sharpe"] == 1.8
        assert best[2].metrics["sharpe"] == 1.7

        # Minimize max_dd
        best_dd = sample_results.get_best_results("max_dd", n=3, minimize=True)
        assert len(best_dd) == 3
        assert best_dd[0].metrics["max_dd"] == -0.1  # Least negative

    def test_pareto_frontier(self, sample_results):
        """Test Pareto frontier calculation."""
        # Two objectives: maximize sharpe, minimize abs(max_dd)
        pareto = sample_results.get_pareto_frontier(
            ["sharpe", "max_dd"], minimize=[False, True]
        )

        assert len(pareto) > 0
        assert len(pareto) <= 10

        # All Pareto points should be non-dominated
        for i, p1 in enumerate(pareto):
            for j, p2 in enumerate(pareto):
                if i != j:
                    # p2 should not dominate p1
                    better_sharpe = p2.metrics["sharpe"] > p1.metrics["sharpe"]
                    better_dd = (
                        p2.metrics["max_dd"] > p1.metrics["max_dd"]
                    )  # Less negative is better
                    assert not (better_sharpe and better_dd)

    def test_parameter_sensitivity(self, sample_results):
        """Test parameter sensitivity analysis."""
        sensitivity = sample_results.get_parameter_sensitivity("alpha", "sharpe")

        assert len(sensitivity) == 10  # One row per unique alpha value
        assert "alpha" in sensitivity.columns
        assert "mean" in sensitivity.columns
        assert "std" in sensitivity.columns
        assert "min" in sensitivity.columns
        assert "max" in sensitivity.columns
        assert "count" in sensitivity.columns

        # Check ordering
        assert sensitivity["alpha"].is_monotonic_increasing

    def test_filter_by_parameters(self, sample_results):
        """Test filtering by parameters."""
        # Filter by exact value
        filtered = sample_results.filter_by_parameters({"method": "fast"})
        assert filtered.size == 5

        # Filter by list of values
        filtered = sample_results.filter_by_parameters({"method": ["fast", "slow"]})
        assert filtered.size == 10

        # Filter by function
        filtered = sample_results.filter_by_parameters({"alpha": lambda x: x > 0.5})
        assert filtered.size == 5

        # Multiple constraints
        filtered = sample_results.filter_by_parameters(
            {"method": "fast", "alpha": lambda x: x > 0.3}
        )
        assert filtered.size == 2

    def test_save_load_json(self, sample_results):
        """Test saving and loading JSON format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "results.json"

            # Save
            sample_results.save_to_file(filepath, format="json")
            assert filepath.exists()

            # Load
            loaded = OptimizationResultSet.load_from_file(filepath)
            assert loaded.size == sample_results.size

            # Check content
            for orig, loaded_res in zip(sample_results.results, loaded.results):
                assert orig.parameters == loaded_res.parameters
                assert orig.metrics == loaded_res.metrics
                assert orig.execution_time == loaded_res.execution_time

    def test_save_load_csv(self, sample_results):
        """Test saving and loading CSV format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "results.csv"

            # Save
            sample_results.save_to_file(filepath, format="csv")
            assert filepath.exists()

            # Load
            loaded = OptimizationResultSet.load_from_file(filepath)
            assert loaded.size == sample_results.size

            # Check content (note: CSV loading may have minor precision differences)
            for orig, loaded_res in zip(sample_results.results, loaded.results):
                assert set(orig.parameters.keys()) == set(loaded_res.parameters.keys())
                assert set(orig.metrics.keys()) == set(loaded_res.metrics.keys())

    def test_summary_statistics(self, sample_results):
        """Test summary statistics calculation."""
        summary = sample_results.get_summary_statistics()

        assert summary["total_results"] == 10
        assert "total_execution_time" in summary
        assert "average_execution_time" in summary
        assert "metrics" in summary

        # Check metric statistics
        assert "sharpe" in summary["metrics"]
        sharpe_stats = summary["metrics"]["sharpe"]
        assert "mean" in sharpe_stats
        assert "std" in sharpe_stats
        assert "min" in sharpe_stats
        assert "max" in sharpe_stats
        assert "median" in sharpe_stats

        # Verify calculations
        assert sharpe_stats["min"] == 1.0
        assert sharpe_stats["max"] == 1.9
        assert abs(sharpe_stats["mean"] - 1.45) < 0.01

    def test_empty_result_set(self):
        """Test empty result set behavior."""
        empty_set = OptimizationResultSet()

        assert empty_set.size == 0
        assert empty_set.to_dataframe().empty
        assert empty_set.get_best_results("metric", n=5) == []
        assert empty_set.get_pareto_frontier(["a", "b"]) == []
        assert empty_set.get_summary_statistics() == {}
