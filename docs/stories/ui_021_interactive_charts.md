# Story UI_021: Interactive Chart Suite

## Story Details
- **Story ID**: UI_021
- **Epic**: Epic 3 - Advanced Analysis & Visualization
- **Story Points**: 8
- **Priority**: High
- **Type**: Data Visualization

## User Story
**As a** trading researcher
**I want** interactive charts with multiple visualization types and advanced interactions
**So that** I can analyze trading performance from different perspectives and identify patterns effectively

## Acceptance Criteria

### 1. Equity Curve Visualization
- [ ] Interactive line chart showing cumulative equity over time
- [ ] Zoom and pan functionality with smooth interactions
- [ ] Crosshair cursor showing precise values and timestamps
- [ ] Benchmark overlay capability (buy-and-hold, market index)
- [ ] Drawdown periods highlighted with shaded regions
- [ ] Multiple timeframe views (tick, minute, hour, day)

### 2. Drawdown Analysis Charts
- [ ] Underwater equity chart showing drawdown periods
- [ ] Maximum drawdown periods clearly identified
- [ ] Recovery time visualization
- [ ] Drawdown distribution histogram
- [ ] Rolling max drawdown chart
- [ ] Drawdown metrics overlay (duration, magnitude)

### 3. Returns Distribution Visualization
- [ ] Histogram of trade returns with configurable bins
- [ ] Normal distribution overlay for comparison
- [ ] Statistical annotations (mean, std dev, skewness, kurtosis)
- [ ] Percentile markers (1%, 5%, 95%, 99%)
- [ ] Interactive brushing to filter data
- [ ] Box plot view for distribution summary

### 4. Performance Heatmaps
- [ ] Profit/Loss heatmap by time of day and day of week
- [ ] Color-coded cells with clear legends
- [ ] Interactive hover showing detailed statistics
- [ ] Configurable aggregation periods (hourly, daily, weekly)
- [ ] Filter controls for date ranges and strategy parameters
- [ ] Export functionality for heatmap data

### 5. Chart Synchronization and Interaction
- [ ] Synchronized zooming across multiple charts
- [ ] Linked brushing for data exploration
- [ ] Consistent time axis alignment
- [ ] Crosshair synchronization between charts
- [ ] Shared legend and color schemes
- [ ] Coordinated animation and transitions

### 6. Chart Export and Configuration
- [ ] Export charts as PNG, SVG, or PDF
- [ ] Chart configuration persistence (zoom levels, settings)
- [ ] Custom color scheme selection
- [ ] Chart size and aspect ratio adjustment
- [ ] Print-friendly layouts
- [ ] Annotation tools for marking important events

## Technical Requirements

### shadcn/ui Chart Integration
```typescript
// Use shadcn/ui Chart components with Recharts
import { ChartContainer, ChartTooltip, ChartTooltipContent, ChartLegend, ChartLegendContent } from '@/components/ui/chart';
import { LineChart, AreaChart, BarChart, ScatterPlot } from 'recharts';
import * as d3 from 'd3';

// shadcn/ui Chart configuration
const chartConfig = {
  equity: {
    label: "Equity",
    color: "hsl(var(--chart-1))",
  },
  benchmark: {
    label: "Benchmark",
    color: "hsl(var(--chart-2))",
  },
  drawdown: {
    label: "Drawdown",
    color: "hsl(var(--chart-3))",
  },
} satisfies ChartConfig;

// Chart component architecture using shadcn/ui
interface ChartProps {
  data: ChartDataPoint[];
  config: ChartConfig;
  className?: string;
  interactive?: boolean;
  synchronized?: boolean;
  exportable?: boolean;
}

interface ChartDataPoint {
  timestamp: number;
  value: number;
  metadata?: Record<string, any>;
}
```

### Equity Curve Implementation
```typescript
const EquityCurveChart: React.FC<EquityCurveProps> = ({
  equityData,
  benchmarkData,
  drawdownPeriods,
  synchronized = true
}) => {
  const [zoomDomain, setZoomDomain] = useState(null);
  const [crosshairValue, setCrosshairValue] = useState(null);

  // Zoom synchronization with other charts
  useEffect(() => {
    if (synchronized && zoomDomain) {
      chartSyncManager.updateZoomDomain(zoomDomain);
    }
  }, [zoomDomain, synchronized]);

  return (
    <ResponsiveContainer width="100%" height={400}>
      <LineChart
        data={equityData}
        onMouseMove={handleMouseMove}
        onMouseLeave={() => setCrosshairValue(null)}
      >
        <XAxis
          dataKey="timestamp"
          type="number"
          scale="time"
          domain={zoomDomain || ['dataMin', 'dataMax']}
        />
        <YAxis domain={['dataMin', 'dataMax']} />
        <CartesianGrid strokeDasharray="3 3" />
        <Tooltip content={<CustomTooltip />} />
        <Line
          type="monotone"
          dataKey="equity"
          stroke="#00cc88"
          strokeWidth={2}
          dot={false}
        />
        {benchmarkData && (
          <Line
            type="monotone"
            dataKey="benchmark"
            stroke="#666"
            strokeDasharray="5 5"
            dot={false}
          />
        )}
        <Brush
          dataKey="timestamp"
          height={30}
          stroke="#8884d8"
          onChange={setZoomDomain}
        />
      </LineChart>
    </ResponsiveContainer>
  );
};
```

