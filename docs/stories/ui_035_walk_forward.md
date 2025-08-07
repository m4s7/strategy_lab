# UI_035: Walk-Forward Optimization

## Story
As a trader, I want to perform walk-forward optimization to validate strategy parameters over time and ensure they remain robust in changing market conditions.

## Acceptance Criteria
1. Configure walk-forward analysis periods (in-sample/out-sample)
2. Set up anchored or rolling window analysis
3. Execute walk-forward optimization with progress tracking
4. Visualize in-sample vs out-of-sample performance
5. Calculate efficiency ratios and consistency metrics
6. Identify parameter drift over time
7. Generate walk-forward analysis reports
8. Compare multiple walk-forward configurations

## Technical Requirements

### Frontend Components
```typescript
// components/optimization/WalkForwardSetup.tsx
interface WalkForwardConfig {
  id: string;
  name: string;
  strategyId: string;
  windowType: 'anchored' | 'rolling';
  periods: WalkForwardPeriod[];
  inSampleRatio: number; // e.g., 0.7 for 70% in-sample
  stepSize: number; // days to step forward
  optimizationConfig: OptimizationConfig;
}

interface WalkForwardPeriod {
  id: string;
  inSampleStart: Date;
  inSampleEnd: Date;
  outSampleStart: Date;
  outSampleEnd: Date;
  status: 'pending' | 'optimizing' | 'testing' | 'completed';
  results?: PeriodResults;
}

export function WalkForwardSetup({ strategyId }: { strategyId: string }) {
  const [config, setConfig] = useState<WalkForwardConfig>({
    windowType: 'rolling',
    inSampleRatio: 0.7,
    stepSize: 30,
    periods: []
  });

  const [dataRange, setDataRange] = useState<DateRange>();
  const [preview, setPreview] = useState<WalkForwardPeriod[]>([]);

  // Load available data range
  useEffect(() => {
    loadDataRange(strategyId).then(setDataRange);
  }, [strategyId]);

  // Generate preview of periods
  useEffect(() => {
    if (dataRange) {
      const periods = generateWalkForwardPeriods(config, dataRange);
      setPreview(periods);
    }
  }, [config, dataRange]);

  return (
    <div className="walk-forward-setup">
      <Card>
        <CardHeader>
          <CardTitle>Walk-Forward Analysis Configuration</CardTitle>
          <CardDescription>
            Configure periods for walk-forward optimization
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            {/* Window configuration */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Window Type</Label>
                <RadioGroup
                  value={config.windowType}
                  onValueChange={(value) => setConfig({...config, windowType: value})}
                >
                  <div className="flex items-center space-x-2">
                    <RadioGroupItem value="rolling" id="rolling" />
                    <Label htmlFor="rolling">Rolling Window</Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <RadioGroupItem value="anchored" id="anchored" />
                    <Label htmlFor="anchored">Anchored Window</Label>
                  </div>
                </RadioGroup>
              </div>

              <div>
                <Label>In-Sample Ratio</Label>
                <div className="flex items-center gap-2">
                  <Slider
                    value={[config.inSampleRatio * 100]}
                    onValueChange={([value]) =>
                      setConfig({...config, inSampleRatio: value / 100})
                    }
                    max={90}
                    min={50}
                    step={5}
                  />
                  <span>{(config.inSampleRatio * 100).toFixed(0)}%</span>
                </div>
              </div>
            </div>

            <div>
              <Label>Step Size (days)</Label>
              <Input
                type="number"
                value={config.stepSize}
                onChange={(e) => setConfig({...config, stepSize: parseInt(e.target.value)})}
                min={1}
                max={365}
              />
            </div>

            {/* Period preview */}
            <WalkForwardPeriodPreview
              periods={preview}
              windowType={config.windowType}
            />

            {/* Optimization settings */}
            <OptimizationSettingsCompact
              config={config.optimizationConfig}
              onChange={(opt) => setConfig({...config, optimizationConfig: opt})}
            />
          </div>

          <div className="mt-6 flex justify-between">
            <Button variant="outline" onClick={saveConfiguration}>
              Save Configuration
            </Button>
            <Button onClick={startWalkForward}>
              Start Analysis ({preview.length} periods)
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
```

