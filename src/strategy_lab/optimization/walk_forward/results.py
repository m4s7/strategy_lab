"""Walk-forward analysis results management."""

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class WalkForwardResult:
    """Results from a single walk-forward window."""

    window_id: int
    in_sample_start: datetime
    in_sample_end: datetime
    out_of_sample_start: datetime
    out_of_sample_end: datetime

    # Optimal parameters from in-sample optimization
    optimal_parameters: Dict[str, Any]

    # Performance metrics
    in_sample_metrics: Dict[str, float]
    out_of_sample_metrics: Dict[str, float]

    # Optimization details
    optimization_time: float
    backtest_time: float
    n_parameter_combinations: int

    # Parameter stability (optional)
    parameter_changes: Optional[Dict[str, float]] = None
    parameter_stability_score: Optional[float] = None

    # Statistical validation (optional)
    statistical_tests: Optional[Dict[str, float]] = None
    is_significant: Optional[bool] = None

    @property
    def in_sample_period(self) -> Tuple[datetime, datetime]:
        """Get in-sample period tuple."""
        return (self.in_sample_start, self.in_sample_end)

    @property
    def out_of_sample_period(self) -> Tuple[datetime, datetime]:
        """Get out-of-sample period tuple."""
        return (self.out_of_sample_start, self.out_of_sample_end)

    @property
    def performance_ratio(self) -> Dict[str, float]:
        """Calculate out-of-sample / in-sample performance ratios."""
        ratios = {}

        for metric in self.in_sample_metrics:
            if metric in self.out_of_sample_metrics:
                in_sample_value = self.in_sample_metrics[metric]
                out_of_sample_value = self.out_of_sample_metrics[metric]

                if in_sample_value != 0:
                    ratios[metric] = out_of_sample_value / in_sample_value
                else:
                    ratios[metric] = np.inf if out_of_sample_value > 0 else 0.0

        return ratios

    def get_degradation_score(self, primary_metric: str = "sharpe_ratio") -> float:
        """Calculate performance degradation score.

        Score > 1.0: Out-of-sample better than in-sample
        Score = 1.0: Same performance
        Score < 1.0: Performance degradation
        Score < 0.5: Severe degradation (potential overfitting)
        """
        if primary_metric not in self.performance_ratio:
            return 0.0

        return self.performance_ratio[primary_metric]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        # Convert datetime objects to ISO format
        data["in_sample_start"] = self.in_sample_start.isoformat()
        data["in_sample_end"] = self.in_sample_end.isoformat()
        data["out_of_sample_start"] = self.out_of_sample_start.isoformat()
        data["out_of_sample_end"] = self.out_of_sample_end.isoformat()
        return data


