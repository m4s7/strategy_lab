# UI_034: Optimization Results Analysis

## Story
As a trader, I want to analyze optimization results with advanced visualizations, parameter sensitivity analysis, and robustness testing so that I can select the best parameters with confidence.

## Acceptance Criteria
1. Display comprehensive optimization results summary
2. Visualize parameter sensitivity and interactions
3. Perform robustness analysis on top parameters
4. Show parameter stability across market conditions
5. Compare multiple optimization runs
6. Export detailed optimization reports
7. Identify parameter overfitting risks
8. Provide parameter selection recommendations

## Technical Requirements

### Frontend Components
```typescript
// components/optimization/OptimizationResults.tsx
interface OptimizationAnalysis {
  runId: string;
  summary: OptimizationSummary;
  topResults: OptimizationResult[];
  parameterAnalysis: ParameterAnalysis;
  robustnessTests: RobustnessTestResults;
  recommendations: ParameterRecommendation[];
}

export function OptimizationResults({ runId }: { runId: string }) {
  const [analysis, setAnalysis] = useState<OptimizationAnalysis>();
  const [selectedResult, setSelectedResult] = useState<OptimizationResult>();
  const [viewMode, setViewMode] = useState<'overview' | 'sensitivity' | 'robustness' | 'comparison'>('overview');

  useEffect(() => {
    loadOptimizationAnalysis(runId).then(setAnalysis);
  }, [runId]);

  return (
    <div className="optimization-results">
      <OptimizationSummaryHeader summary={analysis?.summary} />

      <Tabs value={viewMode} onValueChange={setViewMode}>
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="sensitivity">Sensitivity</TabsTrigger>
          <TabsTrigger value="robustness">Robustness</TabsTrigger>
          <TabsTrigger value="comparison">Comparison</TabsTrigger>
        </TabsList>

        <TabsContent value="overview">
          <ResultsOverview
            analysis={analysis}
            onResultSelect={setSelectedResult}
          />
        </TabsContent>

        <TabsContent value="sensitivity">
          <ParameterSensitivityAnalysis
            results={analysis?.topResults}
            parameterAnalysis={analysis?.parameterAnalysis}
          />
        </TabsContent>

        <TabsContent value="robustness">
          <RobustnessAnalysis
            results={analysis?.topResults}
            robustnessTests={analysis?.robustnessTests}
          />
        </TabsContent>

        <TabsContent value="comparison">
          <ResultComparison
            results={analysis?.topResults}
            selectedResult={selectedResult}
          />
        </TabsContent>
      </Tabs>

      <ParameterRecommendations recommendations={analysis?.recommendations} />
    </div>
  );
}
```

