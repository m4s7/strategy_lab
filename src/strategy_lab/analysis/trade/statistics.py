"""Trade statistics data structures."""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class TradeSummary:
    """Summary statistics for trades."""

    total_trades: int
    winning_trades: int
    losing_trades: int
    breakeven_trades: int
    win_rate: float

    total_pnl: float
    avg_pnl: float
    avg_win: float
    avg_loss: float
    max_win: float
    max_loss: float

    win_loss_ratio: float
    profit_factor: float
    expectancy: float

    avg_holding_time: float
    avg_win_time: float
    avg_loss_time: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "breakeven_trades": self.breakeven_trades,
            "win_rate": self.win_rate,
            "total_pnl": self.total_pnl,
            "avg_pnl": self.avg_pnl,
            "avg_win": self.avg_win,
            "avg_loss": self.avg_loss,
            "max_win": self.max_win,
            "max_loss": self.max_loss,
            "win_loss_ratio": self.win_loss_ratio,
            "profit_factor": self.profit_factor,
            "expectancy": self.expectancy,
            "avg_holding_time": self.avg_holding_time,
            "avg_win_time": self.avg_win_time,
            "avg_loss_time": self.avg_loss_time,
        }


@dataclass
class TradeStatistics:
    """Comprehensive trade analysis statistics."""

    summary: TradeSummary
    pnl_distribution: Dict[str, Any]
    time_analysis: Dict[str, Any]
    streak_analysis: Dict[str, Any]
    entry_exit_analysis: Dict[str, Any]
    sizing_analysis: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "summary": self.summary.to_dict(),
            "pnl_distribution": self.pnl_distribution,
            "time_analysis": self.time_analysis,
            "streak_analysis": self.streak_analysis,
            "entry_exit_analysis": self.entry_exit_analysis,
            "sizing_analysis": self.sizing_analysis,
        }
