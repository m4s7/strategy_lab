"""Main performance analyzer orchestrating all analysis components."""

import logging

import pandas as pd

from ..risk.analyzer import RiskAnalyzer
from ..risk.drawdown import DrawdownCalculator
from ..trade.analyzer import TradeAnalyzer
from .comparison import StrategyComparator
from .metrics import MetricsCalculator, PerformanceMetrics
from .report import PerformanceReport
from .time_series import TimeSeriesAnalyzer

logger = logging.getLogger(__name__)


class PerformanceAnalyzer:
    """Comprehensive performance analysis coordinator."""

    def __init__(self, risk_free_rate: float = 0.02):
        """Initialize performance analyzer.

        Args:
            risk_free_rate: Annual risk-free rate for calculations
        """
        self.metrics_calculator = MetricsCalculator(risk_free_rate)
        self.risk_analyzer = RiskAnalyzer()
        self.trade_analyzer = TradeAnalyzer()
        self.drawdown_calculator = DrawdownCalculator()
        self.time_series_analyzer = TimeSeriesAnalyzer()
        self.comparator = StrategyComparator(risk_free_rate)
        self.risk_free_rate = risk_free_rate

    def analyze(
        self,
        equity_curve: pd.Series,
        trades: pd.DataFrame,
        positions: pd.DataFrame | None = None,
        market_data: pd.DataFrame | None = None,
        benchmark: pd.Series | None = None,
    ) -> PerformanceReport:
        """Perform comprehensive performance analysis.

        Args:
            equity_curve: Time series of portfolio values
            trades: DataFrame with trade information
            positions: Optional positions data
            market_data: Optional market data for context
            benchmark: Optional benchmark returns

        Returns:
            PerformanceReport with all analysis results
        """
        logger.info("Starting comprehensive performance analysis")

        # Calculate performance metrics
        metrics = self.metrics_calculator.calculate_metrics(
            equity_curve, trades, benchmark
        )

        # Risk analysis
        risk_metrics = self.risk_analyzer.analyze_risk(equity_curve, trades, positions)

        # Drawdown analysis
        drawdown_analysis = self.drawdown_calculator.analyze_drawdowns(equity_curve)

        # Trade analysis
        trade_statistics = self.trade_analyzer.analyze_trades(trades, market_data)

        # Time-series analysis
        rolling_metrics = self.metrics_calculator.calculate_rolling_metrics(
            equity_curve
        )

        # Advanced metrics
        returns = equity_curve.pct_change().dropna()
        advanced_metrics = self.metrics_calculator.calculate_advanced_metrics(
            returns, trades, equity_curve
        )

        # Time-based metrics
        time_based_metrics = self.metrics_calculator.calculate_time_based_metrics(
            equity_curve, trades
        )

        # Seasonality analysis
        seasonality = self.time_series_analyzer.analyze_seasonality(returns)

        # Regime detection
        regimes = self.time_series_analyzer.detect_regime_changes(returns)

        # Performance persistence
        persistence = self.time_series_analyzer.calculate_performance_persistence(
            returns
        )

        # Trade clustering
        trade_clustering = self.trade_analyzer.analyze_trade_clustering(trades)

        # Trade patterns
        trade_patterns = self.trade_analyzer.analyze_trade_patterns(trades)

        # Kelly criterion
        kelly_sizing = self.trade_analyzer.calculate_kelly_criterion(trades)

        # Enhanced report with all analysis
        report = PerformanceReport(
            metrics=metrics,
            risk_metrics=risk_metrics,
            drawdown_analysis=drawdown_analysis,
            trade_statistics=trade_statistics,
            rolling_metrics=rolling_metrics,
            equity_curve=equity_curve,
            trades=trades,
        )

        # Add additional analysis to report
        report.advanced_metrics = advanced_metrics
        report.time_based_metrics = time_based_metrics
        report.seasonality = seasonality
        report.market_regimes = regimes
        report.persistence = persistence
        report.trade_clustering = trade_clustering
        report.trade_patterns = trade_patterns
        report.kelly_sizing = kelly_sizing

        logger.info("Performance analysis completed")

        return report

    def compare_strategies(
        self,
        strategies: dict[str, dict[str, pd.DataFrame]],
        benchmark: pd.Series | None = None,
    ) -> dict[str, PerformanceReport]:
        """Compare multiple strategies.

        Args:
            strategies: Dict mapping strategy names to their data
                      Each should have 'equity_curve' and 'trades'
            benchmark: Optional benchmark for comparison

        Returns:
            Dictionary mapping strategy names to performance reports
        """
        reports = {}

        for name, data in strategies.items():
            logger.info(f"Analyzing strategy: {name}")

            report = self.analyze(
                equity_curve=data["equity_curve"],
                trades=data["trades"],
                positions=data.get("positions"),
                market_data=data.get("market_data"),
                benchmark=benchmark,
            )

            reports[name] = report

        return reports

    def analyze_parameter_sensitivity(
        self, parameter_results: dict[tuple[float, ...], dict[str, pd.DataFrame]]
    ) -> pd.DataFrame:
        """Analyze performance sensitivity to parameters.

        Args:
            parameter_results: Dict mapping parameter tuples to results

        Returns:
            DataFrame with parameter sensitivity analysis
        """
        sensitivity_data = []

        for params, data in parameter_results.items():
            # Calculate key metrics
            metrics = self.metrics_calculator.calculate_metrics(
                data["equity_curve"], data["trades"]
            )

            row = {
                "parameters": params,
                "total_return": metrics.total_return,
                "sharpe_ratio": metrics.sharpe_ratio,
                "max_drawdown": metrics.max_drawdown,
                "win_rate": metrics.win_rate,
                "profit_factor": metrics.profit_factor,
            }

            # Add individual parameter values
            if isinstance(params, dict):
                for k, v in params.items():
                    row[f"param_{k}"] = v

            sensitivity_data.append(row)

        return pd.DataFrame(sensitivity_data)

    def generate_executive_summary(self, report: PerformanceReport) -> dict:
        """Generate executive summary from performance report.

        Args:
            report: Performance report

        Returns:
            Dictionary with executive summary
        """
        metrics = report.metrics

        summary = {
            "overview": {
                "total_return": f"{metrics.total_return:.1%}",
                "annualized_return": f"{metrics.annualized_return:.1%}",
                "sharpe_ratio": f"{metrics.sharpe_ratio:.2f}",
                "max_drawdown": f"{metrics.max_drawdown:.1%}",
                "trading_days": metrics.trading_days,
            },
            "risk_profile": {
                "volatility": f"{metrics.volatility:.1%}",
                "var_95": f"{metrics.var_95:.1%}",
                "downside_deviation": f"{metrics.downside_deviation:.1%}",
                "risk_rating": self._get_risk_rating(metrics),
            },
            "trading_performance": {
                "total_trades": metrics.total_trades,
                "win_rate": f"{metrics.win_rate:.1%}",
                "profit_factor": f"{metrics.profit_factor:.2f}",
                "avg_trade": f"${metrics.avg_trade:.2f}",
            },
            "strengths": self._identify_strengths(report),
            "weaknesses": self._identify_weaknesses(report),
            "recommendations": self._generate_recommendations(report),
        }

        return summary

    def _get_risk_rating(self, metrics: PerformanceMetrics) -> str:
        """Determine risk rating based on metrics."""
        if metrics.volatility < 0.10:
            return "Low"
        if metrics.volatility < 0.20:
            return "Medium"
        return "High"

    def _identify_strengths(self, report: PerformanceReport) -> list[str]:
        """Identify strategy strengths."""
        strengths = []
        metrics = report.metrics

        if metrics.sharpe_ratio > 1.5:
            strengths.append("Excellent risk-adjusted returns")

        if metrics.win_rate > 0.6:
            strengths.append("High win rate")

        if metrics.profit_factor > 2.0:
            strengths.append("Strong profit factor")

        if metrics.recovery_factor > 5.0:
            strengths.append("Excellent recovery from drawdowns")

        if metrics.profit_consistency > 0.7:
            strengths.append("Consistent monthly profits")

        return strengths

    def _identify_weaknesses(self, report: PerformanceReport) -> list[str]:
        """Identify strategy weaknesses."""
        weaknesses = []
        metrics = report.metrics

        if metrics.max_drawdown > 0.20:
            weaknesses.append("High maximum drawdown")

        if metrics.sharpe_ratio < 0.5:
            weaknesses.append("Poor risk-adjusted returns")

        if metrics.win_rate < 0.4:
            weaknesses.append("Low win rate")

        if metrics.skewness < -1.0:
            weaknesses.append("Negative skew (tail risk)")

        if metrics.avg_holding_time > 1440:  # More than 1 day
            weaknesses.append("Long holding periods")

        return weaknesses

    def _generate_recommendations(self, report: PerformanceReport) -> list[str]:
        """Generate improvement recommendations."""
        recommendations = []
        metrics = report.metrics

        if metrics.max_drawdown > 0.15:
            recommendations.append(
                "Consider implementing tighter risk controls to reduce drawdowns"
            )

        if metrics.win_rate < 0.5 and metrics.win_loss_ratio < 1.5:
            recommendations.append("Improve entry timing or increase profit targets")

        if metrics.trade_frequency < 0.1:
            recommendations.append(
                "Strategy may benefit from more trading opportunities"
            )

        if report.trade_statistics.streak_analysis.get("max_loss_streak", 0) > 10:
            recommendations.append(
                "Implement streak-based position sizing or circuit breakers"
            )

        return recommendations
