"""Performance metrics for L1+L2 strategy analysis."""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

import numpy as np


@dataclass
class PerformanceMetrics:
    """Overall performance metrics for strategy evaluation."""

    # P&L Metrics
    total_pnl: Decimal = Decimal("0")
    realized_pnl: Decimal = Decimal("0")
    unrealized_pnl: Decimal = Decimal("0")
    gross_profit: Decimal = Decimal("0")
    gross_loss: Decimal = Decimal("0")

    # Return Metrics
    total_return: float = 0.0
    daily_returns: list[float] = field(default_factory=list)
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    max_drawdown: float = 0.0
    max_drawdown_duration_days: int = 0

    # Trade Statistics
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    avg_win: Decimal = Decimal("0")
    avg_loss: Decimal = Decimal("0")
    profit_factor: float = 0.0

    # Commission & Slippage
    total_commission: Decimal = Decimal("0")
    total_slippage: Decimal = Decimal("0")

    def calculate_derived_metrics(self):
        """Calculate derived metrics from raw data."""
        # Win rate
        if self.total_trades > 0:
            self.win_rate = self.winning_trades / self.total_trades

        # Average win/loss
        if self.winning_trades > 0:
            self.avg_win = self.gross_profit / self.winning_trades
        if self.losing_trades > 0:
            self.avg_loss = abs(self.gross_loss) / self.losing_trades

        # Profit factor
        if self.gross_loss != 0:
            self.profit_factor = float(abs(self.gross_profit / self.gross_loss))

        # Sharpe ratio (assuming daily returns)
        if len(self.daily_returns) > 1:
            returns_array = np.array(self.daily_returns)
            if returns_array.std() != 0:
                self.sharpe_ratio = (
                    np.sqrt(252) * returns_array.mean() / returns_array.std()
                )

            # Sortino ratio (downside deviation)
            negative_returns = returns_array[returns_array < 0]
            if len(negative_returns) > 0:
                downside_std = negative_returns.std()
                if downside_std != 0:
                    self.sortino_ratio = (
                        np.sqrt(252) * returns_array.mean() / downside_std
                    )


@dataclass
class SignalQualityMetrics:
    """Metrics specific to L1+L2 signal quality analysis."""

    # Signal Statistics
    total_signals: int = 0
    signals_acted_on: int = 0
    signal_hit_rate: float = 0.0

    # Imbalance Analysis
    avg_imbalance_at_entry: float = 0.0
    avg_imbalance_at_exit: float = 0.0
    imbalance_readings: list[float] = field(default_factory=list)

    # Volume Analysis
    avg_volume_at_signal: float = 0.0
    volume_weighted_signals: int = 0
    volume_readings: list[int] = field(default_factory=list)

    # Confidence Scores
    avg_confidence_score: float = 0.0
    confidence_scores: list[float] = field(default_factory=list)
    high_confidence_hit_rate: float = 0.0  # Hit rate for confidence > 80%

    # Order Book Dynamics
    avg_spread_at_signal: Decimal = Decimal("0")
    avg_book_depth_ratio: float = 0.0  # Bid depth / Ask depth
    microstructure_alpha: float = 0.0  # Predictive power of order book

    def calculate_signal_metrics(self):
        """Calculate derived signal quality metrics."""
        # Signal hit rate
        if self.total_signals > 0:
            self.signal_hit_rate = self.signals_acted_on / self.total_signals

        # Average imbalance
        if self.imbalance_readings:
            self.avg_imbalance_at_entry = np.mean(self.imbalance_readings)

        # Average volume
        if self.volume_readings:
            self.avg_volume_at_signal = np.mean(self.volume_readings)

        # Average confidence
        if self.confidence_scores:
            self.avg_confidence_score = np.mean(self.confidence_scores)

            # High confidence hit rate
            high_conf_signals = [c for c in self.confidence_scores if c > 80]
            if high_conf_signals:
                self.high_confidence_hit_rate = len(high_conf_signals) / len(
                    self.confidence_scores
                )


