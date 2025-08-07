from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
import random
import math

from ..core.dependencies import get_db

router = APIRouter(prefix="/results", tags=["results"])


class EquityPoint(BaseModel):
    timestamp: str
    equity: float
    drawdown_pct: float = 0.0
    trade_pnl: float = 0.0


class TradeSummary(BaseModel):
    total_trades: int
    winning_trades: int
    losing_trades: int
    largest_win: float
    largest_loss: float
    average_win: float
    average_loss: float
    average_trade: float
    win_rate: float
    profit_factor: float
    consecutive_wins: int
    consecutive_losses: int
    avg_trade_duration_minutes: int


class PerformanceMetrics(BaseModel):
    total_return: float
    total_return_pct: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    max_drawdown: float
    max_drawdown_pct: float
    volatility: float
    var_95: float  # Value at Risk
    cvar_95: float  # Conditional VaR
    beta: Optional[float] = None
    alpha: Optional[float] = None
    information_ratio: Optional[float] = None


class PerformanceStatistics(BaseModel):
    returns: Dict[str, float]
    risk_metrics: Dict[str, float]
    trade_metrics: Dict[str, float]
    time_metrics: Dict[str, float]


class BacktestResult(BaseModel):
    id: str
    backtest_id: str
    start_date: str
    end_date: str
    strategy_name: str
    initial_capital: float
    final_capital: float
    configuration: Dict[str, Any]
    metrics: PerformanceMetrics
    equity_curve: List[EquityPoint]
    trade_summary: TradeSummary
    statistics: PerformanceStatistics
    created_at: str
    execution_time_seconds: float


# Mock results storage
MOCK_RESULTS: Dict[str, BacktestResult] = {}


def generate_mock_equity_curve(
    start_date: str, end_date: str, initial_capital: float
) -> List[EquityPoint]:
    """Generate realistic mock equity curve data."""
    curve = []
    current_equity = initial_capital
    max_equity = initial_capital

    start = datetime.fromisoformat(start_date)
    end = datetime.fromisoformat(end_date)
    days = (end - start).days

    # Generate daily points
    for i in range(days + 1):
        current_date = start + timedelta(days=i)

        # Random walk with slight upward bias
        daily_return = random.gauss(0.0005, 0.02)  # 0.05% mean, 2% std
        trade_pnl = current_equity * daily_return
        current_equity += trade_pnl
        max_equity = max(max_equity, current_equity)

        drawdown_pct = (
            (max_equity - current_equity) / max_equity * 100 if max_equity > 0 else 0
        )

        curve.append(
            EquityPoint(
                timestamp=current_date.isoformat(),
                equity=current_equity,
                drawdown_pct=drawdown_pct,
                trade_pnl=trade_pnl,
            )
        )

    return curve


