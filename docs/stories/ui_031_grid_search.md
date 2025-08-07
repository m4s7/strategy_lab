# Story UI_031: Grid Search Optimization

## Story Details
- **Story ID**: UI_031
- **Epic**: Epic 4 - Strategy Optimization
- **Story Points**: 8
- **Priority**: High
- **Type**: Algorithm Implementation + UI

## User Story
**As a** trading researcher
**I want** to configure and run grid search parameter optimization
**So that** I can systematically explore parameter combinations and discover optimal settings for my trading strategies

## Acceptance Criteria

### 1. Parameter Configuration Interface
- [ ] Dynamic parameter input form based on selected strategy
- [ ] Range specification (min, max, step size) for each parameter
- [ ] Parameter validation with meaningful error messages
- [ ] Preview of total parameter combinations with estimation
- [ ] Support for different parameter types (numeric, categorical, boolean)
- [ ] Parameter dependency handling (conditional parameters)

### 2. Grid Search Execution
- [ ] Integration with existing Strategy Lab optimization engine
- [ ] Batch execution of parameter combinations
- [ ] Parallel processing configuration (thread count)
- [ ] Resource allocation and monitoring
- [ ] Progress tracking with completion percentage and ETA
- [ ] Ability to pause/resume/cancel optimization jobs

### 3. Real-time Progress Monitoring
- [ ] Live progress bar showing completion status
- [ ] Current parameter combination being tested
- [ ] Best result so far with parameter values
- [ ] Performance metrics during execution (tests/minute)
- [ ] Error logging and handling for failed combinations
- [ ] Estimated time to completion

### 4. Results Visualization
- [ ] Parameter performance heatmap (2D parameter combinations)
- [ ] Best results table with sortable columns
- [ ] Parameter sensitivity analysis
- [ ] Performance distribution across parameter space
- [ ] Interactive filtering and sorting of results
- [ ] Export functionality for optimization results

### 5. Optimization Job Management
- [ ] Job queue system for multiple optimizations
- [ ] Job history and status tracking
- [ ] Results archival and retrieval
- [ ] Job comparison and analysis
- [ ] Optimization settings persistence
- [ ] Job scheduling and priority management

## Technical Requirements

### Grid Search Configuration Interface
```typescript
interface GridSearchConfig {
  strategyId: string;
  objectiveFunction: 'sharpe_ratio' | 'total_return' | 'max_drawdown' | 'profit_factor';
  parameters: GridSearchParameter[];
  executionSettings: {
    maxConcurrency: number;
    timeoutMinutes: number;
    dataRange: DateRange;
    validationMethod: 'none' | 'walk_forward' | 'cross_validation';
  };
}

interface GridSearchParameter {
  name: string;
  type: 'numeric' | 'categorical' | 'boolean';
  range?: {
    min: number;
    max: number;
    step: number;
  };
  values?: any[]; // For categorical parameters
  default?: any;
  description?: string;
}
```

### Parameter Configuration Component
```typescript
const ParameterConfigForm: React.FC<{
  strategy: Strategy;
  onConfigChange: (config: GridSearchConfig) => void;
}> = ({ strategy, onConfigChange }) => {
  const [parameters, setParameters] = useState<GridSearchParameter[]>([]);
  const [totalCombinations, setTotalCombinations] = useState(0);

  // Calculate total combinations
  useEffect(() => {
    const total = parameters.reduce((acc, param) => {
      if (param.type === 'numeric' && param.range) {
        const steps = Math.floor((param.range.max - param.range.min) / param.range.step) + 1;
        return acc * steps;
      } else if (param.type === 'categorical' && param.values) {
        return acc * param.values.length;
      }
      return acc;
    }, 1);
    setTotalCombinations(total);
  }, [parameters]);

  const renderParameterInput = (param: GridSearchParameter) => {
    switch (param.type) {
      case 'numeric':
        return (
          <NumericRangeInput
            parameter={param}
            onChange={(updatedParam) => updateParameter(param.name, updatedParam)}
          />
        );
      case 'categorical':
        return (
          <CategoricalInput
            parameter={param}
            onChange={(updatedParam) => updateParameter(param.name, updatedParam)}
          />
        );
      default:
        return null;
    }
  };

  return (
    <form className="grid-search-config">
      <div className="parameters-section">
        {parameters.map(param => (
          <div key={param.name} className="parameter-input">
            <label>{param.name}</label>
            {renderParameterInput(param)}
          </div>
        ))}
      </div>

      <div className="execution-settings">
        <EstimationPanel
          totalCombinations={totalCombinations}
          estimatedDuration={calculateEstimatedDuration(totalCombinations)}
        />
      </div>
    </form>
  );
};
```

