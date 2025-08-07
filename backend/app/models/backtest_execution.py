from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class ExecutionStatus(str, Enum):
    QUEUED = "queued"
    INITIALIZING = "initializing"
    LOADING_DATA = "loading_data"
    PROCESSING = "processing"
    CALCULATING_METRICS = "calculating_metrics"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class ExecutionStage(str, Enum):
    INITIALIZATION = "initialization"
    DATA_LOADING = "data_loading"
    STRATEGY_SETUP = "strategy_setup"
    SIMULATION = "simulation"
    METRICS_CALCULATION = "metrics_calculation"
    FINALIZATION = "finalization"


class ExecutionProgress(BaseModel):
    percentage: float = 0.0
    current_tick: int = 0
    total_ticks: int = 0
    processed_trades: int = 0
    current_date: Optional[str] = None
    stage: str = ""
    stage_progress: float = 0.0


class ResourceUsage(BaseModel):
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    peak_memory_mb: float = 0.0
    disk_io_mb: float = 0.0


class ExecutionError(BaseModel):
    timestamp: datetime
    severity: str  # 'error', 'warning', 'info'
    message: str
    details: Optional[str] = None
    recoverable: bool = False


class BacktestMetrics(BaseModel):
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    total_pnl: float = 0.0
    max_drawdown: float = 0.0
    sharpe_ratio: Optional[float] = None
    current_equity: float = 0.0
    last_trade_time: Optional[str] = None


class BacktestExecution(BaseModel):
    id: str
    backtest_id: str
    status: ExecutionStatus
    progress: ExecutionProgress
    start_time: datetime
    end_time: Optional[datetime] = None
    estimated_end_time: Optional[datetime] = None
    current_stage: ExecutionStage
    metrics: BacktestMetrics = Field(default_factory=BacktestMetrics)
    resource_usage: ResourceUsage = Field(default_factory=ResourceUsage)
    errors: List[ExecutionError] = Field(default_factory=list)
    configuration: Dict[str, Any] = Field(default_factory=dict)


class ExecutionRequest(BaseModel):
    strategy_id: str
    strategy_parameters: Dict[str, Any]
    data_configuration: Dict[str, Any]
    priority: int = 5  # 1-10, higher = more priority


class ExecutionResponse(BaseModel):
    execution_id: str
    backtest_id: str
    status: ExecutionStatus
    queue_position: Optional[int] = None
    estimated_start_time: Optional[datetime] = None


class ExecutionControlRequest(BaseModel):
    action: str  # 'pause', 'resume', 'cancel', 'priority_change'
    priority: Optional[int] = None
