"""Performance metrics calculation for trading strategies."""

from dataclasses import dataclass, field
from decimal import Decimal

import pandas as pd


@dataclass
class Trade:
    """Represents a completed trade."""

    entry_price: Decimal
    exit_price: Decimal
    quantity: int
    entry_time: pd.Timestamp
    exit_time: pd.Timestamp
    side: str  # "BUY" or "SELL"
    commission: Decimal = Decimal("0")

    @property
    def pnl(self) -> Decimal:
        """Calculate P&L for this trade."""
        if self.side == "BUY":
            gross_pnl = (self.exit_price - self.entry_price) * self.quantity
        else:  # SELL
            gross_pnl = (self.entry_price - self.exit_price) * self.quantity
        return gross_pnl - self.commission

    @property
    def duration(self) -> pd.Timedelta:
        """Calculate trade duration."""
        return self.exit_time - self.entry_time


@dataclass
class PerformanceMetrics:
    """Container for performance metrics."""

    total_pnl: Decimal = Decimal("0")
    gross_profit: Decimal = Decimal("0")
    gross_loss: Decimal = Decimal("0")
    commission_paid: Decimal = Decimal("0")

    # Trade counts
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0

    # Average metrics
    avg_win: Decimal = Decimal("0")
    avg_loss: Decimal = Decimal("0")

    # Time-based
    daily_pnl: dict[pd.Timestamp, Decimal] = field(default_factory=dict)
    monthly_pnl: dict[pd.Timestamp, Decimal] = field(default_factory=dict)

    # Equity curve
    equity_curve: list[Decimal] = field(default_factory=list)
    timestamps: list[pd.Timestamp] = field(default_factory=list)

    @property
    def net_profit(self) -> Decimal:
        """Net profit after commissions."""
        return self.total_pnl

    @property
    def profit_factor(self) -> Decimal:
        """Ratio of gross profit to gross loss."""
        if self.gross_loss == 0:
            return Decimal("0") if self.gross_profit == 0 else Decimal("inf")
        return abs(self.gross_profit / self.gross_loss)

    @property
    def win_rate(self) -> Decimal:
        """Percentage of winning trades."""
        if self.total_trades == 0:
            return Decimal("0")
        return Decimal(self.winning_trades) / Decimal(self.total_trades) * 100

    @property
    def expectancy(self) -> Decimal:
        """Average expected profit per trade."""
        if self.total_trades == 0:
            return Decimal("0")
        return self.total_pnl / self.total_trades


def calculate_pnl(trades: list[Trade]) -> PerformanceMetrics:
    """Calculate P&L metrics from a list of trades.

    Args:
        trades: List of completed trades

    Returns:
        PerformanceMetrics object with calculated values
    """
    metrics = PerformanceMetrics()

    if not trades:
        # Initialize with starting equity point
        metrics.equity_curve.append(Decimal("0"))
        return metrics

    # Sort trades by exit time for time-based analysis
    sorted_trades = sorted(trades, key=lambda t: t.exit_time)

    # Initialize equity curve with starting capital (0)
    current_equity = Decimal("0")
    metrics.equity_curve.append(current_equity)
    metrics.timestamps.append(sorted_trades[0].entry_time)

    # Process each trade
    for trade in sorted_trades:
        pnl = trade.pnl

        # Update totals
        metrics.total_pnl += pnl
        metrics.commission_paid += trade.commission
        metrics.total_trades += 1

        # Update win/loss stats
        if pnl > 0:
            metrics.gross_profit += pnl
            metrics.winning_trades += 1
        elif pnl < 0:
            metrics.gross_loss += abs(pnl)
            metrics.losing_trades += 1

        # Update equity curve
        current_equity += pnl
        metrics.equity_curve.append(current_equity)
        metrics.timestamps.append(trade.exit_time)

        # Update daily P&L
        trade_date = trade.exit_time.date()
        if trade_date not in metrics.daily_pnl:
            metrics.daily_pnl[trade_date] = Decimal("0")
        metrics.daily_pnl[trade_date] += pnl

        # Update monthly P&L
        month_start = pd.Timestamp(trade.exit_time.year, trade.exit_time.month, 1)
        if month_start not in metrics.monthly_pnl:
            metrics.monthly_pnl[month_start] = Decimal("0")
        metrics.monthly_pnl[month_start] += pnl

    # Calculate averages
    if metrics.winning_trades > 0:
        metrics.avg_win = metrics.gross_profit / metrics.winning_trades
    if metrics.losing_trades > 0:
        metrics.avg_loss = metrics.gross_loss / metrics.losing_trades

    return metrics


def calculate_returns(
    equity_curve: list[Decimal], timestamps: list[pd.Timestamp], period: str = "D"
) -> pd.Series:
    """Calculate returns from equity curve.

    Args:
        equity_curve: List of equity values
        timestamps: List of timestamps
        period: Resampling period ('D' for daily, 'ME' for monthly)

    Returns:
        Pandas Series of returns
    """
    if len(equity_curve) < 2:
        return pd.Series(dtype=float)

    # Convert to DataFrame
    df = pd.DataFrame(
        {"equity": [float(e) for e in equity_curve], "timestamp": timestamps}
    )
    df.set_index("timestamp", inplace=True)

    # Resample to specified period
    resampled = df.resample(period).last()

    # Calculate returns
    returns = resampled["equity"].pct_change().dropna()

    return returns


def calculate_cumulative_returns(returns: pd.Series) -> pd.Series:
    """Calculate cumulative returns from period returns.

    Args:
        returns: Series of period returns

    Returns:
        Series of cumulative returns
    """
    return (1 + returns).cumprod() - 1
