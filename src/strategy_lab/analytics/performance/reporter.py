"""Performance reporting for L1+L2 strategy analytics."""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.figure import Figure

try:
    import seaborn as sns  # noqa: F401

    HAS_SEABORN = True
except ImportError:
    HAS_SEABORN = False

from .analyzer import L1L2PerformanceAnalyzer

logger = logging.getLogger(__name__)


class PerformanceReporter:
    """Generate performance reports for L1+L2 strategies."""

    def __init__(self, analyzer: L1L2PerformanceAnalyzer):
        """Initialize reporter with analyzer instance.

        Args:
            analyzer: Performance analyzer with calculated metrics
        """
        self.analyzer = analyzer
        self.metrics = analyzer.calculate_metrics()

    def generate_text_report(self) -> str:
        """Generate a text-based performance report.

        Returns:
            Formatted text report
        """
        report = []
        report.append("=" * 80)
        report.append("L1+L2 STRATEGY PERFORMANCE REPORT")
        report.append("=" * 80)
        report.append(
            f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}"  # noqa: UP017
        )
        report.append("")

        # Executive Summary
        summary = self.metrics["summary"]
        report.append("EXECUTIVE SUMMARY")
        report.append("-" * 40)
        report.append(f"Total Return: {summary['total_return_pct']:.2f}%")
        report.append(f"Sharpe Ratio: {summary['sharpe_ratio']:.2f}")
        report.append(f"Max Drawdown: {summary['max_drawdown_pct']:.2f}%")
        report.append(f"Win Rate: {summary['win_rate_pct']:.2f}%")
        report.append(f"Profit Factor: {summary['profit_factor']:.2f}")
        report.append(f"Total Trades: {summary['total_trades']}")
        report.append("")

        # Performance Metrics
        perf = self.metrics["performance"]
        report.append("PERFORMANCE METRICS")
        report.append("-" * 40)
        report.append(f"Total P&L: ${perf['total_pnl']:,.2f}")
        report.append(f"Gross Profit: ${perf['gross_profit']:,.2f}")
        report.append(f"Gross Loss: ${perf['gross_loss']:,.2f}")
        report.append(f"Winning Trades: {perf['winning_trades']}")
        report.append(f"Losing Trades: {perf['losing_trades']}")
        report.append(f"Average Win: ${perf['avg_win']:,.2f}")
        report.append(f"Average Loss: ${perf['avg_loss']:,.2f}")
        report.append(f"Total Commission: ${perf['total_commission']:,.2f}")
        report.append(f"Sortino Ratio: {perf['sortino_ratio']:.2f}")
        report.append(
            f"Max Drawdown Duration: {perf['max_drawdown_duration_days']} days"
        )
        report.append("")

        # Signal Quality Metrics
        signal = self.metrics["signal_quality"]
        report.append("SIGNAL QUALITY METRICS")
        report.append("-" * 40)
        report.append(f"Total Signals: {signal['total_signals']}")
        report.append(f"Signals Acted On: {signal['signals_acted_on']}")
        report.append(f"Signal Hit Rate: {signal['signal_hit_rate'] * 100:.2f}%")
        report.append(f"Average Confidence: {signal['avg_confidence_score']:.1f}%")
        report.append(
            f"High Confidence Hit Rate: {signal['high_confidence_hit_rate'] * 100:.2f}%"
        )
        report.append(f"Average Imbalance: {signal['avg_imbalance_at_entry']:.3f}")
        report.append(f"Average Volume: {signal['avg_volume_at_signal']:.0f}")
        report.append(f"Average Spread: ${signal['avg_spread_at_signal']:.4f}")
        report.append("")

        # Execution Metrics
        exec_metrics = self.metrics["execution"]
        report.append("EXECUTION METRICS")
        report.append("-" * 40)
        report.append(f"Total Orders: {exec_metrics['total_orders']}")
        report.append(f"Filled Orders: {exec_metrics['filled_orders']}")
        report.append(f"Rejected Orders: {exec_metrics['rejected_orders']}")
        report.append(f"Fill Rate: {exec_metrics['fill_rate'] * 100:.2f}%")
        report.append(
            f"Average Slippage: {exec_metrics['avg_slippage_ticks']:.2f} ticks"
        )
        report.append(f"Positive Slippage: {exec_metrics['positive_slippage_count']}")
        report.append(f"Negative Slippage: {exec_metrics['negative_slippage_count']}")
        report.append(
            f"Avg Latency: {exec_metrics['avg_signal_to_order_latency_us']:.0f} μs"
        )
        report.append("")

        # Risk Metrics
        risk = self.metrics["risk"]
        report.append("RISK METRICS")
        report.append("-" * 40)
        report.append(f"Max Position Size: {risk['max_position_size']}")
        report.append(f"Average Position Size: {risk['avg_position_size']:.1f}")
        report.append(f"Value at Risk (95%): {risk['var_95'] * 100:.2f}%")
        report.append(f"Value at Risk (99%): {risk['var_99'] * 100:.2f}%")
        report.append(f"Conditional VaR (95%): {risk['cvar_95'] * 100:.2f}%")
        report.append(f"Calmar Ratio: {risk['calmar_ratio']:.2f}")
        report.append(f"Time in Market: {risk['time_in_market_pct']:.1f}%")
        report.append(f"Long Exposure: {risk['long_exposure_pct']:.1f}%")
        report.append(f"Short Exposure: {risk['short_exposure_pct']:.1f}%")
        report.append("")

        return "\n".join(report)

    def generate_json_report(self) -> str:
        """Generate JSON-formatted performance report.

        Returns:
            JSON string with all metrics
        """
        return json.dumps(self.metrics, indent=2, default=str)

    def generate_plots(self, output_dir: str | Path) -> list[str]:
        """Generate performance visualization plots.

        Args:
            output_dir: Directory to save plots

        Returns:
            List of generated plot filenames
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        generated_files = []

        # Set style
        if HAS_SEABORN:
            plt.style.use("seaborn-v0_8-darkgrid")
        else:
            plt.style.use("ggplot")

        # 1. Equity Curve
        fig = self._plot_equity_curve()
        filename = output_dir / "equity_curve.png"
        fig.savefig(filename, dpi=300, bbox_inches="tight")
        generated_files.append(str(filename))
        plt.close(fig)

        # 2. Returns Distribution
        fig = self._plot_returns_distribution()
        filename = output_dir / "returns_distribution.png"
        fig.savefig(filename, dpi=300, bbox_inches="tight")
        generated_files.append(str(filename))
        plt.close(fig)

        # 3. Signal Analysis
        fig = self._plot_signal_analysis()
        filename = output_dir / "signal_analysis.png"
        fig.savefig(filename, dpi=300, bbox_inches="tight")
        generated_files.append(str(filename))
        plt.close(fig)

        # 4. Execution Quality
        fig = self._plot_execution_quality()
        filename = output_dir / "execution_quality.png"
        fig.savefig(filename, dpi=300, bbox_inches="tight")
        generated_files.append(str(filename))
        plt.close(fig)

        # 5. Risk Metrics
        fig = self._plot_risk_metrics()
        filename = output_dir / "risk_metrics.png"
        fig.savefig(filename, dpi=300, bbox_inches="tight")
        generated_files.append(str(filename))
        plt.close(fig)

        logger.info(f"Generated {len(generated_files)} performance plots")
        return generated_files

    def _plot_equity_curve(self) -> Figure:
        """Plot equity curve with drawdowns."""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

        # Get equity curve
        equity_df = self.analyzer.get_equity_curve()
        if equity_df.empty:
            return fig

        # Plot equity curve
        ax1.plot(equity_df.index, equity_df["equity"], linewidth=2, label="Equity")
        ax1.fill_between(equity_df.index, equity_df["equity"], alpha=0.3)
        ax1.set_ylabel("Equity ($)")
        ax1.set_title("Equity Curve and Drawdowns")
        ax1.grid(True, alpha=0.3)

        # Calculate and plot drawdowns
        equity_df["cum_max"] = equity_df["equity"].cummax()
        equity_df["drawdown"] = (
            (equity_df["equity"] - equity_df["cum_max"]) / equity_df["cum_max"] * 100
        )

        ax2.fill_between(
            equity_df.index, 0, equity_df["drawdown"], color="red", alpha=0.3
        )
        ax2.plot(equity_df.index, equity_df["drawdown"], color="red", linewidth=1)
        ax2.set_ylabel("Drawdown (%)")
        ax2.set_xlabel("Date")
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()
        return fig

    def _plot_returns_distribution(self) -> Figure:
        """Plot returns distribution and statistics."""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))

        returns = self.metrics["performance"]["daily_returns"]
        if not returns:
            return fig

        # Returns histogram
        ax1.hist(returns, bins=50, alpha=0.7, edgecolor="black")
        ax1.axvline(np.mean(returns), color="red", linestyle="--", label="Mean")
        ax1.set_xlabel("Daily Returns")
        ax1.set_ylabel("Frequency")
        ax1.set_title("Returns Distribution")
        ax1.legend()

        # Q-Q plot
        from scipy import stats

        stats.probplot(returns, dist="norm", plot=ax2)
        ax2.set_title("Q-Q Plot")

        # Cumulative returns
        cum_returns = pd.Series(returns).add(1).cumprod()
        ax3.plot(cum_returns.values)
        ax3.set_xlabel("Days")
        ax3.set_ylabel("Cumulative Return")
        ax3.set_title("Cumulative Returns")
        ax3.grid(True, alpha=0.3)

        # Rolling volatility
        rolling_vol = pd.Series(returns).rolling(20).std() * np.sqrt(252)
        ax4.plot(rolling_vol.values)
        ax4.set_xlabel("Days")
        ax4.set_ylabel("Annualized Volatility")
        ax4.set_title("20-Day Rolling Volatility")
        ax4.grid(True, alpha=0.3)

        plt.tight_layout()
        return fig

    def _plot_signal_analysis(self) -> Figure:
        """Plot signal quality analysis."""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))

        signal_metrics = self.metrics["signal_quality"]

        # Confidence score distribution
        if signal_metrics["confidence_scores"]:
            ax1.hist(
                signal_metrics["confidence_scores"],
                bins=20,
                alpha=0.7,
                edgecolor="black",
            )
            ax1.axvline(
                signal_metrics["avg_confidence_score"],
                color="red",
                linestyle="--",
                label="Average",
            )
            ax1.set_xlabel("Confidence Score (%)")
            ax1.set_ylabel("Frequency")
            ax1.set_title("Signal Confidence Distribution")
            ax1.legend()

        # Imbalance distribution
        if signal_metrics["imbalance_readings"]:
            ax2.hist(
                signal_metrics["imbalance_readings"],
                bins=30,
                alpha=0.7,
                edgecolor="black",
            )
            ax2.set_xlabel("Order Book Imbalance")
            ax2.set_ylabel("Frequency")
            ax2.set_title("Imbalance Distribution at Signals")

        # Volume analysis
        if signal_metrics["volume_readings"]:
            ax3.scatter(
                range(len(signal_metrics["volume_readings"])),
                signal_metrics["volume_readings"],
                alpha=0.5,
            )
            ax3.axhline(
                signal_metrics["avg_volume_at_signal"],
                color="red",
                linestyle="--",
                label="Average",
            )
            ax3.set_xlabel("Signal Number")
            ax3.set_ylabel("Volume")
            ax3.set_title("Volume at Signal Time")
            ax3.legend()

        # Signal quality summary
        labels = ["Total\nSignals", "Acted\nUpon", "High\nConfidence"]
        values = [
            signal_metrics["total_signals"],
            signal_metrics["signals_acted_on"],
            int(
                signal_metrics["total_signals"]
                * signal_metrics["high_confidence_hit_rate"]
            ),
        ]
        ax4.bar(labels, values, alpha=0.7)
        ax4.set_ylabel("Count")
        ax4.set_title("Signal Statistics")

        plt.tight_layout()
        return fig

    def _plot_execution_quality(self) -> Figure:
        """Plot execution quality metrics."""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))

        exec_metrics = self.metrics["execution"]

        # Order outcomes
        labels = ["Filled", "Rejected", "Partial"]
        sizes = [
            exec_metrics["filled_orders"],
            exec_metrics["rejected_orders"],
            exec_metrics["partially_filled_orders"],
        ]
        if sum(sizes) > 0:
            ax1.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=90)
            ax1.set_title("Order Execution Outcomes")

        # Slippage distribution
        if exec_metrics["slippage_readings"]:
            ax2.hist(
                exec_metrics["slippage_readings"],
                bins=20,
                alpha=0.7,
                edgecolor="black",
            )
            ax2.axvline(
                exec_metrics["avg_slippage_ticks"],
                color="red",
                linestyle="--",
                label="Average",
            )
            ax2.set_xlabel("Slippage (ticks)")
            ax2.set_ylabel("Frequency")
            ax2.set_title("Slippage Distribution")
            ax2.legend()

        # Latency analysis
        if exec_metrics["latency_readings"]:
            ax3.plot(exec_metrics["latency_readings"], alpha=0.7)
            ax3.axhline(
                exec_metrics["avg_signal_to_order_latency_us"],
                color="red",
                linestyle="--",
                label="Average",
            )
            ax3.set_xlabel("Order Number")
            ax3.set_ylabel("Latency (μs)")
            ax3.set_title("Signal to Order Latency")
            ax3.legend()

        # Slippage summary
        pos_slip = exec_metrics["positive_slippage_count"]
        neg_slip = exec_metrics["negative_slippage_count"]
        if pos_slip + neg_slip > 0:
            ax4.bar(
                ["Positive", "Negative"],
                [pos_slip, neg_slip],
                color=["green", "red"],
                alpha=0.7,
            )
            ax4.set_ylabel("Count")
            ax4.set_title("Slippage Direction")

        plt.tight_layout()
        return fig

    def _plot_risk_metrics(self) -> Figure:
        """Plot risk analysis metrics."""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))

        risk_metrics = self.metrics["risk"]

        # Position size distribution
        if risk_metrics["position_sizes"]:
            ax1.hist(
                np.abs(risk_metrics["position_sizes"]),
                bins=20,
                alpha=0.7,
                edgecolor="black",
            )
            ax1.axvline(
                risk_metrics["avg_position_size"],
                color="red",
                linestyle="--",
                label="Average",
            )
            ax1.set_xlabel("Position Size")
            ax1.set_ylabel("Frequency")
            ax1.set_title("Position Size Distribution")
            ax1.legend()

        # Exposure breakdown
        labels = ["Long", "Short", "Flat"]
        sizes = [
            risk_metrics["long_exposure_pct"],
            risk_metrics["short_exposure_pct"],
            100 - risk_metrics["time_in_market_pct"],
        ]
        ax2.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=90)
        ax2.set_title("Market Exposure Breakdown")

        # VaR visualization
        returns = self.metrics["performance"]["daily_returns"]
        if returns:
            ax3.hist(returns, bins=50, alpha=0.7, density=True, edgecolor="black")
            ax3.axvline(
                risk_metrics["var_95"],
                color="orange",
                linestyle="--",
                label="VaR 95%",
            )
            ax3.axvline(
                risk_metrics["var_99"], color="red", linestyle="--", label="VaR 99%"
            )
            ax3.set_xlabel("Daily Returns")
            ax3.set_ylabel("Density")
            ax3.set_title("Value at Risk")
            ax3.legend()

        # Risk-adjusted returns
        ratios = {
            "Sharpe": self.metrics["performance"]["sharpe_ratio"],
            "Sortino": self.metrics["performance"]["sortino_ratio"],
            "Calmar": risk_metrics["calmar_ratio"],
        }
        ax4.bar(ratios.keys(), ratios.values(), alpha=0.7)
        ax4.set_ylabel("Ratio")
        ax4.set_title("Risk-Adjusted Return Ratios")
        ax4.axhline(1.0, color="red", linestyle="--", alpha=0.5)

        plt.tight_layout()
        return fig

    def save_report(self, output_dir: str | Path, include_plots: bool = True):
        """Save complete performance report.

        Args:
            output_dir: Directory to save report files
            include_plots: Whether to generate and include plots
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save text report
        text_report = self.generate_text_report()
        report_path = output_dir / "performance_report.txt"
        with report_path.open("w") as f:
            f.write(text_report)

        # Save JSON report
        json_report = self.generate_json_report()
        metrics_path = output_dir / "performance_metrics.json"
        with metrics_path.open("w") as f:
            f.write(json_report)

        # Save plots
        if include_plots:
            self.generate_plots(output_dir / "plots")

        # Save trade log
        trade_log = self.analyzer.get_trade_log()
        if not trade_log.empty:
            trade_log.to_csv(output_dir / "trade_log.csv", index=False)

        logger.info(f"Performance report saved to {output_dir}")
