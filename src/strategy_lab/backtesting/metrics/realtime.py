"""Real-time metrics calculation and aggregation."""

from collections.abc import Callable
from dataclasses import dataclass, field
from decimal import Decimal

import pandas as pd

from .performance import PerformanceMetrics, Trade, calculate_pnl, calculate_returns
from .risk import RiskMetrics, calculate_risk_metrics
from .trade_analysis import TradeStatistics, analyze_trades


@dataclass
class RealtimeMetrics:
    """Container for real-time metrics during backtesting."""

    # Core metrics
    performance: PerformanceMetrics = field(default_factory=PerformanceMetrics)
    risk: RiskMetrics = field(default_factory=RiskMetrics)
    trade_stats: TradeStatistics = field(default_factory=TradeStatistics)

    # Real-time tracking
    open_trades: dict[int, Trade] = field(default_factory=dict)
    completed_trades: list[Trade] = field(default_factory=list)

    # Current state
    current_equity: Decimal = Decimal("0")
    starting_equity: Decimal = Decimal("0")
    peak_equity: Decimal = Decimal("0")
    current_drawdown: Decimal = Decimal("0")

    # Update callbacks
    on_trade_complete: Callable[[Trade], None] | None = None
    on_equity_update: Callable[[Decimal], None] | None = None
    on_metrics_update: Callable[["RealtimeMetrics"], None] | None = None

    # Update frequency
    update_frequency: int = 100  # Update metrics every N trades
    trades_since_update: int = 0


