"""Time series analysis for performance metrics."""

import logging

import numpy as np
import pandas as pd
from scipy import stats

try:
    from statsmodels.stats.diagnostic import acorr_ljungbox
except ImportError:
    acorr_ljungbox = None

logger = logging.getLogger(__name__)


class TimeSeriesAnalyzer:
    """Analyzes time-series characteristics of performance."""

    def __init__(self, frequency: str = "D"):
        """Initialize time series analyzer.

        Args:
            frequency: Data frequency ('D' for daily, 'H' for hourly, etc.)
        """
        self.frequency = frequency

    def analyze_seasonality(
        self, returns: pd.Series, min_periods: int = 252
    ) -> dict[str, float]:
        """Analyze seasonal patterns in returns.

        Args:
            returns: Return series
            min_periods: Minimum periods for analysis

        Returns:
            Dictionary with seasonality metrics
        """
        if len(returns) < min_periods:
            return {}

        results = {}

        # Monthly seasonality
        monthly_returns = returns.resample("ME").apply(lambda x: (1 + x).prod() - 1)
        if len(monthly_returns) >= 12:
            monthly_avg = monthly_returns.groupby(monthly_returns.index.month).mean()
            results["best_month_seasonal"] = monthly_avg.idxmax()
            results["worst_month_seasonal"] = monthly_avg.idxmin()
            results["monthly_seasonality_strength"] = monthly_avg.std()

        # Day of week effects
        if self.frequency == "D":
            dow_returns = returns.groupby(returns.index.dayofweek).mean()
            results["best_dow"] = dow_returns.idxmax()
            results["worst_dow"] = dow_returns.idxmin()
            results["dow_effect_strength"] = dow_returns.std()

            # Weekend effect
            weekday_avg = dow_returns[0:5].mean()
            monday_return = dow_returns[0]
            results["weekend_effect"] = monday_return - weekday_avg

        # Quarterly patterns
        quarterly_returns = returns.resample("QE").apply(lambda x: (1 + x).prod() - 1)
        if len(quarterly_returns) >= 8:
            quarter_avg = quarterly_returns.groupby(
                quarterly_returns.index.quarter
            ).mean()
            results["best_quarter_seasonal"] = quarter_avg.idxmax()
            results["worst_quarter_seasonal"] = quarter_avg.idxmin()

        return results

    def detect_regime_changes(
        self, returns: pd.Series, window: int = 252
    ) -> pd.DataFrame:
        """Detect regime changes in return series.

        Args:
            returns: Return series
            window: Rolling window for regime detection

        Returns:
            DataFrame with regime indicators
        """
        regimes = pd.DataFrame(index=returns.index)

        # Rolling statistics
        rolling_mean = returns.rolling(window).mean()
        rolling_vol = returns.rolling(window).std()

        # Volatility regimes
        vol_median = rolling_vol.median()
        regimes["volatility_regime"] = "normal"
        regimes.loc[rolling_vol > vol_median * 1.5, "volatility_regime"] = "high_vol"
        regimes.loc[rolling_vol < vol_median * 0.5, "volatility_regime"] = "low_vol"

        # Trend regimes
        regimes["trend_regime"] = "neutral"
        regimes.loc[rolling_mean > rolling_mean.std(), "trend_regime"] = "uptrend"
        regimes.loc[rolling_mean < -rolling_mean.std(), "trend_regime"] = "downtrend"

        # Market stress indicator
        rolling_skew = returns.rolling(window).skew()
        rolling_kurt = returns.rolling(window).apply(lambda x: stats.kurtosis(x))

        stress_score = (
            (rolling_vol > rolling_vol.quantile(0.8)).astype(int)
            + (rolling_skew < rolling_skew.quantile(0.2)).astype(int)
            + (rolling_kurt > rolling_kurt.quantile(0.8)).astype(int)
        )

        regimes["market_stress"] = "normal"
        regimes.loc[stress_score >= 2, "market_stress"] = "stressed"

        return regimes

    def calculate_performance_persistence(
        self, returns: pd.Series, periods: list[int] = [20, 60, 120]
    ) -> dict[str, float]:
        """Calculate performance persistence metrics.

        Args:
            returns: Return series
            periods: List of lookback periods

        Returns:
            Dictionary with persistence metrics
        """
        results = {}

        for period in periods:
            if len(returns) < period * 2:
                continue

            # Calculate rolling returns
            rolling_returns = returns.rolling(period).apply(
                lambda x: (1 + x).prod() - 1
            )

            # Autocorrelation of returns
            if len(rolling_returns.dropna()) > period:
                autocorr = rolling_returns.autocorr(lag=period)
                results[f"return_autocorr_{period}d"] = autocorr

            # Win/loss persistence
            positive_returns = (rolling_returns > 0).astype(int)
            runs = self._count_runs(positive_returns.dropna())

            if runs:
                results[f"avg_win_streak_{period}d"] = np.mean(
                    [r[1] for r in runs if r[0] == 1]
                )
                results[f"avg_loss_streak_{period}d"] = np.mean(
                    [r[1] for r in runs if r[0] == 0]
                )

        return results

    def analyze_volatility_clustering(
        self, returns: pd.Series, lags: int = 10
    ) -> dict[str, float]:
        """Analyze volatility clustering (ARCH effects).

        Args:
            returns: Return series
            lags: Number of lags to test

        Returns:
            Dictionary with volatility clustering metrics
        """
        results = {}

        # Calculate squared returns
        squared_returns = returns**2

        # Ljung-Box test for autocorrelation in squared returns
        if acorr_ljungbox is not None:
            try:
                lb_result = acorr_ljungbox(
                    squared_returns.dropna(), lags=lags, return_df=False
                )
                lb_stat, lb_pvalue = lb_result

                results["ljung_box_stat"] = float(lb_stat[-1])
                results["ljung_box_pvalue"] = float(lb_pvalue[-1])
                results["has_arch_effects"] = bool(lb_pvalue[-1] < 0.05)
            except Exception:
                results["ljung_box_stat"] = 0.0
                results["ljung_box_pvalue"] = 1.0
                results["has_arch_effects"] = False
        else:
            results["ljung_box_stat"] = 0.0
            results["ljung_box_pvalue"] = 1.0
            results["has_arch_effects"] = False

        # Autocorrelation of absolute returns
        abs_returns = returns.abs()
        for lag in [1, 5, 10]:
            if len(abs_returns) > lag:
                results[f"abs_return_autocorr_lag{lag}"] = abs_returns.autocorr(lag=lag)

        return results

    def calculate_stability_metrics(
        self, equity_curve: pd.Series, window: int = 252
    ) -> dict[str, float]:
        """Calculate performance stability metrics.

        Args:
            equity_curve: Equity curve
            window: Rolling window

        Returns:
            Dictionary with stability metrics
        """
        returns = equity_curve.pct_change().dropna()
        results = {}

        # R-squared of equity curve
        x = np.arange(len(equity_curve))
        log_equity = np.log(equity_curve)
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, log_equity)
        results["equity_curve_r_squared"] = r_value**2
        results["equity_curve_slope"] = slope

        # Rolling Sharpe stability
        rolling_sharpe = returns.rolling(window).apply(
            lambda x: x.mean() / x.std() * np.sqrt(252) if x.std() > 0 else 0
        )
        results["sharpe_stability"] = 1 - (rolling_sharpe.std() / rolling_sharpe.mean())

        # Consistency score (% of positive rolling periods)
        rolling_returns = returns.rolling(window).apply(lambda x: (1 + x).prod() - 1)
        results["consistency_score"] = (rolling_returns > 0).mean()

        # Smoothness (average absolute daily change)
        results["smoothness"] = 1 / (returns.abs().mean() * 100)

        return results

    def _count_runs(self, series: pd.Series) -> list[tuple[int, int]]:
        """Count consecutive runs of same values.

        Args:
            series: Binary series (0 or 1)

        Returns:
            List of (value, length) tuples
        """
        if len(series) == 0:
            return []

        runs = []
        current_value = series.iloc[0]
        current_length = 1

        for i in range(1, len(series)):
            if series.iloc[i] == current_value:
                current_length += 1
            else:
                runs.append((current_value, current_length))
                current_value = series.iloc[i]
                current_length = 1

        runs.append((current_value, current_length))
        return runs

    def create_performance_attribution(
        self, returns: pd.Series, factors: pd.DataFrame | None = None, window: int = 60
    ) -> pd.DataFrame:
        """Create performance attribution over time.

        Args:
            returns: Strategy returns
            factors: Optional factor returns for attribution
            window: Rolling window for attribution

        Returns:
            DataFrame with attribution results
        """
        attribution = pd.DataFrame(index=returns.index)

        # Base return attribution
        attribution["strategy_return"] = returns
        attribution["cumulative_return"] = (1 + returns).cumprod() - 1

        # Rolling statistics attribution
        attribution["rolling_mean"] = returns.rolling(window).mean()
        attribution["rolling_vol"] = returns.rolling(window).std()
        attribution["rolling_sharpe"] = (
            attribution["rolling_mean"] / attribution["rolling_vol"] * np.sqrt(252)
        )

        # Contribution to total return
        total_return = (1 + returns).prod() - 1
        attribution["contribution"] = returns / (1 + total_return)

        # Factor attribution if provided
        if factors is not None:
            # Perform rolling regression
            for i in range(window, len(returns)):
                y = returns.iloc[i - window : i]
                X = factors.iloc[i - window : i]

                # Add constant
                X = pd.concat([pd.Series(1, index=X.index), X], axis=1)

                # OLS regression
                try:
                    beta = np.linalg.lstsq(X.values, y.values, rcond=None)[0]
                    attribution.loc[returns.index[i], "alpha"] = beta[0]

                    for j, col in enumerate(factors.columns):
                        attribution.loc[returns.index[i], f"beta_{col}"] = beta[j + 1]
                except:
                    pass

        return attribution
