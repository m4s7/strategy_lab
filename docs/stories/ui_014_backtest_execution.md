# Story UI_014: Backtest Execution Control

## Story Details
- **Story ID**: UI_014
- **Epic**: Epic 2 - Core Backtesting Features
- **Story Points**: 8
- **Priority**: Critical
- **Type**: User Interface + Backend Integration

## User Story
**As a** trading researcher
**I want** to start, monitor, and control backtest execution
**So that** I can track progress in real-time and manage multiple running tests efficiently

## Acceptance Criteria

### 1. Backtest Initialization
- [ ] Configuration review screen before execution
- [ ] Execution confirmation dialog with resource estimates
- [ ] Pre-execution validation with clear error messages
- [ ] Quick start button with last configuration
- [ ] Batch execution setup for multiple parameter sets
- [ ] Priority queue management for multiple backtests

### 2. Real-time Progress Monitoring
- [ ] Live progress bars with meaningful stages (data loading, processing, analysis)
- [ ] Current processing status with timestamps
- [ ] Estimated time remaining with dynamic updates
- [ ] Processing speed indicators (ticks/second, trades/minute)
- [ ] Resource utilization monitoring (CPU, memory)
- [ ] Intermediate results preview during execution

### 3. Execution Controls
- [ ] Pause/resume functionality (if supported by engine)
- [ ] Cancel execution with confirmation dialog
- [ ] Force stop for unresponsive backtests
- [ ] Queue position management
- [ ] Job priority adjustment
- [ ] Automatic retry on transient failures

### 4. Multi-Backtest Management
- [ ] Queue visualization with job statuses
- [ ] Concurrent execution management
- [ ] Job history and status tracking
- [ ] Bulk operations (cancel all, pause all)
- [ ] Resource allocation per job
- [ ] Execution scheduling and dependencies

### 5. Error Handling and Reporting
- [ ] Detailed error messages with context
- [ ] Error log viewing and export
- [ ] Automatic error categorization
- [ ] Recovery suggestions for common errors
- [ ] Error notification system
- [ ] Partial result recovery for failed backtests

### 6. Results Preview
- [ ] Live key metrics during execution
- [ ] Preliminary performance indicators
- [ ] Trade count and win/loss ratio updates
- [ ] Equity curve streaming updates
- [ ] Risk metrics progression
- [ ] Performance comparison with benchmarks

## Technical Requirements

### Backtest Execution Service
```typescript
interface BacktestExecution {
  id: string;
  configurationId: string;
  status: ExecutionStatus;
  progress: ExecutionProgress;
  startTime: string;
  estimatedEndTime?: string;
  currentStage: ExecutionStage;
  metrics: Partial<BacktestMetrics>;
  resourceUsage: ResourceUsage;
  errors: ExecutionError[];
}

enum ExecutionStatus {
  QUEUED = 'queued',
  INITIALIZING = 'initializing',
  LOADING_DATA = 'loading_data',
  PROCESSING = 'processing',
  CALCULATING_METRICS = 'calculating_metrics',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled',
  PAUSED = 'paused'
}

interface ExecutionProgress {
  percentage: number;
  currentTick: number;
  totalTicks: number;
  processedTrades: number;
  currentDate: string;
  stage: string;
  eta: string;
}
```

### Real-time Monitoring Component
```typescript
const BacktestMonitor: React.FC<{
  executionId: string;
}> = ({ executionId }) => {
  const { data: execution } = useBacktestExecution(executionId);
  const { progress, metrics } = useWebSocket(`backtest:${executionId}`);

  const handleCancel = async () => {
    const confirmed = await showConfirmDialog(
      'Cancel Backtest',
      'Are you sure you want to cancel this backtest? Progress will be lost.'
    );

    if (confirmed) {
      await cancelBacktest(executionId);
    }
  };

  return (
    <div className="backtest-monitor">
      <div className="execution-header">
        <h3>Backtest Execution</h3>
        <div className="execution-controls">
          <Button
            variant="outline"
            onClick={handlePause}
            disabled={!canPause(execution.status)}
          >
            {execution.status === 'paused' ? 'Resume' : 'Pause'}
          </Button>
          <Button
            variant="destructive"
            onClick={handleCancel}
          >
            Cancel
          </Button>
        </div>
      </div>

      <div className="progress-section">
        <ProgressBar
          value={progress.percentage}
          text={`${progress.percentage.toFixed(1)}% - ${progress.stage}`}
          subText={`${progress.currentTick.toLocaleString()}/${progress.totalTicks.toLocaleString()} ticks`}
        />

        <div className="progress-details">
          <div className="detail-item">
            <span className="label">Current Date:</span>
            <span className="value">{progress.currentDate}</span>
          </div>
          <div className="detail-item">
            <span className="label">Processing Speed:</span>
            <span className="value">{calculateSpeed(progress)} ticks/sec</span>
          </div>
          <div className="detail-item">
            <span className="label">ETA:</span>
            <span className="value">{progress.eta}</span>
          </div>
        </div>
      </div>

      <div className="live-metrics">
        <MetricCard title="Trades" value={progress.processedTrades} />
        <MetricCard title="P&L" value={formatCurrency(metrics.totalPnl)} />
        <MetricCard title="Win Rate" value={`${metrics.winRate?.toFixed(1)}%`} />
        <MetricCard title="Sharpe" value={metrics.sharpeRatio?.toFixed(3)} />
      </div>

      <div className="resource-monitoring">
        <ResourceChart
          cpuUsage={execution.resourceUsage.cpu}
          memoryUsage={execution.resourceUsage.memory}
        />
      </div>
    </div>
  );
};
```

