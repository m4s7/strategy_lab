# UI_025: Risk Metrics Visualization

## Story
As a trader, I want comprehensive risk metrics visualization including VaR, CVaR, drawdown analysis, and stress testing so that I can understand and manage the risk profile of my strategies.

## Acceptance Criteria
1. Calculate and display Value at Risk (VaR) at multiple confidence levels
2. Show Conditional VaR (CVaR) / Expected Shortfall
3. Visualize drawdown periods and recovery times
4. Provide Monte Carlo simulations for risk assessment
5. Enable stress testing with custom scenarios
6. Display risk-adjusted performance metrics
7. Show rolling risk metrics over time
8. Generate risk reports with recommendations

## Technical Requirements

### Frontend Components
```typescript
// components/risk/RiskDashboard.tsx
interface RiskMetrics {
  var95: number;
  var99: number;
  cvar95: number;
  cvar99: number;
  maxDrawdown: number;
  avgDrawdown: number;
  maxDrawdownDuration: number;
  calmarRatio: number;
  sortinoRatio: number;
  omega: number;
  tailRatio: number;
}

export function RiskDashboard({ strategyId }: { strategyId: string }) {
  const [metrics, setMetrics] = useState<RiskMetrics>();
  const [timeframe, setTimeframe] = useState<'1M' | '3M' | '6M' | '1Y'>('1Y');
  const [riskView, setRiskView] = useState<'overview' | 'var' | 'drawdown' | 'stress'>('overview');

  return (
    <div className="risk-dashboard">
      <RiskSummaryCards metrics={metrics} />

      <Tabs value={riskView} onValueChange={setRiskView}>
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="var">VaR/CVaR</TabsTrigger>
          <TabsTrigger value="drawdown">Drawdowns</TabsTrigger>
          <TabsTrigger value="stress">Stress Testing</TabsTrigger>
        </TabsList>

        <TabsContent value="overview">
          <RiskOverview metrics={metrics} timeframe={timeframe} />
        </TabsContent>

        <TabsContent value="var">
          <ValueAtRiskAnalysis strategyId={strategyId} />
        </TabsContent>

        <TabsContent value="drawdown">
          <DrawdownAnalysis strategyId={strategyId} />
        </TabsContent>

        <TabsContent value="stress">
          <StressTesting strategyId={strategyId} />
        </TabsContent>
      </Tabs>

      <RiskRecommendations metrics={metrics} />
    </div>
  );
}
```

### Value at Risk (VaR) Analysis
```typescript
// components/risk/ValueAtRiskAnalysis.tsx
export function ValueAtRiskAnalysis({ strategyId }: { strategyId: string }) {
  const [method, setMethod] = useState<'historical' | 'parametric' | 'montecarlo'>('historical');
  const [confidenceLevels] = useState([90, 95, 99]);
  const [varResults, setVarResults] = useState<VaRResults>();

  useEffect(() => {
    calculateVaR(strategyId, method).then(setVarResults);
  }, [strategyId, method]);

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Value at Risk Analysis</CardTitle>
          <Select value={method} onValueChange={setMethod}>
            <SelectItem value="historical">Historical VaR</SelectItem>
            <SelectItem value="parametric">Parametric VaR</SelectItem>
            <SelectItem value="montecarlo">Monte Carlo VaR</SelectItem>
          </Select>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4">
            {confidenceLevels.map(level => (
              <VaRCard
                key={level}
                confidence={level}
                var={varResults?.var[level]}
                cvar={varResults?.cvar[level]}
              />
            ))}
          </div>

          <VaRDistributionChart
            returns={varResults?.returns}
            varLevels={varResults?.var}
            method={method}
          />

          <VaRBacktest
            actual={varResults?.actualLosses}
            predicted={varResults?.predictedVaR}
          />
        </CardContent>
      </Card>
    </div>
  );
}

// VaR distribution visualization
function VaRDistributionChart({ returns, varLevels, method }) {
  const chartData = useMemo(() => {
    if (!returns) return [];

    // Create histogram bins
    const bins = d3.histogram()
      .domain(d3.extent(returns))
      .thresholds(50)(returns);

    return bins.map(bin => ({
      x: (bin.x0 + bin.x1) / 2,
      y: bin.length,
      range: [bin.x0, bin.x1]
    }));
  }, [returns]);

  return (
    <div className="mt-6">
      <h4 className="text-sm font-medium mb-2">Return Distribution</h4>
      <ResponsiveContainer width="100%" height={300}>
        <ComposedChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="x" />
          <YAxis />
          <Tooltip />
          <Bar dataKey="y" fill="#8884d8" />

          {/* VaR lines */}
          {Object.entries(varLevels || {}).map(([level, value]) => (
            <ReferenceLine
              key={level}
              x={value}
              stroke="#ff0000"
              strokeDasharray="5 5"
              label={`VaR ${level}%`}
            />
          ))}
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
```

