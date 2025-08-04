"""Comprehensive tests for the enhanced performance analysis module."""

from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import pytest

from strategy_lab.analysis.performance.comparison import StrategyComparator
from strategy_lab.analysis.performance.metrics import MetricsCalculator
from strategy_lab.analysis.performance.time_series import TimeSeriesAnalyzer
from strategy_lab.analysis.trade.analyzer import TradeAnalyzer


class TestAdvancedMetrics:
    """Test advanced metrics calculations."""

    @pytest.fixture
    def sample_data(self):
        """Create comprehensive sample data."""
        dates = pd.date_range(start="2024-01-01", end="2024-12-31", freq="D")
        np.random.seed(42)

        # Create realistic returns with some structure
        base_returns = np.random.normal(0.0003, 0.01, len(dates))

        # Add momentum
        for i in range(1, len(base_returns)):
            base_returns[i] += 0.2 * base_returns[i - 1]

        equity = 100000 * (1 + base_returns).cumprod()

        # Create trades
        trades = []
        for i in range(0, len(dates), 5):
            if i + 2 < len(dates):
                entry_price = 100 + np.random.normal(0, 1)
                exit_price = entry_price + np.random.normal(0.5, 2)
                pnl = (exit_price - entry_price) * 100

                trades.append(
                    {
                        "entry_time": dates[i],
                        "exit_time": dates[i + 2],
                        "pnl": pnl,
                        "holding_time": 120,  # minutes
                        "position_size": np.random.randint(1, 5),
                        "entry_price": entry_price,
                        "exit_price": exit_price,
                    }
                )

        return pd.Series(equity, index=dates), pd.DataFrame(trades)

    def test_advanced_metrics_calculation(self, sample_data):
        """Test calculation of advanced performance metrics."""
        equity_curve, trades = sample_data
        returns = equity_curve.pct_change().dropna()

        calculator = MetricsCalculator()
        advanced = calculator.calculate_advanced_metrics(returns, trades, equity_curve)

        # Test Omega ratio
        assert "omega_ratio" in advanced
        assert advanced["omega_ratio"] > 0

        # Test Gain-to-pain ratio
        assert "gain_to_pain_ratio" in advanced

        # Test Ulcer index
        assert "ulcer_index" in advanced
        assert advanced["ulcer_index"] >= 0

        # Test Martin ratio
        assert "martin_ratio" in advanced

        # Test Burke ratio
        assert "burke_ratio" in advanced

        # Test Rachev ratio
        assert "rachev_ratio" in advanced
        assert advanced["rachev_ratio"] > 0

        # Test Sterling ratio
        assert "sterling_ratio" in advanced

    def test_time_based_metrics(self, sample_data):
        """Test time-based performance metrics."""
        equity_curve, trades = sample_data

        calculator = MetricsCalculator()
        time_metrics = calculator.calculate_time_based_metrics(equity_curve, trades)

        # Daily metrics
        assert "best_day" in time_metrics
        assert "worst_day" in time_metrics
        assert time_metrics["best_day"] > time_metrics["worst_day"]

        # Monthly metrics
        assert "best_month" in time_metrics
        assert "worst_month" in time_metrics
        assert "positive_months_pct" in time_metrics
        assert 0 <= time_metrics["positive_months_pct"] <= 1

        # Time of day analysis
        assert "best_hour" in time_metrics
        assert "worst_hour" in time_metrics
        assert 0 <= time_metrics["best_hour"] <= 23

        # Day of week analysis
        assert "best_dow" in time_metrics
        assert "worst_dow" in time_metrics
        assert 0 <= time_metrics["best_dow"] <= 6


