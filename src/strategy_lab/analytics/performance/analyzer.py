"""Performance analyzer for L1+L2 trading strategies."""

import logging
from decimal import Decimal
from typing import Any

import pandas as pd

from strategy_lab.data.synchronization import UnifiedMarketSnapshot
from strategy_lab.strategies.protocol_enhanced import OrderRequest, OrderSide

from .metrics import (
    ExecutionMetrics,
    PerformanceMetrics,
    RiskMetrics,
    SignalQualityMetrics,
)

logger = logging.getLogger(__name__)


class L1L2PerformanceAnalyzer:
    """Analyzes performance of L1+L2 trading strategies."""

    def __init__(self, initial_capital: Decimal = Decimal("100000")):
        """Initialize the performance analyzer.

        Args:
            initial_capital: Starting capital for calculations
        """
        self.initial_capital = initial_capital
        self.current_capital = initial_capital

        # Metrics containers
        self.performance = PerformanceMetrics()
        self.signal_quality = SignalQualityMetrics()
        self.execution = ExecutionMetrics()
        self.risk = RiskMetrics()

        # Trade tracking
        self.trades: list[dict[str, Any]] = []
        self.open_positions: dict[str, dict[str, Any]] = {}
        self.equity_curve: list[tuple[int, Decimal]] = []

        # Signal tracking
        self.signals: list[dict[str, Any]] = []
        self.market_snapshots: list[UnifiedMarketSnapshot] = []

        # Time tracking
        self.start_time: int | None = None
        self.end_time: int | None = None

    def record_signal(
        self,
        timestamp: int,
        snapshot: UnifiedMarketSnapshot,
        confidence: float,
        imbalance: float,
        volume: int,
        action_taken: bool,
    ):
        """Record a trading signal for analysis.

        Args:
            timestamp: Signal timestamp
            snapshot: Market snapshot at signal time
            confidence: Signal confidence score
            imbalance: Order book imbalance
            volume: Trade volume at signal
            action_taken: Whether signal resulted in trade
        """
        signal = {
            "timestamp": timestamp,
            "confidence": confidence,
            "imbalance": imbalance,
            "volume": volume,
            "spread": float(snapshot.spread) if snapshot.spread else 0,
            "mid_price": float(snapshot.mid_price) if snapshot.mid_price else 0,
            "bid_depth": snapshot.total_bid_depth,
            "ask_depth": snapshot.total_ask_depth,
            "action_taken": action_taken,
        }

        self.signals.append(signal)
        self.signal_quality.total_signals += 1

        if action_taken:
            self.signal_quality.signals_acted_on += 1

        # Update signal quality metrics
        self.signal_quality.confidence_scores.append(confidence)
        self.signal_quality.imbalance_readings.append(imbalance)
        self.signal_quality.volume_readings.append(volume)

        if snapshot.spread:
            self.signal_quality.avg_spread_at_signal = (
                self.signal_quality.avg_spread_at_signal
                + (snapshot.spread - self.signal_quality.avg_spread_at_signal)
                / self.signal_quality.total_signals
            )

    def record_order(
        self,
        order: OrderRequest,
        fill_price: Decimal | None = None,
        fill_timestamp: int | None = None,
        rejected: bool = False,
    ):
        """Record an order execution.

        Args:
            order: Order request
            fill_price: Actual fill price
            fill_timestamp: Fill timestamp
            rejected: Whether order was rejected
        """
        self.execution.total_orders += 1

        if rejected:
            self.execution.rejected_orders += 1
            return

        if fill_price:
            self.execution.filled_orders += 1

            # Calculate slippage
            if order.price:
                slippage_ticks = float((fill_price - order.price) / Decimal("0.25"))
                if order.side == OrderSide.SELL:
                    slippage_ticks = -slippage_ticks

                self.execution.slippage_readings.append(slippage_ticks)

            # Calculate latency if timestamps available
            if fill_timestamp and "signal_time" in order.metadata:
                latency_us = (fill_timestamp - order.metadata["signal_time"]) / 1000
                self.execution.latency_readings.append(latency_us)

    def record_trade(
        self,
        timestamp: int,
        side: OrderSide,
        size: int,
        entry_price: Decimal,
        exit_price: Decimal | None = None,
        commission: Decimal = Decimal("0"),
        metadata: dict[str, Any] | None = None,
    ):
        """Record a completed trade.

        Args:
            timestamp: Trade timestamp
            side: Trade side (buy/sell)
            size: Position size
            entry_price: Entry price
            exit_price: Exit price (if closed)
            commission: Trade commission
            metadata: Additional trade metadata
        """
        if not self.start_time:
            self.start_time = timestamp
        self.end_time = timestamp

        trade = {
            "timestamp": timestamp,
            "side": side,
            "size": size,
            "entry_price": entry_price,
            "exit_price": exit_price,
            "commission": commission,
            "metadata": metadata or {},
            "pnl": Decimal("0"),
        }

        # Handle position tracking
        position_key = f"{side.name}_{timestamp}"

        if exit_price:
            # This is a complete round-trip trade
            if side == OrderSide.BUY:
                # Long trade: buy at entry, sell at exit
                trade["pnl"] = (exit_price - entry_price) * size - commission
            else:
                # Short trade: sell at entry, buy back at exit
                trade["pnl"] = (entry_price - exit_price) * size - commission

            self._update_performance_metrics(trade)

        else:
            # Opening trade
            self.open_positions[position_key] = trade

        self.trades.append(trade)
        self.performance.total_trades += 1
        self.performance.total_commission += commission

        # Update equity curve
        self.current_capital += trade["pnl"]
        self.equity_curve.append((timestamp, self.current_capital))

        # Update position tracking
        if exit_price:
            # For closed trades, track the position size
            self.risk.position_sizes.append(size if side == OrderSide.BUY else -size)
        else:
            # For open positions, also track the size
            self.risk.position_sizes.append(size if side == OrderSide.BUY else -size)

    def _update_performance_metrics(self, trade: dict[str, Any]):
        """Update performance metrics with completed trade."""
        pnl = trade["pnl"]

        self.performance.realized_pnl += pnl
        self.performance.total_pnl = self.performance.realized_pnl

        if pnl > 0:
            self.performance.winning_trades += 1
            self.performance.gross_profit += pnl
        else:
            self.performance.losing_trades += 1
            self.performance.gross_loss += pnl

    def calculate_metrics(self) -> dict[str, Any]:
        """Calculate all performance metrics.

        Returns:
            Dictionary containing all calculated metrics
        """
        # Calculate derived performance metrics
        self.performance.calculate_derived_metrics()

        # Calculate signal quality metrics
        self.signal_quality.calculate_signal_metrics()

        # Calculate execution metrics
        self.execution.calculate_execution_metrics()

        # Calculate daily returns if we have equity curve
        if len(self.equity_curve) > 1:
            self._calculate_returns_and_drawdowns()

        # Calculate risk metrics
        self.risk.calculate_risk_metrics(
            self.performance.daily_returns,
            self.performance.total_return * 252,  # Annualized
        )

        # Compile results
        return {
            "performance": self._metrics_to_dict(self.performance),
            "signal_quality": self._metrics_to_dict(self.signal_quality),
            "execution": self._metrics_to_dict(self.execution),
            "risk": self._metrics_to_dict(self.risk),
            "summary": self._create_summary(),
        }

    def _calculate_returns_and_drawdowns(self):
        """Calculate returns and drawdown metrics from equity curve."""
        # Convert equity curve to DataFrame
        equity_df = pd.DataFrame(self.equity_curve, columns=["timestamp", "equity"])
        equity_df["timestamp"] = pd.to_datetime(equity_df["timestamp"], unit="ns")
        equity_df = equity_df.set_index("timestamp")

        # Resample to daily if needed
        if len(equity_df) > 1:
            daily_equity = equity_df.resample("D").last().ffill()

            # Calculate daily returns
            daily_equity["returns"] = daily_equity["equity"].pct_change()
            self.performance.daily_returns = daily_equity["returns"].dropna().tolist()

            # Total return
            self.performance.total_return = float(
                (self.current_capital - self.initial_capital) / self.initial_capital
            )

            # Calculate drawdowns
            daily_equity["cum_max"] = daily_equity["equity"].cummax()
            daily_equity["drawdown"] = (
                daily_equity["equity"] - daily_equity["cum_max"]
            ) / daily_equity["cum_max"]

            # Max drawdown
            self.performance.max_drawdown = float(daily_equity["drawdown"].min())

            # Drawdown duration
            drawdown_periods = self._identify_drawdown_periods(daily_equity)
            if drawdown_periods:
                max_duration = max(p["duration_days"] for p in drawdown_periods)
                self.performance.max_drawdown_duration_days = max_duration
                self.risk.drawdown_periods = drawdown_periods

    def _identify_drawdown_periods(
        self, daily_equity_df: pd.DataFrame
    ) -> list[dict[str, Any]]:
        """Identify distinct drawdown periods."""
        periods = []
        in_drawdown = False
        start_date = None

        for date, row in daily_equity_df.iterrows():
            if row["drawdown"] < 0 and not in_drawdown:
                # Start of drawdown
                in_drawdown = True
                start_date = date
            elif row["drawdown"] == 0 and in_drawdown:
                # End of drawdown
                in_drawdown = False
                if start_date:
                    duration = (date - start_date).days
                    periods.append(
                        {
                            "start": start_date,
                            "end": date,
                            "duration_days": duration,
                            "max_drawdown": daily_equity_df.loc[
                                start_date:date, "drawdown"
                            ].min(),
                        }
                    )

        return periods

    def _metrics_to_dict(self, metrics: Any) -> dict[str, Any]:
        """Convert metrics dataclass to dictionary."""
        result = {}
        for field_name in metrics.__dataclass_fields__:
            value = getattr(metrics, field_name)
            if isinstance(value, Decimal):
                result[field_name] = float(value)
            elif isinstance(value, list) and value and isinstance(value[0], Decimal):
                result[field_name] = [float(v) for v in value]
            else:
                result[field_name] = value
        return result

    def _create_summary(self) -> dict[str, Any]:
        """Create executive summary of performance."""
        return {
            "total_return_pct": round(self.performance.total_return * 100, 2),
            "sharpe_ratio": round(self.performance.sharpe_ratio, 2),
            "max_drawdown_pct": round(self.performance.max_drawdown * 100, 2),
            "win_rate_pct": round(self.performance.win_rate * 100, 2),
            "profit_factor": round(self.performance.profit_factor, 2),
            "total_trades": self.performance.total_trades,
            "avg_confidence": round(self.signal_quality.avg_confidence_score, 1),
            "signal_hit_rate_pct": round(self.signal_quality.signal_hit_rate * 100, 2),
            "fill_rate_pct": round(self.execution.fill_rate * 100, 2),
            "avg_slippage_ticks": round(self.execution.avg_slippage_ticks, 2),
        }

    def get_equity_curve(self) -> pd.DataFrame:
        """Get equity curve as DataFrame.

        Returns:
            DataFrame with timestamp and equity columns
        """
        if not self.equity_curve:
            return pd.DataFrame()

        equity_df = pd.DataFrame(self.equity_curve, columns=["timestamp", "equity"])
        equity_df["timestamp"] = pd.to_datetime(equity_df["timestamp"], unit="ns")
        return equity_df.set_index("timestamp")

    def get_trade_log(self) -> pd.DataFrame:
        """Get detailed trade log.

        Returns:
            DataFrame with all trade details
        """
        if not self.trades:
            return pd.DataFrame()

        trade_df = pd.DataFrame(self.trades)
        trade_df["timestamp"] = pd.to_datetime(trade_df["timestamp"], unit="ns")
        return trade_df