def calculate_mock_metrics(
    equity_curve: List[EquityPoint], initial_capital: float
) -> PerformanceMetrics:
    """Calculate performance metrics from equity curve."""
    if not equity_curve:
        return PerformanceMetrics(
            total_return=0,
            total_return_pct=0,
            sharpe_ratio=0,
            sortino_ratio=0,
            calmar_ratio=0,
            max_drawdown=0,
            max_drawdown_pct=0,
            volatility=0,
            var_95=0,
            cvar_95=0,
        )

    final_equity = equity_curve[-1].equity
    total_return = final_equity - initial_capital
    total_return_pct = (total_return / initial_capital) * 100

    # Calculate daily returns
    daily_returns = []
    for i in range(1, len(equity_curve)):
        prev_equity = equity_curve[i - 1].equity
        curr_equity = equity_curve[i].equity
        if prev_equity > 0:
            daily_returns.append((curr_equity - prev_equity) / prev_equity)

    # Calculate metrics
    if daily_returns:
        mean_return = sum(daily_returns) / len(daily_returns)
        volatility = math.sqrt(
            sum((r - mean_return) ** 2 for r in daily_returns) / len(daily_returns)
        )
        sharpe_ratio = (
            (mean_return * 252) / (volatility * math.sqrt(252)) if volatility > 0 else 0
        )

        # Sortino ratio (downside deviation)
        downside_returns = [r for r in daily_returns if r < 0]
        downside_dev = (
            math.sqrt(sum(r**2 for r in downside_returns) / len(downside_returns))
            if downside_returns
            else 0
        )
        sortino_ratio = (
            (mean_return * 252) / (downside_dev * math.sqrt(252))
            if downside_dev > 0
            else 0
        )
    else:
        volatility = 0
        sharpe_ratio = 0
        sortino_ratio = 0

    max_drawdown_pct = max([pt.drawdown_pct for pt in equity_curve], default=0)
    max_drawdown = initial_capital * max_drawdown_pct / 100

    # Calculate VaR (95% confidence)
    if daily_returns:
        sorted_returns = sorted(daily_returns)
        var_index = int(len(sorted_returns) * 0.05)
        var_95 = (
            abs(sorted_returns[var_index]) * initial_capital
            if var_index < len(sorted_returns)
            else 0
        )

        # CVaR (average of worst 5%)
        worst_returns = sorted_returns[: var_index + 1]
        cvar_95 = (
            abs(sum(worst_returns) / len(worst_returns)) * initial_capital
            if worst_returns
            else 0
        )
    else:
        var_95 = 0
        cvar_95 = 0

    calmar_ratio = (total_return_pct / max_drawdown_pct) if max_drawdown_pct > 0 else 0

    return PerformanceMetrics(
        total_return=total_return,
        total_return_pct=total_return_pct,
        sharpe_ratio=sharpe_ratio,
        sortino_ratio=sortino_ratio,
        calmar_ratio=calmar_ratio,
        max_drawdown=max_drawdown,
        max_drawdown_pct=max_drawdown_pct,
        volatility=volatility * 252 * 100,  # Annualized %
        var_95=var_95,
        cvar_95=cvar_95,
        beta=random.uniform(0.8, 1.2),
        alpha=random.uniform(-0.02, 0.05),
        information_ratio=random.uniform(-0.5, 1.5),
    )


@router.get("/", response_model=List[Dict[str, Any]])
async def get_all_results():
    """Get summary of all backtest results."""
    summaries = []
    for result in MOCK_RESULTS.values():
        summaries.append(
            {
                "id": result.id,
                "backtest_id": result.backtest_id,
                "strategy_name": result.strategy_name,
                "start_date": result.start_date,
                "end_date": result.end_date,
                "total_return_pct": result.metrics.total_return_pct,
                "sharpe_ratio": result.metrics.sharpe_ratio,
                "max_drawdown_pct": result.metrics.max_drawdown_pct,
                "total_trades": result.trade_summary.total_trades,
                "win_rate": result.trade_summary.win_rate,
                "created_at": result.created_at,
            }
        )

    return sorted(summaries, key=lambda x: x["created_at"], reverse=True)


@router.get("/{result_id}", response_model=BacktestResult)
async def get_result_details(result_id: str):
    """Get detailed backtest results."""
    if result_id not in MOCK_RESULTS:
        raise HTTPException(status_code=404, detail="Result not found")

    return MOCK_RESULTS[result_id]


