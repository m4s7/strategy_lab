# Story UI_015: Basic Results Visualization

## Story Details
- **Story ID**: UI_015
- **Epic**: Epic 2 - Core Backtesting Features
- **Story Points**: 5
- **Priority**: High
- **Type**: Data Visualization + API Integration
- **Status**: Done

## User Story
**As a** trading researcher
**I want** to see backtest results with key metrics and basic charts
**So that** I can quickly evaluate strategy performance and make informed decisions

## Acceptance Criteria

### 1. Key Metrics Dashboard
- [ ] Essential performance metrics displayed prominently (Sharpe, return, drawdown, win rate)
- [ ] Profit factor, total trades, and average trade duration
- [ ] Risk-adjusted returns and volatility measures
- [ ] Comparison with benchmark (if available)
- [ ] Color coding for positive/negative performance
- [ ] Metric explanations via tooltips or info icons

### 2. Equity Curve Visualization
- [ ] Interactive line chart showing cumulative equity over time
- [ ] Zoom and pan functionality for detailed analysis
- [ ] Drawdown periods highlighted with shaded regions
- [ ] Key events and milestones marked on timeline
- [ ] Benchmark overlay capability
- [ ] Time period selector (daily, weekly, monthly aggregation)

### 3. Performance Statistics Table
- [ ] Comprehensive statistics in organized categories (returns, risk, trades)
- [ ] Sortable and searchable statistics
- [ ] Statistical significance indicators
- [ ] Percentile rankings and distribution metrics
- [ ] Export functionality for statistics
- [ ] Comparison with previous backtests

### 4. Trade Summary Overview
- [ ] Total number of trades and win/loss breakdown
- [ ] Largest winning and losing trades
- [ ] Average trade metrics (duration, P&L, return)
- [ ] Trade distribution by month, day of week, time of day
- [ ] Consecutive wins/losses tracking
- [ ] Trade frequency analysis

### 5. Results Export and Sharing
- [ ] Export results to CSV, JSON, PDF formats
- [ ] Chart export as images (PNG, SVG)
- [ ] Results sharing via URL or file
- [ ] Print-friendly report generation
- [ ] Data export for external analysis tools
- [ ] Configuration export for reproducibility

### 6. Navigation to Detailed Analysis
- [ ] Links to advanced analysis tools
- [ ] Quick access to trade-by-trade explorer
- [ ] Navigation to comparative analysis
- [ ] Links to optimization modules
- [ ] Breadcrumb navigation
- [ ] Related results recommendations

## Technical Requirements

### Results Data Model
```typescript
interface BacktestResult {
  id: string;
  backtestId: string;
  startDate: string;
  endDate: string;
  strategyName: string;
  configuration: BacktestConfiguration;
  metrics: PerformanceMetrics;
  equityCurve: EquityPoint[];
  tradeSummary: TradeSummary;
  statistics: PerformanceStatistics;
  createdAt: string;
}

interface PerformanceMetrics {
  totalReturn: number;
  annualizedReturn: number;
  sharpeRatio: number;
  sortinoRatio: number;
  maxDrawdown: number;
  maxDrawdownDuration: number;
  calmarRatio: number;
  winRate: number;
  profitFactor: number;
  averageTrade: number;
  totalTrades: number;
  volatility: number;
}

interface EquityPoint {
  date: string;
  equity: number;
  drawdown: number;
  benchmark?: number;
}
```

### Results API Integration
```typescript
// API endpoints for results
const resultsApi = {
  getResult: (resultId: string) =>
    fetch(`/api/results/${resultId}`).then(r => r.json()),

  getEquityCurve: (resultId: string) =>
    fetch(`/api/results/${resultId}/equity-curve`).then(r => r.json()),

  getStatistics: (resultId: string) =>
    fetch(`/api/results/${resultId}/statistics`).then(r => r.json()),

  exportResults: (resultId: string, format: string) =>
    fetch(`/api/results/${resultId}/export?format=${format}`),

  compareResults: (resultIds: string[]) =>
    fetch(`/api/results/compare`, {
      method: 'POST',
      body: JSON.stringify({ resultIds })
    }).then(r => r.json())
};
```

### Results Dashboard Component
```typescript
const ResultsDashboard: React.FC<{
  resultId: string;
}> = ({ resultId }) => {
  const { data: result, isLoading } = useBacktestResult(resultId);

  if (isLoading) return <ResultsSkeleton />;
  if (!result) return <ResultsNotFound />;

  return (
    <div className="results-dashboard">
      <div className="results-header">
        <h1>{result.strategyName} Results</h1>
        <div className="results-actions">
          <ExportButton result={result} />
          <ShareButton result={result} />
          <CompareButton result={result} />
        </div>
      </div>

      <div className="metrics-grid">
        <KeyMetricsCards metrics={result.metrics} />
      </div>

      <div className="charts-section">
        <EquityCurveChart
          data={result.equityCurve}
          benchmarkData={result.benchmark}
        />
      </div>

      <div className="statistics-section">
        <PerformanceStatisticsTable
          statistics={result.statistics}
          exportable={true}
        />
      </div>

      <div className="trade-summary">
        <TradeSummaryPanel
          summary={result.tradeSummary}
          onDetailClick={() => navigateToTradeExplorer(result.id)}
        />
      </div>

      <div className="navigation-section">
        <QuickActionsPanel
          resultId={result.id}
          onAdvancedAnalysis={() => navigateToAdvancedAnalysis(result.id)}
        />
      </div>
    </div>
  );
};
```

