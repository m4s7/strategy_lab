"""Trade analysis and statistics calculation."""

from collections import defaultdict
from dataclasses import dataclass, field
from decimal import Decimal

import numpy as np
import pandas as pd

from .performance import Trade


@dataclass
class TradeStatistics:
    """Container for trade-related statistics."""

    # Basic stats
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    breakeven_trades: int = 0

    # Win/loss metrics
    win_rate: Decimal = Decimal("0")
    loss_rate: Decimal = Decimal("0")
    avg_win: Decimal = Decimal("0")
    avg_loss: Decimal = Decimal("0")
    avg_trade: Decimal = Decimal("0")

    # Ratios
    profit_factor: Decimal = Decimal("0")
    win_loss_ratio: Decimal = Decimal("0")
    expectancy: Decimal = Decimal("0")

    # Consecutive trades
    max_consecutive_wins: int = 0
    max_consecutive_losses: int = 0
    current_streak: int = 0

    # Duration metrics
    avg_trade_duration: pd.Timedelta = pd.Timedelta(0)
    avg_winning_duration: pd.Timedelta = pd.Timedelta(0)
    avg_losing_duration: pd.Timedelta = pd.Timedelta(0)

    # Distribution
    largest_win: Decimal = Decimal("0")
    largest_loss: Decimal = Decimal("0")
    trade_pnl_distribution: list[Decimal] = field(default_factory=list)

    # Time-based analysis
    trades_by_hour: dict[int, int] = field(default_factory=lambda: defaultdict(int))
    trades_by_day: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    pnl_by_hour: dict[int, Decimal] = field(
        default_factory=lambda: defaultdict(Decimal)
    )
    pnl_by_day: dict[str, Decimal] = field(default_factory=lambda: defaultdict(Decimal))


def analyze_trades(trades: list[Trade]) -> TradeStatistics:
    """Analyze trades and calculate comprehensive statistics.

    Args:
        trades: List of completed trades

    Returns:
        TradeStatistics object with calculated values
    """
    stats = TradeStatistics()

    if not trades:
        return stats

    # Initialize counters
    winning_pnl = Decimal("0")
    losing_pnl = Decimal("0")
    total_pnl = Decimal("0")

    winning_durations = []
    losing_durations = []
    all_durations = []

    consecutive_wins = 0
    consecutive_losses = 0

    # Process each trade
    for trade in trades:
        pnl = trade.pnl
        duration = trade.duration

        stats.total_trades += 1
        stats.trade_pnl_distribution.append(pnl)
        total_pnl += pnl
        all_durations.append(duration)

        # Time-based analysis
        hour = trade.exit_time.hour
        day_name = trade.exit_time.strftime("%A")
        stats.trades_by_hour[hour] += 1
        stats.trades_by_day[day_name] += 1
        stats.pnl_by_hour[hour] += pnl
        stats.pnl_by_day[day_name] += pnl

        # Categorize trade
        if pnl > 0:
            stats.winning_trades += 1
            winning_pnl += pnl
            winning_durations.append(duration)

            # Update streaks
            consecutive_wins += 1
            consecutive_losses = 0
            stats.max_consecutive_wins = max(
                stats.max_consecutive_wins, consecutive_wins
            )

            # Update largest win
            stats.largest_win = max(stats.largest_win, pnl)

        elif pnl < 0:
            stats.losing_trades += 1
            losing_pnl += abs(pnl)
            losing_durations.append(duration)

            # Update streaks
            consecutive_losses += 1
            consecutive_wins = 0
            stats.max_consecutive_losses = max(
                stats.max_consecutive_losses, consecutive_losses
            )

            # Update largest loss
            stats.largest_loss = max(stats.largest_loss, abs(pnl))

        else:
            stats.breakeven_trades += 1
            consecutive_wins = 0
            consecutive_losses = 0

    # Calculate rates
    if stats.total_trades > 0:
        stats.win_rate = (
            Decimal(stats.winning_trades) / Decimal(stats.total_trades) * 100
        )
        stats.loss_rate = (
            Decimal(stats.losing_trades) / Decimal(stats.total_trades) * 100
        )
        stats.avg_trade = total_pnl / stats.total_trades
        stats.expectancy = total_pnl / stats.total_trades

    # Calculate averages
    if stats.winning_trades > 0:
        stats.avg_win = winning_pnl / stats.winning_trades
    if stats.losing_trades > 0:
        stats.avg_loss = losing_pnl / stats.losing_trades

    # Calculate ratios
    if losing_pnl > 0:
        stats.profit_factor = winning_pnl / losing_pnl
    elif winning_pnl > 0:
        stats.profit_factor = Decimal("inf")

    if stats.avg_loss > 0:
        stats.win_loss_ratio = stats.avg_win / stats.avg_loss

    # Calculate duration metrics
    if all_durations:
        avg_seconds = np.mean([d.total_seconds() for d in all_durations])
        stats.avg_trade_duration = pd.Timedelta(seconds=avg_seconds)

    if winning_durations:
        avg_win_seconds = np.mean([d.total_seconds() for d in winning_durations])
        stats.avg_winning_duration = pd.Timedelta(seconds=avg_win_seconds)

    if losing_durations:
        avg_loss_seconds = np.mean([d.total_seconds() for d in losing_durations])
        stats.avg_losing_duration = pd.Timedelta(seconds=avg_loss_seconds)

    # Set current streak
    stats.current_streak = (
        consecutive_wins if consecutive_wins > 0 else -consecutive_losses
    )

    return stats


