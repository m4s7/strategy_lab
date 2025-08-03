"""Tests for risk metrics calculations."""

from decimal import Decimal

import numpy as np
import pandas as pd
import pytest

from strategy_lab.backtesting.metrics.risk import (
    calculate_calmar_ratio,
    calculate_cvar,
    calculate_max_drawdown,
    calculate_risk_metrics,
    calculate_sharpe_ratio,
    calculate_sortino_ratio,
    calculate_var,
    calculate_volatility,
)


class TestMaxDrawdown:
    """Test maximum drawdown calculation."""

    def test_no_drawdown(self):
        """Test with equity curve that never declines."""
        equity_curve = [Decimal(str(i)) for i in [100000, 101000, 102000, 103000]]
        timestamps = pd.date_range("2024-01-01", periods=4, freq="D")

        max_dd, duration, start, end = calculate_max_drawdown(equity_curve, timestamps)

        assert max_dd == Decimal("0")
        assert duration == pd.Timedelta(0)

    def test_single_drawdown(self):
        """Test with single drawdown period."""
        equity_curve = [Decimal(str(i)) for i in [100000, 110000, 105000, 108000]]
        timestamps = pd.date_range("2024-01-01", periods=4, freq="D")

        max_dd, duration, start, end = calculate_max_drawdown(equity_curve, timestamps)

        # Drawdown from 110000 to 105000 = 5000/110000 = 0.0454545
        assert pytest.approx(float(max_dd), rel=1e-5) == 0.0454545
        assert start == timestamps[1]
        assert end == timestamps[3]

    def test_multiple_drawdowns(self):
        """Test with multiple drawdown periods."""
        equity_curve = [
            Decimal(str(i)) for i in [100000, 110000, 105000, 115000, 108000, 112000]
        ]
        timestamps = pd.date_range("2024-01-01", periods=6, freq="D")

        max_dd, duration, start, end = calculate_max_drawdown(equity_curve, timestamps)

        # Max drawdown from 115000 to 108000 = 7000/115000 = 0.0608696
        assert pytest.approx(float(max_dd), rel=1e-5) == 0.0608696
        assert start == timestamps[3]
        assert end == timestamps[5]

    def test_no_recovery_drawdown(self):
        """Test drawdown that doesn't recover."""
        equity_curve = [Decimal(str(i)) for i in [100000, 110000, 105000, 103000]]
        timestamps = pd.date_range("2024-01-01", periods=4, freq="D")

        max_dd, duration, start, end = calculate_max_drawdown(equity_curve, timestamps)

        # Drawdown from 110000 to 103000 = 7000/110000 = 0.0636364
        assert pytest.approx(float(max_dd), rel=1e-5) == 0.0636364
        assert start == timestamps[1]
        assert end == timestamps[3]


class TestSharpeRatio:
    """Test Sharpe ratio calculation."""

    def test_positive_sharpe(self):
        """Test Sharpe ratio with positive returns."""
        returns = pd.Series([0.01, 0.02, -0.005, 0.015, 0.01])

        sharpe = calculate_sharpe_ratio(returns, risk_free_rate=0.02)

        # Manual calculation:
        # rf_daily = 0.02/252 = 0.0000794
        # excess_returns = returns - rf_daily
        # mean_excess = 0.009921
        # std_excess = 0.00968
        # sharpe = 0.009921 / 0.00968 * sqrt(252) = 16.27

        assert sharpe > 0  # Positive Sharpe ratio
        assert 10 < sharpe < 20  # Reasonable range

    def test_negative_sharpe(self):
        """Test Sharpe ratio with negative returns."""
        returns = pd.Series([-0.01, -0.02, -0.005, -0.015, -0.01])

        sharpe = calculate_sharpe_ratio(returns, risk_free_rate=0.02)

        assert sharpe < 0  # Negative Sharpe ratio

    def test_zero_volatility(self):
        """Test Sharpe ratio with zero volatility."""
        returns = pd.Series([0.01, 0.01, 0.01, 0.01])

        sharpe = calculate_sharpe_ratio(returns, risk_free_rate=0.0)

        # With zero volatility and positive returns, Sharpe should be 0
        assert sharpe == 0.0