### Results Overview
```typescript
// components/optimization/ResultsOverview.tsx
export function ResultsOverview({
  analysis,
  onResultSelect
}: ResultsOverviewProps) {
  const [sortMetric, setSortMetric] = useState<string>('sharpe');
  const [filterCriteria, setFilterCriteria] = useState<FilterCriteria>({
    minSharpe: 1.0,
    maxDrawdown: 0.2,
    minTrades: 100
  });

  const filteredResults = useMemo(() => {
    if (!analysis?.topResults) return [];

    return analysis.topResults
      .filter(r =>
        r.sharpe >= filterCriteria.minSharpe &&
        r.maxDrawdown <= filterCriteria.maxDrawdown &&
        r.totalTrades >= filterCriteria.minTrades
      )
      .sort((a, b) => b[sortMetric] - a[sortMetric]);
  }, [analysis, filterCriteria, sortMetric]);

  return (
    <div className="space-y-6">
      {/* Results summary cards */}
      <div className="grid grid-cols-4 gap-4">
        <SummaryCard
          title="Total Combinations"
          value={analysis?.summary.totalCombinations.toLocaleString()}
          icon={Grid}
        />
        <SummaryCard
          title="Best Sharpe"
          value={analysis?.summary.bestSharpe.toFixed(2)}
          icon={TrendingUp}
          trend="up"
        />
        <SummaryCard
          title="Avg Improvement"
          value={`${(analysis?.summary.avgImprovement * 100).toFixed(1)}%`}
          icon={BarChart}
        />
        <SummaryCard
          title="Computation Time"
          value={formatDuration(analysis?.summary.totalTime)}
          icon={Clock}
        />
      </div>

      {/* Parameter distribution */}
      <Card>
        <CardHeader>
          <CardTitle>Parameter Distribution in Top Results</CardTitle>
        </CardHeader>
        <CardContent>
          <ParameterDistributionChart
            results={analysis?.topResults.slice(0, 50)}
          />
        </CardContent>
      </Card>

      {/* Results table */}
      <Card>
        <CardHeader>
          <CardTitle>Top Parameter Sets</CardTitle>
          <ResultsFilter
            criteria={filterCriteria}
            onChange={setFilterCriteria}
          />
        </CardHeader>
        <CardContent>
          <ResultsDataTable
            results={filteredResults}
            onSelect={onResultSelect}
            sortMetric={sortMetric}
            onSortChange={setSortMetric}
          />
        </CardContent>
      </Card>

      {/* Performance scatter plot */}
      <PerformanceScatterPlot
        results={analysis?.topResults}
        xMetric="maxDrawdown"
        yMetric="sharpe"
        colorMetric="totalReturn"
      />
    </div>
  );
}

// Parameter distribution visualization
function ParameterDistributionChart({ results }) {
  const distributions = useMemo(() => {
    if (!results || results.length === 0) return [];

    const params = Object.keys(results[0].parameters);

    return params.map(param => {
      const values = results.map(r => r.parameters[param]);
      const uniqueValues = [...new Set(values)];

      const distribution = uniqueValues.map(val => ({
        value: val,
        count: values.filter(v => v === val).length,
        avgSharpe: results
          .filter(r => r.parameters[param] === val)
          .reduce((sum, r) => sum + r.sharpe, 0) /
          values.filter(v => v === val).length
      }));

      return {
        parameter: param,
        distribution,
        entropy: calculateEntropy(distribution.map(d => d.count))
      };
    });
  }, [results]);

  return (
    <div className="space-y-4">
      {distributions.map(dist => (
        <div key={dist.parameter}>
          <div className="flex justify-between items-center mb-2">
            <Label>{dist.parameter}</Label>
            <span className="text-sm text-muted-foreground">
              Entropy: {dist.entropy.toFixed(2)}
            </span>
          </div>
          <ResponsiveContainer width="100%" height={60}>
            <BarChart data={dist.distribution}>
              <XAxis dataKey="value" />
              <YAxis hide />
              <Tooltip />
              <Bar dataKey="count" fill="#8884d8" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      ))}
    </div>
  );
}
```

