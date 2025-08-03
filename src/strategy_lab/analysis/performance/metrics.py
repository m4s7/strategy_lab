"""Performance metrics calculations."""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Comprehensive performance metrics for strategy evaluation."""

    # Profitability Metrics
    total_return: float
    annualized_return: float
    profit_factor: float
    win_rate: float
    expectancy: float

    # Risk Metrics
    volatility: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    max_drawdown: float

    # Advanced Risk Metrics
    var_95: float  # Value at Risk (95%)
    cvar_95: float  # Conditional Value at Risk (95%)
    downside_deviation: float
    tail_ratio: float
    skewness: float
    kurtosis: float

    # Trade Statistics
    total_trades: int
    winning_trades: int
    losing_trades: int
    avg_win: float
    avg_loss: float
    win_loss_ratio: float
    avg_trade: float
    avg_holding_time: float

    # Additional Metrics
    recovery_factor: float
    profit_consistency: float
    trade_frequency: float

    # Time Period
    start_date: datetime
    end_date: datetime
    trading_days: int

    def to_dict(self) -> Dict[str, float]:
        """Convert metrics to dictionary."""
        return {
            # Profitability
            "total_return": self.total_return,
            "annualized_return": self.annualized_return,
            "profit_factor": self.profit_factor,
            "win_rate": self.win_rate,
            "expectancy": self.expectancy,
            # Risk
            "volatility": self.volatility,
            "sharpe_ratio": self.sharpe_ratio,
            "sortino_ratio": self.sortino_ratio,
            "calmar_ratio": self.calmar_ratio,
            "max_drawdown": self.max_drawdown,
            # Advanced Risk
            "var_95": self.var_95,
            "cvar_95": self.cvar_95,
            "downside_deviation": self.downside_deviation,
            "tail_ratio": self.tail_ratio,
            "skewness": self.skewness,
            "kurtosis": self.kurtosis,
            # Trade Stats
            "total_trades": self.total_trades,
            "win_rate": self.win_rate,
            "avg_trade": self.avg_trade,
            "win_loss_ratio": self.win_loss_ratio,
            "avg_holding_time": self.avg_holding_time,
            # Additional
            "recovery_factor": self.recovery_factor,
            "profit_consistency": self.profit_consistency,
            "trade_frequency": self.trade_frequency,
            "trading_days": self.trading_days,
        }


class MetricsCalculator:
    """Calculates performance metrics from trading data."""

    def __init__(self, risk_free_rate: float = 0.02):
        """Initialize calculator.

        Args:
            risk_free_rate: Annual risk-free rate for Sharpe ratio
        """
        self.risk_free_rate = risk_free_rate

    def calculate_metrics(
        self,
        equity_curve: pd.Series,
        trades: pd.DataFrame,
        benchmark: Optional[pd.Series] = None,
    ) -> PerformanceMetrics:
        """Calculate comprehensive performance metrics.

        Args:
            equity_curve: Time series of portfolio values
            trades: DataFrame with trade information
            benchmark: Optional benchmark returns

        Returns:
            PerformanceMetrics object
        """
        # Calculate returns
        returns = equity_curve.pct_change().dropna()

        # Time period
        start_date = equity_curve.index[0]
        end_date = equity_curve.index[-1]
        trading_days = len(equity_curve)
        years = (end_date - start_date).days / 365.25

        # Profitability metrics
        total_return = (equity_curve.iloc[-1] / equity_curve.iloc[0]) - 1
        annualized_return = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0

        # Trade statistics
        winning_trades = trades[trades["pnl"] > 0]
        losing_trades = trades[trades["pnl"] < 0]

        total_trades = len(trades)
        n_winning = len(winning_trades)
        n_losing = len(losing_trades)

        win_rate = n_winning / total_trades if total_trades > 0 else 0

        avg_win = winning_trades["pnl"].mean() if n_winning > 0 else 0
        avg_loss = abs(losing_trades["pnl"].mean()) if n_losing > 0 else 0
        win_loss_ratio = avg_win / avg_loss if avg_loss > 0 else np.inf

        avg_trade = trades["pnl"].mean() if total_trades > 0 else 0
        expectancy = win_rate * avg_win - (1 - win_rate) * avg_loss

        # Profit factor
        gross_profit = winning_trades["pnl"].sum() if n_winning > 0 else 0
        gross_loss = abs(losing_trades["pnl"].sum()) if n_losing > 0 else 0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else np.inf

        # Holding time
        if "holding_time" in trades.columns:
            avg_holding_time = trades["holding_time"].mean()
        else:
            avg_holding_time = 0

        # Risk metrics
        volatility = returns.std() * np.sqrt(252)  # Annualized

        # Sharpe ratio
        excess_returns = returns.mean() * 252 - self.risk_free_rate
        sharpe_ratio = excess_returns / volatility if volatility > 0 else 0

        # Sortino ratio (downside deviation)
        downside_returns = returns[returns < 0]
        downside_deviation = downside_returns.std() * np.sqrt(252)
        sortino_ratio = (
            excess_returns / downside_deviation if downside_deviation > 0 else 0
        )

        # Drawdown analysis
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = abs(drawdown.min())

        # Calmar ratio
        calmar_ratio = annualized_return / max_drawdown if max_drawdown > 0 else 0

        # VaR and CVaR
        var_95 = np.percentile(returns, 5)
        cvar_95 = returns[returns <= var_95].mean()

        # Tail ratio
        right_tail = np.percentile(returns, 95)
        left_tail = abs(np.percentile(returns, 5))
        tail_ratio = right_tail / left_tail if left_tail > 0 else np.inf

        # Distribution metrics
        skewness = stats.skew(returns)
        kurtosis = stats.kurtosis(returns)

        # Recovery factor
        recovery_factor = total_return / max_drawdown if max_drawdown > 0 else np.inf

        # Profit consistency (% of positive months)
        if len(returns) >= 20:  # At least 20 days
            monthly_returns = returns.resample("M").apply(lambda x: (1 + x).prod() - 1)
            profit_consistency = (monthly_returns > 0).mean()
        else:
            profit_consistency = win_rate

        # Trade frequency (trades per day)
        trade_frequency = total_trades / trading_days if trading_days > 0 else 0

        return PerformanceMetrics(
            # Profitability
            total_return=total_return,
            annualized_return=annualized_return,
            profit_factor=profit_factor,
            win_rate=win_rate,
            expectancy=expectancy,
            # Risk
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            calmar_ratio=calmar_ratio,
            max_drawdown=max_drawdown,
            # Advanced Risk
            var_95=var_95,
            cvar_95=cvar_95,
            downside_deviation=downside_deviation,
            tail_ratio=tail_ratio,
            skewness=skewness,
            kurtosis=kurtosis,
            # Trade Statistics
            total_trades=total_trades,
            winning_trades=n_winning,
            losing_trades=n_losing,
            avg_win=avg_win,
            avg_loss=avg_loss,
            win_loss_ratio=win_loss_ratio,
            avg_trade=avg_trade,
            avg_holding_time=avg_holding_time,
            # Additional
            recovery_factor=recovery_factor,
            profit_consistency=profit_consistency,
            trade_frequency=trade_frequency,
            # Time Period
            start_date=start_date,
            end_date=end_date,
            trading_days=trading_days,
        )

    def calculate_rolling_metrics(
        self, equity_curve: pd.Series, window: int = 252, min_periods: int = 30
    ) -> pd.DataFrame:
        """Calculate rolling performance metrics.

        Args:
            equity_curve: Time series of portfolio values
            window: Rolling window size in days
            min_periods: Minimum periods for calculation

        Returns:
            DataFrame with rolling metrics
        """
        returns = equity_curve.pct_change().dropna()

        rolling_metrics = pd.DataFrame(index=returns.index)

        # Rolling returns
        rolling_metrics["return"] = returns.rolling(
            window, min_periods=min_periods
        ).apply(lambda x: (1 + x).prod() - 1)

        # Rolling volatility
        rolling_metrics["volatility"] = returns.rolling(
            window, min_periods=min_periods
        ).std() * np.sqrt(252)

        # Rolling Sharpe
        rolling_mean = returns.rolling(window, min_periods=min_periods).mean() * 252
        rolling_metrics["sharpe_ratio"] = (
            rolling_mean - self.risk_free_rate
        ) / rolling_metrics["volatility"]

        # Rolling max drawdown
        rolling_metrics["max_drawdown"] = returns.rolling(
            window, min_periods=min_periods
        ).apply(self._calculate_max_drawdown)

        # Rolling win rate
        rolling_metrics["win_rate"] = returns.rolling(
            window, min_periods=min_periods
        ).apply(lambda x: (x > 0).mean())

        return rolling_metrics

    def _calculate_max_drawdown(self, returns: pd.Series) -> float:
        """Calculate maximum drawdown for a returns series."""
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        return abs(drawdown.min())

    def calculate_regime_metrics(
        self, equity_curve: pd.Series, market_regimes: pd.Series
    ) -> Dict[str, PerformanceMetrics]:
        """Calculate metrics for different market regimes.

        Args:
            equity_curve: Time series of portfolio values
            market_regimes: Series indicating market regime for each period

        Returns:
            Dictionary mapping regime names to metrics
        """
        regime_metrics = {}

        for regime in market_regimes.unique():
            regime_mask = market_regimes == regime
            regime_equity = equity_curve[regime_mask]

            if len(regime_equity) < 2:
                continue

            # Create synthetic trades for regime
            regime_trades = self._create_synthetic_trades(regime_equity)

            regime_metrics[regime] = self.calculate_metrics(
                regime_equity, regime_trades
            )

        return regime_metrics

    def _create_synthetic_trades(self, equity_curve: pd.Series) -> pd.DataFrame:
        """Create synthetic trade data from equity curve."""
        returns = equity_curve.pct_change().dropna()

        trades = []
        trade_start = 0

        for i in range(1, len(returns)):
            if returns.iloc[i] * returns.iloc[i - 1] < 0:  # Sign change
                pnl = equity_curve.iloc[i] - equity_curve.iloc[trade_start]
                trades.append(
                    {
                        "entry_time": equity_curve.index[trade_start],
                        "exit_time": equity_curve.index[i],
                        "pnl": pnl,
                        "holding_time": i - trade_start,
                    }
                )
                trade_start = i

        # Last trade
        if trade_start < len(returns) - 1:
            pnl = equity_curve.iloc[-1] - equity_curve.iloc[trade_start]
            trades.append(
                {
                    "entry_time": equity_curve.index[trade_start],
                    "exit_time": equity_curve.index[-1],
                    "pnl": pnl,
                    "holding_time": len(returns) - 1 - trade_start,
                }
            )

        return pd.DataFrame(trades)