### Key Metrics Cards
```typescript
const KeyMetricsCards: React.FC<{
  metrics: PerformanceMetrics;
}> = ({ metrics }) => {
  const metricCards = [
    {
      title: 'Total Return',
      value: `${(metrics.totalReturn * 100).toFixed(2)}%`,
      trend: metrics.totalReturn >= 0 ? 'positive' : 'negative',
      description: 'Cumulative percentage return over the entire period'
    },
    {
      title: 'Sharpe Ratio',
      value: metrics.sharpeRatio.toFixed(3),
      trend: metrics.sharpeRatio >= 1 ? 'positive' : metrics.sharpeRatio >= 0 ? 'neutral' : 'negative',
      description: 'Risk-adjusted return measure'
    },
    {
      title: 'Max Drawdown',
      value: `${(Math.abs(metrics.maxDrawdown) * 100).toFixed(2)}%`,
      trend: 'negative',
      description: 'Maximum peak-to-trough decline'
    },
    {
      title: 'Win Rate',
      value: `${(metrics.winRate * 100).toFixed(1)}%`,
      trend: metrics.winRate >= 0.5 ? 'positive' : 'negative',
      description: 'Percentage of winning trades'
    }
  ];

  return (
    <div className="metrics-cards-grid">
      {metricCards.map(metric => (
        <MetricCard
          key={metric.title}
          title={metric.title}
          value={metric.value}
          trend={metric.trend}
          description={metric.description}
        />
      ))}
    </div>
  );
};
```

### Equity Curve Chart
```typescript
const EquityCurveChart: React.FC<{
  data: EquityPoint[];
  benchmarkData?: EquityPoint[];
}> = ({ data, benchmarkData }) => {
  const [timeFrame, setTimeFrame] = useState('daily');
  const [showDrawdown, setShowDrawdown] = useState(false);

  const aggregatedData = useMemo(() =>
    aggregateEquityData(data, timeFrame),
    [data, timeFrame]
  );

  return (
    <div className="equity-curve-chart">
      <div className="chart-controls">
        <TimeFrameSelector
          value={timeFrame}
          onChange={setTimeFrame}
          options={['daily', 'weekly', 'monthly']}
        />
        <Toggle
          label="Show Drawdown"
          checked={showDrawdown}
          onChange={setShowDrawdown}
        />
      </div>

      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={aggregatedData}>
          <XAxis dataKey="date" type="category" />
          <YAxis />
          <CartesianGrid strokeDasharray="3 3" />
          <Tooltip content={<CustomTooltip />} />

          <Line
            type="monotone"
            dataKey="equity"
            stroke="#00cc88"
            strokeWidth={2}
            dot={false}
            name="Strategy"
          />

          {benchmarkData && (
            <Line
              type="monotone"
              dataKey="benchmark"
              stroke="#666"
              strokeDasharray="5 5"
              dot={false}
              name="Benchmark"
            />
          )}

          {showDrawdown && (
            <Area
              type="monotone"
              dataKey="drawdown"
              stackId="1"
              stroke="#ff4757"
              fill="#ff4757"
              fillOpacity={0.3}
              name="Drawdown"
            />
          )}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};
```

### Export Functionality
```typescript
const useResultsExport = () => {
  const exportToPDF = async (result: BacktestResult) => {
    const response = await fetch(`/api/results/${result.id}/export?format=pdf`);
    const blob = await response.blob();

    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `backtest-results-${result.id}.pdf`;
    link.click();

    window.URL.revokeObjectURL(url);
  };

  const exportToCSV = async (result: BacktestResult) => {
    const csvData = generateCSVData(result);
    const blob = new Blob([csvData], { type: 'text/csv' });

    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `backtest-results-${result.id}.csv`;
    link.click();

    window.URL.revokeObjectURL(url);
  };

  const exportChart = async (chartRef: RefObject<HTMLDivElement>, filename: string) => {
    if (!chartRef.current) return;

    const canvas = await html2canvas(chartRef.current);
    const url = canvas.toDataURL('image/png');

    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
  };

  return { exportToPDF, exportToCSV, exportChart };
};
```

## Definition of Done
- [ ] All key metrics display correctly
- [ ] Equity curve chart renders properly with interactions
- [ ] Statistics table shows comprehensive performance data
- [ ] Export functionality works for all supported formats
- [ ] Navigation links lead to appropriate sections
- [ ] Loading states provide good user feedback
- [ ] Error handling covers missing or invalid data
- [ ] Performance is acceptable for large result sets

## Testing Checklist
- [ ] Metrics calculations are accurate
- [ ] Charts render without JavaScript errors
- [ ] Export functions produce valid files
- [ ] Navigation works correctly
- [ ] Data loads properly from API
- [ ] Error states display helpful messages
- [ ] Loading skeletons appear during data fetch
- [ ] Responsive layout works on different screen sizes

## Performance Requirements
- Initial results load < 3 seconds
- Chart rendering < 1 second for standard datasets
- Export operations < 10 seconds
- Statistics table sorting < 500ms
- Memory usage < 200MB for typical results

## Integration Points
- **Backtest Execution**: Receives results from UI_014
- **Advanced Analysis**: Links to UI_021 (Interactive Charts)
- **Trade Explorer**: Links to UI_022 (Trade Explorer)
- **Comparative Analysis**: Links to UI_025 (Comparative Analysis)

## Accessibility Requirements
- Screen reader support for metrics and statistics
- Keyboard navigation for all interactive elements
- High contrast mode for charts and data
- Alternative text for visual elements

## Follow-up Stories
- UI_021: Interactive Chart Suite (enhanced visualization)
- UI_022: Trade Explorer Interface (detailed trade analysis)
- UI_025: Comparative Analysis Tools (multi-result comparison)
