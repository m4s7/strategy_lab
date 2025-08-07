# UI_033: Optimization Execution & Monitoring

## Story
As a trader, I want to execute and monitor grid search optimizations with real-time progress updates, pause/resume capabilities, and partial results so that I can efficiently find optimal parameters.

## Acceptance Criteria
1. Start/pause/resume/cancel optimization runs
2. Display real-time progress with ETA
3. Show partial results as they complete
4. Visualize optimization convergence
5. Handle failures gracefully with retry logic
6. Support distributed execution across multiple cores
7. Save checkpoint data for resumption
8. Provide optimization performance metrics

## Technical Requirements

### Frontend Components
```typescript
// components/optimization/OptimizationRunner.tsx
interface OptimizationRun {
  id: string;
  configId: string;
  status: 'pending' | 'running' | 'paused' | 'completed' | 'failed';
  progress: {
    completed: number;
    total: number;
    currentBatch: number;
    failedCount: number;
  };
  performance: {
    startTime: Date;
    elapsedTime: number;
    avgTimePerRun: number;
    estimatedCompletion: Date;
  };
  bestResults: OptimizationResult[];
  currentParameters?: ParameterSet;
}

export function OptimizationRunner({ configId }: { configId: string }) {
  const [run, setRun] = useState<OptimizationRun>();
  const [partialResults, setPartialResults] = useState<OptimizationResult[]>([]);
  const [viewMode, setViewMode] = useState<'progress' | 'results' | 'analysis'>('progress');

  // WebSocket connection for real-time updates
  useEffect(() => {
    const ws = new WebSocket(`ws://localhost:8000/optimization/${configId}/stream`);

    ws.onmessage = (event) => {
      const update = JSON.parse(event.data);
      handleOptimizationUpdate(update);
    };

    return () => ws.close();
  }, [configId]);

  const handleOptimizationUpdate = (update: OptimizationUpdate) => {
    switch (update.type) {
      case 'progress':
        setRun(prev => ({
          ...prev,
          progress: update.progress,
          performance: update.performance
        }));
        break;

      case 'result':
        setPartialResults(prev => [...prev, update.result]);
        updateBestResults(update.result);
        break;

      case 'status':
        setRun(prev => ({ ...prev, status: update.status }));
        break;
    }
  };

  return (
    <div className="optimization-runner">
      <OptimizationControl
        run={run}
        onStart={startOptimization}
        onPause={pauseOptimization}
        onResume={resumeOptimization}
        onCancel={cancelOptimization}
      />

      <Tabs value={viewMode} onValueChange={setViewMode}>
        <TabsList>
          <TabsTrigger value="progress">Progress</TabsTrigger>
          <TabsTrigger value="results">Results</TabsTrigger>
          <TabsTrigger value="analysis">Analysis</TabsTrigger>
        </TabsList>

        <TabsContent value="progress">
          <OptimizationProgress run={run} />
        </TabsContent>

        <TabsContent value="results">
          <PartialResultsView
            results={partialResults}
            bestResults={run?.bestResults}
          />
        </TabsContent>

        <TabsContent value="analysis">
          <ConvergenceAnalysis
            results={partialResults}
            totalRuns={run?.progress.total}
          />
        </TabsContent>
      </Tabs>
    </div>
  );
}
```

### Optimization Progress View
```typescript
// components/optimization/OptimizationProgress.tsx
export function OptimizationProgress({ run }: { run: OptimizationRun }) {
  const progressPercentage = (run.progress.completed / run.progress.total) * 100;

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Optimization Progress</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Main progress bar */}
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span>Overall Progress</span>
                <span>{progressPercentage.toFixed(1)}%</span>
              </div>
              <Progress value={progressPercentage} />
              <div className="flex justify-between text-xs text-muted-foreground mt-1">
                <span>{run.progress.completed} / {run.progress.total} runs</span>
                <span>ETA: {formatDateTime(run.performance.estimatedCompletion)}</span>
              </div>
            </div>

            {/* Performance metrics */}
            <div className="grid grid-cols-4 gap-4">
              <MetricCard
                title="Elapsed Time"
                value={formatDuration(run.performance.elapsedTime)}
                icon={Clock}
              />
              <MetricCard
                title="Runs/Hour"
                value={(3600 / run.performance.avgTimePerRun).toFixed(0)}
                icon={Activity}
              />
              <MetricCard
                title="Failed Runs"
                value={run.progress.failedCount}
                icon={AlertCircle}
                trend={run.progress.failedCount > 0 ? 'down' : null}
              />
              <MetricCard
                title="Current Batch"
                value={`${run.progress.currentBatch} / ${Math.ceil(run.progress.total / BATCH_SIZE)}`}
                icon={Layers}
              />
            </div>

            {/* Current parameters being tested */}
            {run.currentParameters && (
              <CurrentParametersDisplay params={run.currentParameters} />
            )}
          </div>
        </CardContent>
      </Card>

      <ResourceMonitor runId={run.id} />
    </div>
  );
}