### VaR Calculation Backend
```python
# api/risk/var_calculator.py
import numpy as np
from scipy import stats
from typing import Dict, List, Tuple

class VaRCalculator:
    @staticmethod
    def historical_var(returns: np.ndarray, confidence_levels: List[float]) -> Dict[float, float]:
        """Calculate historical VaR using percentile method"""
        var_results = {}
        for confidence in confidence_levels:
            var_results[confidence] = np.percentile(returns, 100 - confidence)
        return var_results

    @staticmethod
    def parametric_var(returns: np.ndarray, confidence_levels: List[float]) -> Dict[float, float]:
        """Calculate parametric VaR assuming normal distribution"""
        mean = np.mean(returns)
        std = np.std(returns)
        var_results = {}

        for confidence in confidence_levels:
            z_score = stats.norm.ppf(1 - confidence/100)
            var_results[confidence] = mean + z_score * std

        return var_results

    @staticmethod
    def monte_carlo_var(returns: np.ndarray, confidence_levels: List[float],
                       n_simulations: int = 10000) -> Dict[float, float]:
        """Calculate VaR using Monte Carlo simulation"""
        mean = np.mean(returns)
        std = np.std(returns)

        # Generate simulated returns
        simulated_returns = np.random.normal(mean, std, n_simulations)

        var_results = {}
        for confidence in confidence_levels:
            var_results[confidence] = np.percentile(simulated_returns, 100 - confidence)

        return var_results

    @staticmethod
    def calculate_cvar(returns: np.ndarray, var_levels: Dict[float, float]) -> Dict[float, float]:
        """Calculate Conditional VaR (Expected Shortfall)"""
        cvar_results = {}

        for confidence, var in var_levels.items():
            # Get returns worse than VaR
            tail_returns = returns[returns <= var]
            cvar_results[confidence] = np.mean(tail_returns) if len(tail_returns) > 0 else var

        return cvar_results

# API endpoint
@router.get("/risk/var/{strategy_id}")
async def calculate_var(
    strategy_id: str,
    method: str = "historical",
    timeframe: str = "1Y"
):
    returns = await get_strategy_returns(strategy_id, timeframe)
    confidence_levels = [90, 95, 99]

    calculator = VaRCalculator()

    if method == "historical":
        var_results = calculator.historical_var(returns, confidence_levels)
    elif method == "parametric":
        var_results = calculator.parametric_var(returns, confidence_levels)
    else:  # monte_carlo
        var_results = calculator.monte_carlo_var(returns, confidence_levels)

    cvar_results = calculator.calculate_cvar(returns, var_results)

    # Backtesting VaR
    backtest_results = backtest_var(returns, var_results[95], window=252)

    return {
        "var": var_results,
        "cvar": cvar_results,
        "returns": returns.tolist(),
        "backtest": backtest_results,
        "method": method
    }
```