@dataclass
class ExecutionMetrics:
    """Metrics for order execution quality."""

    # Fill Statistics
    total_orders: int = 0
    filled_orders: int = 0
    partially_filled_orders: int = 0
    rejected_orders: int = 0
    fill_rate: float = 0.0

    # Latency Analysis
    avg_signal_to_order_latency_us: float = 0.0
    avg_order_to_fill_latency_us: float = 0.0
    latency_readings: list[float] = field(default_factory=list)

    # Slippage Analysis
    avg_slippage_ticks: float = 0.0
    positive_slippage_count: int = 0
    negative_slippage_count: int = 0
    slippage_readings: list[float] = field(default_factory=list)

    # Market Impact
    avg_market_impact_bps: float = 0.0
    immediate_impact_bps: float = 0.0
    permanent_impact_bps: float = 0.0

    def calculate_execution_metrics(self):
        """Calculate derived execution metrics."""
        # Fill rate
        if self.total_orders > 0:
            self.fill_rate = self.filled_orders / self.total_orders

        # Average latencies
        if self.latency_readings:
            total_latency = sum(self.latency_readings)
            self.avg_signal_to_order_latency_us = total_latency / len(
                self.latency_readings
            )

        # Slippage analysis
        if self.slippage_readings:
            self.avg_slippage_ticks = np.mean(self.slippage_readings)
            self.positive_slippage_count = sum(
                1 for s in self.slippage_readings if s > 0
            )
            self.negative_slippage_count = sum(
                1 for s in self.slippage_readings if s < 0
            )


@dataclass
class RiskMetrics:
    """Risk management metrics."""

    # Position Risk
    max_position_size: int = 0
    avg_position_size: float = 0.0
    position_sizes: list[int] = field(default_factory=list)

    # Drawdown Analysis
    current_drawdown: float = 0.0
    drawdown_periods: list[dict[str, Any]] = field(default_factory=list)
    recovery_time_days: float = 0.0

    # Risk-Adjusted Returns
    calmar_ratio: float = 0.0  # Annual return / Max drawdown
    sterling_ratio: float = 0.0
    burke_ratio: float = 0.0

    # Value at Risk
    var_95: float = 0.0  # 95% VaR
    var_99: float = 0.0  # 99% VaR
    cvar_95: float = 0.0  # Conditional VaR

    # Exposure Metrics
    long_exposure_pct: float = 0.0
    short_exposure_pct: float = 0.0
    net_exposure_pct: float = 0.0
    time_in_market_pct: float = 0.0

    def calculate_risk_metrics(self, returns: list[float], annual_return: float):
        """Calculate risk metrics from returns data."""
        if not returns:
            return

        returns_array = np.array(returns)

        # Position statistics
        if self.position_sizes:
            positions_array = np.array(self.position_sizes)
            self.avg_position_size = np.mean(np.abs(positions_array))
            self.max_position_size = int(np.max(np.abs(positions_array)))

        # VaR calculations
        if len(returns_array) > 20:
            self.var_95 = np.percentile(returns_array, 5)
            self.var_99 = np.percentile(returns_array, 1)

            # CVaR (Expected Shortfall)
            var_95_returns = returns_array[returns_array <= self.var_95]
            if len(var_95_returns) > 0:
                self.cvar_95 = var_95_returns.mean()

        # Risk-adjusted ratios
        if hasattr(self, "max_drawdown") and self.max_drawdown != 0:
            self.calmar_ratio = annual_return / abs(self.max_drawdown)

        # Market exposure
        if self.position_sizes:
            total_periods = len(self.position_sizes)
            long_periods = sum(1 for p in self.position_sizes if p > 0)
            short_periods = sum(1 for p in self.position_sizes if p < 0)

            self.long_exposure_pct = long_periods / total_periods * 100
            self.short_exposure_pct = short_periods / total_periods * 100
            self.time_in_market_pct = (
                (long_periods + short_periods) / total_periods * 100
            )