def calculate_win_rate(trades: list[Trade]) -> Decimal:
    """Calculate win rate from trades.

    Args:
        trades: List of completed trades

    Returns:
        Win rate as percentage
    """
    if not trades:
        return Decimal("0")

    winning_trades = sum(1 for trade in trades if trade.pnl > 0)
    return Decimal(winning_trades) / Decimal(len(trades)) * 100


def calculate_profit_factor(trades: list[Trade]) -> Decimal:
    """Calculate profit factor from trades.

    Args:
        trades: List of completed trades

    Returns:
        Profit factor (gross profit / gross loss)
    """
    if not trades:
        return Decimal("0")

    gross_profit = sum(trade.pnl for trade in trades if trade.pnl > 0)
    gross_loss = sum(abs(trade.pnl) for trade in trades if trade.pnl < 0)

    if gross_loss == 0:
        return Decimal("inf") if gross_profit > 0 else Decimal("0")

    return gross_profit / gross_loss


def analyze_trade_distribution(trades: list[Trade]) -> dict[str, float]:
    """Analyze the distribution of trade P&L.

    Args:
        trades: List of completed trades

    Returns:
        Dictionary with distribution statistics
    """
    if not trades:
        return {
            "mean": 0.0,
            "median": 0.0,
            "std": 0.0,
            "skew": 0.0,
            "kurtosis": 0.0,
            "percentile_25": 0.0,
            "percentile_75": 0.0,
        }

    pnl_values = [float(trade.pnl) for trade in trades]
    pnl_array = np.array(pnl_values)

    return {
        "mean": np.mean(pnl_array),
        "median": np.median(pnl_array),
        "std": np.std(pnl_array),
        "skew": float(pd.Series(pnl_array).skew()),
        "kurtosis": float(pd.Series(pnl_array).kurtosis()),
        "percentile_25": np.percentile(pnl_array, 25),
        "percentile_75": np.percentile(pnl_array, 75),
    }


def find_best_worst_periods(
    trades: list[Trade], period: str = "D"
) -> tuple[pd.Timestamp, Decimal, pd.Timestamp, Decimal]:
    """Find best and worst trading periods.

    Args:
        trades: List of completed trades
        period: Period for grouping ('D' for daily, 'ME' for monthly)

    Returns:
        Tuple of (best_period, best_pnl, worst_period, worst_pnl)
    """
    if not trades:
        return None, Decimal("0"), None, Decimal("0")

    # Group trades by period
    df = pd.DataFrame(
        [{"timestamp": trade.exit_time, "pnl": float(trade.pnl)} for trade in trades]
    )
    df.set_index("timestamp", inplace=True)

    # Resample and sum P&L by period
    period_pnl = df.resample(period)["pnl"].sum()

    if period_pnl.empty:
        return None, Decimal("0"), None, Decimal("0")

    # Find best and worst periods
    best_idx = period_pnl.idxmax()
    worst_idx = period_pnl.idxmin()

    return (
        best_idx,
        Decimal(str(period_pnl[best_idx])),
        worst_idx,
        Decimal(str(period_pnl[worst_idx])),
    )