// Resource monitoring
function ResourceMonitor({ runId }: { runId: string }) {
  const [resources, setResources] = useState<ResourceUsage>();

  useEffect(() => {
    const interval = setInterval(async () => {
      const usage = await fetchResourceUsage(runId);
      setResources(usage);
    }, 5000);

    return () => clearInterval(interval);
  }, [runId]);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Resource Usage</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          <ResourceBar
            label="CPU"
            value={resources?.cpu || 0}
            max={100}
            unit="%"
          />
          <ResourceBar
            label="Memory"
            value={resources?.memory || 0}
            max={100}
            unit="%"
          />
          <ResourceBar
            label="Disk I/O"
            value={resources?.diskIO || 0}
            max={1000}
            unit="MB/s"
          />
        </div>
      </CardContent>
    </Card>
  );
}
```

### Partial Results View
```typescript
// components/optimization/PartialResultsView.tsx
export function PartialResultsView({
  results,
  bestResults
}: PartialResultsViewProps) {
  const [sortBy, setSortBy] = useState<'sharpe' | 'return' | 'drawdown'>('sharpe');
  const [filterMode, setFilterMode] = useState<'all' | 'top10' | 'improving'>('top10');

  const displayResults = useMemo(() => {
    let filtered = [...results];

    // Apply filter
    switch (filterMode) {
      case 'top10':
        filtered = filtered
          .sort((a, b) => b[sortBy] - a[sortBy])
          .slice(0, 10);
        break;

      case 'improving':
        filtered = filtered.filter((result, idx) => {
          if (idx === 0) return true;
          const prevBest = Math.max(...results.slice(0, idx).map(r => r[sortBy]));
          return result[sortBy] > prevBest;
        });
        break;
    }

    return filtered;
  }, [results, sortBy, filterMode]);

  return (
    <div className="space-y-6">
      {/* Best results summary */}
      <Card>
        <CardHeader>
          <CardTitle>Top Performing Parameters</CardTitle>
          <div className="flex gap-4">
            <Select value={sortBy} onValueChange={setSortBy}>
              <SelectItem value="sharpe">Sharpe Ratio</SelectItem>
              <SelectItem value="return">Total Return</SelectItem>
              <SelectItem value="drawdown">Max Drawdown</SelectItem>
            </Select>

            <Select value={filterMode} onValueChange={setFilterMode}>
              <SelectItem value="all">All Results</SelectItem>
              <SelectItem value="top10">Top 10</SelectItem>
              <SelectItem value="improving">Improving Only</SelectItem>
            </Select>
          </div>
        </CardHeader>
        <CardContent>
          <ResultsTable
            results={displayResults}
            onResultClick={showResultDetails}
          />
        </CardContent>
      </Card>

      {/* Performance surface plot */}
      <Card>
        <CardHeader>
          <CardTitle>Performance Surface</CardTitle>
        </CardHeader>
        <CardContent>
          <PerformanceSurface
            results={results}
            metric={sortBy}
          />
        </CardContent>
      </Card>

      {/* Parameter importance */}
      <ParameterImportance results={results} />
    </div>
  );
}

