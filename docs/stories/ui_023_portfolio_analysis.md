# UI_023: Portfolio Analysis Dashboard

## Story Details
- **Story ID**: UI_023
- **Status**: Done

## Story
As a trader, I want to analyze portfolio-level metrics across multiple strategies including correlation analysis, risk contributions, and portfolio optimization suggestions so that I can build robust trading systems.

## Acceptance Criteria
1. Display portfolio-level statistics (total PnL, Sharpe, volatility)
2. Show correlation matrix between strategies
3. Calculate risk contribution by strategy
4. Provide portfolio optimization suggestions
5. Enable what-if analysis for portfolio changes
6. Show drawdown analysis at portfolio level
7. Display position sizing recommendations
8. Export portfolio analytics reports

## Technical Requirements

### Frontend Components
```typescript
// components/portfolio/PortfolioDashboard.tsx
interface PortfolioMetrics {
  totalPnL: number;
  sharpeRatio: number;
  volatility: number;
  maxDrawdown: number;
  calmarRatio: number;
  strategies: StrategyAllocation[];
  correlations: CorrelationMatrix;
  riskContributions: RiskContribution[];
}

export function PortfolioDashboard({ strategies }: { strategies: Strategy[] }) {
  const [metrics, setMetrics] = useState<PortfolioMetrics>();
  const [selectedTimeframe, setTimeframe] = useState<Timeframe>('1Y');
  const [optimizationTarget, setOptimizationTarget] = useState<'sharpe' | 'risk'>('sharpe');

  // Calculate portfolio metrics
  useEffect(() => {
    const calculateMetrics = async () => {
      const data = await fetchPortfolioData(strategies, selectedTimeframe);
      const calculated = calculatePortfolioMetrics(data);
      setMetrics(calculated);
    };
    calculateMetrics();
  }, [strategies, selectedTimeframe]);

  return (
    <div className="portfolio-dashboard">
      <PortfolioSummary metrics={metrics} />
      <div className="grid grid-cols-2 gap-6">
        <CorrelationHeatmap data={metrics?.correlations} />
        <RiskContributionChart data={metrics?.riskContributions} />
      </div>
      <OptimizationPanel
        strategies={strategies}
        target={optimizationTarget}
        onOptimize={handleOptimization}
      />
      <WhatIfAnalysis strategies={strategies} />
    </div>
  );
}
```

### Correlation Analysis
```typescript
// components/portfolio/CorrelationHeatmap.tsx
import { HeatmapChart } from '@/components/charts/Heatmap';

export function CorrelationHeatmap({ data }: { data: CorrelationMatrix }) {
  const [selectedPair, setSelectedPair] = useState<[string, string] | null>(null);

  const heatmapData = useMemo(() => {
    if (!data) return [];

    return data.strategies.flatMap((strat1, i) =>
      data.strategies.map((strat2, j) => ({
        x: strat1,
        y: strat2,
        value: data.values[i][j],
        color: getCorrelationColor(data.values[i][j])
      }))
    );
  }, [data]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Strategy Correlations</CardTitle>
        <CardDescription>
          Correlation coefficients between strategy returns
        </CardDescription>
      </CardHeader>
      <CardContent>
        <HeatmapChart
          data={heatmapData}
          onCellClick={(x, y) => setSelectedPair([x, y])}
          colorScale={correlationColorScale}
          showValues
        />
        {selectedPair && (
          <CorrelationDetails
            strategy1={selectedPair[0]}
            strategy2={selectedPair[1]}
            correlation={getCorrelation(data, selectedPair)}
          />
        )}
      </CardContent>
    </Card>
  );
}

// Correlation calculation backend
class CorrelationCalculator {
  static calculate(returns: Record<string, number[]>): CorrelationMatrix {
    const strategies = Object.keys(returns);
    const n = strategies.length;
    const matrix: number[][] = Array(n).fill(null).map(() => Array(n).fill(0));

    for (let i = 0; i < n; i++) {
      for (let j = 0; j < n; j++) {
        matrix[i][j] = this.pearsonCorrelation(
          returns[strategies[i]],
          returns[strategies[j]]
        );
      }
    }

    return { strategies, values: matrix };
  }

  private static pearsonCorrelation(x: number[], y: number[]): number {
    const n = x.length;
    const sumX = x.reduce((a, b) => a + b, 0);
    const sumY = y.reduce((a, b) => a + b, 0);
    const sumXY = x.reduce((total, xi, i) => total + xi * y[i], 0);
    const sumX2 = x.reduce((total, xi) => total + xi * xi, 0);
    const sumY2 = y.reduce((total, yi) => total + yi * yi, 0);

    const correlation = (n * sumXY - sumX * sumY) /
      Math.sqrt((n * sumX2 - sumX * sumX) * (n * sumY2 - sumY * sumY));

    return correlation;
  }
}
```