### Drawdown Analysis
```typescript
// components/risk/DrawdownAnalysis.tsx
export function DrawdownAnalysis({ strategyId }: { strategyId: string }) {
  const [drawdowns, setDrawdowns] = useState<DrawdownPeriod[]>([]);
  const [selectedDrawdown, setSelectedDrawdown] = useState<DrawdownPeriod>();

  return (
    <div className="space-y-6">
      <DrawdownChart
        drawdowns={drawdowns}
        onDrawdownSelect={setSelectedDrawdown}
      />

      <div className="grid grid-cols-2 gap-6">
        <DrawdownTable
          drawdowns={drawdowns}
          selectedId={selectedDrawdown?.id}
          onSelect={setSelectedDrawdown}
        />

        {selectedDrawdown && (
          <DrawdownDetails drawdown={selectedDrawdown} />
        )}
      </div>

      <DrawdownStatistics drawdowns={drawdowns} />
    </div>
  );
}

// Drawdown visualization
function DrawdownChart({ drawdowns, onDrawdownSelect }) {
  const chartData = useMemo(() => {
    // Convert drawdown periods to chart data
    return drawdowns.flatMap(dd => [
      { date: dd.start, value: 0, type: 'start' },
      { date: dd.trough, value: dd.maxDrawdown, type: 'trough' },
      { date: dd.end, value: 0, type: 'recovery' }
    ]);
  }, [drawdowns]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Drawdown Periods</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={400}>
          <AreaChart data={chartData}>
            <defs>
              <linearGradient id="drawdownGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#ef4444" stopOpacity={0.8}/>
                <stop offset="95%" stopColor="#ef4444" stopOpacity={0.2}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip />
            <Area
              type="monotone"
              dataKey="value"
              stroke="#ef4444"
              fillOpacity={1}
              fill="url(#drawdownGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>

        <DrawdownTimeline
          drawdowns={drawdowns}
          onSelect={onDrawdownSelect}
        />
      </CardContent>
    </Card>
  );
}

// Drawdown statistics
function DrawdownStatistics({ drawdowns }) {
  const stats = useMemo(() => {
    if (!drawdowns.length) return null;

    const maxDrawdown = Math.max(...drawdowns.map(d => Math.abs(d.maxDrawdown)));
    const avgDrawdown = drawdowns.reduce((sum, d) => sum + Math.abs(d.maxDrawdown), 0) / drawdowns.length;
    const avgDuration = drawdowns.reduce((sum, d) => sum + d.duration, 0) / drawdowns.length;
    const avgRecovery = drawdowns
      .filter(d => d.recovered)
      .reduce((sum, d) => sum + d.recoveryTime, 0) / drawdowns.filter(d => d.recovered).length;

    return {
      count: drawdowns.length,
      maxDrawdown,
      avgDrawdown,
      avgDuration,
      avgRecovery,
      currentDrawdown: drawdowns.find(d => !d.recovered)?.maxDrawdown || 0
    };
  }, [drawdowns]);

  return (
    <div className="grid grid-cols-3 gap-4">
      <StatCard
        title="Max Drawdown"
        value={`${(stats.maxDrawdown * 100).toFixed(2)}%`}
        description="Largest peak-to-trough decline"
      />
      <StatCard
        title="Average Drawdown"
        value={`${(stats.avgDrawdown * 100).toFixed(2)}%`}
        description="Mean of all drawdowns"
      />
      <StatCard
        title="Avg Recovery Time"
        value={`${stats.avgRecovery.toFixed(0)} days`}
        description="Time to recover from drawdown"
      />
    </div>
  );
}
```