// Performance surface visualization
function PerformanceSurface({ results, metric }) {
  const [xParam, setXParam] = useState<string>();
  const [yParam, setYParam] = useState<string>();

  const plotData = useMemo(() => {
    if (!xParam || !yParam || results.length === 0) return null;

    // Create surface data
    const xValues = [...new Set(results.map(r => r.parameters[xParam]))];
    const yValues = [...new Set(results.map(r => r.parameters[yParam]))];

    const z = yValues.map(y =>
      xValues.map(x => {
        const result = results.find(r =>
          r.parameters[xParam] === x && r.parameters[yParam] === y
        );
        return result ? result[metric] : null;
      })
    );

    return [{
      type: 'surface',
      x: xValues,
      y: yValues,
      z: z,
      colorscale: 'Viridis'
    }];
  }, [results, xParam, yParam, metric]);

  return (
    <div>
      <div className="flex gap-4 mb-4">
        <ParameterSelector
          label="X Axis"
          parameters={getParameterNames(results)}
          value={xParam}
          onChange={setXParam}
        />
        <ParameterSelector
          label="Y Axis"
          parameters={getParameterNames(results)}
          value={yParam}
          onChange={setYParam}
        />
      </div>

      {plotData && (
        <Plot
          data={plotData}
          layout={{
            scene: {
              xaxis: { title: xParam },
              yaxis: { title: yParam },
              zaxis: { title: metric }
            }
          }}
        />
      )}
    </div>
  );
}
```

### Convergence Analysis
```typescript
// components/optimization/ConvergenceAnalysis.tsx
export function ConvergenceAnalysis({
  results,
  totalRuns
}: ConvergenceAnalysisProps) {
  const convergenceData = useMemo(() => {
    // Track best value over time
    let bestSharpe = -Infinity;
    let bestReturn = -Infinity;
    let bestDrawdown = Infinity;

    return results.map((result, idx) => {
      bestSharpe = Math.max(bestSharpe, result.sharpe);
      bestReturn = Math.max(bestReturn, result.totalReturn);
      bestDrawdown = Math.min(bestDrawdown, result.maxDrawdown);

      return {
        run: idx + 1,
        bestSharpe,
        bestReturn,
        bestDrawdown: Math.abs(bestDrawdown),
        improvementRate: idx > 0 ?
          (bestSharpe - results[0].sharpe) / idx : 0
      };
    });
  }, [results]);

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Optimization Convergence</CardTitle>
          <CardDescription>
            How quickly the optimization is finding better parameters
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={convergenceData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="run" />
              <YAxis yAxisId="left" />
              <YAxis yAxisId="right" orientation="right" />
              <Tooltip />
              <Legend />

              <Line
                yAxisId="left"
                type="monotone"
                dataKey="bestSharpe"
                stroke="#8884d8"
                name="Best Sharpe"
                strokeWidth={2}
              />

              <Line
                yAxisId="right"
                type="monotone"
                dataKey="improvementRate"
                stroke="#82ca9d"
                name="Improvement Rate"
                strokeDasharray="5 5"
              />
            </LineChart>
          </ResponsiveContainer>

          <ConvergenceMetrics data={convergenceData} totalRuns={totalRuns} />
        </CardContent>
      </Card>

      <ParameterConvergence results={results} />
    </div>
  );
}