### Risk Contribution Analysis
```typescript
// components/portfolio/RiskContribution.tsx
interface RiskContribution {
  strategy: string;
  marginalRisk: number;
  contributionToRisk: number;
  percentageOfRisk: number;
}

export function RiskContributionChart({ data }: { data: RiskContribution[] }) {
  const chartData = useMemo(() => {
    return data?.map(item => ({
      name: item.strategy,
      value: item.percentageOfRisk,
      marginal: item.marginalRisk,
      contribution: item.contributionToRisk
    })) || [];
  }, [data]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Risk Contributions</CardTitle>
        <CardDescription>
          Each strategy's contribution to portfolio risk
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={renderCustomLabel}
              outerRadius={80}
              fill="#8884d8"
              dataKey="value"
            >
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
        <RiskMetricsTable data={data} />
      </CardContent>
    </Card>
  );
}

// Risk calculation
class RiskAnalyzer {
  static calculateRiskContributions(
    weights: number[],
    returns: number[][],
    covMatrix: number[][]
  ): RiskContribution[] {
    const portfolioVariance = this.portfolioVariance(weights, covMatrix);
    const portfolioStdDev = Math.sqrt(portfolioVariance);

    const contributions = weights.map((weight, i) => {
      const marginalRisk = this.marginalRisk(i, weights, covMatrix);
      const contributionToRisk = weight * marginalRisk;
      const percentageOfRisk = (contributionToRisk / portfolioStdDev) * 100;

      return {
        strategy: `Strategy ${i + 1}`,
        marginalRisk,
        contributionToRisk,
        percentageOfRisk
      };
    });

    return contributions;
  }

  private static marginalRisk(index: number, weights: number[], covMatrix: number[][]): number {
    let marginal = 0;
    for (let j = 0; j < weights.length; j++) {
      marginal += weights[j] * covMatrix[index][j];
    }
    return marginal / Math.sqrt(this.portfolioVariance(weights, covMatrix));
  }
}
```

### Portfolio Optimization
```typescript
// components/portfolio/OptimizationPanel.tsx
export function OptimizationPanel({
  strategies,
  target,
  onOptimize
}: OptimizationPanelProps) {
  const [constraints, setConstraints] = useState<Constraints>({
    minWeight: 0,
    maxWeight: 1,
    targetReturn: null,
    maxRisk: null
  });

  const [optimizationResult, setResult] = useState<OptimizationResult>();

  const runOptimization = async () => {
    const result = await optimizePortfolio({
      strategies,
      target,
      constraints,
      method: 'mean-variance'
    });
    setResult(result);
    onOptimize(result);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Portfolio Optimization</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div>
            <Label>Optimization Target</Label>
            <Select value={target} onValueChange={setTarget}>
              <SelectItem value="sharpe">Maximize Sharpe Ratio</SelectItem>
              <SelectItem value="risk">Minimize Risk</SelectItem>
              <SelectItem value="return">Maximize Return</SelectItem>
            </Select>
          </div>

          <ConstraintsForm
            constraints={constraints}
            onChange={setConstraints}
          />

          <Button onClick={runOptimization}>
            Run Optimization
          </Button>

          {optimizationResult && (
            <OptimizationResults result={optimizationResult} />
          )}
        </div>
      </CardContent>
    </Card>
  );
}

// Backend optimization
async function optimizePortfolio(params: OptimizationParams): Promise<OptimizationResult> {
  const { strategies, target, constraints } = params;

  // Calculate returns and covariance matrix
  const returns = strategies.map(s => s.returns);
  const meanReturns = returns.map(r => mean(r));
  const covMatrix = calculateCovarianceMatrix(returns);

  // Set up optimization problem
  const n = strategies.length;
  const objective = getObjectiveFunction(target, meanReturns, covMatrix);
  const constraintFunctions = buildConstraints(constraints, n);

  // Solve using optimization library (e.g., numeric.js)
  const result = await solveOptimization({
    objective,
    constraints: constraintFunctions,
    initialGuess: Array(n).fill(1/n),
    method: 'SLSQP'
  });

  return {
    weights: result.x,
    expectedReturn: calculateExpectedReturn(result.x, meanReturns),
    expectedRisk: calculatePortfolioRisk(result.x, covMatrix),
    sharpeRatio: calculateSharpe(result.x, meanReturns, covMatrix)
  };
}
```

