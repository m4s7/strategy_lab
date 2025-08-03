"""Drawdown analysis implementation."""

import logging
from dataclasses import dataclass
from datetime import datetime

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class DrawdownPeriod:
    """Represents a single drawdown period."""

    start_date: datetime
    end_date: datetime | None
    trough_date: datetime
    peak_value: float
    trough_value: float
    end_value: float | None
    drawdown_pct: float
    duration_days: int
    recovery_days: int | None
    is_active: bool

    @property
    def magnitude(self) -> float:
        """Get drawdown magnitude in absolute terms."""
        return self.peak_value - self.trough_value

    @property
    def total_duration(self) -> int:
        """Get total duration including recovery."""
        if self.recovery_days is not None:
            return self.duration_days + self.recovery_days
        return self.duration_days


@dataclass
class DrawdownAnalysis:
    """Comprehensive drawdown analysis results."""

    max_drawdown: float
    max_drawdown_duration: int
    avg_drawdown: float
    avg_recovery_time: int
    drawdown_periods: list[DrawdownPeriod]
    underwater_curve: pd.Series
    recovery_factor: float
    worst_periods: list[DrawdownPeriod]
    current_drawdown: float | None
    time_underwater_pct: float

    @property
    def n_drawdowns(self) -> int:
        """Get number of drawdown periods."""
        return len(self.drawdown_periods)

    @property
    def is_in_drawdown(self) -> bool:
        """Check if currently in drawdown."""
        return self.current_drawdown is not None and self.current_drawdown < 0

    def get_summary_stats(self) -> dict:
        """Get summary statistics."""
        return {
            "max_drawdown": self.max_drawdown,
            "max_duration": self.max_drawdown_duration,
            "avg_drawdown": self.avg_drawdown,
            "avg_recovery": self.avg_recovery_time,
            "n_drawdowns": self.n_drawdowns,
            "recovery_factor": self.recovery_factor,
            "time_underwater_pct": self.time_underwater_pct,
            "current_drawdown": self.current_drawdown or 0.0,
        }