class MetricsAggregator:
    """Aggregates and updates metrics in real-time during backtesting."""

    def __init__(
        self,
        starting_equity: Decimal = Decimal("100000"),
        update_frequency: int = 100,
        risk_free_rate: float = 0.02,
    ):
        """Initialize metrics aggregator.

        Args:
            starting_equity: Starting capital
            update_frequency: How often to recalculate full metrics
            risk_free_rate: Risk-free rate for Sharpe calculation
        """
        self.metrics = RealtimeMetrics(
            starting_equity=starting_equity,
            current_equity=starting_equity,
            peak_equity=starting_equity,
            update_frequency=update_frequency,
        )
        self.risk_free_rate = risk_free_rate

    def open_trade(
        self,
        trade_id: int,
        entry_price: Decimal,
        quantity: int,
        entry_time: pd.Timestamp,
        side: str,
    ) -> None:
        """Record a new trade opening.

        Args:
            trade_id: Unique trade identifier
            entry_price: Entry price
            quantity: Trade quantity
            entry_time: Entry timestamp
            side: "BUY" or "SELL"
        """
        # Create partial trade object
        trade = Trade(
            entry_price=entry_price,
            exit_price=Decimal("0"),  # Will be set on close
            quantity=quantity,
            entry_time=entry_time,
            exit_time=entry_time,  # Will be updated on close
            side=side,
        )

        self.metrics.open_trades[trade_id] = trade

    def close_trade(
        self,
        trade_id: int,
        exit_price: Decimal,
        exit_time: pd.Timestamp,
        commission: Decimal = Decimal("0"),
    ) -> Trade | None:
        """Close an open trade and update metrics.

        Args:
            trade_id: Trade identifier to close
            exit_price: Exit price
            exit_time: Exit timestamp
            commission: Total commission for the trade

        Returns:
            Completed Trade object or None if trade not found
        """
        if trade_id not in self.metrics.open_trades:
            return None

        # Complete the trade
        trade = self.metrics.open_trades.pop(trade_id)
        trade.exit_price = exit_price
        trade.exit_time = exit_time
        trade.commission = commission

        # Add to completed trades
        self.metrics.completed_trades.append(trade)

        # Update equity
        self._update_equity(trade.pnl)

        # Trigger callback
        if self.metrics.on_trade_complete:
            self.metrics.on_trade_complete(trade)

        # Check if full update needed
        self.metrics.trades_since_update += 1
        if self.metrics.trades_since_update >= self.metrics.update_frequency:
            self.update_all_metrics()
            self.metrics.trades_since_update = 0
        else:
            # Quick update of essential metrics
            self._quick_update(trade)

        return trade

    def _update_equity(self, pnl: Decimal) -> None:
        """Update equity and drawdown tracking.

        Args:
            pnl: P&L from the trade
        """
        self.metrics.current_equity += pnl

        # Update peak equity
        if self.metrics.current_equity > self.metrics.peak_equity:
            self.metrics.peak_equity = self.metrics.current_equity
            self.metrics.current_drawdown = Decimal("0")
        else:
            # Calculate current drawdown
            self.metrics.current_drawdown = (
                self.metrics.peak_equity - self.metrics.current_equity
            ) / self.metrics.peak_equity

        # Update performance equity curve
        self.metrics.performance.equity_curve.append(self.metrics.current_equity)

        # Trigger callback
        if self.metrics.on_equity_update:
            self.metrics.on_equity_update(self.metrics.current_equity)

    def _quick_update(self, trade: Trade) -> None:
        """Quick update of essential metrics after a trade.

        Args:
            trade: Completed trade
        """
        perf = self.metrics.performance

        # Update P&L
        perf.total_pnl += trade.pnl
        perf.commission_paid += trade.commission
        perf.total_trades += 1

        # Update win/loss counts
        if trade.pnl > 0:
            perf.winning_trades += 1
            perf.gross_profit += trade.pnl
        elif trade.pnl < 0:
            perf.losing_trades += 1
            perf.gross_loss += abs(trade.pnl)

        # Update trade stats
        stats = self.metrics.trade_stats
        stats.total_trades = perf.total_trades
        stats.winning_trades = perf.winning_trades
        stats.losing_trades = perf.losing_trades

        if perf.total_trades > 0:
            stats.win_rate = (
                Decimal(perf.winning_trades) / Decimal(perf.total_trades) * 100
            )

    def update_all_metrics(self) -> None:
        """Recalculate all metrics from completed trades."""
        if not self.metrics.completed_trades:
            return

        # Update performance metrics
        self.metrics.performance = calculate_pnl(self.metrics.completed_trades)

        # Update trade statistics
        self.metrics.trade_stats = analyze_trades(self.metrics.completed_trades)

        # Calculate returns for risk metrics
        if len(self.metrics.performance.equity_curve) > 1:
            returns = calculate_returns(
                self.metrics.performance.equity_curve,
                self.metrics.performance.timestamps,
            )

            # Update risk metrics
            self.metrics.risk = calculate_risk_metrics(
                self.metrics.performance.equity_curve,
                self.metrics.performance.timestamps,
                returns,
                self.risk_free_rate,
            )

        # Trigger callback
        if self.metrics.on_metrics_update:
            self.metrics.on_metrics_update(self.metrics)

    def get_current_metrics(self) -> RealtimeMetrics:
        """Get current metrics snapshot.

        Returns:
            Current RealtimeMetrics object
        """
        return self.metrics

    def get_summary(self) -> dict[str, float]:
        """Get summary of key metrics.

        Returns:
            Dictionary of key metric values
        """
        perf = self.metrics.performance
        risk = self.metrics.risk
        stats = self.metrics.trade_stats

        return {
            # Performance
            "total_pnl": float(perf.total_pnl),
            "total_trades": perf.total_trades,
            "win_rate": float(stats.win_rate),
            "profit_factor": float(perf.profit_factor),
            # Risk
            "max_drawdown": float(risk.max_drawdown),
            "sharpe_ratio": risk.sharpe_ratio,
            "volatility": risk.volatility,
            # Current state
            "current_equity": float(self.metrics.current_equity),
            "current_drawdown": float(self.metrics.current_drawdown),
            "open_trades": len(self.metrics.open_trades),
        }

    def reset(self) -> None:
        """Reset all metrics to initial state."""
        self.metrics = RealtimeMetrics(
            starting_equity=self.metrics.starting_equity,
            current_equity=self.metrics.starting_equity,
            peak_equity=self.metrics.starting_equity,
            update_frequency=self.metrics.update_frequency,
        )