class TestSortinoRatio:
    """Test Sortino ratio calculation."""

    def test_no_downside_deviation(self):
        """Test Sortino ratio with no negative returns."""
        returns = pd.Series([0.01, 0.02, 0.005, 0.015, 0.01])

        sortino = calculate_sortino_ratio(returns, risk_free_rate=0.0)

        assert sortino == float("inf")  # No downside, infinite Sortino

    def test_positive_sortino(self):
        """Test Sortino ratio with mixed returns."""
        returns = pd.Series([0.01, -0.005, 0.02, -0.01, 0.015])

        sortino = calculate_sortino_ratio(returns, risk_free_rate=0.02)

        assert sortino > 0

    def test_sortino_vs_sharpe(self):
        """Test that Sortino >= Sharpe for same returns."""
        returns = pd.Series([0.01, -0.005, 0.02, -0.01, 0.015, -0.002])

        sharpe = calculate_sharpe_ratio(returns, risk_free_rate=0.02)
        sortino = calculate_sortino_ratio(returns, risk_free_rate=0.02)

        # Sortino should be >= Sharpe (uses only downside deviation)
        assert sortino >= sharpe


class TestVolatility:
    """Test volatility calculation."""

    def test_annualized_volatility(self):
        """Test annualized volatility calculation."""
        returns = pd.Series([0.01, -0.02, 0.015, -0.005, 0.01])

        vol = calculate_volatility(returns, periods_per_year=252)

        # Manual calculation:
        # std_daily = 0.0137
        # annualized = 0.0137 * sqrt(252) = 0.218

        assert 0.15 < vol < 0.25  # Reasonable volatility range

    def test_zero_volatility(self):
        """Test volatility with constant returns."""
        returns = pd.Series([0.01, 0.01, 0.01, 0.01])

        vol = calculate_volatility(returns)

        assert vol == 0.0


class TestValueAtRisk:
    """Test VaR and CVaR calculations."""

    def test_var_95(self):
        """Test 95% VaR calculation."""
        # Create returns with known distribution
        np.random.seed(42)
        returns = pd.Series(np.random.normal(-0.001, 0.02, 1000))

        var_95 = calculate_var(returns, confidence_level=0.95)

        # 95% VaR should be around 5th percentile of losses
        assert 0.02 < var_95 < 0.04

    def test_cvar_95(self):
        """Test 95% CVaR calculation."""
        np.random.seed(42)
        returns = pd.Series(np.random.normal(-0.001, 0.02, 1000))

        var_95 = calculate_var(returns, confidence_level=0.95)
        cvar_95 = calculate_cvar(returns, confidence_level=0.95)

        # CVaR should be greater than VaR (expected tail loss)
        assert cvar_95 > var_95

    def test_var_cvar_empty_returns(self):
        """Test VaR/CVaR with empty returns."""
        returns = pd.Series([])

        var_95 = calculate_var(returns)
        cvar_95 = calculate_cvar(returns)

        assert var_95 == 0.0
        assert cvar_95 == 0.0


class TestCalmarRatio:
    """Test Calmar ratio calculation."""

    def test_positive_calmar(self):
        """Test Calmar ratio with positive returns."""
        total_return = 0.20  # 20% total return
        max_drawdown = 0.10  # 10% max drawdown
        years = 2.0

        calmar = calculate_calmar_ratio(total_return, max_drawdown, years)

        # Annual return = (1.20)^(1/2) - 1 = 0.0954
        # Calmar = 0.0954 / 0.10 = 0.954
        assert pytest.approx(calmar, rel=1e-3) == 0.954

    def test_zero_drawdown(self):
        """Test Calmar ratio with zero drawdown."""
        calmar = calculate_calmar_ratio(0.20, 0.0, 2.0)
        assert calmar == 0.0

    def test_zero_years(self):
        """Test Calmar ratio with zero years."""
        calmar = calculate_calmar_ratio(0.20, 0.10, 0.0)
        assert calmar == 0.0


class TestRiskMetricsAggregation:
    """Test comprehensive risk metrics calculation."""

    def test_calculate_risk_metrics(self):
        """Test full risk metrics calculation."""
        # Create sample equity curve and returns
        equity_curve = [
            Decimal(str(i)) for i in [100000, 102000, 101000, 103000, 102500, 104000]
        ]
        timestamps = pd.date_range("2024-01-01", periods=6, freq="D")
        returns = pd.Series([0.02, -0.0098, 0.0198, -0.0049, 0.0146])

        metrics = calculate_risk_metrics(
            equity_curve, timestamps, returns, risk_free_rate=0.02, periods_per_year=252
        )

        # Verify all metrics are calculated
        assert metrics.max_drawdown > Decimal("0")
        assert metrics.sharpe_ratio != 0.0
        assert metrics.sortino_ratio != 0.0
        assert metrics.volatility > 0.0
        assert metrics.var_95 > 0.0
        assert metrics.cvar_95 > 0.0
        assert metrics.calmar_ratio != 0.0

    def test_empty_data_handling(self):
        """Test risk metrics with empty data."""
        metrics = calculate_risk_metrics([], [], pd.Series([]))

        assert metrics.max_drawdown == Decimal("0")
        assert metrics.sharpe_ratio == 0.0
        assert metrics.volatility == 0.0
        assert metrics.var_95 == 0.0