### Parameter Sensitivity Analysis
```typescript
// components/optimization/ParameterSensitivityAnalysis.tsx
export function ParameterSensitivityAnalysis({
  results,
  parameterAnalysis
}: SensitivityAnalysisProps) {
  const [targetMetric, setTargetMetric] = useState<string>('sharpe');
  const [analysisType, setAnalysisType] = useState<'main' | 'interaction'>('main');

  const sensitivityData = useMemo(() => {
    if (!results || !parameterAnalysis) return null;

    if (analysisType === 'main') {
      return calculateMainEffects(results, targetMetric);
    } else {
      return calculateInteractionEffects(results, targetMetric);
    }
  }, [results, parameterAnalysis, targetMetric, analysisType]);

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Parameter Sensitivity Analysis</CardTitle>
          <div className="flex gap-4">
            <Select value={targetMetric} onValueChange={setTargetMetric}>
              <SelectItem value="sharpe">Sharpe Ratio</SelectItem>
              <SelectItem value="totalReturn">Total Return</SelectItem>
              <SelectItem value="maxDrawdown">Max Drawdown</SelectItem>
              <SelectItem value="winRate">Win Rate</SelectItem>
            </Select>

            <RadioGroup value={analysisType} onValueChange={setAnalysisType}>
              <RadioGroupItem value="main">Main Effects</RadioGroupItem>
              <RadioGroupItem value="interaction">Interactions</RadioGroupItem>
            </RadioGroup>
          </div>
        </CardHeader>
        <CardContent>
          {analysisType === 'main' ? (
            <MainEffectsChart data={sensitivityData} metric={targetMetric} />
          ) : (
            <InteractionHeatmap data={sensitivityData} metric={targetMetric} />
          )}
        </CardContent>
      </Card>

      <ParameterImportanceRanking
        analysis={parameterAnalysis}
        metric={targetMetric}
      />

      <ParameterStabilityAnalysis
        results={results}
        metric={targetMetric}
      />
    </div>
  );
}

// Main effects visualization
function MainEffectsChart({ data, metric }) {
  return (
    <div className="space-y-4">
      {data.parameters.map(param => (
        <div key={param.name}>
          <h4 className="text-sm font-medium mb-2">{param.name}</h4>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={param.effects}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="value" />
              <YAxis />
              <Tooltip />
              <Line
                type="monotone"
                dataKey="avgMetric"
                stroke="#8884d8"
                strokeWidth={2}
              />
              <Line
                type="monotone"
                dataKey="confidence95Upper"
                stroke="#82ca9d"
                strokeDasharray="5 5"
              />
              <Line
                type="monotone"
                dataKey="confidence95Lower"
                stroke="#82ca9d"
                strokeDasharray="5 5"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      ))}
    </div>
  );
}

// Parameter importance ranking
function ParameterImportanceRanking({ analysis, metric }) {
  const importanceScores = useMemo(() => {
    if (!analysis) return [];

    return analysis.parameters.map(param => ({
      name: param.name,
      importance: param.importance[metric],
      variance: param.varianceExplained[metric],
      correlation: param.correlation[metric]
    }))
    .sort((a, b) => b.importance - a.importance);
  }, [analysis, metric]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Parameter Importance</CardTitle>
        <CardDescription>
          Relative importance for {metric}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {importanceScores.map((param, idx) => (
            <div key={param.name} className="flex items-center gap-4">
              <span className="text-sm font-medium w-32">{param.name}</span>
              <div className="flex-1">
                <Progress value={param.importance * 100} />
              </div>
              <span className="text-sm text-muted-foreground">
                {(param.importance * 100).toFixed(1)}%
              </span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
```