// Parameter convergence analysis
function ParameterConvergence({ results }) {
  const parameterTrends = useMemo(() => {
    // Analyze how parameter values converge
    const params = getParameterNames(results);

    return params.map(param => {
      const values = results.map(r => r.parameters[param]);
      const performance = results.map(r => r.sharpe);

      // Calculate weighted average based on performance
      const weights = performance.map(p => Math.exp(p));
      const weightSum = weights.reduce((a, b) => a + b, 0);
      const weightedAvg = values.reduce((sum, val, idx) =>
        sum + val * weights[idx] / weightSum, 0
      );

      return {
        parameter: param,
        convergenceValue: weightedAvg,
        variance: calculateVariance(values, weights),
        trend: calculateTrend(values, performance)
      };
    });
  }, [results]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Parameter Convergence</CardTitle>
        <CardDescription>
          Where parameters are converging based on performance
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Parameter</TableHead>
              <TableHead>Converging To</TableHead>
              <TableHead>Confidence</TableHead>
              <TableHead>Trend</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {parameterTrends.map(trend => (
              <TableRow key={trend.parameter}>
                <TableCell>{trend.parameter}</TableCell>
                <TableCell>{trend.convergenceValue.toFixed(4)}</TableCell>
                <TableCell>
                  <Progress
                    value={(1 - trend.variance) * 100}
                    className="w-20"
                  />
                </TableCell>
                <TableCell>
                  <TrendIndicator trend={trend.trend} />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
```

### Backend Optimization Engine
```python
# api/optimization/grid_search_engine.py
import asyncio
from concurrent.futures import ProcessPoolExecutor
import numpy as np
from typing import List, Dict, AsyncIterator
import pickle

class GridSearchEngine:
    def __init__(self, config: OptimizationConfig, max_workers: int = None):
        self.config = config
        self.max_workers = max_workers or cpu_count()
        self.executor = ProcessPoolExecutor(max_workers=self.max_workers)
        self.checkpoint_file = f"checkpoints/{config.id}.pkl"
        self.results = []
        self.failed_runs = []

    async def run(self) -> AsyncIterator[OptimizationUpdate]:
        """Run grid search optimization with streaming updates"""
        # Load checkpoint if exists
        start_idx = self._load_checkpoint()

        # Generate parameter combinations
        combinations = list(self._generate_combinations())
        total = len(combinations)

        # Process in batches for better resource management
        batch_size = self.max_workers * 4

        for batch_idx in range(start_idx, total, batch_size):
            batch = combinations[batch_idx:batch_idx + batch_size]

            # Run batch in parallel
            tasks = [
                self._run_single_backtest(params, idx + batch_idx)
                for idx, params in enumerate(batch)
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            for idx, result in enumerate(results):
                if isinstance(result, Exception):
                    self.failed_runs.append({
                        'index': batch_idx + idx,
                        'params': batch[idx],
                        'error': str(result)
                    })
                    yield OptimizationUpdate(
                        type='error',
                        error=str(result),
                        parameters=batch[idx]
                    )
                else:
                    self.results.append(result)
                    yield OptimizationUpdate(
                        type='result',
                        result=result
                    )

            # Update progress
            completed = batch_idx + len(batch)
            yield OptimizationUpdate(
                type='progress',
                progress={
                    'completed': completed,
                    'total': total,
                    'currentBatch': batch_idx // batch_size + 1,
                    'failedCount': len(self.failed_runs)
                },
                performance=self._calculate_performance(completed)
            )

            # Save checkpoint
            self._save_checkpoint(batch_idx + batch_size)

            # Check for pause/cancel
            if await self._check_control_signal():
                break

    async def _run_single_backtest(self, params: Dict, index: int) -> OptimizationResult:
        """Run a single backtest with given parameters"""
        try:
            # Update strategy configuration
            strategy_config = self.config.base_strategy_config.copy()
            strategy_config.update(params)

            # Run backtest
            backtest_result = await run_backtest(
                strategy_id=self.config.strategy_id,
                config=strategy_config,
                data_config=self.config.data_config
            )

            # Extract metrics
            return OptimizationResult(
                index=index,
                parameters=params,
                sharpe=backtest_result.sharpe_ratio,
                totalReturn=backtest_result.total_return,
                maxDrawdown=backtest_result.max_drawdown,
                winRate=backtest_result.win_rate,
                profitFactor=backtest_result.profit_factor,
                totalTrades=backtest_result.total_trades,
                metrics=backtest_result.metrics
            )

        except Exception as e:
            # Log error and re-raise
            logger.error(f"Backtest failed for params {params}: {str(e)}")
            raise

    def _save_checkpoint(self, current_index: int):
        """Save optimization state for resumption"""
        checkpoint = {
            'current_index': current_index,
            'results': self.results,
            'failed_runs': self.failed_runs,
            'timestamp': datetime.now()
        }

        with open(self.checkpoint_file, 'wb') as f:
            pickle.dump(checkpoint, f)

    def _load_checkpoint(self) -> int:
        """Load checkpoint if exists"""
        try:
            with open(self.checkpoint_file, 'rb') as f:
                checkpoint = pickle.load(f)
                self.results = checkpoint['results']
                self.failed_runs = checkpoint['failed_runs']
                return checkpoint['current_index']
        except FileNotFoundError:
            return 0

# WebSocket handler
async def optimization_websocket(websocket, path):
    config_id = path.split('/')[-2]
    config = await load_optimization_config(config_id)

    engine = GridSearchEngine(config)

    try:
        async for update in engine.run():
            await websocket.send(json.dumps(update.dict()))
    except WebSocketException:
        # Handle disconnect
        pass
    finally:
        engine.executor.shutdown()
```

### Optimization Control
```typescript
// components/optimization/OptimizationControl.tsx
export function OptimizationControl({
  run,
  onStart,
  onPause,
  onResume,
  onCancel
}: OptimizationControlProps) {
  const canStart = !run || run.status === 'pending';
  const canPause = run?.status === 'running';
  const canResume = run?.status === 'paused';
  const canCancel = run && ['running', 'paused'].includes(run.status);

  return (
    <Card>
      <CardContent className="pt-6">
        <div className="flex items-center justify-between">
          <div className="flex gap-2">
            {canStart && (
              <Button onClick={onStart} size="sm">
                <Play className="h-4 w-4 mr-2" />
                Start Optimization
              </Button>
            )}

            {canPause && (
              <Button onClick={onPause} variant="secondary" size="sm">
                <Pause className="h-4 w-4 mr-2" />
                Pause
              </Button>
            )}

            {canResume && (
              <Button onClick={onResume} size="sm">
                <Play className="h-4 w-4 mr-2" />
                Resume
              </Button>
            )}

            {canCancel && (
              <Button onClick={onCancel} variant="destructive" size="sm">
                <X className="h-4 w-4 mr-2" />
                Cancel
              </Button>
            )}
          </div>

          <div className="flex items-center gap-4">
            <StatusBadge status={run?.status} />
            <OptimizationMenu
              onExportResults={exportResults}
              onSaveCheckpoint={saveCheckpoint}
              onViewLogs={viewLogs}
            />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
```

## UI/UX Considerations
- Real-time progress updates without overwhelming the UI
- Clear visualization of convergence
- Responsive design for monitoring on mobile
- Efficient rendering of large result sets
- Clear status indicators
- Intuitive pause/resume functionality

## Testing Requirements
1. Optimization engine correctness
2. Checkpoint save/load functionality
3. Parallel execution efficiency
4. WebSocket stability under load
5. Result aggregation accuracy
6. Resource monitoring accuracy

## Dependencies
- UI_001: Next.js foundation
- UI_004: WebSocket infrastructure
- UI_032: Grid search setup
- UI_014: Backtest execution

## Story Points: 21

## Priority: High

## Implementation Notes
- Use process pool for CPU-bound backtests
- Implement adaptive batch sizing
- Add retry logic for transient failures
- Consider result caching for duplicate parameters