### Grid Search Execution Engine Integration
```python
# Backend FastAPI endpoint for grid search
@router.post("/optimization/grid-search")
async def start_grid_search(
    config: GridSearchConfig,
    background_tasks: BackgroundTasks
) -> OptimizationJob:

    # Validate configuration
    validation_result = validate_grid_search_config(config)
    if not validation_result.valid:
        raise HTTPException(400, validation_result.errors)

    # Create optimization job
    job = OptimizationJob(
        id=str(uuid.uuid4()),
        type="grid_search",
        config=config.dict(),
        status="pending",
        created_at=datetime.utcnow()
    )

    # Save job to database
    await optimization_repository.save(job)

    # Start grid search in background
    background_tasks.add_task(execute_grid_search, job)

    return job

async def execute_grid_search(job: OptimizationJob):
    try:
        job.status = "running"
        await optimization_repository.update(job)

        # Generate parameter combinations
        combinations = generate_parameter_combinations(job.config["parameters"])
        total_combinations = len(combinations)

        # Execute backtests for each combination
        results = []
        for i, params in enumerate(combinations):
            try:
                # Run backtest with parameters
                result = await run_backtest_with_params(
                    strategy_id=job.config["strategyId"],
                    parameters=params,
                    data_range=job.config["executionSettings"]["dataRange"]
                )

                results.append({
                    "parameters": params,
                    "metrics": result.metrics,
                    "performance": result.objective_value
                })

                # Update progress
                progress = (i + 1) / total_combinations
                await broadcast_progress_update(job.id, progress, params)

            except Exception as e:
                # Log error but continue with other combinations
                logger.error(f"Grid search combination failed: {params}, error: {e}")

        # Find best result
        best_result = max(results, key=lambda r: r["performance"])

        # Update job with results
        job.status = "completed"
        job.best_params = best_result["parameters"]
        job.results = results
        await optimization_repository.update(job)

        # Broadcast completion
        await broadcast_optimization_complete(job)

    except Exception as e:
        job.status = "failed"
        job.error_message = str(e)
        await optimization_repository.update(job)
```

### Progress Monitoring and Visualization
```typescript
const GridSearchMonitor: React.FC<{
  jobId: string;
}> = ({ jobId }) => {
  const { data: job } = useOptimizationJob(jobId);
  const { progress } = useWebSocket(`optimization:${jobId}`);

  if (!job) return <LoadingSkeleton />;

  return (
    <div className="grid-search-monitor">
      <div className="progress-section">
        <ProgressBar
          value={progress.percentage}
          text={`${progress.completed}/${progress.total} combinations`}
        />
        <div className="current-test">
          Testing: {JSON.stringify(progress.currentParameters)}
        </div>
        <div className="best-so-far">
          Best so far: {progress.bestResult?.performance.toFixed(4)}
          ({JSON.stringify(progress.bestResult?.parameters)})
        </div>
      </div>

      <div className="performance-metrics">
        <MetricsCard
          title="Execution Rate"
          value={`${progress.rate}/min`}
          trend={progress.rateTrend}
        />
        <MetricsCard
          title="ETA"
          value={formatDuration(progress.eta)}
        />
        <MetricsCard
          title="Success Rate"
          value={`${progress.successRate}%`}
        />
      </div>
    </div>
  );
};
```

### Results Analysis and Visualization
```typescript
const GridSearchResults: React.FC<{
  results: GridSearchResult[];
  parameters: string[];
}> = ({ results, parameters }) => {
  const [selectedParams, setSelectedParams] = useState(parameters.slice(0, 2));
  const [sortBy, setSortBy] = useState('performance');

  // Generate heatmap data for 2D parameter visualization
  const heatmapData = useMemo(() => {
    if (selectedParams.length !== 2) return [];

    return generateHeatmapData(results, selectedParams);
  }, [results, selectedParams]);

  return (
    <div className="grid-search-results">
      <div className="controls">
        <ParameterSelector
          parameters={parameters}
          selected={selectedParams}
          onChange={setSelectedParams}
        />
        <SortControl
          options={['performance', 'sharpe_ratio', 'max_drawdown']}
          value={sortBy}
          onChange={setSortBy}
        />
      </div>

      <div className="visualization">
        <ParameterHeatmap
          data={heatmapData}
          xAxis={selectedParams[0]}
          yAxis={selectedParams[1]}
          colorBy="performance"
        />
      </div>

      <div className="results-table">
        <ResultsDataTable
          results={results}
          sortBy={sortBy}
          onRowClick={showResultDetails}
        />
      </div>
    </div>
  );
};
```

## Definition of Done
- [ ] Parameter configuration form works for all parameter types
- [ ] Grid search executes successfully with progress tracking
- [ ] Real-time progress updates via WebSocket
- [ ] Results visualization shows parameter performance clearly
- [ ] Export functionality works for optimization results
- [ ] Job management handles multiple concurrent optimizations
- [ ] Error handling provides useful feedback to users
- [ ] Performance handles parameter spaces up to 10,000 combinations

## Testing Checklist
- [ ] Parameter validation catches invalid configurations
- [ ] Grid search completes successfully with sample strategy
- [ ] Progress updates arrive in real-time during execution
- [ ] Results heatmap displays parameter relationships correctly
- [ ] Job cancellation works without leaving orphaned processes
- [ ] Large parameter spaces don't crash the system
- [ ] Error conditions are handled gracefully
- [ ] Results can be exported and imported successfully

## Performance Requirements
- Parameter form responsiveness < 100ms for configuration changes
- Grid search execution rate > 10 combinations/minute (depends on strategy complexity)
- Results visualization renders smoothly with 1000+ results
- Memory usage scales linearly with result set size
- WebSocket updates don't impact UI performance

## Integration Points
- **Strategy System**: Integration with existing strategy registry and execution
- **Backtest Engine**: Uses existing backtest execution infrastructure
- **Results Storage**: Stores optimization results in database
- **WebSocket System**: Uses existing WebSocket infrastructure for real-time updates
- **Export System**: Integrates with general export functionality

## Follow-up Stories
- UI_032: Genetic Algorithm Optimization (similar UI patterns)
- UI_034: 3D Parameter Surface Visualization (extends results visualization)
- UI_036: Optimization Results Analysis (comparative analysis across methods)
