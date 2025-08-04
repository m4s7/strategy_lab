"""Risk metrics calculation for trading strategies."""

from dataclasses import dataclass
from decimal import Decimal

import numpy as np
import pandas as pd


@dataclass
class RiskMetrics:
    """Container for risk-related metrics."""

    max_drawdown: Decimal = Decimal("0")
    max_drawdown_duration: pd.Timedelta = pd.Timedelta(0)
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    volatility: float = 0.0
    downside_deviation: float = 0.0
    var_95: float = 0.0  # Value at Risk at 95% confidence
    cvar_95: float = 0.0  # Conditional Value at Risk at 95%
    calmar_ratio: float = 0.0

    # Drawdown series
    drawdown_start: pd.Timestamp | None = None
    drawdown_end: pd.Timestamp | None = None
    current_drawdown: Decimal = Decimal("0")

    # Risk-adjusted returns
    risk_adjusted_return: float = 0.0


def calculate_max_drawdown(
    equity_curve: list[Decimal], timestamps: list[pd.Timestamp]
) -> tuple[Decimal, pd.Timedelta, pd.Timestamp, pd.Timestamp]:
    """Calculate maximum drawdown and duration.

    Args:
        equity_curve: List of equity values
        timestamps: List of timestamps

    Returns:
        Tuple of (max_drawdown, duration, start_time, end_time)
    """
    if len(equity_curve) < 2:
        return Decimal("0"), pd.Timedelta(0), None, None

    # Convert to numpy array for efficiency
    equity_array = np.array([float(e) for e in equity_curve])

    # Calculate running maximum
    running_max = np.maximum.accumulate(equity_array)

    # Calculate drawdown at each point
    # Avoid division by zero by using np.where
    drawdown = np.where(
        running_max > 0, (equity_array - running_max) / running_max, 0.0
    )

    # Find maximum drawdown
    max_dd_idx = np.argmin(drawdown)
    max_dd = abs(drawdown[max_dd_idx])

    # Find drawdown start (peak before max drawdown)
    peak_idx = np.where(equity_array[:max_dd_idx] == running_max[max_dd_idx])[0]
    if len(peak_idx) > 0:
        start_idx = peak_idx[-1]
    else:
        start_idx = 0

    # Find drawdown end (recovery point)
    recovery_idx = np.where(equity_array[max_dd_idx:] >= equity_array[start_idx])[0]
    if len(recovery_idx) > 0:
        end_idx = max_dd_idx + recovery_idx[0]
    else:
        end_idx = len(equity_array) - 1

    # Calculate duration
    start_time = timestamps[start_idx]
    end_time = timestamps[end_idx]
    duration = end_time - start_time

    return Decimal(str(max_dd)), duration, start_time, end_time


def calculate_sharpe_ratio(
    returns: pd.Series, risk_free_rate: float = 0.02, periods_per_year: int = 252
) -> float:
    """Calculate Sharpe ratio.

    Args:
        returns: Series of period returns
        risk_free_rate: Annual risk-free rate
        periods_per_year: Number of periods in a year (252 for daily)

    Returns:
        Sharpe ratio
    """
    if len(returns) < 2:
        return 0.0

    # Convert risk-free rate to period rate
    period_rf = risk_free_rate / periods_per_year

    # Calculate excess returns
    excess_returns = returns - period_rf

    # Calculate Sharpe ratio
    mean_excess = excess_returns.mean()
    std_excess = excess_returns.std()

    if std_excess == 0:
        return 0.0

    # Annualize
    sharpe = mean_excess / std_excess * np.sqrt(periods_per_year)

    return float(sharpe)


def calculate_sortino_ratio(
    returns: pd.Series, risk_free_rate: float = 0.02, periods_per_year: int = 252
) -> float:
    """Calculate Sortino ratio (uses downside deviation).

    Args:
        returns: Series of period returns
        risk_free_rate: Annual risk-free rate
        periods_per_year: Number of periods in a year

    Returns:
        Sortino ratio
    """
    if len(returns) < 2:
        return 0.0

    # Convert risk-free rate to period rate
    period_rf = risk_free_rate / periods_per_year

    # Calculate excess returns
    excess_returns = returns - period_rf

    # Calculate downside returns (negative excess returns)
    downside_returns = excess_returns[excess_returns < 0]

    if len(downside_returns) == 0:
        return float("inf") if excess_returns.mean() > 0 else 0.0

    # Calculate downside deviation
    downside_dev = np.sqrt((downside_returns**2).mean())

    if downside_dev == 0:
        return 0.0

    # Calculate Sortino ratio
    mean_excess = excess_returns.mean()
    sortino = mean_excess / downside_dev * np.sqrt(periods_per_year)

    return float(sortino)