### Stress Testing
```typescript
// components/risk/StressTesting.tsx
export function StressTesting({ strategyId }: { strategyId: string }) {
  const [scenarios, setScenarios] = useState<StressScenario[]>([
    { name: 'Market Crash', marketDrop: -20, volatilityMultiplier: 3 },
    { name: 'Flash Crash', marketDrop: -10, volatilityMultiplier: 5, duration: 1 },
    { name: 'Prolonged Bear', marketDrop: -30, volatilityMultiplier: 2, duration: 90 },
    { name: 'Custom', marketDrop: 0, volatilityMultiplier: 1 }
  ]);

  const [results, setResults] = useState<StressTestResults>();
  const [selectedScenario, setSelectedScenario] = useState(scenarios[0]);

  const runStressTest = async () => {
    const result = await performStressTest(strategyId, selectedScenario);
    setResults(result);
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Stress Test Scenarios</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-6">
            <div>
              <ScenarioSelector
                scenarios={scenarios}
                selected={selectedScenario}
                onChange={setSelectedScenario}
              />

              {selectedScenario.name === 'Custom' && (
                <CustomScenarioForm
                  scenario={selectedScenario}
                  onChange={setSelectedScenario}
                />
              )}

              <Button onClick={runStressTest} className="mt-4">
                Run Stress Test
              </Button>
            </div>

            <div>
              {results && (
                <StressTestResults
                  scenario={selectedScenario}
                  results={results}
                />
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      <HistoricalStressEvents strategyId={strategyId} />
    </div>
  );
}

// Historical stress events
function HistoricalStressEvents({ strategyId }) {
  const events = [
    { name: '2008 Financial Crisis', start: '2008-09-15', end: '2009-03-09' },
    { name: 'COVID-19 Crash', start: '2020-02-20', end: '2020-03-23' },
    { name: 'Volmageddon', start: '2018-02-02', end: '2018-02-09' },
    { name: 'China Devaluation', start: '2015-08-11', end: '2015-08-26' }
  ];

  const [eventResults, setEventResults] = useState<Map<string, EventResult>>();

  useEffect(() => {
    analyzeHistoricalEvents(strategyId, events).then(setEventResults);
  }, [strategyId]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Historical Stress Events</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Event</TableHead>
              <TableHead>Period</TableHead>
              <TableHead>Market Return</TableHead>
              <TableHead>Strategy Return</TableHead>
              <TableHead>Relative Performance</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {events.map(event => {
              const result = eventResults?.get(event.name);
              return (
                <TableRow key={event.name}>
                  <TableCell>{event.name}</TableCell>
                  <TableCell>{formatDateRange(event.start, event.end)}</TableCell>
                  <TableCell className="text-red-600">
                    {result ? `${(result.marketReturn * 100).toFixed(2)}%` : '-'}
                  </TableCell>
                  <TableCell className={result?.strategyReturn >= 0 ? 'text-green-600' : 'text-red-600'}>
                    {result ? `${(result.strategyReturn * 100).toFixed(2)}%` : '-'}
                  </TableCell>
                  <TableCell>
                    {result ? `${((result.strategyReturn - result.marketReturn) * 100).toFixed(2)}%` : '-'}
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
```