### Chart Synchronization Manager
```typescript
class ChartSyncManager {
  private subscribers: Map<string, Function[]> = new Map();

  subscribe(chartId: string, callback: Function): void {
    if (!this.subscribers.has(chartId)) {
      this.subscribers.set(chartId, []);
    }
    this.subscribers.get(chartId)!.push(callback);
  }

  updateZoomDomain(domain: [number, number]): void {
    this.subscribers.forEach(callbacks => {
      callbacks.forEach(callback => callback(domain));
    });
  }

  updateCrosshair(position: { x: number, y: number }): void {
    // Broadcast crosshair updates to all synchronized charts
  }
}
```

### Performance Heatmap Component
```typescript
const PerformanceHeatmap: React.FC<HeatmapProps> = ({
  data,
  timeFormat = 'hour',
  valueFormat = 'pnl'
}) => {
  const heatmapData = useMemo(() =>
    aggregateDataForHeatmap(data, timeFormat, valueFormat),
    [data, timeFormat, valueFormat]
  );

  return (
    <div className="heatmap-container">
      <HeatmapGrid
        data={heatmapData}
        colorScale={d3.scaleSequential(d3.interpolateRdYlGn)}
        onCellHover={showTooltip}
        onCellClick={handleCellClick}
      />
      <HeatmapLegend colorScale={colorScale} />
      <HeatmapControls
        timeFormat={timeFormat}
        valueFormat={valueFormat}
        onFormatChange={handleFormatChange}
      />
    </div>
  );
};
```

### Chart Export Functionality
```typescript
const useChartExport = (chartRef: RefObject<HTMLElement>) => {
  const exportAsPNG = useCallback(async () => {
    if (!chartRef.current) return;

    const canvas = await html2canvas(chartRef.current);
    const link = document.createElement('a');
    link.download = `chart-${Date.now()}.png`;
    link.href = canvas.toDataURL();
    link.click();
  }, [chartRef]);

  const exportAsSVG = useCallback(() => {
    // SVG export implementation
  }, [chartRef]);

  return { exportAsPNG, exportAsSVG };
};
```

## Definition of Done
- [ ] All chart types render correctly with sample data
- [ ] Interactive features (zoom, pan, hover) work smoothly
- [ ] Chart synchronization works across multiple charts
- [ ] Export functionality produces high-quality outputs
- [ ] Performance handles 100K+ data points without lag
- [ ] Charts are responsive and mobile-friendly
- [ ] Accessibility features work with screen readers
- [ ] Chart configuration persists across sessions

## Testing Checklist
- [ ] Charts render without JavaScript errors
- [ ] Zoom and pan interactions work smoothly
- [ ] Data updates trigger chart re-renders
- [ ] Export functions produce valid files
- [ ] Synchronized charts update together
- [ ] Performance remains good with large datasets
- [ ] Charts work on different screen sizes
- [ ] Color schemes are accessible (colorblind-friendly)

## Performance Requirements
- Chart rendering time < 500ms for 100K data points
- Smooth interactions (60fps) during zoom/pan
- Memory usage < 200MB for complex chart combinations
- Export operations complete < 5 seconds
- Real-time updates without performance degradation

### Data Processing Optimizations
```typescript
// Data decimation for performance
const decimateData = (data: DataPoint[], maxPoints: number): DataPoint[] => {
  if (data.length <= maxPoints) return data;

  const step = Math.ceil(data.length / maxPoints);
  return data.filter((_, index) => index % step === 0);
};

// Virtual scrolling for large datasets
const useVirtualizedChart = (data: DataPoint[], viewportWidth: number) => {
  return useMemo(() => {
    const pixelsPerPoint = viewportWidth / 1000; // Max 1000 visible points
    return decimateData(data, Math.floor(viewportWidth / pixelsPerPoint));
  }, [data, viewportWidth]);
};
```

## Accessibility Requirements
- Keyboard navigation for chart interactions
- Screen reader support with data summaries
- High contrast mode compatible color schemes
- Alternative text descriptions for complex visuals
- Focus indicators for interactive elements

## Integration Points
- **Data Source**: Integration with backtest results from UI_015
- **Export System**: Integration with general export functionality
- **Theme System**: Consistent with application design system
- **Performance Monitoring**: Integration with UI_041 for performance tracking

## Follow-up Stories
- UI_022: Trade Explorer (uses similar chart components)
- UI_024: Order Book Visualization (advanced chart types)
- UI_034: 3D Parameter Visualization (extends charting capabilities)