### What-If Analysis
```typescript
// components/portfolio/WhatIfAnalysis.tsx
export function WhatIfAnalysis({ strategies }: { strategies: Strategy[] }) {
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [activeScenario, setActiveScenario] = useState<Scenario>();

  const addScenario = () => {
    const newScenario: Scenario = {
      id: generateId(),
      name: `Scenario ${scenarios.length + 1}`,
      modifications: strategies.map(s => ({
        strategyId: s.id,
        weight: 1 / strategies.length,
        enabled: true
      }))
    };
    setScenarios([...scenarios, newScenario]);
  };

  const compareScenarios = () => {
    const results = scenarios.map(scenario => ({
      ...scenario,
      metrics: calculateScenarioMetrics(scenario, strategies)
    }));

    return (
      <ScenarioComparison scenarios={results} />
    );
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>What-If Analysis</CardTitle>
        <Button onClick={addScenario} size="sm">
          Add Scenario
        </Button>
      </CardHeader>
      <CardContent>
        <Tabs value={activeScenario?.id} onValueChange={setActiveScenario}>
          <TabsList>
            {scenarios.map(scenario => (
              <TabsTrigger key={scenario.id} value={scenario.id}>
                {scenario.name}
              </TabsTrigger>
            ))}
          </TabsList>

          {scenarios.map(scenario => (
            <TabsContent key={scenario.id} value={scenario.id}>
              <ScenarioEditor
                scenario={scenario}
                strategies={strategies}
                onChange={(updated) => updateScenario(scenario.id, updated)}
              />
            </TabsContent>
          ))}
        </Tabs>

        {scenarios.length > 1 && compareScenarios()}
      </CardContent>
    </Card>
  );
}
```

### Portfolio Reports
```typescript
// lib/portfolio/report-generator.ts
export class PortfolioReportGenerator {
  static async generatePDF(portfolio: Portfolio, metrics: PortfolioMetrics) {
    const doc = new PDFDocument();

    // Title page
    doc.fontSize(24).text('Portfolio Analysis Report', { align: 'center' });
    doc.fontSize(12).text(`Generated: ${new Date().toLocaleDateString()}`);

    // Executive summary
    doc.addPage();
    doc.fontSize(18).text('Executive Summary');
    doc.fontSize(12).text(`Total Strategies: ${portfolio.strategies.length}`);
    doc.text(`Portfolio Sharpe Ratio: ${metrics.sharpeRatio.toFixed(2)}`);
    doc.text(`Maximum Drawdown: ${(metrics.maxDrawdown * 100).toFixed(2)}%`);

    // Strategy breakdown
    doc.addPage();
    doc.fontSize(18).text('Strategy Performance');
    const table = {
      headers: ['Strategy', 'Weight', 'Return', 'Risk', 'Sharpe'],
      rows: portfolio.strategies.map(s => [
        s.name,
        `${(s.weight * 100).toFixed(1)}%`,
        `${(s.annualReturn * 100).toFixed(2)}%`,
        `${(s.volatility * 100).toFixed(2)}%`,
        s.sharpeRatio.toFixed(2)
      ])
    };
    doc.table(table);

    // Risk analysis
    doc.addPage();
    doc.fontSize(18).text('Risk Analysis');
    // Add correlation matrix image
    const correlationImage = await generateCorrelationImage(metrics.correlations);
    doc.image(correlationImage, { width: 400 });

    // Save PDF
    return doc.save();
  }

  static generateExcel(portfolio: Portfolio, metrics: PortfolioMetrics): Workbook {
    const workbook = new ExcelJS.Workbook();

    // Summary sheet
    const summarySheet = workbook.addWorksheet('Summary');
    summarySheet.addRow(['Portfolio Analysis Report']);
    summarySheet.addRow(['Generated', new Date()]);
    summarySheet.addRow([]);
    summarySheet.addRow(['Metric', 'Value']);
    summarySheet.addRow(['Total PnL', metrics.totalPnL]);
    summarySheet.addRow(['Sharpe Ratio', metrics.sharpeRatio]);
    summarySheet.addRow(['Max Drawdown', metrics.maxDrawdown]);

    // Strategy details sheet
    const strategySheet = workbook.addWorksheet('Strategies');
    strategySheet.columns = [
      { header: 'Strategy', key: 'name', width: 20 },
      { header: 'Weight', key: 'weight', width: 10 },
      { header: 'Return', key: 'return', width: 10 },
      { header: 'Risk', key: 'risk', width: 10 },
      { header: 'Sharpe', key: 'sharpe', width: 10 }
    ];

    portfolio.strategies.forEach(strategy => {
      strategySheet.addRow({
        name: strategy.name,
        weight: strategy.weight,
        return: strategy.annualReturn,
        risk: strategy.volatility,
        sharpe: strategy.sharpeRatio
      });
    });

    return workbook;
  }
}
```

## UI/UX Considerations
- Interactive visualizations with drill-down capability
- Color coding for risk levels
- Clear labeling of complex metrics
- Tooltips explaining calculations
- Responsive design for different devices
- Export options prominently displayed

## Testing Requirements
1. Portfolio calculation accuracy tests
2. Optimization algorithm verification
3. Correlation matrix correctness
4. Risk contribution calculations
5. What-if scenario comparisons
6. Report generation completeness

## Dependencies
- UI_001: Next.js foundation
- UI_015: Basic results visualization
- UI_021: Interactive performance charts
- UI_022: Advanced time series charts

## Story Points: 21

## Priority: Medium

## Implementation Notes
- Use numerical optimization libraries for portfolio optimization
- Consider caching correlation matrices for performance
- Implement incremental updates for what-if scenarios
- Add validation for portfolio constraints
