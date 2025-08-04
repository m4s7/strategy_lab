"""Statistical validation for walk-forward analysis."""

import logging
from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy import stats

logger = logging.getLogger(__name__)


@dataclass
class StatisticalTests:
    """Results from statistical validation tests."""

    # T-test for in-sample vs out-of-sample performance
    t_statistic: float
    t_p_value: float
    t_significant: bool

    # Wilcoxon signed-rank test (non-parametric)
    wilcoxon_statistic: float | None = None
    wilcoxon_p_value: float | None = None
    wilcoxon_significant: bool | None = None

    # Bootstrap confidence intervals
    bootstrap_mean: float | None = None
    bootstrap_ci_lower: float | None = None
    bootstrap_ci_upper: float | None = None
    bootstrap_percentile: float | None = None

    # Overall assessment
    is_robust: bool = False
    confidence_level: float = 0.0

    def to_dict(self) -> dict[str, float]:
        """Convert to dictionary."""
        return {
            "t_statistic": self.t_statistic,
            "t_p_value": self.t_p_value,
            "t_significant": float(self.t_significant),
            "wilcoxon_statistic": self.wilcoxon_statistic or 0.0,
            "wilcoxon_p_value": self.wilcoxon_p_value or 0.0,
            "bootstrap_mean": self.bootstrap_mean or 0.0,
            "bootstrap_ci_lower": self.bootstrap_ci_lower or 0.0,
            "bootstrap_ci_upper": self.bootstrap_ci_upper or 0.0,
            "is_robust": float(self.is_robust),
            "confidence_level": self.confidence_level,
        }


