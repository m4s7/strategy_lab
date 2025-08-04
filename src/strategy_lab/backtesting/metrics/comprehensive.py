"""Comprehensive performance metrics calculation system."""

import logging
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .performance import PerformanceMetrics, Trade, calculate_pnl, calculate_returns
from .risk import RiskMetrics, calculate_risk_metrics
from .trade_analysis import TradeStatistics, analyze_trades

logger = logging.getLogger(__name__)


@dataclass
class ComprehensiveMetrics:
    """Container for all comprehensive performance metrics."""

    # Performance metrics
    performance: PerformanceMetrics = field(default_factory=PerformanceMetrics)

    # Risk metrics
    risk: RiskMetrics = field(default_factory=RiskMetrics)

    # Trade analysis
    trade_stats: TradeStatistics = field(default_factory=TradeStatistics)

    # Return analysis
    total_return: float = 0.0
    annualized_return: float = 0.0
    excess_return: float = 0.0

    # Time series data
    daily_returns: pd.Series = field(default_factory=lambda: pd.Series(dtype=float))
    monthly_returns: pd.Series = field(default_factory=lambda: pd.Series(dtype=float))
    drawdown_series: pd.Series = field(default_factory=lambda: pd.Series(dtype=float))

    # Additional metrics
    calmar_ratio: float = 0.0
    recovery_factor: float = 0.0
    profit_to_max_dd_ratio: float = 0.0

    # Rolling performance
    rolling_sharpe_30d: pd.Series = field(
        default_factory=lambda: pd.Series(dtype=float)
    )
    rolling_sharpe_90d: pd.Series = field(
        default_factory=lambda: pd.Series(dtype=float)
    )

    # Best/worst periods
    best_month: tuple[pd.Timestamp, float] = field(
        default_factory=lambda: (pd.Timestamp.now(), 0.0)
    )
    worst_month: tuple[pd.Timestamp, float] = field(
        default_factory=lambda: (pd.Timestamp.now(), 0.0)
    )
    best_day: tuple[pd.Timestamp, float] = field(
        default_factory=lambda: (pd.Timestamp.now(), 0.0)
    )
    worst_day: tuple[pd.Timestamp, float] = field(
        default_factory=lambda: (pd.Timestamp.now(), 0.0)
    )