class DrawdownCalculator:
    """Calculates drawdown statistics and analysis."""

    def __init__(self, threshold: float = 0.01):
        """Initialize calculator.

        Args:
            threshold: Minimum drawdown threshold to track (1%)
        """
        self.threshold = threshold

    def analyze_drawdowns(
        self, equity_curve: pd.Series, initial_capital: float | None = None
    ) -> DrawdownAnalysis:
        """Perform comprehensive drawdown analysis.

        Args:
            equity_curve: Time series of portfolio values
            initial_capital: Initial capital for recovery factor

        Returns:
            DrawdownAnalysis with all statistics
        """
        if initial_capital is None:
            initial_capital = equity_curve.iloc[0]

        # Calculate drawdown series
        running_max = equity_curve.cummax()
        drawdown = (equity_curve - running_max) / running_max
        underwater_curve = drawdown

        # Find drawdown periods
        periods = self._identify_drawdown_periods(equity_curve, drawdown)

        # Calculate statistics
        max_drawdown = abs(drawdown.min())

        # Duration statistics
        if periods:
            durations = [p.duration_days for p in periods]
            recovery_times = [
                p.recovery_days for p in periods if p.recovery_days is not None
            ]

            max_duration = max(durations)
            avg_drawdown = np.mean([abs(p.drawdown_pct) for p in periods])
            avg_recovery = np.mean(recovery_times) if recovery_times else 0
        else:
            max_duration = 0
            avg_drawdown = 0
            avg_recovery = 0

        # Recovery factor
        total_return = (equity_curve.iloc[-1] / initial_capital) - 1
        recovery_factor = total_return / max_drawdown if max_drawdown > 0 else np.inf

        # Time underwater
        time_underwater = (drawdown < -self.threshold).sum()
        time_underwater_pct = time_underwater / len(drawdown)

        # Current drawdown
        current_dd = drawdown.iloc[-1]
        current_drawdown = current_dd if current_dd < -self.threshold else None

        # Worst periods
        worst_periods = sorted(periods, key=lambda x: x.drawdown_pct)[:5]

        return DrawdownAnalysis(
            max_drawdown=max_drawdown,
            max_drawdown_duration=max_duration,
            avg_drawdown=avg_drawdown,
            avg_recovery_time=int(avg_recovery),
            drawdown_periods=periods,
            underwater_curve=underwater_curve,
            recovery_factor=recovery_factor,
            worst_periods=worst_periods,
            current_drawdown=current_drawdown,
            time_underwater_pct=time_underwater_pct,
        )

    def _identify_drawdown_periods(
        self, equity_curve: pd.Series, drawdown: pd.Series
    ) -> list[DrawdownPeriod]:
        """Identify individual drawdown periods."""
        periods = []
        in_drawdown = False

        peak_idx = 0
        peak_value = equity_curve.iloc[0]

        for i in range(1, len(equity_curve)):
            current_dd = drawdown.iloc[i]

            if not in_drawdown and current_dd < -self.threshold:
                # Start of new drawdown
                in_drawdown = True
                start_idx = i
                trough_idx = i
                trough_value = equity_curve.iloc[i]

            elif in_drawdown:
                if current_dd < drawdown.iloc[trough_idx]:
                    # New trough
                    trough_idx = i
                    trough_value = equity_curve.iloc[i]

                elif current_dd >= -self.threshold:
                    # Recovery complete
                    period = DrawdownPeriod(
                        start_date=equity_curve.index[start_idx],
                        end_date=equity_curve.index[i],
                        trough_date=equity_curve.index[trough_idx],
                        peak_value=peak_value,
                        trough_value=trough_value,
                        end_value=equity_curve.iloc[i],
                        drawdown_pct=drawdown.iloc[trough_idx],
                        duration_days=(
                            equity_curve.index[trough_idx]
                            - equity_curve.index[peak_idx]
                        ).days,
                        recovery_days=(
                            equity_curve.index[i] - equity_curve.index[trough_idx]
                        ).days,
                        is_active=False,
                    )
                    periods.append(period)

                    # Reset for next drawdown
                    in_drawdown = False
                    peak_idx = i
                    peak_value = equity_curve.iloc[i]

            else:
                # Update peak
                if equity_curve.iloc[i] > peak_value:
                    peak_idx = i
                    peak_value = equity_curve.iloc[i]

        # Handle active drawdown
        if in_drawdown:
            period = DrawdownPeriod(
                start_date=equity_curve.index[start_idx],
                end_date=None,
                trough_date=equity_curve.index[trough_idx],
                peak_value=peak_value,
                trough_value=trough_value,
                end_value=None,
                drawdown_pct=drawdown.iloc[trough_idx],
                duration_days=(
                    equity_curve.index[-1] - equity_curve.index[peak_idx]
                ).days,
                recovery_days=None,
                is_active=True,
            )
            periods.append(period)

        return periods

    def calculate_rolling_drawdowns(
        self, equity_curve: pd.Series, window: int = 252
    ) -> pd.DataFrame:
        """Calculate rolling drawdown statistics.

        Args:
            equity_curve: Time series of portfolio values
            window: Rolling window size

        Returns:
            DataFrame with rolling drawdown metrics
        """
        results = pd.DataFrame(index=equity_curve.index)

        for i in range(window, len(equity_curve)):
            window_data = equity_curve.iloc[i - window : i + 1]
            window_max = window_data.cummax()
            window_dd = (window_data - window_max) / window_max

            results.loc[equity_curve.index[i], "max_drawdown"] = abs(window_dd.min())
            results.loc[equity_curve.index[i], "current_drawdown"] = window_dd.iloc[-1]

            # Count drawdown days
            dd_days = (window_dd < -self.threshold).sum()
            results.loc[equity_curve.index[i], "drawdown_days"] = dd_days
            results.loc[equity_curve.index[i], "underwater_pct"] = dd_days / window

        return results

    def analyze_recovery_patterns(self, drawdown_periods: list[DrawdownPeriod]) -> dict:
        """Analyze recovery patterns from drawdowns.

        Args:
            drawdown_periods: List of drawdown periods

        Returns:
            Dictionary with recovery analysis
        """
        if not drawdown_periods:
            return {}

        recovered = [p for p in drawdown_periods if not p.is_active]

        if not recovered:
            return {
                "avg_recovery_ratio": 0,
                "recovery_success_rate": 0,
                "avg_recovery_speed": 0,
            }

        # Recovery ratio: recovery days / drawdown days
        recovery_ratios = [
            p.recovery_days / p.duration_days
            for p in recovered
            if p.recovery_days and p.duration_days > 0
        ]

        # Recovery speed: % recovered per day
        recovery_speeds = []
        for p in recovered:
            if p.recovery_days and p.recovery_days > 0:
                recovery_pct = abs(p.drawdown_pct)
                speed = recovery_pct / p.recovery_days
                recovery_speeds.append(speed)

        return {
            "avg_recovery_ratio": np.mean(recovery_ratios) if recovery_ratios else 0,
            "recovery_success_rate": len(recovered) / len(drawdown_periods),
            "avg_recovery_speed": np.mean(recovery_speeds) if recovery_speeds else 0,
            "median_recovery_days": np.median(
                [p.recovery_days for p in recovered if p.recovery_days]
            ),
            "worst_recovery_days": max(
                [p.recovery_days for p in recovered if p.recovery_days], default=0
            ),
        }