class TestTimeSeriesAnalysis:
    """Test time series analysis functionality."""

    @pytest.fixture
    def returns_with_patterns(self):
        """Create returns with known patterns."""
        dates = pd.date_range(start="2022-01-01", end="2024-12-31", freq="D")
        np.random.seed(42)

        returns = []
        for date in dates:
            # Base random return
            r = np.random.normal(0, 0.01)

            # Add monthly seasonality
            if date.month in [1, 11, 12]:  # Strong months
                r += 0.002
            elif date.month in [8, 9]:  # Weak months
                r -= 0.002

            # Add day of week effect
            if date.dayofweek == 0:  # Monday
                r -= 0.001
            elif date.dayofweek == 4:  # Friday
                r += 0.001

            returns.append(r)

        return pd.Series(returns, index=dates)

    def test_seasonality_detection(self, returns_with_patterns):
        """Test seasonality analysis."""
        analyzer = TimeSeriesAnalyzer()
        seasonality = analyzer.analyze_seasonality(returns_with_patterns)

        # Monthly seasonality
        assert "best_month_seasonal" in seasonality
        assert seasonality["best_month_seasonal"] in [1, 11, 12]
        assert "worst_month_seasonal" in seasonality
        assert seasonality["worst_month_seasonal"] in [8, 9]

        # Day of week effects
        assert "best_dow" in seasonality
        assert "worst_dow" in seasonality
        assert "weekend_effect" in seasonality

    def test_regime_detection(self, returns_with_patterns):
        """Test market regime detection."""
        analyzer = TimeSeriesAnalyzer()

        # Add a volatility spike
        spike_start = 500
        spike_end = 550
        returns_with_spike = returns_with_patterns.copy()
        returns_with_spike.iloc[spike_start:spike_end] *= 3  # Triple volatility

        regimes = analyzer.detect_regime_changes(returns_with_spike, window=60)

        # Check regime classifications
        assert not regimes.empty
        assert set(regimes["volatility_regime"].unique()).issubset(
            {"low_vol", "normal", "high_vol"}
        )

        # Should detect high volatility during spike
        spike_regimes = regimes.iloc[spike_start:spike_end]["volatility_regime"]
        assert (spike_regimes == "high_vol").any()

    def test_performance_persistence(self, returns_with_patterns):
        """Test performance persistence metrics."""
        analyzer = TimeSeriesAnalyzer()
        persistence = analyzer.calculate_performance_persistence(
            returns_with_patterns, periods=[20, 60, 120]
        )

        # Autocorrelation metrics
        assert "return_autocorr_20d" in persistence
        assert "return_autocorr_60d" in persistence
        assert "return_autocorr_120d" in persistence

        # Streak metrics
        assert "avg_win_streak_20d" in persistence
        assert "avg_loss_streak_20d" in persistence

    def test_volatility_clustering(self, returns_with_patterns):
        """Test volatility clustering analysis."""
        analyzer = TimeSeriesAnalyzer()
        clustering = analyzer.analyze_volatility_clustering(
            returns_with_patterns, lags=10
        )

        assert "ljung_box_stat" in clustering
        assert "ljung_box_pvalue" in clustering
        assert "has_arch_effects" in clustering
        assert isinstance(clustering["has_arch_effects"], bool)

        # Test autocorrelation metrics
        assert "abs_return_autocorr_lag1" in clustering
        assert "abs_return_autocorr_lag5" in clustering
        assert "abs_return_autocorr_lag10" in clustering