@router.post("/generate/{execution_id}")
async def generate_mock_result(execution_id: str):
    """Generate mock result for completed execution (for demo purposes)."""

    # Mock configuration
    start_date = "2024-01-01"
    end_date = "2024-06-30"
    initial_capital = 100000.0
    strategy_name = "Order Book Scalper"

    # Generate equity curve
    equity_curve = generate_mock_equity_curve(start_date, end_date, initial_capital)

    # Calculate metrics
    metrics = calculate_mock_metrics(equity_curve, initial_capital)

    # Generate trade summary
    total_trades = random.randint(150, 500)
    winning_trades = int(total_trades * random.uniform(0.4, 0.7))
    losing_trades = total_trades - winning_trades

    trade_summary = TradeSummary(
        total_trades=total_trades,
        winning_trades=winning_trades,
        losing_trades=losing_trades,
        largest_win=random.uniform(800, 2000),
        largest_loss=random.uniform(-1500, -500),
        average_win=random.uniform(150, 400),
        average_loss=random.uniform(-200, -100),
        average_trade=metrics.total_return / total_trades if total_trades > 0 else 0,
        win_rate=(winning_trades / total_trades * 100) if total_trades > 0 else 0,
        profit_factor=random.uniform(1.1, 2.5),
        consecutive_wins=random.randint(3, 12),
        consecutive_losses=random.randint(2, 8),
        avg_trade_duration_minutes=random.randint(45, 300),
    )

    # Generate statistics
    statistics = PerformanceStatistics(
        returns={
            "Total Return": metrics.total_return,
            "Total Return %": metrics.total_return_pct,
            "Annual Return %": metrics.total_return_pct * 2,  # Assume 6 months
            "Monthly Return %": metrics.total_return_pct / 6,
            "Daily Return %": metrics.total_return_pct / 180,
        },
        risk_metrics={
            "Sharpe Ratio": metrics.sharpe_ratio,
            "Sortino Ratio": metrics.sortino_ratio,
            "Calmar Ratio": metrics.calmar_ratio,
            "Max Drawdown": metrics.max_drawdown,
            "Max Drawdown %": metrics.max_drawdown_pct,
            "Volatility %": metrics.volatility,
            "VaR 95%": metrics.var_95,
            "CVaR 95%": metrics.cvar_95,
        },
        trade_metrics={
            "Total Trades": trade_summary.total_trades,
            "Win Rate %": trade_summary.win_rate,
            "Profit Factor": trade_summary.profit_factor,
            "Average Trade": trade_summary.average_trade,
            "Largest Win": trade_summary.largest_win,
            "Largest Loss": trade_summary.largest_loss,
        },
        time_metrics={
            "Avg Trade Duration (min)": trade_summary.avg_trade_duration_minutes,
            "Trades per Day": total_trades / 180,
            "Trading Days": 180,
            "Consecutive Wins": trade_summary.consecutive_wins,
            "Consecutive Losses": trade_summary.consecutive_losses,
        },
    )

    # Create result
    result_id = f"result_{execution_id}"
    result = BacktestResult(
        id=result_id,
        backtest_id=execution_id,
        start_date=start_date,
        end_date=end_date,
        strategy_name=strategy_name,
        initial_capital=initial_capital,
        final_capital=equity_curve[-1].equity,
        configuration={"strategy_id": "order_book_scalper", "data_level": "L1"},
        metrics=metrics,
        equity_curve=equity_curve,
        trade_summary=trade_summary,
        statistics=statistics,
        created_at=datetime.now().isoformat(),
        execution_time_seconds=random.uniform(60, 300),
    )

    MOCK_RESULTS[result_id] = result

    return {"result_id": result_id, "message": "Mock result generated"}


@router.get("/{result_id}/export/{format}")
async def export_result(result_id: str, format: str):
    """Export result in various formats (csv, json, pdf)."""
    if result_id not in MOCK_RESULTS:
        raise HTTPException(status_code=404, detail="Result not found")

    result = MOCK_RESULTS[result_id]

    if format.lower() == "json":
        return result.model_dump()
    elif format.lower() == "csv":
        # Return CSV data structure (simplified for demo)
        return {
            "format": "csv",
            "data": "Mock CSV export data would be here",
            "filename": f"{result.strategy_name}_{result_id}.csv",
        }
    elif format.lower() == "pdf":
        return {
            "format": "pdf",
            "data": "Mock PDF export data would be here",
            "filename": f"{result.strategy_name}_{result_id}.pdf",
        }
    else:
        raise HTTPException(status_code=400, detail="Unsupported export format")
