"""Strategy comparison and benchmarking framework."""

import logging

import numpy as np
import pandas as pd
from scipy import stats

from .metrics import MetricsCalculator

logger = logging.getLogger(__name__)


class StrategyComparator:
    """Compares multiple strategies and performs statistical analysis."""

    def __init__(self, risk_free_rate: float = 0.02):
        """Initialize comparator.

        Args:
            risk_free_rate: Annual risk-free rate
        """
        self.risk_free_rate = risk_free_rate
        self.metrics_calculator = MetricsCalculator(risk_free_rate)

    def compare_strategies(
        self,
        strategies: dict[str, dict[str, pd.DataFrame]],
        benchmark: pd.Series | None = None,
    ) -> pd.DataFrame:
        """Compare multiple strategies side by side.

        Args:
            strategies: Dict mapping strategy names to their data
            benchmark: Optional benchmark returns

        Returns:
            DataFrame with comparison metrics
        """
        comparison_data = []

        for name, data in strategies.items():
            # Calculate metrics for each strategy
            metrics = self.metrics_calculator.calculate_metrics(
                data["equity_curve"], data["trades"], benchmark
            )

            # Create row for comparison
            row = {
                "strategy": name,
                "total_return": metrics.total_return,
                "annual_return": metrics.annualized_return,
                "volatility": metrics.volatility,
                "sharpe_ratio": metrics.sharpe_ratio,
                "sortino_ratio": metrics.sortino_ratio,
                "calmar_ratio": metrics.calmar_ratio,
                "max_drawdown": metrics.max_drawdown,
                "var_95": metrics.var_95,
                "win_rate": metrics.win_rate,
                "profit_factor": metrics.profit_factor,
                "total_trades": metrics.total_trades,
                "avg_trade": metrics.avg_trade,
                "recovery_factor": metrics.recovery_factor,
            }

            comparison_data.append(row)

        # Create comparison DataFrame
        comparison_df = pd.DataFrame(comparison_data)
        comparison_df.set_index("strategy", inplace=True)

        # Add rankings
        self._add_rankings(comparison_df)

        return comparison_df

    def calculate_correlation_matrix(
        self, strategies: dict[str, pd.Series]
    ) -> pd.DataFrame:
        """Calculate correlation matrix between strategy returns.

        Args:
            strategies: Dict mapping strategy names to return series

        Returns:
            Correlation matrix DataFrame
        """
        # Align all return series to common dates
        returns_df = pd.DataFrame(strategies)
        returns_df = returns_df.dropna()

        # Calculate correlation matrix
        correlation_matrix = returns_df.corr()

        return correlation_matrix

    def perform_statistical_tests(
        self, strategy1: pd.Series, strategy2: pd.Series
    ) -> dict[str, float]:
        """Perform statistical tests between two strategies.

        Args:
            strategy1: First strategy equity curve
            strategy2: Second strategy equity curve

        Returns:
            Dictionary with test results
        """
        # Calculate returns
        returns1 = strategy1.pct_change().dropna()
        returns2 = strategy2.pct_change().dropna()

        # Align returns
        aligned = pd.DataFrame({"s1": returns1, "s2": returns2}).dropna()

        results = {}

        # T-test for mean returns
        t_stat, t_pvalue = stats.ttest_ind(aligned["s1"], aligned["s2"])
        results["t_test_statistic"] = t_stat
        results["t_test_pvalue"] = t_pvalue
        results["means_different"] = t_pvalue < 0.05

        # F-test for variance
        f_stat = np.var(aligned["s1"]) / np.var(aligned["s2"])
        f_pvalue = stats.f.cdf(f_stat, len(aligned) - 1, len(aligned) - 1)
        results["f_test_statistic"] = f_stat
        results["f_test_pvalue"] = f_pvalue
        results["variances_different"] = f_pvalue < 0.05

        # Mann-Whitney U test (non-parametric)
        u_stat, u_pvalue = stats.mannwhitneyu(aligned["s1"], aligned["s2"])
        results["mann_whitney_statistic"] = u_stat
        results["mann_whitney_pvalue"] = u_pvalue

        # Sharpe ratio test
        sharpe1 = aligned["s1"].mean() / aligned["s1"].std() * np.sqrt(252)
        sharpe2 = aligned["s2"].mean() / aligned["s2"].std() * np.sqrt(252)
        results["sharpe_difference"] = sharpe1 - sharpe2

        return results

    def calculate_efficient_frontier(
        self, strategies: dict[str, pd.Series], n_portfolios: int = 1000
    ) -> pd.DataFrame:
        """Calculate efficient frontier for strategy combinations.

        Args:
            strategies: Dict mapping strategy names to equity curves
            n_portfolios: Number of portfolios to simulate

        Returns:
            DataFrame with efficient frontier points
        """
        # Calculate returns for each strategy
        returns = {}
        for name, equity in strategies.items():
            returns[name] = equity.pct_change().dropna()

        # Align returns
        returns_df = pd.DataFrame(returns).dropna()

        # Calculate mean returns and covariance
        mean_returns = returns_df.mean() * 252  # Annualized
        cov_matrix = returns_df.cov() * 252  # Annualized

        # Generate random portfolio weights
        portfolios = []
        np.random.seed(42)

        for _ in range(n_portfolios):
            # Random weights
            weights = np.random.random(len(strategies))
            weights /= weights.sum()

            # Portfolio statistics
            portfolio_return = np.dot(weights, mean_returns)
            portfolio_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
            portfolio_sharpe = (portfolio_return - self.risk_free_rate) / portfolio_vol

            portfolios.append(
                {
                    "return": portfolio_return,
                    "volatility": portfolio_vol,
                    "sharpe": portfolio_sharpe,
                    **{
                        f"weight_{name}": w
                        for name, w in zip(strategies.keys(), weights)
                    },
                }
            )

        frontier_df = pd.DataFrame(portfolios)

        # Find efficient frontier
        frontier_df["is_efficient"] = False
        for idx, row in frontier_df.iterrows():
            # Check if any other portfolio has higher return with same or lower volatility
            better_exists = (
                (frontier_df["return"] > row["return"])
                & (frontier_df["volatility"] <= row["volatility"])
            ).any()

            if not better_exists:
                frontier_df.loc[idx, "is_efficient"] = True

        return frontier_df

    def calculate_benchmark_tracking(
        self, strategy: pd.Series, benchmark: pd.Series
    ) -> dict[str, float]:
        """Calculate tracking error and information ratio.

        Args:
            strategy: Strategy equity curve
            benchmark: Benchmark equity curve

        Returns:
            Dictionary with tracking metrics
        """
        # Calculate returns
        strategy_returns = strategy.pct_change().dropna()
        benchmark_returns = benchmark.pct_change().dropna()

        # Align returns
        aligned = pd.DataFrame(
            {"strategy": strategy_returns, "benchmark": benchmark_returns}
        ).dropna()

        # Active returns
        active_returns = aligned["strategy"] - aligned["benchmark"]

        tracking = {}
        tracking["tracking_error"] = active_returns.std() * np.sqrt(252)
        tracking["information_ratio"] = (
            active_returns.mean() * 252 / tracking["tracking_error"]
            if tracking["tracking_error"] > 0
            else 0
        )

        # Beta and alpha
        if len(aligned) > 20:
            beta, alpha, r_value, p_value, std_err = stats.linregress(
                aligned["benchmark"], aligned["strategy"]
            )
            tracking["beta"] = beta
            tracking["alpha"] = alpha * 252  # Annualized
            tracking["r_squared"] = r_value**2
        else:
            tracking["beta"] = 0
            tracking["alpha"] = 0
            tracking["r_squared"] = 0

        # Up/down capture
        up_market = aligned[aligned["benchmark"] > 0]
        down_market = aligned[aligned["benchmark"] < 0]

        if len(up_market) > 0:
            tracking["up_capture"] = (
                up_market["strategy"].mean() / up_market["benchmark"].mean()
            )
        else:
            tracking["up_capture"] = 0

        if len(down_market) > 0:
            tracking["down_capture"] = (
                down_market["strategy"].mean() / down_market["benchmark"].mean()
            )
        else:
            tracking["down_capture"] = 0

        return tracking

    def _add_rankings(self, comparison_df: pd.DataFrame):
        """Add rankings to comparison DataFrame."""
        # Define which metrics are better when higher vs lower
        higher_better = [
            "total_return",
            "annual_return",
            "sharpe_ratio",
            "sortino_ratio",
            "calmar_ratio",
            "win_rate",
            "profit_factor",
            "recovery_factor",
        ]

        lower_better = ["volatility", "max_drawdown", "var_95"]

        # Add rank columns
        for col in higher_better:
            if col in comparison_df.columns:
                comparison_df[f"{col}_rank"] = comparison_df[col].rank(
                    ascending=False, method="min"
                )

        for col in lower_better:
            if col in comparison_df.columns:
                comparison_df[f"{col}_rank"] = comparison_df[col].rank(
                    ascending=True, method="min"
                )

        # Calculate overall rank (average of individual ranks)
        rank_cols = [col for col in comparison_df.columns if col.endswith("_rank")]
        if rank_cols:
            comparison_df["overall_rank"] = comparison_df[rank_cols].mean(axis=1).rank()

    def generate_comparison_report(
        self,
        comparison_df: pd.DataFrame,
        correlation_matrix: pd.DataFrame,
        statistical_tests: dict[str, dict] | None = None,
    ) -> str:
        """Generate comparison report text.

        Args:
            comparison_df: Comparison metrics DataFrame
            correlation_matrix: Correlation matrix
            statistical_tests: Optional statistical test results

        Returns:
            Formatted report string
        """
        lines = []
        lines.append("=" * 80)
        lines.append("STRATEGY COMPARISON REPORT")
        lines.append("=" * 80)
        lines.append("")

        # Performance comparison
        lines.append("PERFORMANCE METRICS")
        lines.append("-" * 40)
        lines.append(comparison_df.to_string())
        lines.append("")

        # Correlation analysis
        lines.append("CORRELATION MATRIX")
        lines.append("-" * 40)
        lines.append(correlation_matrix.to_string())
        lines.append("")

        # Best strategies by metric
        lines.append("BEST STRATEGIES BY METRIC")
        lines.append("-" * 40)

        metrics_to_check = [
            ("Total Return", "total_return", True),
            ("Sharpe Ratio", "sharpe_ratio", True),
            ("Max Drawdown", "max_drawdown", False),
            ("Win Rate", "win_rate", True),
        ]

        for metric_name, col_name, higher_better in metrics_to_check:
            if col_name in comparison_df.columns:
                if higher_better:
                    best_strategy = comparison_df[col_name].idxmax()
                    best_value = comparison_df.loc[best_strategy, col_name]
                else:
                    best_strategy = comparison_df[col_name].idxmin()
                    best_value = comparison_df.loc[best_strategy, col_name]

                lines.append(f"{metric_name}: {best_strategy} ({best_value:.4f})")

        lines.append("")

        # Statistical tests if provided
        if statistical_tests:
            lines.append("STATISTICAL COMPARISONS")
            lines.append("-" * 40)
            for comparison, results in statistical_tests.items():
                lines.append(f"\n{comparison}:")
                lines.append(
                    f"  Means different: {results.get('means_different', 'N/A')}"
                )
                lines.append(
                    f"  T-test p-value: {results.get('t_test_pvalue', 'N/A'):.4f}"
                )
                lines.append(
                    f"  Sharpe difference: {results.get('sharpe_difference', 'N/A'):.4f}"
                )

        lines.append("")
        lines.append("=" * 80)

        return "\n".join(lines)