### Monte Carlo Simulation
```typescript
// lib/risk/monte-carlo.ts
export class MonteCarloSimulator {
  constructor(
    private returns: number[],
    private initialCapital: number = 100000
  ) {}

  simulate(
    numSimulations: number = 1000,
    numPeriods: number = 252
  ): SimulationResults {
    const results: number[][] = [];

    for (let i = 0; i < numSimulations; i++) {
      const path = this.generatePath(numPeriods);
      results.push(path);
    }

    return this.analyzeResults(results);
  }

  private generatePath(numPeriods: number): number[] {
    const path = [this.initialCapital];
    let currentValue = this.initialCapital;

    for (let i = 1; i <= numPeriods; i++) {
      // Sample from historical returns
      const randomReturn = this.returns[Math.floor(Math.random() * this.returns.length)];
      currentValue *= (1 + randomReturn);
      path.push(currentValue);
    }

    return path;
  }

  private analyzeResults(simulations: number[][]): SimulationResults {
    const finalValues = simulations.map(path => path[path.length - 1]);
    const percentiles = [5, 25, 50, 75, 95];

    const percentilesResults = {};
    percentiles.forEach(p => {
      percentilesResults[p] = this.percentile(finalValues, p);
    });

    // Calculate probability of loss
    const probLoss = finalValues.filter(v => v < this.initialCapital).length / simulations.length;

    // Calculate expected shortfall
    const losses = finalValues
      .filter(v => v < this.initialCapital)
      .map(v => (this.initialCapital - v) / this.initialCapital);
    const expectedShortfall = losses.length > 0 ?
      losses.reduce((a, b) => a + b) / losses.length : 0;

    return {
      simulations,
      percentiles: percentilesResults,
      probabilityOfLoss: probLoss,
      expectedShortfall,
      bestCase: Math.max(...finalValues),
      worstCase: Math.min(...finalValues),
      expected: finalValues.reduce((a, b) => a + b) / finalValues.length
    };
  }
}
```

### Risk Recommendations
```typescript
// components/risk/RiskRecommendations.tsx
export function RiskRecommendations({ metrics }: { metrics: RiskMetrics }) {
  const recommendations = useMemo(() => {
    const recs: Recommendation[] = [];

    // Analyze metrics and generate recommendations
    if (metrics.maxDrawdown > 0.2) {
      recs.push({
        severity: 'high',
        title: 'High Maximum Drawdown',
        description: `Your maximum drawdown of ${(metrics.maxDrawdown * 100).toFixed(1)}% exceeds recommended levels.`,
        action: 'Consider implementing stricter stop-loss rules or reducing position sizes.'
      });
    }

    if (metrics.tailRatio < 1) {
      recs.push({
        severity: 'medium',
        title: 'Negative Tail Ratio',
        description: 'Your strategy has larger left tail risk than right tail potential.',
        action: 'Review risk management rules and consider asymmetric position sizing.'
      });
    }

    if (metrics.calmarRatio < 1) {
      recs.push({
        severity: 'medium',
        title: 'Low Calmar Ratio',
        description: 'Return relative to maximum drawdown is suboptimal.',
        action: 'Focus on improving risk-adjusted returns or reducing drawdown severity.'
      });
    }

    return recs;
  }, [metrics]);

  if (!recommendations.length) {
    return (
      <Alert>
        <CheckCircle className="h-4 w-4" />
        <AlertTitle>Risk Profile Acceptable</AlertTitle>
        <AlertDescription>
          Your strategy's risk metrics are within acceptable parameters.
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">Risk Management Recommendations</h3>
      {recommendations.map((rec, idx) => (
        <Alert key={idx} variant={rec.severity === 'high' ? 'destructive' : 'default'}>
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>{rec.title}</AlertTitle>
          <AlertDescription>
            <p>{rec.description}</p>
            <p className="mt-2 font-medium">Recommended Action: {rec.action}</p>
          </AlertDescription>
        </Alert>
      ))}
    </div>
  );
}
```

## UI/UX Considerations
- Use color coding for risk levels (green/yellow/red)
- Interactive charts with zoom and pan
- Clear explanations of complex metrics
- Tooltips with calculation details
- Progressive disclosure for advanced features
- Export functionality for reports

## Testing Requirements
1. VaR calculation accuracy across methods
2. Drawdown detection algorithm verification
3. Monte Carlo simulation convergence
4. Stress test scenario validation
5. Risk metric calculations
6. Performance with large datasets

## Dependencies
- UI_001: Next.js foundation
- UI_003: Database setup
- UI_015: Basic results visualization
- UI_021: Interactive performance charts

## Story Points: 21

## Priority: High

## Implementation Notes
- Consider using QuantLib or similar library for risk calculations
- Implement caching for expensive calculations
- Use Web Workers for Monte Carlo simulations
- Add real-time risk monitoring capabilities