### Period Preview Visualization
```typescript
// components/optimization/WalkForwardPeriodPreview.tsx
export function WalkForwardPeriodPreview({
  periods,
  windowType
}: WalkForwardPeriodPreviewProps) {
  const timelineData = useMemo(() => {
    return periods.map((period, idx) => ({
      id: period.id,
      index: idx + 1,
      inSample: {
        start: period.inSampleStart,
        end: period.inSampleEnd,
        duration: differenceInDays(period.inSampleEnd, period.inSampleStart)
      },
      outSample: {
        start: period.outSampleStart,
        end: period.outSampleEnd,
        duration: differenceInDays(period.outSampleEnd, period.outSampleStart)
      }
    }));
  }, [periods]);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Period Timeline</CardTitle>
        <CardDescription>
          {periods.length} walk-forward periods
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {timelineData.slice(0, 5).map(period => (
            <div key={period.id} className="relative h-8">
              <div className="absolute inset-y-0 flex items-center">
                <span className="text-xs text-muted-foreground w-8">
                  {period.index}
                </span>

                {/* In-sample period */}
                <div
                  className="h-6 bg-blue-500 opacity-70"
                  style={{
                    marginLeft: '2rem',
                    width: `${period.inSample.duration}px`
                  }}
                />

                {/* Out-sample period */}
                <div
                  className="h-6 bg-green-500 opacity-70"
                  style={{
                    width: `${period.outSample.duration}px`
                  }}
                />
              </div>
            </div>
          ))}

          {periods.length > 5 && (
            <div className="text-sm text-muted-foreground text-center">
              ... and {periods.length - 5} more periods
            </div>
          )}
        </div>

        <div className="flex gap-4 mt-4">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-blue-500 opacity-70" />
            <span className="text-sm">In-Sample</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-green-500 opacity-70" />
            <span className="text-sm">Out-of-Sample</span>
          </div>
        </div>

        {windowType === 'anchored' && (
          <Alert className="mt-4">
            <Info className="h-4 w-4" />
            <AlertDescription>
              Anchored window: In-sample period starts from the beginning and grows with each step.
            </AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  );
}
```

### Walk-Forward Execution
```typescript
// components/optimization/WalkForwardExecution.tsx
export function WalkForwardExecution({ configId }: { configId: string }) {
  const [execution, setExecution] = useState<WalkForwardExecution>();
  const [currentPeriod, setCurrentPeriod] = useState<number>(0);
  const [periodResults, setPeriodResults] = useState<Map<string, PeriodResults>>(new Map());

  // WebSocket for real-time updates
  useEffect(() => {
    const ws = new WebSocket(`ws://localhost:8000/walk-forward/${configId}/stream`);

    ws.onmessage = (event) => {
      const update = JSON.parse(event.data);
      handleWalkForwardUpdate(update);
    };

    return () => ws.close();
  }, [configId]);

  const handleWalkForwardUpdate = (update: WalkForwardUpdate) => {
    switch (update.type) {
      case 'period_start':
        setCurrentPeriod(update.periodIndex);
        break;

      case 'optimization_progress':
        // Update optimization progress for current period
        break;

      case 'period_complete':
        setPeriodResults(prev => new Map(prev).set(
          update.periodId,
          update.results
        ));
        break;

      case 'analysis_complete':
        setExecution(prev => ({ ...prev, status: 'completed' }));
        break;
    }
  };

  return (
    <div className="walk-forward-execution">
      <WalkForwardProgress
        execution={execution}
        currentPeriod={currentPeriod}
        totalPeriods={execution?.config.periods.length || 0}
      />

      <div className="grid grid-cols-3 gap-6 mt-6">
        <div className="col-span-2">
          <PeriodResultsChart
            periods={execution?.config.periods}
            results={periodResults}
          />
        </div>

        <div>
          <EfficiencyMetrics
            results={periodResults}
          />
        </div>
      </div>

      <ParameterEvolution
        periods={execution?.config.periods}
        results={periodResults}
      />
    </div>
  );
}