### Robustness Analysis
```typescript
// components/optimization/RobustnessAnalysis.tsx
export function RobustnessAnalysis({
  results,
  robustnessTests
}: RobustnessAnalysisProps) {
  const [selectedTest, setSelectedTest] = useState<'walk-forward' | 'monte-carlo' | 'stress'>('walk-forward');
  const [selectedParams, setSelectedParams] = useState<string[]>([]);

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Robustness Testing</CardTitle>
          <Tabs value={selectedTest} onValueChange={setSelectedTest}>
            <TabsList>
              <TabsTrigger value="walk-forward">Walk-Forward</TabsTrigger>
              <TabsTrigger value="monte-carlo">Monte Carlo</TabsTrigger>
              <TabsTrigger value="stress">Stress Test</TabsTrigger>
            </TabsList>
          </Tabs>
        </CardHeader>
        <CardContent>
          {selectedTest === 'walk-forward' && (
            <WalkForwardAnalysis
              results={results}
              tests={robustnessTests?.walkForward}
            />
          )}

          {selectedTest === 'monte-carlo' && (
            <MonteCarloRobustness
              results={results}
              tests={robustnessTests?.monteCarlo}
            />
          )}

          {selectedTest === 'stress' && (
            <StressTestRobustness
              results={results}
              tests={robustnessTests?.stressTests}
            />
          )}
        </CardContent>
      </Card>

      <ParameterStabilityMatrix
        results={results}
        selectedParams={selectedParams}
        onParamSelect={setSelectedParams}
      />
    </div>
  );
}

// Walk-forward analysis
function WalkForwardAnalysis({ results, tests }) {
  const chartData = useMemo(() => {
    if (!tests) return [];

    return tests.periods.map(period => ({
      period: period.name,
      inSample: period.inSamplePerformance,
      outOfSample: period.outOfSamplePerformance,
      efficiency: period.outOfSamplePerformance / period.inSamplePerformance
    }));
  }, [tests]);

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-3 gap-4">
        <MetricCard
          title="Average Efficiency"
          value={`${(tests?.avgEfficiency * 100).toFixed(1)}%`}
          description="Out-of-sample vs In-sample"
        />
        <MetricCard
          title="Consistency"
          value={`${(tests?.consistency * 100).toFixed(1)}%`}
          description="Periods with positive OOS"
        />
        <MetricCard
          title="Stability Score"
          value={tests?.stabilityScore.toFixed(2)}
          description="Parameter stability metric"
        />
      </div>

      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="period" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Bar dataKey="inSample" fill="#8884d8" name="In-Sample" />
          <Bar dataKey="outOfSample" fill="#82ca9d" name="Out-of-Sample" />
        </BarChart>
      </ResponsiveContainer>

      <Alert>
        <AlertCircle className="h-4 w-4" />
        <AlertTitle>Walk-Forward Efficiency</AlertTitle>
        <AlertDescription>
          Parameters showing efficiency above 70% are considered robust.
          Current average: {(tests?.avgEfficiency * 100).toFixed(1)}%
        </AlertDescription>
      </Alert>
    </div>
  );
}

// Parameter stability matrix
function ParameterStabilityMatrix({ results, selectedParams, onParamSelect }) {
  const stabilityData = useMemo(() => {
    if (!results || results.length < 10) return null;

    // Calculate parameter stability across different market regimes
    const params = Object.keys(results[0].parameters);

    return params.map(param => {
      const values = results.map(r => r.parameters[param]);
      const performance = results.map(r => r.sharpe);

      // Split into quintiles by performance
      const quintiles = Array(5).fill(null).map((_, i) => {
        const start = Math.floor(i * results.length / 5);
        const end = Math.floor((i + 1) * results.length / 5);
        const quintileValues = values.slice(start, end);
        const quintilePerf = performance.slice(start, end);

        return {
          avgValue: mean(quintileValues),
          stdDev: std(quintileValues),
          avgPerformance: mean(quintilePerf)
        };
      });

      const stability = 1 - (std(quintiles.map(q => q.avgValue)) / mean(values));

      return {
        parameter: param,
        stability,
        quintiles,
        optimal: weightedAverage(values, performance)
      };
    });
  }, [results]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Parameter Stability Analysis</CardTitle>
        <CardDescription>
          How stable parameters are across performance quintiles
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Parameter</TableHead>
              <TableHead>Stability</TableHead>
              <TableHead>Q1</TableHead>
              <TableHead>Q2</TableHead>
              <TableHead>Q3</TableHead>
              <TableHead>Q4</TableHead>
              <TableHead>Q5</TableHead>
              <TableHead>Optimal</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {stabilityData?.map(param => (
              <TableRow key={param.parameter}>
                <TableCell>{param.parameter}</TableCell>
                <TableCell>
                  <Progress
                    value={param.stability * 100}
                    className="w-20"
                  />
                </TableCell>
                {param.quintiles.map((q, idx) => (
                  <TableCell key={idx}>
                    {q.avgValue.toFixed(2)}
                  </TableCell>
                ))}
                <TableCell className="font-medium">
                  {param.optimal.toFixed(2)}
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

### Parameter Recommendations
```typescript
// components/optimization/ParameterRecommendations.tsx
export function ParameterRecommendations({
  recommendations
}: { recommendations: ParameterRecommendation[] }) {
  if (!recommendations || recommendations.length === 0) return null;

  const grouped = groupBy(recommendations, 'category');

  return (
    <Card className="mt-6">
      <CardHeader>
        <CardTitle>Parameter Selection Recommendations</CardTitle>
        <CardDescription>
          Based on optimization results and robustness analysis
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Accordion type="single" collapsible>
          {Object.entries(grouped).map(([category, recs]) => (
            <AccordionItem key={category} value={category}>
              <AccordionTrigger>
                <div className="flex items-center gap-2">
                  <span>{category}</span>
                  <Badge variant="secondary">{recs.length}</Badge>
                </div>
              </AccordionTrigger>
              <AccordionContent>
                <div className="space-y-3">
                  {recs.map((rec, idx) => (
                    <RecommendationCard key={idx} recommendation={rec} />
                  ))}
                </div>
              </AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>

        <div className="mt-6">
          <h4 className="text-sm font-medium mb-3">Recommended Parameter Set</h4>
          <RecommendedParameters recommendations={recommendations} />
        </div>
      </CardContent>
    </Card>
  );
}

// Recommendation card
function RecommendationCard({ recommendation }) {
  const severityColors = {
    info: 'blue',
    warning: 'yellow',
    critical: 'red'
  };

  return (
    <Alert variant={recommendation.severity === 'critical' ? 'destructive' : 'default'}>
      <AlertCircle className="h-4 w-4" />
      <AlertTitle>{recommendation.title}</AlertTitle>
      <AlertDescription>
        <p>{recommendation.description}</p>
        {recommendation.action && (
          <p className="mt-2 font-medium">
            Recommended Action: {recommendation.action}
          </p>
        )}
        {recommendation.parameterSuggestions && (
          <div className="mt-2">
            <span className="font-medium">Suggested Values:</span>
            <ul className="list-disc list-inside">
              {Object.entries(recommendation.parameterSuggestions).map(([param, value]) => (
                <li key={param}>{param}: {value}</li>
              ))}
            </ul>
          </div>
        )}
      </AlertDescription>
    </Alert>
  );
}
```

### Backend Analysis Engine
```python
# api/optimization/results_analyzer.py
import numpy as np
from scipy import stats
from sklearn.ensemble import RandomForestRegressor
from typing import List, Dict

class OptimizationAnalyzer:
    def __init__(self, results: List[OptimizationResult]):
        self.results = results
        self.df = self._results_to_dataframe(results)

    def analyze(self) -> OptimizationAnalysis:
        """Perform comprehensive analysis of optimization results"""
        return OptimizationAnalysis(
            summary=self._calculate_summary(),
            topResults=self._get_top_results(50),
            parameterAnalysis=self._analyze_parameters(),
            robustnessTests=self._perform_robustness_tests(),
            recommendations=self._generate_recommendations()
        )

    def _analyze_parameters(self) -> ParameterAnalysis:
        """Analyze parameter importance and sensitivity"""
        # Extract parameter columns and target metrics
        param_cols = [col for col in self.df.columns if col.startswith('param_')]
        metrics = ['sharpe', 'total_return', 'max_drawdown', 'win_rate']

        analysis = ParameterAnalysis()

        for metric in metrics:
            # Calculate feature importance using Random Forest
            rf = RandomForestRegressor(n_estimators=100, random_state=42)
            X = self.df[param_cols]
            y = self.df[metric]
            rf.fit(X, y)

            # Store importance scores
            importance = dict(zip(param_cols, rf.feature_importances_))
            analysis.importance[metric] = importance

            # Calculate main effects
            for param in param_cols:
                effects = self._calculate_main_effect(param, metric)
                analysis.main_effects[metric][param] = effects

            # Calculate interaction effects
            interactions = self._calculate_interactions(param_cols, metric)
            analysis.interactions[metric] = interactions

        return analysis

    def _calculate_main_effect(self, param: str, metric: str) -> Dict:
        """Calculate main effect of a parameter on a metric"""
        param_values = sorted(self.df[param].unique())
        effects = []

        for value in param_values:
            subset = self.df[self.df[param] == value]
            effects.append({
                'value': value,
                'avgMetric': subset[metric].mean(),
                'stdMetric': subset[metric].std(),
                'count': len(subset),
                'confidence95Upper': subset[metric].mean() + 1.96 * subset[metric].sem(),
                'confidence95Lower': subset[metric].mean() - 1.96 * subset[metric].sem()
            })

        return effects

    def _perform_robustness_tests(self) -> RobustnessTestResults:
        """Perform various robustness tests"""
        top_results = self._get_top_results(10)

        return RobustnessTestResults(
            walkForward=self._walk_forward_analysis(top_results),
            monteCarlo=self._monte_carlo_robustness(top_results),
            stressTests=self._stress_test_robustness(top_results),
            stabilityScores=self._calculate_stability_scores(top_results)
        )

    def _walk_forward_analysis(self, results: List[OptimizationResult]) -> WalkForwardResults:
        """Perform walk-forward analysis on top results"""
        periods = self._split_data_periods(num_periods=5)
        wf_results = []

        for result in results:
            period_performances = []

            for period in periods:
                # Run backtest on in-sample period
                in_sample_perf = self._run_backtest(
                    result.parameters,
                    period['in_sample_start'],
                    period['in_sample_end']
                )

                # Run backtest on out-of-sample period
                out_sample_perf = self._run_backtest(
                    result.parameters,
                    period['out_sample_start'],
                    period['out_sample_end']
                )

                period_performances.append({
                    'period': period['name'],
                    'inSamplePerformance': in_sample_perf['sharpe'],
                    'outOfSamplePerformance': out_sample_perf['sharpe'],
                    'efficiency': out_sample_perf['sharpe'] / in_sample_perf['sharpe']
                        if in_sample_perf['sharpe'] > 0 else 0
                })

            wf_results.append({
                'parameters': result.parameters,
                'periods': period_performances,
                'avgEfficiency': np.mean([p['efficiency'] for p in period_performances]),
                'consistency': sum(1 for p in period_performances
                                 if p['outOfSamplePerformance'] > 0) / len(period_performances)
            })

        return WalkForwardResults(
            results=wf_results,
            avgEfficiency=np.mean([r['avgEfficiency'] for r in wf_results]),
            consistency=np.mean([r['consistency'] for r in wf_results]),
            stabilityScore=self._calculate_wf_stability(wf_results)
        )

    def _generate_recommendations(self) -> List[ParameterRecommendation]:
        """Generate parameter selection recommendations"""
        recommendations = []

        # Check for overfitting
        if self._detect_overfitting():
            recommendations.append(ParameterRecommendation(
                category='Risk Management',
                severity='warning',
                title='Potential Overfitting Detected',
                description='Top parameters show significant performance degradation in robustness tests.',
                action='Consider using more conservative parameters or expanding the parameter ranges.',
                parameterSuggestions=self._suggest_conservative_params()
            ))

        # Check parameter stability
        unstable_params = self._find_unstable_parameters()
        if unstable_params:
            recommendations.append(ParameterRecommendation(
                category='Parameter Stability',
                severity='info',
                title='Unstable Parameters Identified',
                description=f'Parameters {", ".join(unstable_params)} show high variance across top results.',
                action='Consider fixing these parameters or using narrower ranges.'
            ))

        # Suggest optimal parameter set
        optimal_params = self._find_optimal_robust_parameters()
        recommendations.append(ParameterRecommendation(
            category='Optimal Selection',
            severity='info',
            title='Recommended Parameter Set',
            description='Based on performance and robustness analysis.',
            parameterSuggestions=optimal_params
        ))

        return recommendations
```

## UI/UX Considerations
- Interactive visualizations for exploring results
- Clear indicators for robust vs overfit parameters
- Comparative views for multiple parameter sets
- Export functionality for detailed reports
- Responsive design for various screen sizes
- Tooltips explaining complex metrics

## Testing Requirements
1. Analysis algorithm accuracy
2. Robustness test implementations
3. Visualization performance with large datasets
4. Statistical calculation correctness
5. Recommendation engine logic
6. Export functionality completeness

## Dependencies
- UI_001: Next.js foundation
- UI_032: Grid search setup
- UI_033: Optimization execution
- UI_022: Advanced charts

## Story Points: 21

## Priority: High

## Implementation Notes
- Use statistical libraries for robust calculations
- Implement caching for expensive analyses
- Consider using Web Workers for heavy computations
- Add confidence intervals to all estimates
