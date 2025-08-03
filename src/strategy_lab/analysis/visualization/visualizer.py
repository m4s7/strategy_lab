"""Performance visualization implementation."""

import logging

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.figure import Figure
from matplotlib.gridspec import GridSpec

# Make seaborn optional
try:
    import seaborn as sns

    SEABORN_AVAILABLE = True
except ImportError:
    SEABORN_AVAILABLE = False

from ..performance.report import PerformanceReport
from ..risk.drawdown import DrawdownAnalysis
from .config import PlotConfig

logger = logging.getLogger(__name__)


class PerformanceVisualizer:
    """Creates visualizations for performance analysis."""

    def __init__(self, config: PlotConfig | None = None):
        """Initialize visualizer.

        Args:
            config: Plot configuration
        """
        self.config = config or PlotConfig()

        # Set style
        try:
            plt.style.use(self.config.style)
        except:
            try:
                plt.style.use("seaborn-v0_8-darkgrid")
            except:
                plt.style.use("default")

    def create_performance_dashboard(
        self, report: PerformanceReport, title: str = "Strategy Performance Dashboard"
    ) -> Figure:
        """Create comprehensive performance dashboard.

        Args:
            report: Performance report
            title: Dashboard title

        Returns:
            Matplotlib figure
        """
        # Create figure with subplots
        fig = plt.figure(figsize=(16, 12))
        gs = GridSpec(3, 3, figure=fig, hspace=0.3, wspace=0.3)

        # 1. Equity curve with drawdown
        ax1 = fig.add_subplot(gs[0, :2])
        self._plot_equity_curve(ax1, report.equity_curve, report.drawdown_analysis)

        # 2. Monthly returns heatmap
        ax2 = fig.add_subplot(gs[0, 2])
        self._plot_monthly_returns(ax2, report.equity_curve)

        # 3. Trade distribution
        ax3 = fig.add_subplot(gs[1, 0])
        self._plot_trade_distribution(ax3, report.trades)

        # 4. Rolling metrics
        ax4 = fig.add_subplot(gs[1, 1:])
        self._plot_rolling_metrics(ax4, report.rolling_metrics)

        # 5. Risk metrics
        ax5 = fig.add_subplot(gs[2, 0])
        self._plot_risk_metrics(ax5, report.metrics)

        # 6. Performance statistics table
        ax6 = fig.add_subplot(gs[2, 1:])
        self._plot_performance_table(ax6, report.metrics)

        fig.suptitle(title, fontsize=self.config.title_size, y=0.98)

        return fig

    def plot_equity_curve(
        self,
        equity_curve: pd.Series,
        drawdown: pd.Series | None = None,
        benchmark: pd.Series | None = None,
    ) -> Figure:
        """Plot equity curve with optional drawdown.

        Args:
            equity_curve: Portfolio value series
            drawdown: Optional drawdown series
            benchmark: Optional benchmark series

        Returns:
            Matplotlib figure
        """
        fig, axes = plt.subplots(
            2 if drawdown is not None else 1,
            1,
            figsize=self.config.figure_size,
            sharex=True,
        )

        if drawdown is not None:
            ax_equity = axes[0]
            ax_dd = axes[1]
        else:
            ax_equity = axes
            ax_dd = None

        # Plot equity curve
        ax_equity.plot(
            equity_curve.index,
            equity_curve.values,
            color=self.config.primary_color,
            linewidth=2,
            label="Strategy",
        )

        # Plot benchmark if provided
        if benchmark is not None:
            ax_equity.plot(
                benchmark.index,
                benchmark.values,
                color=self.config.secondary_color,
                linewidth=1.5,
                alpha=0.7,
                label="Benchmark",
            )

        ax_equity.set_ylabel("Portfolio Value", fontsize=self.config.label_size)
        ax_equity.set_title("Equity Curve", fontsize=self.config.title_size)
        ax_equity.legend()
        ax_equity.grid(True, alpha=self.config.grid_alpha)

        # Plot drawdown if provided
        if ax_dd is not None and drawdown is not None:
            ax_dd.fill_between(
                drawdown.index,
                0,
                drawdown.values * 100,
                color=self.config.negative_color,
                alpha=0.3,
            )
            ax_dd.plot(
                drawdown.index,
                drawdown.values * 100,
                color=self.config.negative_color,
                linewidth=1,
            )
            ax_dd.set_ylabel("Drawdown (%)", fontsize=self.config.label_size)
            ax_dd.set_xlabel("Date", fontsize=self.config.label_size)
            ax_dd.grid(True, alpha=self.config.grid_alpha)

        plt.tight_layout()

        return fig

    def plot_trade_analysis(self, trades: pd.DataFrame) -> Figure:
        """Create trade analysis visualizations.

        Args:
            trades: Trade data

        Returns:
            Matplotlib figure
        """
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))

        # 1. PnL distribution
        ax1 = axes[0, 0]
        self._plot_trade_distribution(ax1, trades)

        # 2. Trade outcomes over time
        ax2 = axes[0, 1]
        self._plot_trade_outcomes(ax2, trades)

        # 3. Holding time analysis
        ax3 = axes[1, 0]
        self._plot_holding_times(ax3, trades)

        # 4. Win/loss streaks
        ax4 = axes[1, 1]
        self._plot_win_loss_streaks(ax4, trades)

        fig.suptitle("Trade Analysis", fontsize=self.config.title_size)
        plt.tight_layout()

        return fig

    def plot_risk_analysis(self, report: PerformanceReport) -> Figure:
        """Create risk analysis visualizations.

        Args:
            report: Performance report

        Returns:
            Matplotlib figure
        """
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))

        # 1. Return distribution
        ax1 = axes[0, 0]
        self._plot_return_distribution(ax1, report.equity_curve)

        # 2. Risk metrics radar
        ax2 = axes[0, 1]
        self._plot_risk_radar(ax2, report.risk_metrics)

        # 3. Drawdown periods
        ax3 = axes[1, 0]
        self._plot_drawdown_periods(ax3, report.drawdown_analysis)

        # 4. Rolling volatility
        ax4 = axes[1, 1]
        self._plot_rolling_volatility(ax4, report.equity_curve)

        fig.suptitle("Risk Analysis", fontsize=self.config.title_size)
        plt.tight_layout()

        return fig

    def _plot_equity_curve(
        self, ax: plt.Axes, equity_curve: pd.Series, drawdown_analysis: DrawdownAnalysis
    ):
        """Plot equity curve with drawdown shading."""
        # Plot equity curve
        ax.plot(
            equity_curve.index,
            equity_curve.values,
            color=self.config.primary_color,
            linewidth=2,
        )

        # Shade drawdown periods
        for period in drawdown_analysis.drawdown_periods:
            if not period.is_active:
                ax.axvspan(
                    period.start_date,
                    period.end_date,
                    alpha=0.2,
                    color=self.config.negative_color,
                )

        ax.set_title("Equity Curve", fontsize=self.config.label_size)
        ax.set_ylabel("Portfolio Value")
        ax.grid(True, alpha=self.config.grid_alpha)

        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)

    def _plot_monthly_returns(self, ax: plt.Axes, equity_curve: pd.Series):
        """Plot monthly returns heatmap."""
        # Calculate monthly returns
        monthly_returns = equity_curve.resample("M").last().pct_change()

        # Create matrix for heatmap
        returns_matrix = []
        years = []

        for year in monthly_returns.index.year.unique():
            year_data = monthly_returns[monthly_returns.index.year == year]
            monthly_values = []

            for month in range(1, 13):
                month_data = year_data[year_data.index.month == month]
                if len(month_data) > 0:
                    monthly_values.append(month_data.iloc[0] * 100)
                else:
                    monthly_values.append(np.nan)

            returns_matrix.append(monthly_values)
            years.append(year)

        # Plot heatmap
        if SEABORN_AVAILABLE:
            sns.heatmap(
                returns_matrix,
                ax=ax,
                cmap="RdYlGn",
                center=0,
                annot=True,
                fmt=".1f",
                cbar_kws={"label": "Return (%)"},
                xticklabels=[
                    "J",
                    "F",
                    "M",
                    "A",
                    "M",
                    "J",
                    "J",
                    "A",
                    "S",
                    "O",
                    "N",
                    "D",
                ],
                yticklabels=years,
            )
        else:
            # Fallback without seaborn
            im = ax.imshow(returns_matrix, cmap="RdYlGn", aspect="auto")
            ax.set_xticks(range(12))
            ax.set_xticklabels(
                ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"]
            )
            ax.set_yticks(range(len(years)))
            ax.set_yticklabels(years)
            plt.colorbar(im, ax=ax, label="Return (%)")

        ax.set_title("Monthly Returns (%)", fontsize=self.config.label_size)
        ax.set_xlabel("")
        ax.set_ylabel("Year")

    def _plot_trade_distribution(self, ax: plt.Axes, trades: pd.DataFrame):
        """Plot trade PnL distribution."""
        if "pnl" not in trades.columns:
            return

        wins = trades[trades["pnl"] > 0]["pnl"]
        losses = trades[trades["pnl"] < 0]["pnl"]

        # Plot histogram
        ax.hist(
            wins,
            bins=30,
            alpha=0.6,
            color=self.config.positive_color,
            label=f"Wins (n={len(wins)})",
        )
        ax.hist(
            losses,
            bins=30,
            alpha=0.6,
            color=self.config.negative_color,
            label=f"Losses (n={len(losses)})",
        )

        ax.axvline(x=0, color="black", linestyle="--", alpha=0.5)
        ax.set_xlabel("Trade P&L")
        ax.set_ylabel("Frequency")
        ax.set_title("Trade Distribution", fontsize=self.config.label_size)
        ax.legend()
        ax.grid(True, alpha=self.config.grid_alpha)

    def _plot_rolling_metrics(self, ax: plt.Axes, rolling_metrics: pd.DataFrame):
        """Plot rolling performance metrics."""
        if rolling_metrics.empty:
            return

        # Create twin axis for Sharpe ratio
        ax2 = ax.twinx()

        # Plot rolling return
        ax.plot(
            rolling_metrics.index,
            rolling_metrics["return"] * 100,
            color=self.config.primary_color,
            label="Rolling Return",
            linewidth=2,
        )

        # Plot rolling Sharpe
        ax2.plot(
            rolling_metrics.index,
            rolling_metrics["sharpe_ratio"],
            color=self.config.secondary_color,
            label="Rolling Sharpe",
            linewidth=2,
            linestyle="--",
        )

        ax.set_ylabel("Return (%)", color=self.config.primary_color)
        ax2.set_ylabel("Sharpe Ratio", color=self.config.secondary_color)
        ax.set_title("Rolling Performance (252-day)", fontsize=self.config.label_size)
        ax.grid(True, alpha=self.config.grid_alpha)

        # Combine legends
        lines1, labels1 = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax.legend(lines1 + lines2, labels1 + labels2, loc="upper left")

    def _plot_risk_metrics(self, ax: plt.Axes, metrics):
        """Plot risk metrics as bar chart."""
        risk_data = {
            "Volatility": metrics.volatility * 100,
            "Max DD": metrics.max_drawdown * 100,
            "VaR 95%": abs(metrics.var_95) * 100,
            "Skewness": metrics.skewness,
            "Kurtosis": metrics.kurtosis,
        }

        colors = [
            self.config.negative_color if v < 0 else self.config.positive_color
            for v in risk_data.values()
        ]

        bars = ax.bar(risk_data.keys(), risk_data.values(), color=colors, alpha=0.7)

        # Add value labels
        for bar in bars:
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                height,
                f"{height:.1f}",
                ha="center",
                va="bottom" if height >= 0 else "top",
            )

        ax.set_title("Risk Metrics", fontsize=self.config.label_size)
        ax.set_ylabel("Value")
        ax.grid(True, alpha=self.config.grid_alpha, axis="y")
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)

    def _plot_performance_table(self, ax: plt.Axes, metrics):
        """Plot performance statistics table."""
        # Hide axes
        ax.axis("off")

        # Create table data
        table_data = [
            ["Metric", "Value"],
            ["Total Return", f"{metrics.total_return:.1%}"],
            ["Annual Return", f"{metrics.annualized_return:.1%}"],
            ["Sharpe Ratio", f"{metrics.sharpe_ratio:.2f}"],
            ["Sortino Ratio", f"{metrics.sortino_ratio:.2f}"],
            ["Win Rate", f"{metrics.win_rate:.1%}"],
            ["Profit Factor", f"{metrics.profit_factor:.2f}"],
            ["Avg Trade", f"{metrics.avg_trade:.2f}"],
            ["Total Trades", f"{metrics.total_trades}"],
            ["Recovery Factor", f"{metrics.recovery_factor:.2f}"],
        ]

        # Create table
        table = ax.table(
            cellText=table_data[1:],
            colLabels=table_data[0],
            cellLoc="left",
            loc="center",
            colWidths=[0.6, 0.4],
        )

        # Style table
        table.auto_set_font_size(False)
        table.set_fontsize(self.config.tick_size)
        table.scale(1, 2)

        # Color header
        for i in range(2):
            table[(0, i)].set_facecolor("#4472C4")
            table[(0, i)].set_text_props(weight="bold", color="white")

        ax.set_title("Performance Summary", fontsize=self.config.label_size, pad=20)

    def _plot_trade_outcomes(self, ax: plt.Axes, trades: pd.DataFrame):
        """Plot trade outcomes over time."""
        if "entry_time" not in trades.columns or "pnl" not in trades.columns:
            return

        trades_sorted = trades.sort_values("entry_time")

        # Color by win/loss
        colors = [
            self.config.positive_color if pnl > 0 else self.config.negative_color
            for pnl in trades_sorted["pnl"]
        ]

        ax.scatter(
            trades_sorted["entry_time"], trades_sorted["pnl"], c=colors, alpha=0.6, s=50
        )

        ax.axhline(y=0, color="black", linestyle="--", alpha=0.5)
        ax.set_xlabel("Trade Date")
        ax.set_ylabel("Trade P&L")
        ax.set_title("Trade Outcomes Over Time")
        ax.grid(True, alpha=self.config.grid_alpha)

    def _plot_return_distribution(self, ax: plt.Axes, equity_curve: pd.Series):
        """Plot return distribution with normal overlay."""
        returns = equity_curve.pct_change().dropna()

        # Plot histogram
        n, bins, patches = ax.hist(
            returns * 100,
            bins=50,
            density=True,
            alpha=0.7,
            color=self.config.primary_color,
        )

        # Fit normal distribution
        mu, sigma = returns.mean() * 100, returns.std() * 100
        x = np.linspace(returns.min() * 100, returns.max() * 100, 100)
        normal_dist = (1 / (np.sqrt(2 * np.pi) * sigma)) * np.exp(
            -0.5 * ((x - mu) / sigma) ** 2
        )

        ax.plot(x, normal_dist, "r-", linewidth=2, label="Normal")

        ax.set_xlabel("Daily Return (%)")
        ax.set_ylabel("Density")
        ax.set_title("Return Distribution")
        ax.legend()
        ax.grid(True, alpha=self.config.grid_alpha)

    def save_figure(self, fig: Figure, filename: str):
        """Save figure to file.

        Args:
            fig: Matplotlib figure
            filename: Output filename
        """
        if self.config.save_path:
            filepath = f"{self.config.save_path}/{filename}.{self.config.save_format}"
        else:
            filepath = f"{filename}.{self.config.save_format}"

        fig.savefig(
            filepath, dpi=self.config.dpi, bbox_inches="tight", facecolor="white"
        )

        logger.info(f"Saved figure to {filepath}")

    def _plot_holding_times(self, ax: plt.Axes, trades: pd.DataFrame):
        """Plot holding time distribution."""
        if "holding_time" not in trades.columns:
            return

        holding_times = trades["holding_time"]

        # Convert to appropriate units (e.g., minutes to hours)
        holding_hours = holding_times / 60

        ax.hist(holding_hours, bins=30, alpha=0.7, color=self.config.primary_color)
        ax.axvline(
            holding_hours.mean(),
            color="red",
            linestyle="--",
            label=f"Mean: {holding_hours.mean():.1f}h",
        )

        ax.set_xlabel("Holding Time (hours)")
        ax.set_ylabel("Frequency")
        ax.set_title("Holding Time Distribution")
        ax.legend()
        ax.grid(True, alpha=self.config.grid_alpha)

    def _plot_win_loss_streaks(self, ax: plt.Axes, trades: pd.DataFrame):
        """Plot win/loss streak visualization."""
        if "pnl" not in trades.columns:
            return

        # Calculate cumulative win/loss streaks
        is_win = (trades["pnl"] > 0).astype(int)
        streak_changes = is_win.diff().fillna(is_win.iloc[0])
        streak_groups = streak_changes.ne(0).cumsum()

        streaks = []
        for group, data in is_win.groupby(streak_groups):
            streak_type = data.iloc[0]
            streak_length = len(data)
            streaks.append((streak_type, streak_length))

        # Plot streaks
        x_pos = 0
        for streak_type, length in streaks:
            color = (
                self.config.positive_color
                if streak_type
                else self.config.negative_color
            )
            ax.barh(0, length, left=x_pos, height=0.5, color=color, alpha=0.7)
            x_pos += length

        ax.set_ylim(-0.5, 0.5)
        ax.set_xlabel("Trade Number")
        ax.set_title("Win/Loss Streaks")
        ax.set_yticks([])

        # Add legend
        win_patch = plt.Rectangle(
            (0, 0), 1, 1, fc=self.config.positive_color, alpha=0.7
        )
        loss_patch = plt.Rectangle(
            (0, 0), 1, 1, fc=self.config.negative_color, alpha=0.7
        )
        ax.legend([win_patch, loss_patch], ["Winning Streak", "Losing Streak"])

    def _plot_risk_radar(self, ax: plt.Axes, risk_metrics):
        """Plot risk metrics radar chart."""
        # Define metrics to include
        categories = ["Volatility", "Drawdown", "VaR", "Skewness", "Tail Risk"]

        # Normalize metrics to 0-1 scale
        values = [
            min(risk_metrics.volatility / 0.3, 1),  # Cap at 30% vol
            min(abs(risk_metrics.max_drawdown_duration) / 180, 1),  # Cap at 180 days
            min(abs(risk_metrics.var_95) / 0.05, 1),  # Cap at 5% VaR
            min(abs(risk_metrics.skewness) / 2, 1),  # Cap at |2| skewness
            1 / risk_metrics.tail_ratio if risk_metrics.tail_ratio > 0 else 1,
        ]

        # Number of variables
        num_vars = len(categories)

        # Compute angle for each axis
        angles = [n / float(num_vars) * 2 * np.pi for n in range(num_vars)]
        values += values[:1]
        angles += angles[:1]

        # Plot
        ax.plot(angles, values, "o-", linewidth=2, color=self.config.primary_color)
        ax.fill(angles, values, alpha=0.25, color=self.config.primary_color)

        # Set labels
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories)
        ax.set_ylim(0, 1)
        ax.set_title("Risk Profile")
        ax.grid(True)

    def _plot_drawdown_periods(self, ax: plt.Axes, drawdown_analysis: DrawdownAnalysis):
        """Plot drawdown periods analysis."""
        if not drawdown_analysis.drawdown_periods:
            return

        # Extract drawdown magnitudes and durations
        magnitudes = [
            abs(p.drawdown_pct) * 100 for p in drawdown_analysis.drawdown_periods
        ]
        durations = [p.duration_days for p in drawdown_analysis.drawdown_periods]

        # Create scatter plot
        scatter = ax.scatter(
            durations, magnitudes, s=100, alpha=0.6, c=magnitudes, cmap="Reds"
        )

        # Highlight worst drawdown
        worst_idx = np.argmax(magnitudes)
        ax.scatter(
            durations[worst_idx],
            magnitudes[worst_idx],
            s=200,
            color="red",
            marker="*",
            label=f"Worst: {magnitudes[worst_idx]:.1f}%",
        )

        ax.set_xlabel("Duration (days)")
        ax.set_ylabel("Drawdown (%)")
        ax.set_title("Drawdown Periods")
        ax.legend()
        ax.grid(True, alpha=self.config.grid_alpha)

        # Add colorbar
        plt.colorbar(scatter, ax=ax, label="Magnitude (%)")

    def _plot_rolling_volatility(self, ax: plt.Axes, equity_curve: pd.Series):
        """Plot rolling volatility."""
        returns = equity_curve.pct_change().dropna()

        # Calculate rolling volatilities
        vol_30 = returns.rolling(30).std() * np.sqrt(252) * 100
        vol_60 = returns.rolling(60).std() * np.sqrt(252) * 100
        vol_120 = returns.rolling(120).std() * np.sqrt(252) * 100

        ax.plot(vol_30.index, vol_30, label="30-day", alpha=0.8)
        ax.plot(vol_60.index, vol_60, label="60-day", alpha=0.8)
        ax.plot(vol_120.index, vol_120, label="120-day", alpha=0.8)

        ax.set_ylabel("Volatility (%)")
        ax.set_title("Rolling Volatility")
        ax.legend()
        ax.grid(True, alpha=self.config.grid_alpha)

        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)

    def plot_strategy_comparison(
        self, strategies: dict[str, pd.Series], normalize: bool = True
    ) -> Figure:
        """Plot multiple strategy equity curves for comparison.

        Args:
            strategies: Dict mapping strategy names to equity curves
            normalize: Whether to normalize curves to start at 1

        Returns:
            Matplotlib figure
        """
        fig, ax = plt.subplots(figsize=self.config.figure_size)

        for name, equity_curve in strategies.items():
            if normalize:
                normalized = equity_curve / equity_curve.iloc[0]
                ax.plot(
                    normalized.index,
                    normalized.values,
                    label=name,
                    linewidth=2,
                    alpha=0.8,
                )
            else:
                ax.plot(
                    equity_curve.index,
                    equity_curve.values,
                    label=name,
                    linewidth=2,
                    alpha=0.8,
                )

        ax.set_ylabel("Portfolio Value" + (" (Normalized)" if normalize else ""))
        ax.set_title("Strategy Comparison")
        ax.legend(loc="best")
        ax.grid(True, alpha=self.config.grid_alpha)

        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)

        plt.tight_layout()
        return fig

    def plot_correlation_heatmap(self, correlation_matrix: pd.DataFrame) -> Figure:
        """Plot correlation heatmap between strategies.

        Args:
            correlation_matrix: Correlation matrix DataFrame

        Returns:
            Matplotlib figure
        """
        fig, ax = plt.subplots(figsize=(10, 8))

        if SEABORN_AVAILABLE:
            sns.heatmap(
                correlation_matrix,
                annot=True,
                fmt=".2f",
                cmap="coolwarm",
                center=0,
                square=True,
                linewidths=1,
                cbar_kws={"shrink": 0.8},
                ax=ax,
            )
        else:
            im = ax.imshow(correlation_matrix, cmap="coolwarm", aspect="auto")

            # Add text annotations
            for i in range(len(correlation_matrix)):
                for j in range(len(correlation_matrix)):
                    text = ax.text(
                        j,
                        i,
                        f"{correlation_matrix.iloc[i, j]:.2f}",
                        ha="center",
                        va="center",
                        color="black",
                    )

            # Set ticks
            ax.set_xticks(np.arange(len(correlation_matrix.columns)))
            ax.set_yticks(np.arange(len(correlation_matrix.index)))
            ax.set_xticklabels(correlation_matrix.columns)
            ax.set_yticklabels(correlation_matrix.index)

            plt.colorbar(im, ax=ax, shrink=0.8)

        ax.set_title("Strategy Correlation Matrix")
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha="right")

        plt.tight_layout()
        return fig