def calculate_volatility(returns: pd.Series, periods_per_year: int = 252) -> float:
    """Calculate annualized volatility.

    Args:
        returns: Series of period returns
        periods_per_year: Number of periods in a year

    Returns:
        Annualized volatility
    """
    if len(returns) < 2:
        return 0.0

    # Calculate standard deviation and annualize
    vol = returns.std() * np.sqrt(periods_per_year)

    return float(vol)


def calculate_var(returns: pd.Series, confidence_level: float = 0.95) -> float:
    """Calculate Value at Risk (VaR).

    Args:
        returns: Series of period returns
        confidence_level: Confidence level (e.g., 0.95 for 95%)

    Returns:
        VaR at specified confidence level
    """
    if len(returns) < 2:
        return 0.0

    # Calculate percentile
    var = np.percentile(returns, (1 - confidence_level) * 100)

    return float(abs(var))


def calculate_cvar(returns: pd.Series, confidence_level: float = 0.95) -> float:
    """Calculate Conditional Value at Risk (CVaR).

    Args:
        returns: Series of period returns
        confidence_level: Confidence level

    Returns:
        CVaR at specified confidence level
    """
    if len(returns) < 2:
        return 0.0

    # Get VaR threshold
    var_threshold = np.percentile(returns, (1 - confidence_level) * 100)

    # Calculate mean of returns below VaR
    tail_returns = returns[returns <= var_threshold]

    if len(tail_returns) == 0:
        return 0.0

    cvar = tail_returns.mean()

    return float(abs(cvar))


def calculate_calmar_ratio(
    total_return: float, max_drawdown: float, years: float
) -> float:
    """Calculate Calmar ratio (annual return / max drawdown).

    Args:
        total_return: Total return over period
        max_drawdown: Maximum drawdown
        years: Number of years in period

    Returns:
        Calmar ratio
    """
    if max_drawdown == 0 or years == 0:
        return 0.0

    annual_return = (1 + total_return) ** (1 / years) - 1
    calmar = annual_return / max_drawdown

    return float(calmar)


def calculate_risk_metrics(
    equity_curve: list[Decimal],
    timestamps: list[pd.Timestamp],
    returns: pd.Series,
    risk_free_rate: float = 0.02,
    periods_per_year: int = 252,
) -> RiskMetrics:
    """Calculate comprehensive risk metrics.

    Args:
        equity_curve: List of equity values
        timestamps: List of timestamps
        returns: Series of period returns
        risk_free_rate: Annual risk-free rate
        periods_per_year: Number of periods in a year

    Returns:
        RiskMetrics object with calculated values
    """
    metrics = RiskMetrics()

    if len(equity_curve) < 2 or len(returns) < 2:
        return metrics

    # Calculate drawdown metrics
    max_dd, dd_duration, dd_start, dd_end = calculate_max_drawdown(
        equity_curve, timestamps
    )
    metrics.max_drawdown = max_dd
    metrics.max_drawdown_duration = dd_duration
    metrics.drawdown_start = dd_start
    metrics.drawdown_end = dd_end

    # Calculate risk ratios
    metrics.sharpe_ratio = calculate_sharpe_ratio(
        returns, risk_free_rate, periods_per_year
    )
    metrics.sortino_ratio = calculate_sortino_ratio(
        returns, risk_free_rate, periods_per_year
    )

    # Calculate volatility metrics
    metrics.volatility = calculate_volatility(returns, periods_per_year)

    # Calculate VaR and CVaR
    metrics.var_95 = calculate_var(returns, 0.95)
    metrics.cvar_95 = calculate_cvar(returns, 0.95)

    # Calculate Calmar ratio
    if len(timestamps) > 1 and float(equity_curve[0]) != 0:
        years = (timestamps[-1] - timestamps[0]).days / 365.25
        total_return = float(equity_curve[-1] - equity_curve[0]) / float(
            equity_curve[0]
        )
        metrics.calmar_ratio = calculate_calmar_ratio(
            total_return, float(max_dd), years
        )

    return metrics
