"""Performance report generation and management."""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

from ..risk.drawdown import DrawdownAnalysis
from ..risk.metrics import RiskMetrics
from ..trade.statistics import TradeStatistics
from .metrics import PerformanceMetrics

logger = logging.getLogger(__name__)


@dataclass
class PerformanceReport:
    """Comprehensive performance analysis report."""

    metrics: PerformanceMetrics
    risk_metrics: RiskMetrics
    drawdown_analysis: DrawdownAnalysis
    trade_statistics: TradeStatistics
    rolling_metrics: pd.DataFrame
    equity_curve: pd.Series
    trades: pd.DataFrame

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "metrics": self.metrics.to_dict(),
            "risk_metrics": self.risk_metrics.to_dict(),
            "drawdown_analysis": self.drawdown_analysis.get_summary_stats(),
            "trade_statistics": self.trade_statistics.to_dict(),
            "summary": self.get_summary(),
        }

    def get_summary(self) -> Dict[str, Any]:
        """Get executive summary of performance."""
        return {
            "performance": {
                "total_return": f"{self.metrics.total_return:.1%}",
                "annual_return": f"{self.metrics.annualized_return:.1%}",
                "sharpe_ratio": self.metrics.sharpe_ratio,
                "max_drawdown": f"{self.metrics.max_drawdown:.1%}",
                "win_rate": f"{self.metrics.win_rate:.1%}",
            },
            "risk": {
                "volatility": f"{self.risk_metrics.volatility:.1%}",
                "var_95": f"{self.risk_metrics.var_95:.1%}",
                "risk_score": self.risk_metrics.get_risk_score(),
            },
            "trading": {
                "total_trades": self.metrics.total_trades,
                "avg_trade": self.metrics.avg_trade,
                "profit_factor": self.metrics.profit_factor,
            },
        }

    def generate_text_report(self) -> str:
        """Generate formatted text report."""
        lines = []
        lines.append("=" * 80)
        lines.append("PERFORMANCE ANALYSIS REPORT")
        lines.append("=" * 80)
        lines.append(
            f"Period: {self.metrics.start_date.date()} to {self.metrics.end_date.date()}"
        )
        lines.append(f"Trading Days: {self.metrics.trading_days}")
        lines.append("")

        # Performance Section
        lines.append("PERFORMANCE METRICS")
        lines.append("-" * 40)
        lines.append(f"Total Return:        {self.metrics.total_return:>10.1%}")
        lines.append(f"Annualized Return:   {self.metrics.annualized_return:>10.1%}")
        lines.append(f"Sharpe Ratio:        {self.metrics.sharpe_ratio:>10.2f}")
        lines.append(f"Sortino Ratio:       {self.metrics.sortino_ratio:>10.2f}")
        lines.append(f"Calmar Ratio:        {self.metrics.calmar_ratio:>10.2f}")
        lines.append("")

        # Risk Section
        lines.append("RISK METRICS")
        lines.append("-" * 40)
        lines.append(f"Volatility:          {self.risk_metrics.volatility:>10.1%}")
        lines.append(f"Max Drawdown:        {self.metrics.max_drawdown:>10.1%}")
        lines.append(f"VaR (95%):           {self.risk_metrics.var_95:>10.1%}")
        lines.append(f"CVaR (95%):          {self.risk_metrics.cvar_95:>10.1%}")
        lines.append(f"Skewness:            {self.risk_metrics.skewness:>10.2f}")
        lines.append(f"Kurtosis:            {self.risk_metrics.kurtosis:>10.2f}")
        lines.append("")

        # Trading Section
        lines.append("TRADING STATISTICS")
        lines.append("-" * 40)
        lines.append(f"Total Trades:        {self.metrics.total_trades:>10d}")
        lines.append(f"Win Rate:            {self.metrics.win_rate:>10.1%}")
        lines.append(f"Profit Factor:       {self.metrics.profit_factor:>10.2f}")
        lines.append(f"Average Trade:       ${self.metrics.avg_trade:>9.2f}")
        lines.append(f"Average Win:         ${self.metrics.avg_win:>9.2f}")
        lines.append(f"Average Loss:        ${self.metrics.avg_loss:>9.2f}")
        lines.append(f"Win/Loss Ratio:      {self.metrics.win_loss_ratio:>10.2f}")
        lines.append("")

        # Drawdown Section
        lines.append("DRAWDOWN ANALYSIS")
        lines.append("-" * 40)
        dd = self.drawdown_analysis
        lines.append(f"Max Drawdown:        {dd.max_drawdown:>10.1%}")
        lines.append(f"Max Duration:        {dd.max_drawdown_duration:>10d} days")
        lines.append(f"Avg Drawdown:        {dd.avg_drawdown:>10.1%}")
        lines.append(f"Avg Recovery:        {dd.avg_recovery_time:>10d} days")
        lines.append(f"Time Underwater:     {dd.time_underwater_pct:>10.1%}")
        lines.append("")

        # Risk Assessment
        lines.append("RISK ASSESSMENT")
        lines.append("-" * 40)
        risk_score = self.risk_metrics.get_risk_score()
        lines.append(f"Overall Risk Score:  {risk_score:>10.0f}/100")
        lines.append(f"Risk of Ruin:        {self.risk_metrics.risk_of_ruin:>10.1%}")
        lines.append("")

        lines.append("=" * 80)

        return "\n".join(lines)

    def save_to_file(self, filepath: Path, format: str = "json"):
        """Save report to file.

        Args:
            filepath: Output file path
            format: Output format ('json', 'csv', 'html')
        """
        if format == "json":
            with open(filepath, "w") as f:
                json.dump(self.to_dict(), f, indent=2, default=str)

        elif format == "csv":
            # Save key metrics to CSV
            metrics_df = pd.DataFrame([self.metrics.to_dict()])
            metrics_df.to_csv(filepath, index=False)

        elif format == "html":
            # Generate HTML report
            html = self._generate_html_report()
            with open(filepath, "w") as f:
                f.write(html)

        else:
            raise ValueError(f"Unsupported format: {format}")

        logger.info(f"Saved performance report to {filepath}")

    def _generate_html_report(self) -> str:
        """Generate HTML report."""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Performance Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                h1 {{ color: #333; }}
                h2 {{ color: #666; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #4472C4; color: white; }}
                tr:nth-child(even) {{ background-color: #f2f2f2; }}
                .metric {{ font-weight: bold; }}
                .positive {{ color: green; }}
                .negative {{ color: red; }}
            </style>
        </head>
        <body>
            <h1>Performance Analysis Report</h1>
            <p>Period: {self.metrics.start_date.date()} to {self.metrics.end_date.date()}</p>

            <h2>Performance Summary</h2>
            <table>
                <tr>
                    <th>Metric</th>
                    <th>Value</th>
                </tr>
                <tr>
                    <td>Total Return</td>
                    <td class="{'positive' if self.metrics.total_return > 0 else 'negative'}">
                        {self.metrics.total_return:.1%}
                    </td>
                </tr>
                <tr>
                    <td>Annualized Return</td>
                    <td>{self.metrics.annualized_return:.1%}</td>
                </tr>
                <tr>
                    <td>Sharpe Ratio</td>
                    <td>{self.metrics.sharpe_ratio:.2f}</td>
                </tr>
                <tr>
                    <td>Maximum Drawdown</td>
                    <td class="negative">{self.metrics.max_drawdown:.1%}</td>
                </tr>
                <tr>
                    <td>Win Rate</td>
                    <td>{self.metrics.win_rate:.1%}</td>
                </tr>
            </table>

            <h2>Risk Analysis</h2>
            <table>
                <tr>
                    <th>Metric</th>
                    <th>Value</th>
                </tr>
                <tr>
                    <td>Volatility</td>
                    <td>{self.risk_metrics.volatility:.1%}</td>
                </tr>
                <tr>
                    <td>Value at Risk (95%)</td>
                    <td>{self.risk_metrics.var_95:.1%}</td>
                </tr>
                <tr>
                    <td>Risk Score</td>
                    <td>{self.risk_metrics.get_risk_score():.0f}/100</td>
                </tr>
            </table>

            <h2>Trading Statistics</h2>
            <table>
                <tr>
                    <th>Metric</th>
                    <th>Value</th>
                </tr>
                <tr>
                    <td>Total Trades</td>
                    <td>{self.metrics.total_trades}</td>
                </tr>
                <tr>
                    <td>Profit Factor</td>
                    <td>{self.metrics.profit_factor:.2f}</td>
                </tr>
                <tr>
                    <td>Average Trade</td>
                    <td>${self.metrics.avg_trade:.2f}</td>
                </tr>
            </table>

            <p><em>Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</em></p>
        </body>
        </html>
        """

        return html