### Backtest Queue Management
```typescript
const BacktestQueue: React.FC = () => {
  const { data: queue } = useBacktestQueue();
  const [selectedJobs, setSelectedJobs] = useState<string[]>([]);

  const handleBulkCancel = async () => {
    const confirmed = await showConfirmDialog(
      'Cancel Selected Backtests',
      `Cancel ${selectedJobs.length} selected backtests?`
    );

    if (confirmed) {
      await Promise.all(selectedJobs.map(id => cancelBacktest(id)));
      setSelectedJobs([]);
    }
  };

  const handlePriorityChange = async (jobId: string, priority: number) => {
    await updateBacktestPriority(jobId, priority);
  };

  return (
    <div className="backtest-queue">
      <div className="queue-header">
        <h3>Execution Queue ({queue.length})</h3>
        <div className="queue-controls">
          <Button
            variant="outline"
            onClick={handleBulkCancel}
            disabled={selectedJobs.length === 0}
          >
            Cancel Selected ({selectedJobs.length})
          </Button>
        </div>
      </div>

      <div className="queue-list">
        {queue.map(job => (
          <QueueItem
            key={job.id}
            job={job}
            selected={selectedJobs.includes(job.id)}
            onSelect={(selected) => toggleJobSelection(job.id, selected)}
            onPriorityChange={(priority) => handlePriorityChange(job.id, priority)}
            onCancel={() => cancelBacktest(job.id)}
          />
        ))}
      </div>
    </div>
  );
};
```

### Execution API Integration
```python
# FastAPI Backend Integration
@router.post("/backtests/execute")
async def execute_backtest(
    config: BacktestConfiguration,
    background_tasks: BackgroundTasks
) -> BacktestExecution:

    # Validate configuration
    validation_result = await validate_backtest_config(config)
    if not validation_result.is_valid:
        raise HTTPException(400, validation_result.errors)

    # Create execution record
    execution = BacktestExecution(
        id=str(uuid.uuid4()),
        configuration_id=config.id,
        status=ExecutionStatus.QUEUED,
        start_time=datetime.utcnow(),
        current_stage=ExecutionStage.QUEUED
    )

    # Save to database
    await execution_repository.save(execution)

    # Add to execution queue
    background_tasks.add_task(execute_backtest_async, execution.id)

    return execution

async def execute_backtest_async(execution_id: str):
    execution = await execution_repository.get(execution_id)

    try:
        # Update status
        execution.status = ExecutionStatus.INITIALIZING
        await execution_repository.update(execution)
        await broadcast_execution_update(execution)

        # Load strategy
        strategy = await strategy_registry.get(execution.configuration.strategy_id)

        # Initialize backtest engine
        engine = BacktestEngine(
            strategy=strategy,
            data_config=execution.configuration.data,
            parameters=execution.configuration.parameters
        )

        # Execute with progress reporting
        async for progress in engine.execute_with_progress():
            execution.progress = progress
            execution.current_stage = progress.stage
            await execution_repository.update(execution)
            await broadcast_progress_update(execution_id, progress)

        # Complete execution
        execution.status = ExecutionStatus.COMPLETED
        execution.end_time = datetime.utcnow()
        await execution_repository.update(execution)
        await broadcast_execution_complete(execution)

    except Exception as e:
        execution.status = ExecutionStatus.FAILED
        execution.error_message = str(e)
        await execution_repository.update(execution)
        await broadcast_execution_error(execution_id, str(e))
```

### WebSocket Progress Updates
```typescript
const useBacktestProgress = (executionId: string) => {
  const { subscribe, unsubscribe } = useWebSocket();
  const [progress, setProgress] = useState<ExecutionProgress | null>(null);
  const [metrics, setMetrics] = useState<Partial<BacktestMetrics>>({});

  useEffect(() => {
    const handleProgressUpdate = (data: any) => {
      setProgress(data.progress);
      if (data.metrics) {
        setMetrics(prev => ({ ...prev, ...data.metrics }));
      }
    };

    subscribe(`backtest:${executionId}:progress`, handleProgressUpdate);
    subscribe(`backtest:${executionId}:metrics`, setMetrics);

    return () => {
      unsubscribe(`backtest:${executionId}:progress`);
      unsubscribe(`backtest:${executionId}:metrics`);
    };
  }, [executionId]);

  return { progress, metrics };
};
```

## Definition of Done
- [ ] Backtest starts successfully from configuration
- [ ] Real-time progress updates work via WebSocket
- [ ] Cancel functionality stops execution cleanly
- [ ] Queue management handles multiple backtests
- [ ] Error handling provides useful feedback
- [ ] Resource monitoring shows accurate usage
- [ ] Live metrics update during execution
- [ ] All execution states handled properly

## Testing Checklist
- [ ] Backtest execution starts without errors
- [ ] Progress updates arrive in real-time
- [ ] Cancel operation stops backtest and cleans up
- [ ] Error conditions are handled gracefully
- [ ] Resource monitoring is accurate
- [ ] Queue operations work correctly
- [ ] Pause/resume functionality works (if implemented)
- [ ] Live metrics are accurate and timely

## Integration Points
- **Strategy Configuration**: Uses output from UI_012
- **Data Configuration**: Uses output from UI_013
- **WebSocket System**: Uses UI_004 for real-time updates
- **Backtest Engine**: Core integration with Strategy Lab Python backend

## Performance Requirements
- Execution start time < 10 seconds
- Progress update latency < 200ms
- Cancel operation response < 5 seconds
- Queue operations < 1 second
- Resource monitoring accuracy > 95%

## Follow-up Stories
- UI_015: Basic Results Visualization (receives execution results)
- UI_016: Real-time Monitoring System (enhanced monitoring)
- UI_031: Grid Search Optimization (uses execution system)
