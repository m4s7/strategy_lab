"""Optimization results management."""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


@dataclass
class OptimizationResult:
    """Single optimization result."""

    parameters: dict[str, Any]
    metrics: dict[str, float]
    execution_time: float
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def primary_metric(self) -> float | None:
        """Get primary metric value (first metric)."""
        if not self.metrics:
            return None
        return next(iter(self.metrics.values()))

    def get_metric(self, name: str) -> float | None:
        """Get specific metric value."""
        return self.metrics.get(name)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "parameters": self.parameters,
            "metrics": self.metrics,
            "execution_time": self.execution_time,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OptimizationResult":
        """Create from dictionary."""
        return cls(
            parameters=data["parameters"],
            metrics=data["metrics"],
            execution_time=data["execution_time"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {}),
        )


class OptimizationResultSet:
    """Collection of optimization results with analysis capabilities."""

    def __init__(self, results: list[OptimizationResult] | None = None):
        """Initialize result set.

        Args:
            results: Initial list of results
        """
        self.results = results or []
        self._df_cache: pd.DataFrame | None = None

    def add_result(self, result: OptimizationResult) -> None:
        """Add a result to the set."""
        self.results.append(result)
        self._df_cache = None  # Invalidate cache

    def add_results(self, results: list[OptimizationResult]) -> None:
        """Add multiple results."""
        self.results.extend(results)
        self._df_cache = None  # Invalidate cache

    @property
    def size(self) -> int:
        """Get number of results."""
        return len(self.results)

    def to_dataframe(self) -> pd.DataFrame:
        """Convert results to pandas DataFrame."""
        if self._df_cache is not None:
            return self._df_cache

        if not self.results:
            return pd.DataFrame()

        # Extract data
        rows = []
        for result in self.results:
            row = {
                **{f"param_{k}": v for k, v in result.parameters.items()},
                **{f"metric_{k}": v for k, v in result.metrics.items()},
                "execution_time": result.execution_time,
                "timestamp": result.timestamp,
            }
            rows.append(row)

        self._df_cache = pd.DataFrame(rows)
        return self._df_cache

    def get_best_results(
        self, metric: str, n: int = 10, minimize: bool = False
    ) -> list[OptimizationResult]:
        """Get best results by metric.

        Args:
            metric: Metric name to rank by
            n: Number of results to return
            minimize: Whether to minimize (True) or maximize (False) the metric

        Returns:
            List of best results
        """
        # Sort results by metric
        sorted_results = sorted(
            self.results,
            key=lambda r: r.get_metric(metric) or float("inf" if minimize else "-inf"),
            reverse=not minimize,
        )

        return sorted_results[:n]

    def get_pareto_frontier(
        self, metrics: list[str], minimize: list[bool] | None = None
    ) -> list[OptimizationResult]:
        """Get Pareto optimal results for multi-objective optimization.

        Args:
            metrics: List of metric names to consider
            minimize: List of booleans indicating whether to minimize each metric
                     (defaults to False for all)

        Returns:
            List of Pareto optimal results
        """
        if not self.results:
            return []

        if minimize is None:
            minimize = [False] * len(metrics)

        # Extract metric values
        points = []
        valid_results = []

        for result in self.results:
            values = []
            valid = True

            for metric in metrics:
                value = result.get_metric(metric)
                if value is None:
                    valid = False
                    break
                values.append(value)

            if valid:
                points.append(values)
                valid_results.append(result)

        if not points:
            return []

        points = np.array(points)

        # Find Pareto frontier
        pareto_mask = np.ones(len(points), dtype=bool)

        for i in range(len(points)):
            if not pareto_mask[i]:
                continue

            # Check if point i is dominated by any other point
            for j in range(len(points)):
                if i == j or not pareto_mask[j]:
                    continue

                # Check domination
                better = []
                for k, minimize_k in enumerate(minimize):
                    if minimize_k:
                        better.append(points[j, k] <= points[i, k])
                    else:
                        better.append(points[j, k] >= points[i, k])

                # If j dominates i (better or equal in all, strictly better in at least one)
                if all(better) and any(
                    points[j, k] < points[i, k]
                    if minimize[k]
                    else points[j, k] > points[i, k]
                    for k in range(len(metrics))
                ):
                    pareto_mask[i] = False
                    break

        return [result for i, result in enumerate(valid_results) if pareto_mask[i]]

    def get_parameter_sensitivity(self, parameter: str, metric: str) -> pd.DataFrame:
        """Analyze parameter sensitivity.

        Args:
            parameter: Parameter name to analyze
            metric: Metric to measure sensitivity against

        Returns:
            DataFrame with sensitivity analysis
        """
        df = self.to_dataframe()

        if df.empty:
            return pd.DataFrame()

        param_col = f"param_{parameter}"
        metric_col = f"metric_{metric}"

        if param_col not in df.columns or metric_col not in df.columns:
            return pd.DataFrame()

        # Group by parameter value and calculate statistics
        sensitivity = (
            df.groupby(param_col)[metric_col]
            .agg(["mean", "std", "min", "max", "count"])
            .reset_index()
        )

        sensitivity.columns = [parameter, "mean", "std", "min", "max", "count"]

        return sensitivity

    def filter_by_parameters(
        self, constraints: dict[str, Any]
    ) -> "OptimizationResultSet":
        """Filter results by parameter constraints.

        Args:
            constraints: Dictionary of parameter constraints

        Returns:
            New OptimizationResultSet with filtered results
        """
        filtered_results = []

        for result in self.results:
            match = True
            for param, value in constraints.items():
                if param not in result.parameters:
                    match = False
                    break

                # Handle different constraint types
                if isinstance(value, (list, tuple)):
                    if result.parameters[param] not in value:
                        match = False
                        break
                elif callable(value):
                    if not value(result.parameters[param]):
                        match = False
                        break
                else:
                    if result.parameters[param] != value:
                        match = False
                        break

            if match:
                filtered_results.append(result)

        return OptimizationResultSet(filtered_results)

    def save_to_file(self, filepath: Path, format: str = "json") -> None:
        """Save results to file.

        Args:
            filepath: Path to save file
            format: File format ('json' or 'csv')
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        if format == "json":
            data = [result.to_dict() for result in self.results]
            with open(filepath, "w") as f:
                json.dump(data, f, indent=2)

        elif format == "csv":
            df = self.to_dataframe()
            df.to_csv(filepath, index=False)

        else:
            raise ValueError(f"Unsupported format: {format}")

    @classmethod
    def load_from_file(cls, filepath: Path) -> "OptimizationResultSet":
        """Load results from file.

        Args:
            filepath: Path to load from

        Returns:
            OptimizationResultSet
        """
        filepath = Path(filepath)

        if filepath.suffix == ".json":
            with open(filepath) as f:
                data = json.load(f)
            results = [OptimizationResult.from_dict(d) for d in data]
            return cls(results)

        if filepath.suffix == ".csv":
            df = pd.read_csv(filepath)
            results = []

            # Extract parameters and metrics from columns
            param_cols = [col for col in df.columns if col.startswith("param_")]
            metric_cols = [col for col in df.columns if col.startswith("metric_")]

            for _, row in df.iterrows():
                parameters = {col[6:]: row[col] for col in param_cols}
                metrics = {col[7:]: row[col] for col in metric_cols}

                result = OptimizationResult(
                    parameters=parameters,
                    metrics=metrics,
                    execution_time=row.get("execution_time", 0.0),
                    timestamp=pd.to_datetime(row.get("timestamp", datetime.now())),
                )
                results.append(result)

            return cls(results)

        raise ValueError(f"Unsupported file type: {filepath.suffix}")

    def get_summary_statistics(self) -> dict[str, Any]:
        """Get summary statistics for the result set."""
        if not self.results:
            return {}

        df = self.to_dataframe()

        # Get metric columns
        metric_cols = [col for col in df.columns if col.startswith("metric_")]

        summary = {
            "total_results": len(self.results),
            "total_execution_time": sum(r.execution_time for r in self.results),
            "average_execution_time": np.mean([r.execution_time for r in self.results]),
            "metrics": {},
        }

        # Calculate statistics for each metric
        for col in metric_cols:
            metric_name = col[7:]  # Remove "metric_" prefix
            summary["metrics"][metric_name] = {
                "mean": df[col].mean(),
                "std": df[col].std(),
                "min": df[col].min(),
                "max": df[col].max(),
                "median": df[col].median(),
            }

        return summary

    def __repr__(self) -> str:
        """String representation."""
        return f"OptimizationResultSet(size={self.size})"
