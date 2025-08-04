"""Backtest results storage and management."""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from .config import BacktestConfig


@dataclass
class TradeRecord:
    """Individual trade record."""

    symbol: str
    side: str  # "BUY" or "SELL"
    entry_time: pd.Timestamp
    entry_price: float
    exit_time: pd.Timestamp
    exit_price: float
    quantity: int
    pnl: float
    commission: float

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "symbol": self.symbol,
            "side": self.side,
            "entry_time": self.entry_time.isoformat(),
            "entry_price": self.entry_price,
            "exit_time": self.exit_time.isoformat(),
            "exit_price": self.exit_price,
            "quantity": self.quantity,
            "pnl": self.pnl,
            "commission": self.commission,
        }


@dataclass
class BacktestResult:
    """Complete backtest execution results."""

    # Configuration
    config: BacktestConfig

    # Execution metadata
    start_time: datetime
    end_time: datetime
    backtest_id: str = field(
        default_factory=lambda: datetime.now().strftime("%Y%m%d_%H%M%S")
    )

    # Performance metrics
    total_pnl: float = 0.0
    total_return: float = 0.0
    annualized_return: float = 0.0
    excess_return: float = 0.0
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    expectancy: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    largest_win: float = 0.0
    largest_loss: float = 0.0

    # Risk metrics
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    volatility: float = 0.0
    var_95: float = 0.0
    cvar_95: float = 0.0

    # Execution metrics
    total_ticks: int = 0
    execution_time: float = 0.0
    peak_memory_mb: float = 0.0
    avg_cpu_percent: float = 0.0

    # Detailed data
    trades: list[TradeRecord] = field(default_factory=list)
    equity_curve: list[float] = field(default_factory=list)
    timestamps: list[pd.Timestamp] = field(default_factory=list)

    # Additional metrics
    custom_metrics: dict[str, Any] = field(default_factory=dict)

    @property
    def duration(self) -> float:
        """Get backtest duration in seconds."""
        return (self.end_time - self.start_time).total_seconds()

    @property
    def ticks_per_second(self) -> float:
        """Calculate processing speed."""
        if self.execution_time > 0:
            return self.total_ticks / self.execution_time
        return 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "backtest_id": self.backtest_id,
            "config": self.config.to_dict(),
            "metadata": {
                "start_time": self.start_time.isoformat(),
                "end_time": self.end_time.isoformat(),
                "duration": self.duration,
            },
            "performance": {
                "total_pnl": self.total_pnl,
                "total_return": self.total_return,
                "annualized_return": self.annualized_return,
                "excess_return": self.excess_return,
                "total_trades": self.total_trades,
                "winning_trades": self.winning_trades,
                "losing_trades": self.losing_trades,
                "win_rate": self.win_rate,
                "profit_factor": self.profit_factor,
                "expectancy": self.expectancy,
                "avg_win": self.avg_win,
                "avg_loss": self.avg_loss,
                "largest_win": self.largest_win,
                "largest_loss": self.largest_loss,
            },
            "risk": {
                "max_drawdown": self.max_drawdown,
                "sharpe_ratio": self.sharpe_ratio,
                "sortino_ratio": self.sortino_ratio,
                "calmar_ratio": self.calmar_ratio,
                "volatility": self.volatility,
                "var_95": self.var_95,
                "cvar_95": self.cvar_95,
            },
            "execution": {
                "total_ticks": self.total_ticks,
                "execution_time": self.execution_time,
                "ticks_per_second": self.ticks_per_second,
                "peak_memory_mb": self.peak_memory_mb,
                "avg_cpu_percent": self.avg_cpu_percent,
            },
            "custom_metrics": self.custom_metrics,
        }

    def get_summary(self) -> str:
        """Get human-readable summary."""
        return f"""
Backtest Results Summary
========================
Backtest ID: {self.backtest_id}
Strategy: {self.config.strategy.name}
Duration: {self.duration:.2f} seconds

Performance Metrics:
- Total P&L: ${self.total_pnl:,.2f}
- Total Return: {self.total_return:.2%}
- Annualized Return: {self.annualized_return:.2%}
- Total Trades: {self.total_trades}
- Win Rate: {self.win_rate:.2f}%
- Profit Factor: {self.profit_factor:.2f}
- Expectancy: ${self.expectancy:.2f}

Risk Metrics:
- Max Drawdown: {self.max_drawdown:.2%}
- Sharpe Ratio: {self.sharpe_ratio:.3f}
- Sortino Ratio: {self.sortino_ratio:.3f}
- Calmar Ratio: {self.calmar_ratio:.3f}
- Volatility: {self.volatility:.2%}
- VaR (95%): {self.var_95:.2%}

Execution Metrics:
- Total Ticks: {self.total_ticks:,}
- Processing Speed: {self.ticks_per_second:,.0f} ticks/second
- Peak Memory: {self.peak_memory_mb:.2f} MB
- Avg CPU: {self.avg_cpu_percent:.1f}%
"""