class PerformanceValidator:
    """Validates walk-forward performance with statistical tests."""

    def __init__(
        self,
        significance_level: float = 0.05,
        bootstrap_samples: int = 1000,
        min_windows_for_test: int = 5,
    ):
        """Initialize validator.

        Args:
            significance_level: Alpha level for statistical tests
            bootstrap_samples: Number of bootstrap resamples
            min_windows_for_test: Minimum windows needed for valid test
        """
        self.significance_level = significance_level
        self.bootstrap_samples = bootstrap_samples
        self.min_windows_for_test = min_windows_for_test

    def validate_performance(
        self,
        in_sample_values: list[float],
        out_of_sample_values: list[float],
        metric_name: str = "performance",
    ) -> StatisticalTests:
        """Run statistical validation tests.

        Args:
            in_sample_values: In-sample performance values
            out_of_sample_values: Out-of-sample performance values
            metric_name: Name of metric being tested

        Returns:
            StatisticalTests results
        """
        n = len(in_sample_values)

        if n != len(out_of_sample_values):
            raise ValueError("In-sample and out-of-sample lists must have same length")

        if n < self.min_windows_for_test:
            logger.warning(
                f"Only {n} windows available, need {self.min_windows_for_test} "
                f"for reliable statistical tests"
            )

        # Calculate performance differences
        differences = np.array(out_of_sample_values) - np.array(in_sample_values)

        # T-test for paired samples
        t_stat, t_p = self._paired_t_test(differences)
        t_significant = t_p < self.significance_level

        # Wilcoxon signed-rank test (non-parametric alternative)
        wilcoxon_stat = None
        wilcoxon_p = None
        wilcoxon_significant = None

        if n >= 5:  # Wilcoxon needs at least 5 samples
            try:
                wilcoxon_stat, wilcoxon_p = stats.wilcoxon(differences)
                wilcoxon_significant = wilcoxon_p < self.significance_level
            except Exception as e:
                logger.warning(f"Wilcoxon test failed: {e}")

        # Bootstrap analysis
        bootstrap_mean = None
        bootstrap_ci_lower = None
        bootstrap_ci_upper = None
        bootstrap_percentile = None

        if n >= self.min_windows_for_test:
            bootstrap_results = self._bootstrap_analysis(
                in_sample_values, out_of_sample_values
            )
            bootstrap_mean = bootstrap_results["mean"]
            bootstrap_ci_lower = bootstrap_results["ci_lower"]
            bootstrap_ci_upper = bootstrap_results["ci_upper"]
            bootstrap_percentile = bootstrap_results["percentile"]

        # Overall robustness assessment
        is_robust, confidence = self._assess_robustness(
            t_significant,
            wilcoxon_significant,
            bootstrap_ci_lower,
            bootstrap_ci_upper,
            differences,
        )

        return StatisticalTests(
            t_statistic=t_stat,
            t_p_value=t_p,
            t_significant=t_significant,
            wilcoxon_statistic=wilcoxon_stat,
            wilcoxon_p_value=wilcoxon_p,
            wilcoxon_significant=wilcoxon_significant,
            bootstrap_mean=bootstrap_mean,
            bootstrap_ci_lower=bootstrap_ci_lower,
            bootstrap_ci_upper=bootstrap_ci_upper,
            bootstrap_percentile=bootstrap_percentile,
            is_robust=is_robust,
            confidence_level=confidence,
        )

    def _paired_t_test(self, differences: np.ndarray) -> tuple[float, float]:
        """Perform paired t-test on differences.

        H0: Mean difference = 0 (no performance degradation)
        H1: Mean difference < 0 (performance degradation)
        """
        if len(differences) < 2:
            return 0.0, 1.0

        # One-sample t-test on differences
        t_stat, p_value = stats.ttest_1samp(differences, 0)

        # Convert to one-tailed p-value (testing for degradation)
        if t_stat < 0:
            p_value = p_value / 2
        else:
            p_value = 1 - p_value / 2

        return t_stat, p_value

    def _bootstrap_analysis(
        self, in_sample: list[float], out_of_sample: list[float]
    ) -> dict[str, float]:
        """Perform bootstrap analysis on performance ratios.

        Returns:
            Dictionary with bootstrap statistics
        """
        n = len(in_sample)
        ratios = []

        # Calculate bootstrap samples
        for _ in range(self.bootstrap_samples):
            # Resample with replacement
            indices = np.random.choice(n, size=n, replace=True)

            # Calculate mean ratio for this sample
            sample_in = [in_sample[i] for i in indices]
            sample_out = [out_of_sample[i] for i in indices]

            # Calculate performance ratio
            mean_in = np.mean(sample_in)
            mean_out = np.mean(sample_out)

            if mean_in != 0:
                ratio = mean_out / mean_in
            else:
                ratio = 1.0

            ratios.append(ratio)

        # Calculate bootstrap statistics
        ratios = np.array(ratios)

        return {
            "mean": np.mean(ratios),
            "std": np.std(ratios),
            "ci_lower": np.percentile(ratios, (self.significance_level / 2) * 100),
            "ci_upper": np.percentile(ratios, (1 - self.significance_level / 2) * 100),
            "percentile": np.mean(ratios < 1.0),  # Percentage showing degradation
        }

    def _assess_robustness(
        self,
        t_significant: bool,
        wilcoxon_significant: bool | None,
        bootstrap_ci_lower: float | None,
        bootstrap_ci_upper: float | None,
        differences: np.ndarray,
    ) -> tuple[bool, float]:
        """Assess overall robustness of strategy.

        Returns:
            Tuple of (is_robust, confidence_level)
        """
        confidence_score = 0.0
        checks_passed = 0
        total_checks = 0

        # Check 1: No significant degradation (t-test)
        total_checks += 1
        if not t_significant:
            checks_passed += 1
            confidence_score += 0.3

        # Check 2: No significant degradation (Wilcoxon)
        if wilcoxon_significant is not None:
            total_checks += 1
            if not wilcoxon_significant:
                checks_passed += 1
                confidence_score += 0.2

        # Check 3: Bootstrap CI includes 1.0 (no degradation)
        if bootstrap_ci_lower is not None and bootstrap_ci_upper is not None:
            total_checks += 1
            if bootstrap_ci_lower <= 1.0 <= bootstrap_ci_upper:
                checks_passed += 1
                confidence_score += 0.3

        # Check 4: Mean performance ratio > threshold
        mean_diff = np.mean(differences)
        total_checks += 1
        if mean_diff > -0.1:  # Less than 10% degradation
            checks_passed += 1
            confidence_score += 0.2

        # Determine if robust
        is_robust = checks_passed >= total_checks * 0.5  # At least half checks pass

        return is_robust, min(confidence_score, 1.0)

    def calculate_parameter_stability(
        self, parameter_values: dict[str, list[float]]
    ) -> dict[str, float]:
        """Calculate stability scores for each parameter.

        Args:
            parameter_values: Dictionary mapping parameter names to
                            lists of values across windows

        Returns:
            Dictionary of stability scores (0-1, higher is more stable)
        """
        stability_scores = {}

        for param_name, values in parameter_values.items():
            if len(values) < 2:
                stability_scores[param_name] = 1.0
                continue

            values = np.array(values)

            # Skip if all values are the same
            if np.all(values == values[0]):
                stability_scores[param_name] = 1.0
                continue

            # Calculate coefficient of variation
            cv = np.std(values) / np.mean(values) if np.mean(values) != 0 else 1.0

            # Calculate trend (absolute slope of linear fit)
            x = np.arange(len(values))
            slope = np.abs(np.polyfit(x, values, 1)[0])
            normalized_slope = slope / np.mean(values) if np.mean(values) != 0 else 0

            # Combine metrics (lower is more stable)
            instability = (cv + normalized_slope) / 2

            # Convert to stability score (0-1, higher is better)
            stability_scores[param_name] = 1.0 / (1.0 + instability)

        return stability_scores

    def detect_overfitting(
        self, performance_ratios: list[float], parameter_changes: list[float]
    ) -> dict[str, Any]:
        """Detect signs of overfitting.

        Args:
            performance_ratios: Out-of-sample / in-sample ratios
            parameter_changes: Parameter change magnitudes

        Returns:
            Dictionary with overfitting indicators
        """
        indicators = {"likely_overfitted": False, "confidence": 0.0, "reasons": []}

        overfitting_score = 0.0

        # Indicator 1: Poor out-of-sample performance
        mean_ratio = np.mean(performance_ratios)
        if mean_ratio < 0.7:
            overfitting_score += 0.4
            indicators["reasons"].append(
                f"Poor out-of-sample performance (ratio={mean_ratio:.2f})"
            )

        # Indicator 2: High performance variance
        ratio_std = np.std(performance_ratios)
        if ratio_std > 0.5:
            overfitting_score += 0.2
            indicators["reasons"].append(
                f"High performance variance (std={ratio_std:.2f})"
            )

        # Indicator 3: Unstable parameters
        if parameter_changes:
            mean_change = np.mean(parameter_changes)
            if mean_change > 0.3:
                overfitting_score += 0.2
                indicators["reasons"].append(
                    f"Unstable parameters (mean change={mean_change:.2f})"
                )

        # Indicator 4: Consistent degradation trend
        if len(performance_ratios) >= 5:
            x = np.arange(len(performance_ratios))
            slope = np.polyfit(x, performance_ratios, 1)[0]
            if slope < -0.05:
                overfitting_score += 0.2
                indicators["reasons"].append(
                    f"Degrading performance trend (slope={slope:.3f})"
                )

        # Set overall assessment
        indicators["confidence"] = min(overfitting_score, 1.0)
        indicators["likely_overfitted"] = overfitting_score >= 0.5

        return indicators