class ComprehensiveMetricsCalculator:
    """Calculator for comprehensive performance metrics."""

    def __init__(self, risk_free_rate: float = 0.02, periods_per_year: int = 252):
        """Initialize the metrics calculator.

        Args:
            risk_free_rate: Annual risk-free rate for Sharpe/Sortino calculations
            periods_per_year: Number of trading periods per year (252 for daily)
        """
        self.risk_free_rate = risk_free_rate
        self.periods_per_year = periods_per_year

    def calculate_all_metrics(
        self,
        trades: list[Trade],
        equity_curve: list[Decimal],
        timestamps: list[pd.Timestamp],
        initial_capital: Decimal,
    ) -> ComprehensiveMetrics:
        """Calculate comprehensive metrics from trade data.

        Args:
            trades: List of completed trades
            equity_curve: Equity values over time
            timestamps: Corresponding timestamps
            initial_capital: Starting capital

        Returns:
            ComprehensiveMetrics object with all calculated values
        """
        metrics = ComprehensiveMetrics()

        if not trades and len(equity_curve) < 2:
            logger.warning(
                "No trades or equity data provided - returning empty metrics"
            )
            return metrics

        # Calculate basic performance metrics
        logger.debug("Calculating performance metrics...")
        metrics.performance = calculate_pnl(trades)

        # Calculate trade statistics
        logger.debug("Calculating trade statistics...")
        metrics.trade_stats = analyze_trades(trades)

        # Calculate returns series
        if len(equity_curve) >= 2 and len(timestamps) >= 2:
            logger.debug("Calculating return series...")
            metrics.daily_returns = calculate_returns(equity_curve, timestamps, "D")
            metrics.monthly_returns = calculate_returns(equity_curve, timestamps, "ME")

            # Calculate total and annualized returns
            metrics.total_return = self._calculate_total_return(
                equity_curve, initial_capital
            )
            metrics.annualized_return = self._calculate_annualized_return(
                metrics.total_return, timestamps
            )
            metrics.excess_return = metrics.annualized_return - self.risk_free_rate

            # Calculate risk metrics
            logger.debug("Calculating risk metrics...")
            metrics.risk = calculate_risk_metrics(
                equity_curve,
                timestamps,
                metrics.daily_returns,
                self.risk_free_rate,
                self.periods_per_year,
            )

            # Calculate additional risk-adjusted metrics
            metrics.calmar_ratio = self._calculate_calmar_ratio(
                metrics.annualized_return, float(metrics.risk.max_drawdown)
            )
            metrics.recovery_factor = self._calculate_recovery_factor(
                float(metrics.performance.total_pnl), float(metrics.risk.max_drawdown)
            )
            metrics.profit_to_max_dd_ratio = self._calculate_profit_to_max_dd_ratio(
                float(metrics.performance.total_pnl), float(metrics.risk.max_drawdown)
            )

            # Calculate drawdown series
            metrics.drawdown_series = self._calculate_drawdown_series(
                equity_curve, timestamps
            )

            # Calculate rolling performance metrics
            if len(metrics.daily_returns) >= 30:
                metrics.rolling_sharpe_30d = self._calculate_rolling_sharpe(
                    metrics.daily_returns, window=30
                )
            if len(metrics.daily_returns) >= 90:
                metrics.rolling_sharpe_90d = self._calculate_rolling_sharpe(
                    metrics.daily_returns, window=90
                )

            # Find best/worst periods
            metrics.best_month, metrics.worst_month = self._find_best_worst_months(
                trades
            )
            metrics.best_day, metrics.worst_day = self._find_best_worst_days(trades)

        logger.info("Comprehensive metrics calculation completed")
        return metrics

    def _calculate_total_return(
        self, equity_curve: list[Decimal], initial_capital: Decimal
    ) -> float:
        """Calculate total return percentage."""
        if len(equity_curve) < 2 or initial_capital == 0:
            return 0.0
        final_equity = equity_curve[-1]
        return float((final_equity - initial_capital) / initial_capital)

    def _calculate_annualized_return(
        self, total_return: float, timestamps: list[pd.Timestamp]
    ) -> float:
        """Calculate annualized return."""
        if len(timestamps) < 2:
            return 0.0
        years = (timestamps[-1] - timestamps[0]).days / 365.25
        if years <= 0:
            return 0.0
        return (1 + total_return) ** (1 / years) - 1

    def _calculate_calmar_ratio(
        self, annual_return: float, max_drawdown: float
    ) -> float:
        """Calculate Calmar ratio (annual return / max drawdown)."""
        if max_drawdown == 0:
            return 0.0
        return annual_return / max_drawdown

    def _calculate_recovery_factor(
        self, total_pnl: float, max_drawdown: float
    ) -> float:
        """Calculate recovery factor (net profit / max drawdown)."""
        if max_drawdown == 0:
            return 0.0
        return total_pnl / max_drawdown

    def _calculate_profit_to_max_dd_ratio(
        self, total_pnl: float, max_drawdown: float
    ) -> float:
        """Calculate profit to max drawdown ratio."""
        if max_drawdown == 0:
            return 0.0
        return abs(total_pnl) / max_drawdown

    def _calculate_drawdown_series(
        self, equity_curve: list[Decimal], timestamps: list[pd.Timestamp]
    ) -> pd.Series:
        """Calculate drawdown series."""
        if len(equity_curve) < 2:
            return pd.Series(dtype=float)

        equity_array = np.array([float(e) for e in equity_curve])
        running_max = np.maximum.accumulate(equity_array)

        # Calculate drawdown percentage
        drawdown = np.where(
            running_max > 0, (equity_array - running_max) / running_max, 0.0
        )

        return pd.Series(drawdown, index=timestamps)

    def _calculate_rolling_sharpe(self, returns: pd.Series, window: int) -> pd.Series:
        """Calculate rolling Sharpe ratio."""
        if len(returns) < window:
            return pd.Series(dtype=float)

        period_rf = self.risk_free_rate / self.periods_per_year
        excess_returns = returns - period_rf

        rolling_mean = excess_returns.rolling(window=window).mean()
        rolling_std = excess_returns.rolling(window=window).std()

        # Avoid division by zero
        rolling_sharpe = np.where(
            rolling_std > 0,
            rolling_mean / rolling_std * np.sqrt(self.periods_per_year),
            0.0,
        )

        return pd.Series(rolling_sharpe, index=returns.index)

    def _find_best_worst_months(
        self, trades: list[Trade]
    ) -> tuple[tuple[pd.Timestamp, float], tuple[pd.Timestamp, float]]:
        """Find best and worst performing months."""
        if not trades:
            now = pd.Timestamp.now()
            return (now, 0.0), (now, 0.0)

        # Group trades by month
        monthly_pnl = {}
        for trade in trades:
            month_start = pd.Timestamp(trade.exit_time.year, trade.exit_time.month, 1)
            if month_start not in monthly_pnl:
                monthly_pnl[month_start] = 0.0
            monthly_pnl[month_start] += float(trade.pnl)

        if not monthly_pnl:
            now = pd.Timestamp.now()
            return (now, 0.0), (now, 0.0)

        best_month = max(monthly_pnl.items(), key=lambda x: x[1])
        worst_month = min(monthly_pnl.items(), key=lambda x: x[1])

        return best_month, worst_month

    def _find_best_worst_days(
        self, trades: list[Trade]
    ) -> tuple[tuple[pd.Timestamp, float], tuple[pd.Timestamp, float]]:
        """Find best and worst performing days."""
        if not trades:
            now = pd.Timestamp.now()
            return (now, 0.0), (now, 0.0)

        # Group trades by day
        daily_pnl = {}
        for trade in trades:
            day = trade.exit_time.date()
            if day not in daily_pnl:
                daily_pnl[day] = 0.0
            daily_pnl[day] += float(trade.pnl)

        if not daily_pnl:
            now = pd.Timestamp.now()
            return (now, 0.0), (now, 0.0)

        best_day_date, best_pnl = max(daily_pnl.items(), key=lambda x: x[1])
        worst_day_date, worst_pnl = min(daily_pnl.items(), key=lambda x: x[1])

        best_day = (pd.Timestamp(best_day_date), best_pnl)
        worst_day = (pd.Timestamp(worst_day_date), worst_pnl)

        return best_day, worst_day

    def export_detailed_report(
        self,
        metrics: ComprehensiveMetrics,
        output_path: Path,
        config_info: dict[str, Any] | None = None,
    ) -> None:
        """Export detailed performance report to files.

        Args:
            metrics: Calculated metrics
            output_path: Directory to save files
            config_info: Optional configuration information
        """
        output_path.mkdir(parents=True, exist_ok=True)

        # Create summary report
        self._create_summary_report(
            metrics, output_path / "performance_summary.txt", config_info
        )

        # Export CSV files
        self._export_csv_files(metrics, output_path)

        # Export JSON summary
        self._export_json_summary(
            metrics, output_path / "metrics_summary.json", config_info
        )

        logger.info(f"Detailed performance report exported to {output_path}")

    def _create_summary_report(
        self,
        metrics: ComprehensiveMetrics,
        file_path: Path,
        config_info: dict[str, Any] | None = None,
    ) -> None:
        """Create human-readable summary report."""
        with open(file_path, "w") as f:
            f.write("COMPREHENSIVE PERFORMANCE REPORT\n")
            f.write("=" * 50 + "\n\n")

            if config_info:
                f.write("Configuration:\n")
                f.write(f"  Strategy: {config_info.get('strategy_name', 'Unknown')}\n")
                f.write(
                    f"  Period: {config_info.get('start_date', 'N/A')} to {config_info.get('end_date', 'N/A')}\n"
                )
                f.write(
                    f"  Initial Capital: ${config_info.get('initial_capital', 'N/A'):,}\n\n"
                )

            # Performance Summary
            f.write("PERFORMANCE SUMMARY\n")
            f.write("-" * 20 + "\n")
            f.write(f"Total Return: {metrics.total_return:.2%}\n")
            f.write(f"Annualized Return: {metrics.annualized_return:.2%}\n")
            f.write(f"Excess Return: {metrics.excess_return:.2%}\n")
            f.write(f"Total P&L: ${float(metrics.performance.total_pnl):,.2f}\n")
            f.write(f"Net Profit: ${float(metrics.performance.net_profit):,.2f}\n\n")

            # Risk Metrics
            f.write("RISK METRICS\n")
            f.write("-" * 12 + "\n")
            f.write(f"Sharpe Ratio: {metrics.risk.sharpe_ratio:.3f}\n")
            f.write(f"Sortino Ratio: {metrics.risk.sortino_ratio:.3f}\n")
            f.write(f"Calmar Ratio: {metrics.calmar_ratio:.3f}\n")
            f.write(f"Max Drawdown: {float(metrics.risk.max_drawdown):.2%}\n")
            f.write(f"Volatility (Ann.): {metrics.risk.volatility:.2%}\n")
            f.write(f"VaR (95%): {metrics.risk.var_95:.2%}\n")
            f.write(f"CVaR (95%): {metrics.risk.cvar_95:.2%}\n\n")

            # Trade Analysis
            f.write("TRADE ANALYSIS\n")
            f.write("-" * 14 + "\n")
            f.write(f"Total Trades: {metrics.trade_stats.total_trades}\n")
            f.write(f"Winning Trades: {metrics.trade_stats.winning_trades}\n")
            f.write(f"Losing Trades: {metrics.trade_stats.losing_trades}\n")
            f.write(f"Win Rate: {float(metrics.trade_stats.win_rate):.2f}%\n")
            f.write(f"Profit Factor: {float(metrics.trade_stats.profit_factor):.2f}\n")
            f.write(f"Average Trade: ${float(metrics.trade_stats.avg_trade):,.2f}\n")
            f.write(f"Average Win: ${float(metrics.trade_stats.avg_win):,.2f}\n")
            f.write(f"Average Loss: ${float(metrics.trade_stats.avg_loss):,.2f}\n")
            f.write(f"Largest Win: ${float(metrics.trade_stats.largest_win):,.2f}\n")
            f.write(
                f"Largest Loss: ${float(metrics.trade_stats.largest_loss):,.2f}\n\n"
            )

            # Best/Worst Periods
            f.write("BEST/WORST PERIODS\n")
            f.write("-" * 18 + "\n")
            f.write(
                f"Best Month: {metrics.best_month[0].strftime('%Y-%m')} (${metrics.best_month[1]:,.2f})\n"
            )
            f.write(
                f"Worst Month: {metrics.worst_month[0].strftime('%Y-%m')} (${metrics.worst_month[1]:,.2f})\n"
            )
            f.write(
                f"Best Day: {metrics.best_day[0].strftime('%Y-%m-%d')} (${metrics.best_day[1]:,.2f})\n"
            )
            f.write(
                f"Worst Day: {metrics.worst_day[0].strftime('%Y-%m-%d')} (${metrics.worst_day[1]:,.2f})\n\n"
            )

    def _export_csv_files(
        self, metrics: ComprehensiveMetrics, output_path: Path
    ) -> None:
        """Export data to CSV files."""
        # Export daily returns
        if not metrics.daily_returns.empty:
            returns_df = pd.DataFrame(
                {
                    "date": metrics.daily_returns.index,
                    "daily_return": metrics.daily_returns.values,
                }
            )
            returns_df.to_csv(output_path / "daily_returns.csv", index=False)

        # Export monthly returns
        if not metrics.monthly_returns.empty:
            monthly_df = pd.DataFrame(
                {
                    "month": metrics.monthly_returns.index,
                    "monthly_return": metrics.monthly_returns.values,
                }
            )
            monthly_df.to_csv(output_path / "monthly_returns.csv", index=False)

        # Export drawdown series
        if not metrics.drawdown_series.empty:
            dd_df = pd.DataFrame(
                {
                    "timestamp": metrics.drawdown_series.index,
                    "drawdown": metrics.drawdown_series.values,
                }
            )
            dd_df.to_csv(output_path / "drawdown_series.csv", index=False)

    def _export_json_summary(
        self,
        metrics: ComprehensiveMetrics,
        file_path: Path,
        config_info: dict[str, Any] | None = None,
    ) -> None:
        """Export metrics summary as JSON."""
        import json

        summary = {
            "configuration": config_info or {},
            "performance": {
                "total_return": metrics.total_return,
                "annualized_return": metrics.annualized_return,
                "excess_return": metrics.excess_return,
                "total_pnl": float(metrics.performance.total_pnl),
                "net_profit": float(metrics.performance.net_profit),
                "profit_factor": float(metrics.performance.profit_factor),
                "expectancy": float(metrics.performance.expectancy),
            },
            "risk": {
                "sharpe_ratio": metrics.risk.sharpe_ratio,
                "sortino_ratio": metrics.risk.sortino_ratio,
                "calmar_ratio": metrics.calmar_ratio,
                "max_drawdown": float(metrics.risk.max_drawdown),
                "volatility": metrics.risk.volatility,
                "var_95": metrics.risk.var_95,
                "cvar_95": metrics.risk.cvar_95,
                "recovery_factor": metrics.recovery_factor,
            },
            "trade_analysis": {
                "total_trades": metrics.trade_stats.total_trades,
                "winning_trades": metrics.trade_stats.winning_trades,
                "losing_trades": metrics.trade_stats.losing_trades,
                "win_rate": float(metrics.trade_stats.win_rate),
                "avg_trade": float(metrics.trade_stats.avg_trade),
                "avg_win": float(metrics.trade_stats.avg_win),
                "avg_loss": float(metrics.trade_stats.avg_loss),
                "largest_win": float(metrics.trade_stats.largest_win),
                "largest_loss": float(metrics.trade_stats.largest_loss),
                "max_consecutive_wins": metrics.trade_stats.max_consecutive_wins,
                "max_consecutive_losses": metrics.trade_stats.max_consecutive_losses,
            },
            "periods": {
                "best_month": {
                    "date": metrics.best_month[0].isoformat(),
                    "pnl": metrics.best_month[1],
                },
                "worst_month": {
                    "date": metrics.worst_month[0].isoformat(),
                    "pnl": metrics.worst_month[1],
                },
                "best_day": {
                    "date": metrics.best_day[0].isoformat(),
                    "pnl": metrics.best_day[1],
                },
                "worst_day": {
                    "date": metrics.worst_day[0].isoformat(),
                    "pnl": metrics.worst_day[1],
                },
            },
        }

        with open(file_path, "w") as f:
            json.dump(summary, f, indent=2, default=str)


def convert_portfolio_trades_to_performance_trades(
    portfolio_trades: list[Any],
) -> list[Trade]:
    """Convert portfolio trade records to performance Trade objects.

    Args:
        portfolio_trades: List of portfolio trade records

    Returns:
        List of Trade objects
    """
    trades = []
    for trade in portfolio_trades:
        # Convert portfolio trade to performance Trade
        perf_trade = Trade(
            entry_price=trade.entry_price,
            exit_price=trade.exit_price,
            quantity=trade.quantity,
            entry_time=trade.entry_time,
            exit_time=trade.exit_time,
            side="BUY" if trade.side.value == "LONG" else "SELL",
            commission=trade.commission
            if hasattr(trade, "commission")
            else Decimal("0"),
        )
        trades.append(perf_trade)
    return trades