def save_results(result: BacktestResult, output_dir: Path | None = None) -> Path:
    """Save backtest results to disk.

    Args:
        result: BacktestResult to save
        output_dir: Output directory (default: from config)

    Returns:
        Path to saved results directory
    """
    if output_dir is None:
        output_dir = result.config.output_dir

    # Create result directory
    result_dir = output_dir / result.backtest_id
    result_dir.mkdir(parents=True, exist_ok=True)

    # Save metadata as JSON
    metadata_path = result_dir / "metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(result.to_dict(), f, indent=2)

    # Save trades as Parquet
    if result.trades and result.config.save_trades:
        trades_df = pd.DataFrame([t.to_dict() for t in result.trades])
        trades_path = result_dir / "trades.parquet"
        trades_df.to_parquet(trades_path)

    # Save equity curve as Parquet
    if result.equity_curve and result.config.save_equity_curve:
        equity_df = pd.DataFrame(
            {"timestamp": result.timestamps, "equity": result.equity_curve}
        )
        equity_path = result_dir / "equity_curve.parquet"
        equity_df.to_parquet(equity_path)

    # Save summary as text
    summary_path = result_dir / "summary.txt"
    with open(summary_path, "w") as f:
        f.write(result.get_summary())

    return result_dir


def load_results(result_dir: Path) -> BacktestResult:
    """Load backtest results from disk.

    Args:
        result_dir: Directory containing saved results

    Returns:
        Loaded BacktestResult
    """
    # Load metadata
    metadata_path = result_dir / "metadata.json"
    with open(metadata_path) as f:
        data = json.load(f)

    # Reconstruct config
    config = BacktestConfig.from_dict(data["config"])

    # Create result object
    result = BacktestResult(
        config=config,
        backtest_id=data["backtest_id"],
        start_time=datetime.fromisoformat(data["metadata"]["start_time"]),
        end_time=datetime.fromisoformat(data["metadata"]["end_time"]),
        # Performance metrics
        total_pnl=data["performance"]["total_pnl"],
        total_return=data["performance"].get("total_return", 0.0),
        annualized_return=data["performance"].get("annualized_return", 0.0),
        excess_return=data["performance"].get("excess_return", 0.0),
        total_trades=data["performance"]["total_trades"],
        winning_trades=data["performance"]["winning_trades"],
        losing_trades=data["performance"]["losing_trades"],
        win_rate=data["performance"]["win_rate"],
        profit_factor=data["performance"]["profit_factor"],
        expectancy=data["performance"].get("expectancy", 0.0),
        avg_win=data["performance"].get("avg_win", 0.0),
        avg_loss=data["performance"].get("avg_loss", 0.0),
        largest_win=data["performance"].get("largest_win", 0.0),
        largest_loss=data["performance"].get("largest_loss", 0.0),
        # Risk metrics
        max_drawdown=data["risk"]["max_drawdown"],
        sharpe_ratio=data["risk"]["sharpe_ratio"],
        sortino_ratio=data["risk"].get("sortino_ratio", 0.0),
        calmar_ratio=data["risk"].get("calmar_ratio", 0.0),
        volatility=data["risk"].get("volatility", 0.0),
        var_95=data["risk"].get("var_95", 0.0),
        cvar_95=data["risk"].get("cvar_95", 0.0),
        # Execution metrics
        total_ticks=data["execution"]["total_ticks"],
        execution_time=data["execution"]["execution_time"],
        peak_memory_mb=data["execution"]["peak_memory_mb"],
        avg_cpu_percent=data["execution"]["avg_cpu_percent"],
        # Custom metrics
        custom_metrics=data.get("custom_metrics", {}),
    )

    # Load trades if available
    trades_path = result_dir / "trades.parquet"
    if trades_path.exists():
        trades_df = pd.read_parquet(trades_path)
        result.trades = [
            TradeRecord(
                symbol=row["symbol"],
                side=row["side"],
                entry_time=pd.Timestamp(row["entry_time"]),
                entry_price=row["entry_price"],
                exit_time=pd.Timestamp(row["exit_time"]),
                exit_price=row["exit_price"],
                quantity=row["quantity"],
                pnl=row["pnl"],
                commission=row["commission"],
            )
            for _, row in trades_df.iterrows()
        ]

    # Load equity curve if available
    equity_path = result_dir / "equity_curve.parquet"
    if equity_path.exists():
        equity_df = pd.read_parquet(equity_path)
        result.equity_curve = equity_df["equity"].tolist()
        result.timestamps = equity_df["timestamp"].tolist()

    return result


def query_results(
    output_dir: Path,
    strategy_name: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    min_sharpe: float | None = None,
) -> list[BacktestResult]:
    """Query saved backtest results.

    Args:
        output_dir: Directory containing results
        strategy_name: Filter by strategy name
        start_date: Filter by start date
        end_date: Filter by end date
        min_sharpe: Minimum Sharpe ratio filter

    Returns:
        List of matching BacktestResult objects
    """
    results = []

    # Iterate through result directories
    for result_dir in output_dir.iterdir():
        if not result_dir.is_dir():
            continue

        try:
            # Load result
            result = load_results(result_dir)

            # Apply filters
            if strategy_name and result.config.strategy.name != strategy_name:
                continue

            if start_date and result.start_time < start_date:
                continue

            if end_date and result.end_time > end_date:
                continue

            if min_sharpe is not None and result.sharpe_ratio < min_sharpe:
                continue

            results.append(result)

        except Exception as e:
            # Skip invalid results
            print(f"Error loading {result_dir}: {e}")
            continue

    # Sort by start time
    results.sort(key=lambda r: r.start_time)

    return results