class TestEnhancedTradeAnalysis:
    """Test enhanced trade analysis features."""

    @pytest.fixture
    def detailed_trades(self):
        """Create detailed trade data with patterns."""
        np.random.seed(42)
        trades = []

        # Create trades with clustering
        base_time = datetime(2024, 1, 1, 9, 0)

        # Cluster 1: Morning trades
        for i in range(10):
            trades.append(
                {
                    "entry_time": base_time + timedelta(minutes=i * 5),
                    "exit_time": base_time + timedelta(minutes=i * 5 + 30),
                    "pnl": np.random.normal(100, 50),
                    "holding_time": 30,
                    "position_size": 2,
                }
            )

        # Gap
        base_time = datetime(2024, 1, 1, 14, 0)

        # Cluster 2: Afternoon trades
        for i in range(8):
            trades.append(
                {
                    "entry_time": base_time + timedelta(minutes=i * 10),
                    "exit_time": base_time + timedelta(minutes=i * 10 + 45),
                    "pnl": np.random.normal(-50, 30),
                    "holding_time": 45,
                    "position_size": 1,
                }
            )

        # Spread out trades
        for day in range(2, 30):
            for hour in [10, 14]:
                trades.append(
                    {
                        "entry_time": datetime(2024, 1, day, hour, 0),
                        "exit_time": datetime(2024, 1, day, hour, 30),
                        "pnl": np.random.normal(0, 100),
                        "holding_time": 30,
                        "position_size": np.random.randint(1, 4),
                    }
                )

        return pd.DataFrame(trades)

    def test_trade_clustering_analysis(self, detailed_trades):
        """Test trade clustering detection."""
        analyzer = TradeAnalyzer()
        clustering = analyzer.analyze_trade_clustering(detailed_trades)

        assert "n_clusters" in clustering
        assert clustering["n_clusters"] >= 2  # Should detect at least 2 clusters

        assert "avg_cluster_size" in clustering
        assert clustering["avg_cluster_size"] > 1

        assert "max_cluster_size" in clustering
        assert clustering["max_cluster_size"] >= 8

        assert "trade_density" in clustering
        assert clustering["trade_density"] > 0

    def test_trade_pattern_analysis(self, detailed_trades):
        """Test trade pattern detection."""
        analyzer = TradeAnalyzer()
        patterns = analyzer.analyze_trade_patterns(detailed_trades)

        # Win/loss patterns
        assert "win_rate_after_win" in patterns
        assert "win_rate_after_loss" in patterns
        assert 0 <= patterns["win_rate_after_win"] <= 1
        assert 0 <= patterns["win_rate_after_loss"] <= 1

        # Momentum vs mean reversion
        assert "has_momentum" in patterns
        assert "has_mean_reversion" in patterns
        assert isinstance(patterns["has_momentum"], bool)
        assert isinstance(patterns["has_mean_reversion"], bool)

        # Position sizing patterns
        assert "avg_size_after_win" in patterns
        assert "avg_size_after_loss" in patterns
        assert "scales_up_after_wins" in patterns

    def test_kelly_criterion(self, detailed_trades):
        """Test Kelly Criterion calculation."""
        analyzer = TradeAnalyzer()
        kelly = analyzer.calculate_kelly_criterion(detailed_trades)

        assert "kelly_fraction" in kelly
        assert "half_kelly" in kelly
        assert "quarter_kelly" in kelly

        # Kelly fractions should be reasonable
        assert 0 <= kelly["kelly_fraction"] <= 0.25
        assert kelly["half_kelly"] == pytest.approx(
            kelly["kelly_fraction"] / 2, abs=0.001
        )
        assert kelly["quarter_kelly"] == pytest.approx(
            kelly["kelly_fraction"] / 4, abs=0.001
        )


