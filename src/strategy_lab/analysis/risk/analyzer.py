"""Risk analysis implementation."""

import logging
from typing import Optional

import numpy as np
import pandas as pd

from .metrics import RiskMetrics

logger = logging.getLogger(__name__)


class RiskAnalyzer:
    """Analyzes various risk metrics and characteristics."""

    def __init__(self):
        """Initialize risk analyzer."""
        pass

    def analyze_risk(
        self,
        equity_curve: pd.Series,
        trades: pd.DataFrame,
        positions: Optional[pd.DataFrame] = None,
    ) -> RiskMetrics:
        """Perform comprehensive risk analysis.

        Args:
            equity_curve: Time series of portfolio values
            trades: DataFrame with trade information
            positions: Optional positions data

        Returns:
            RiskMetrics with analysis results
        """
        returns = equity_curve.pct_change().dropna()

        # Basic risk metrics
        volatility = returns.std() * np.sqrt(252)

        # Downside risk
        downside_returns = returns[returns < 0]
        downside_deviation = downside_returns.std() * np.sqrt(252)

        # Value at Risk
        var_95 = np.percentile(returns, 5)
        var_99 = np.percentile(returns, 1)

        # Conditional Value at Risk
        cvar_95 = returns[returns <= var_95].mean()
        cvar_99 = returns[returns <= var_99].mean()

        # Higher moments
        skewness = returns.skew()
        kurtosis = returns.kurtosis()

        # Maximum drawdown duration
        drawdown = self._calculate_drawdown_series(equity_curve)
        max_dd_duration = self._calculate_max_drawdown_duration(drawdown)

        # Risk of ruin
        risk_of_ruin = self._calculate_risk_of_ruin(trades)

        # Tail risk metrics
        tail_ratio = self._calculate_tail_ratio(returns)

        # Position concentration
        concentration_risk = 0.0
        if positions is not None:
            concentration_risk = self._calculate_concentration_risk(positions)

        # Correlation risk (if multiple assets)
        correlation_risk = 0.0

        # Beta (if benchmark provided)
        beta = 0.0

        return RiskMetrics(
            volatility=volatility,
            downside_deviation=downside_deviation,
            var_95=var_95,
            var_99=var_99,
            cvar_95=cvar_95,
            cvar_99=cvar_99,
            skewness=skewness,
            kurtosis=kurtosis,
            max_drawdown_duration=max_dd_duration,
            risk_of_ruin=risk_of_ruin,
            tail_ratio=tail_ratio,
            concentration_risk=concentration_risk,
            correlation_risk=correlation_risk,
            beta=beta,
        )

    def _calculate_drawdown_series(self, equity_curve: pd.Series) -> pd.Series:
        """Calculate drawdown series."""
        running_max = equity_curve.cummax()
        drawdown = (equity_curve - running_max) / running_max
        return drawdown

    def _calculate_max_drawdown_duration(self, drawdown: pd.Series) -> int:
        """Calculate maximum drawdown duration in days."""
        underwater = drawdown < -0.01  # 1% threshold

        # Find consecutive underwater periods
        max_duration = 0
        current_duration = 0

        for is_underwater in underwater:
            if is_underwater:
                current_duration += 1
                max_duration = max(max_duration, current_duration)
            else:
                current_duration = 0

        return max_duration

    def _calculate_risk_of_ruin(self, trades: pd.DataFrame) -> float:
        """Calculate risk of ruin probability."""
        if trades.empty:
            return 0.0

        wins = trades[trades["pnl"] > 0]
        losses = trades[trades["pnl"] < 0]

        if len(wins) == 0 or len(losses) == 0:
            return 0.0

        win_rate = len(wins) / len(trades)
        avg_win = wins["pnl"].mean()
        avg_loss = abs(losses["pnl"].mean())

        if avg_win == 0:
            return 1.0

        # Kelly criterion based calculation
        edge = win_rate * avg_win - (1 - win_rate) * avg_loss

        if edge <= 0:
            return 1.0

        # Simplified risk of ruin formula
        risk_of_ruin = ((1 - win_rate) / win_rate) ** (avg_win / avg_loss)

        return min(risk_of_ruin, 1.0)

    def _calculate_tail_ratio(self, returns: pd.Series) -> float:
        """Calculate tail ratio (95th percentile / 5th percentile)."""
        if len(returns) < 20:
            return 0.0

        right_tail = np.percentile(returns, 95)
        left_tail = abs(np.percentile(returns, 5))

        if left_tail == 0:
            return np.inf

        return right_tail / left_tail

    def _calculate_concentration_risk(self, positions: pd.DataFrame) -> float:
        """Calculate position concentration risk."""
        if "value" not in positions.columns:
            return 0.0

        # Calculate position sizes as percentage of portfolio
        total_value = positions["value"].abs().sum()

        if total_value == 0:
            return 0.0

        position_pcts = positions["value"].abs() / total_value

        # Herfindahl index for concentration
        herfindahl = (position_pcts**2).sum()

        return herfindahl