class WalkForwardResultSet:
    """Collection of walk-forward analysis results."""

    def __init__(self):
        """Initialize result set."""
        self.results: List[WalkForwardResult] = []
        self._df_cache: Optional[pd.DataFrame] = None

    def add_result(self, result: WalkForwardResult) -> None:
        """Add a walk-forward result."""
        self.results.append(result)
        self._df_cache = None  # Invalidate cache

    def get_result(self, window_id: int) -> Optional[WalkForwardResult]:
        """Get result by window ID."""
        for result in self.results:
            if result.window_id == window_id:
                return result
        return None

    @property
    def size(self) -> int:
        """Get number of results."""
        return len(self.results)

    def to_dataframe(self) -> pd.DataFrame:
        """Convert results to DataFrame.

        Returns:
            DataFrame with one row per window
        """
        if self._df_cache is not None:
            return self._df_cache

        if not self.results:
            return pd.DataFrame()

        rows = []
        for result in self.results:
            row = {
                "window_id": result.window_id,
                "in_sample_start": result.in_sample_start,
                "in_sample_end": result.in_sample_end,
                "out_of_sample_start": result.out_of_sample_start,
                "out_of_sample_end": result.out_of_sample_end,
                "optimization_time": result.optimization_time,
                "backtest_time": result.backtest_time,
                "n_parameters": result.n_parameter_combinations,
            }

            # Add parameters
            for param, value in result.optimal_parameters.items():
                row[f"param_{param}"] = value

            # Add in-sample metrics
            for metric, value in result.in_sample_metrics.items():
                row[f"in_sample_{metric}"] = value

            # Add out-of-sample metrics
            for metric, value in result.out_of_sample_metrics.items():
                row[f"out_of_sample_{metric}"] = value

            # Add performance ratios
            for metric, ratio in result.performance_ratio.items():
                row[f"ratio_{metric}"] = ratio

            # Add optional fields
            if result.parameter_stability_score is not None:
                row["parameter_stability"] = result.parameter_stability_score

            if result.is_significant is not None:
                row["is_significant"] = result.is_significant

            rows.append(row)

        self._df_cache = pd.DataFrame(rows)
        return self._df_cache

    def get_parameter_evolution(self) -> pd.DataFrame:
        """Get parameter evolution over time.

        Returns:
            DataFrame with parameters as columns, windows as rows
        """
        if not self.results:
            return pd.DataFrame()

        # Get all parameter names
        all_params = set()
        for result in self.results:
            all_params.update(result.optimal_parameters.keys())

        # Build evolution data
        rows = []
        for result in self.results:
            row = {
                "window_id": result.window_id,
                "out_of_sample_start": result.out_of_sample_start,
            }
            for param in all_params:
                row[param] = result.optimal_parameters.get(param, np.nan)
            rows.append(row)

        df = pd.DataFrame(rows)
        df.set_index("out_of_sample_start", inplace=True)
        return df

    def calculate_aggregate_metrics(self) -> Dict[str, Any]:
        """Calculate aggregate performance metrics."""
        if not self.results:
            return {}

        df = self.to_dataframe()

        # Get metric columns
        in_sample_cols = [col for col in df.columns if col.startswith("in_sample_")]
        out_of_sample_cols = [
            col for col in df.columns if col.startswith("out_of_sample_")
        ]
        ratio_cols = [col for col in df.columns if col.startswith("ratio_")]

        aggregate = {
            "n_windows": len(self.results),
            "total_optimization_time": df["optimization_time"].sum(),
            "total_backtest_time": df["backtest_time"].sum(),
        }

        # Calculate mean and std for each metric type
        for cols, prefix in [
            (in_sample_cols, "in_sample"),
            (out_of_sample_cols, "out_of_sample"),
            (ratio_cols, "ratio"),
        ]:
            for col in cols:
                metric_name = col.replace(f"{prefix}_", "")
                aggregate[f"mean_{prefix}_{metric_name}"] = df[col].mean()
                aggregate[f"std_{prefix}_{metric_name}"] = df[col].std()

        # Calculate overfitting indicators
        if "ratio_sharpe_ratio" in df.columns:
            sharpe_ratios = df["ratio_sharpe_ratio"]
            aggregate["overfitting_indicators"] = {
                "mean_performance_ratio": sharpe_ratios.mean(),
                "windows_with_degradation": (sharpe_ratios < 1.0).sum(),
                "windows_with_severe_degradation": (sharpe_ratios < 0.5).sum(),
                "consistency_score": 1.0 - sharpe_ratios.std(),
            }

        # Parameter stability
        param_cols = [col for col in df.columns if col.startswith("param_")]
        if param_cols:
            param_stability = {}
            for col in param_cols:
                param_name = col.replace("param_", "")
                values = df[col]
                if values.dtype in [np.float64, np.int64]:
                    param_stability[param_name] = {
                        "cv": values.std() / values.mean()
                        if values.mean() != 0
                        else np.inf,
                        "range": values.max() - values.min(),
                        "drift": np.polyfit(range(len(values)), values, 1)[
                            0
                        ],  # Linear trend
                    }
            aggregate["parameter_stability"] = param_stability

        return aggregate

    def identify_breakdown_periods(
        self, metric: str = "sharpe_ratio", threshold: float = 0.5
    ) -> List[Dict[str, Any]]:
        """Identify periods where strategy breaks down.

        Args:
            metric: Metric to use for breakdown detection
            threshold: Performance ratio threshold for breakdown

        Returns:
            List of breakdown periods with details
        """
        breakdowns = []

        for result in self.results:
            ratio = result.performance_ratio.get(metric, 1.0)

            if ratio < threshold:
                breakdowns.append(
                    {
                        "window_id": result.window_id,
                        "out_of_sample_period": result.out_of_sample_period,
                        "performance_ratio": ratio,
                        "in_sample_value": result.in_sample_metrics.get(metric),
                        "out_of_sample_value": result.out_of_sample_metrics.get(metric),
                        "parameters": result.optimal_parameters,
                    }
                )

        return breakdowns

    def save(self, filepath: Path) -> None:
        """Save results to file."""
        data = {
            "results": [result.to_dict() for result in self.results],
            "aggregate_metrics": self.calculate_aggregate_metrics(),
        }

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2, default=str)

        logger.info(f"Saved {len(self.results)} walk-forward results to {filepath}")

    @classmethod
    def load(cls, filepath: Path) -> "WalkForwardResultSet":
        """Load results from file."""
        with open(filepath, "r") as f:
            data = json.load(f)

        result_set = cls()

        for result_data in data["results"]:
            # Convert ISO strings back to datetime
            for date_field in [
                "in_sample_start",
                "in_sample_end",
                "out_of_sample_start",
                "out_of_sample_end",
            ]:
                result_data[date_field] = datetime.fromisoformat(
                    result_data[date_field]
                )

            result = WalkForwardResult(**result_data)
            result_set.add_result(result)

        logger.info(f"Loaded {result_set.size} walk-forward results from {filepath}")
        return result_set

    def __repr__(self) -> str:
        """String representation."""
        return f"WalkForwardResultSet(n_results={self.size})"