class TestStrategyComparison:
    """Test strategy comparison functionality."""

    @pytest.fixture
    def multiple_strategies(self):
        """Create multiple strategies for comparison."""
        dates = pd.date_range(start="2024-01-01", end="2024-12-31", freq="D")
        np.random.seed(42)

        strategies = {}

        # Conservative strategy
        returns = np.random.normal(0.0002, 0.005, len(dates))
        equity = 100000 * (1 + returns).cumprod()
        trades = self._generate_trades(50, 0.65, 50, 30)
        strategies["Conservative"] = {
            "equity_curve": pd.Series(equity, index=dates),
            "trades": trades,
        }

        # Aggressive strategy
        returns = np.random.normal(0.0008, 0.02, len(dates))
        equity = 100000 * (1 + returns).cumprod()
        trades = self._generate_trades(150, 0.55, 200, 150)
        strategies["Aggressive"] = {
            "equity_curve": pd.Series(equity, index=dates),
            "trades": trades,
        }

        # Balanced strategy
        returns = np.random.normal(0.0005, 0.01, len(dates))
        equity = 100000 * (1 + returns).cumprod()
        trades = self._generate_trades(100, 0.60, 100, 80)
        strategies["Balanced"] = {
            "equity_curve": pd.Series(equity, index=dates),
            "trades": trades,
        }

        return strategies

    def _generate_trades(self, n_trades, win_rate, avg_win, avg_loss):
        """Helper to generate trade data."""
        trades = []
        for i in range(n_trades):
            is_win = np.random.random() < win_rate
            pnl = (
                np.random.normal(avg_win, 20)
                if is_win
                else -np.random.normal(avg_loss, 20)
            )
            trades.append({"pnl": pnl, "holding_time": np.random.randint(30, 180)})
        return pd.DataFrame(trades)

    def test_strategy_comparison(self, multiple_strategies):
        """Test multi-strategy comparison."""
        comparator = StrategyComparator()
        comparison_df = comparator.compare_strategies(multiple_strategies)

        # Check structure
        assert len(comparison_df) == 3
        assert all(name in comparison_df.index for name in multiple_strategies.keys())

        # Check metrics
        required_metrics = [
            "total_return",
            "annual_return",
            "volatility",
            "sharpe_ratio",
            "max_drawdown",
            "win_rate",
            "profit_factor",
        ]
        for metric in required_metrics:
            assert metric in comparison_df.columns

        # Check rankings
        assert "overall_rank" in comparison_df.columns
        assert comparison_df["overall_rank"].min() == 1
        assert comparison_df["overall_rank"].max() == 3

    def test_correlation_analysis(self, multiple_strategies):
        """Test correlation matrix calculation."""
        comparator = StrategyComparator()

        equity_curves = {
            name: data["equity_curve"] for name, data in multiple_strategies.items()
        }

        corr_matrix = comparator.calculate_correlation_matrix(equity_curves)

        # Check properties
        assert corr_matrix.shape == (3, 3)
        assert np.allclose(np.diag(corr_matrix), 1.0)
        assert corr_matrix.equals(corr_matrix.T)
        assert ((corr_matrix >= -1) & (corr_matrix <= 1)).all().all()

    def test_statistical_tests(self, multiple_strategies):
        """Test statistical comparison tests."""
        comparator = StrategyComparator()

        results = comparator.perform_statistical_tests(
            multiple_strategies["Conservative"]["equity_curve"],
            multiple_strategies["Aggressive"]["equity_curve"],
        )

        # Check test results
        assert "t_test_statistic" in results
        assert "t_test_pvalue" in results
        assert 0 <= results["t_test_pvalue"] <= 1

        assert "f_test_statistic" in results
        assert results["f_test_statistic"] > 0

        assert "mann_whitney_statistic" in results
        assert "sharpe_difference" in results

    def test_efficient_frontier(self, multiple_strategies):
        """Test efficient frontier calculation."""
        comparator = StrategyComparator()

        equity_curves = {
            name: data["equity_curve"] for name, data in multiple_strategies.items()
        }

        frontier_df = comparator.calculate_efficient_frontier(
            equity_curves, n_portfolios=100
        )

        assert len(frontier_df) == 100
        assert "return" in frontier_df.columns
        assert "volatility" in frontier_df.columns
        assert "sharpe" in frontier_df.columns
        assert "is_efficient" in frontier_df.columns

        # Check weight columns
        for name in equity_curves:
            assert f"weight_{name}" in frontier_df.columns

        # Weights should sum to 1
        weight_cols = [col for col in frontier_df.columns if col.startswith("weight_")]
        weight_sums = frontier_df[weight_cols].sum(axis=1)
        assert np.allclose(weight_sums, 1.0, atol=1e-6)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