// Period results visualization
function PeriodResultsChart({ periods, results }) {
  const chartData = useMemo(() => {
    if (!periods) return [];

    return periods.map((period, idx) => {
      const result = results.get(period.id);
      return {
        period: idx + 1,
        inSample: result?.inSamplePerformance?.sharpe || 0,
        outSample: result?.outSamplePerformance?.sharpe || 0,
        efficiency: result ?
          (result.outSamplePerformance.sharpe / result.inSamplePerformance.sharpe) : 0
      };
    });
  }, [periods, results]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Walk-Forward Results</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={400}>
          <ComposedChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="period" />
            <YAxis yAxisId="left" />
            <YAxis yAxisId="right" orientation="right" />
            <Tooltip />
            <Legend />

            <Bar yAxisId="left" dataKey="inSample" fill="#8884d8" name="In-Sample Sharpe" />
            <Bar yAxisId="left" dataKey="outSample" fill="#82ca9d" name="Out-Sample Sharpe" />
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="efficiency"
              stroke="#ff7300"
              name="Efficiency"
              strokeWidth={2}
            />

            <ReferenceLine yAxisId="right" y={0.7} stroke="#666" strokeDasharray="3 3" />
          </ComposedChart>
        </ResponsiveContainer>

        <div className="mt-4 text-sm text-muted-foreground">
          Efficiency above 0.7 (70%) indicates robust parameters
        </div>
      </CardContent>
    </Card>
  );
}
```

### Parameter Evolution Analysis
```typescript
// components/optimization/ParameterEvolution.tsx
export function ParameterEvolution({ periods, results }) {
  const [selectedParam, setSelectedParam] = useState<string>();

  const evolutionData = useMemo(() => {
    if (!periods || !results.size) return null;

    // Extract parameter values over time
    const paramNames = new Set<string>();
    const evolution: Record<string, any[]> = {};

    periods.forEach((period, idx) => {
      const result = results.get(period.id);
      if (result?.optimalParameters) {
        Object.entries(result.optimalParameters).forEach(([param, value]) => {
          paramNames.add(param);
          if (!evolution[param]) evolution[param] = [];
          evolution[param].push({
            period: idx + 1,
            value: value,
            inSampleSharpe: result.inSamplePerformance.sharpe,
            outSampleSharpe: result.outSamplePerformance.sharpe,
            date: period.inSampleEnd
          });
        });
      }
    });

    return {
      parameters: Array.from(paramNames),
      evolution
    };
  }, [periods, results]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Parameter Evolution</CardTitle>
        <CardDescription>
          How optimal parameters change over time
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <Select value={selectedParam} onValueChange={setSelectedParam}>
            <SelectTrigger>
              <SelectValue placeholder="Select parameter" />
            </SelectTrigger>
            <SelectContent>
              {evolutionData?.parameters.map(param => (
                <SelectItem key={param} value={param}>
                  {param}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          {selectedParam && evolutionData && (
            <>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={evolutionData.evolution[selectedParam]}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="period" />
                  <YAxis />
                  <Tooltip />
                  <Line
                    type="monotone"
                    dataKey="value"
                    stroke="#8884d8"
                    strokeWidth={2}
                    dot={{ r: 4 }}
                  />
                </LineChart>
              </ResponsiveContainer>

              <ParameterStabilityAnalysis
                parameterName={selectedParam}
                evolution={evolutionData.evolution[selectedParam]}
              />
            </>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

// Parameter stability analysis
function ParameterStabilityAnalysis({ parameterName, evolution }) {
  const stats = useMemo(() => {
    const values = evolution.map(e => e.value);
    const mean = values.reduce((a, b) => a + b) / values.length;
    const variance = values.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / values.length;
    const stdDev = Math.sqrt(variance);
    const cv = stdDev / mean; // Coefficient of variation

    // Calculate trend
    const trend = calculateTrend(values);

    // Calculate regime changes
    const regimeChanges = detectRegimeChanges(values);

    return {
      mean,
      stdDev,
      cv,
      trend,
      regimeChanges,
      stability: 1 - cv // Higher is more stable
    };
  }, [evolution]);

  return (
    <div className="grid grid-cols-2 gap-4">
      <MetricCard
        title="Average Value"
        value={stats.mean.toFixed(3)}
        description="Mean parameter value"
      />
      <MetricCard
        title="Stability Score"
        value={`${(stats.stability * 100).toFixed(1)}%`}
        description="Parameter consistency"
        trend={stats.stability > 0.8 ? 'up' : 'down'}
      />
      <MetricCard
        title="Trend"
        value={stats.trend > 0 ? 'Increasing' : stats.trend < 0 ? 'Decreasing' : 'Stable'}
        description="Parameter direction"
      />
      <MetricCard
        title="Regime Changes"
        value={stats.regimeChanges}
        description="Significant shifts"
      />
    </div>
  );
}
```

### Walk-Forward Analysis Report
```typescript
// components/optimization/WalkForwardReport.tsx
export function WalkForwardReport({ executionId }: { executionId: string }) {
  const [report, setReport] = useState<WalkForwardReport>();
  const [exportFormat, setExportFormat] = useState<'pdf' | 'excel'>('pdf');

  useEffect(() => {
    generateWalkForwardReport(executionId).then(setReport);
  }, [executionId]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Walk-Forward Analysis Report</CardTitle>
        <div className="flex gap-2">
          <Select value={exportFormat} onValueChange={setExportFormat}>
            <SelectItem value="pdf">PDF</SelectItem>
            <SelectItem value="excel">Excel</SelectItem>
          </Select>
          <Button onClick={() => exportReport(report, exportFormat)}>
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {/* Executive Summary */}
          <div>
            <h3 className="text-lg font-medium mb-3">Executive Summary</h3>
            <div className="prose prose-sm">
              <p>{report?.summary.description}</p>
              <ul>
                <li>Total Periods: {report?.summary.totalPeriods}</li>
                <li>Average Efficiency: {(report?.summary.avgEfficiency * 100).toFixed(1)}%</li>
                <li>Consistency: {(report?.summary.consistency * 100).toFixed(1)}%</li>
                <li>Recommendation: {report?.summary.recommendation}</li>
              </ul>
            </div>
          </div>

          {/* Period-by-period results */}
          <div>
            <h3 className="text-lg font-medium mb-3">Period Results</h3>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Period</TableHead>
                  <TableHead>Date Range</TableHead>
                  <TableHead>In-Sample</TableHead>
                  <TableHead>Out-Sample</TableHead>
                  <TableHead>Efficiency</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {report?.periodResults.map((period, idx) => (
                  <TableRow key={period.id}>
                    <TableCell>{idx + 1}</TableCell>
                    <TableCell>{formatDateRange(period.dateRange)}</TableCell>
                    <TableCell>{period.inSampleSharpe.toFixed(2)}</TableCell>
                    <TableCell>{period.outSampleSharpe.toFixed(2)}</TableCell>
                    <TableCell>
                      <Badge variant={period.efficiency > 0.7 ? 'success' : 'warning'}>
                        {(period.efficiency * 100).toFixed(0)}%
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {period.efficiency > 0.7 ? '✓ Robust' : '⚠ Overfit'}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>

          {/* Parameter stability */}
          <div>
            <h3 className="text-lg font-medium mb-3">Parameter Stability</h3>
            <ParameterStabilityTable parameters={report?.parameterStability} />
          </div>

          {/* Recommendations */}
          <div>
            <h3 className="text-lg font-medium mb-3">Recommendations</h3>
            <RecommendationsList recommendations={report?.recommendations} />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
```

### Backend Walk-Forward Engine
```python
# api/optimization/walk_forward_engine.py
class WalkForwardEngine:
    def __init__(self, config: WalkForwardConfig):
        self.config = config
        self.results = {}

    async def run(self) -> AsyncIterator[WalkForwardUpdate]:
        """Execute walk-forward analysis"""
        for idx, period in enumerate(self.config.periods):
            yield WalkForwardUpdate(
                type='period_start',
                periodIndex=idx,
                periodId=period.id
            )

            # Run optimization on in-sample period
            optimal_params = await self._optimize_period(
                period.in_sample_start,
                period.in_sample_end
            )

            # Test on out-of-sample period
            in_sample_perf = await self._test_parameters(
                optimal_params,
                period.in_sample_start,
                period.in_sample_end
            )

            out_sample_perf = await self._test_parameters(
                optimal_params,
                period.out_sample_start,
                period.out_sample_end
            )

            period_result = PeriodResults(
                periodId=period.id,
                optimalParameters=optimal_params,
                inSamplePerformance=in_sample_perf,
                outSamplePerformance=out_sample_perf,
                efficiency=out_sample_perf.sharpe / in_sample_perf.sharpe
                    if in_sample_perf.sharpe > 0 else 0
            )

            self.results[period.id] = period_result

            yield WalkForwardUpdate(
                type='period_complete',
                periodId=period.id,
                results=period_result
            )

        # Generate final analysis
        analysis = self._analyze_results()
        yield WalkForwardUpdate(
            type='analysis_complete',
            analysis=analysis
        )

    async def _optimize_period(self, start_date: date, end_date: date) -> Dict:
        """Run optimization for a specific period"""
        # Create temporary optimization config for this period
        period_config = self.config.optimization_config.copy()
        period_config.data_config.start_date = start_date
        period_config.data_config.end_date = end_date

        # Run grid search
        optimizer = GridSearchEngine(period_config)
        best_result = None

        async for update in optimizer.run():
            if update.type == 'result' and (
                best_result is None or
                update.result.sharpe > best_result.sharpe
            ):
                best_result = update.result

        return best_result.parameters if best_result else {}
```

## UI/UX Considerations
- Visual timeline for period configuration
- Real-time progress tracking
- Clear efficiency indicators
- Parameter evolution visualization
- Comparative analysis tools
- Export functionality for reports

## Testing Requirements
1. Period generation accuracy
2. Walk-forward calculation correctness
3. Parameter evolution tracking
4. Efficiency metric calculations
5. Report generation completeness
6. Large dataset performance

## Dependencies
- UI_001: Next.js foundation
- UI_032: Grid search setup
- UI_033: Optimization execution
- UI_034: Optimization results

## Story Points: 21

## Priority: Medium

## Implementation Notes
- Cache optimization results for each period
- Implement parallel period processing where possible
- Add support for custom efficiency metrics
- Consider adaptive period sizing based on market volatility
