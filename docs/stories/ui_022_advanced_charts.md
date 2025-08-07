# UI_022: Advanced Time Series Charts

## Story
As a trader, I want to visualize backtest results with advanced charting capabilities including candlestick charts, technical indicators, and custom overlays so that I can perform detailed market analysis.

## Acceptance Criteria
1. Display interactive candlestick/OHLC charts
2. Support multiple timeframes (1m, 5m, 15m, 1h, 1d)
3. Add technical indicators (SMA, EMA, RSI, MACD, Bollinger Bands)
4. Show trade entry/exit points on charts
5. Support custom drawing tools (trendlines, channels)
6. Enable chart comparison (multiple strategies)
7. Provide zoom/pan functionality
8. Export charts as images or data

## Technical Requirements

### Frontend Components
```typescript
// components/charts/AdvancedChart.tsx
import { Chart } from '@/lib/charting/chart-engine';
import { Indicator } from '@/lib/charting/indicators';

interface ChartConfig {
  symbol: string;
  timeframe: '1m' | '5m' | '15m' | '1h' | '1d';
  indicators: IndicatorConfig[];
  overlays: OverlayConfig[];
  theme: 'light' | 'dark';
}

export function AdvancedChart({ data, config, trades }: AdvancedChartProps) {
  const [selectedTimeframe, setTimeframe] = useState(config.timeframe);
  const [indicators, setIndicators] = useState<Indicator[]>([]);

  // Chart engine initialization
  const chart = useChart({
    container: 'chart-container',
    width: 1200,
    height: 600,
    theme: config.theme
  });

  // Render candlesticks
  useEffect(() => {
    chart.renderCandlesticks(
      resampleData(data, selectedTimeframe)
    );
  }, [data, selectedTimeframe]);

  // Trade markers
  const tradeMarkers = trades.map(trade => ({
    time: trade.timestamp,
    position: trade.price,
    type: trade.side === 'buy' ? 'entry' : 'exit',
    color: trade.pnl > 0 ? '#10b981' : '#ef4444'
  }));

  return (
    <div className="chart-container">
      <ChartToolbar
        onTimeframeChange={setTimeframe}
        onIndicatorAdd={addIndicator}
        onExport={exportChart}
      />
      <div id="chart-container" />
      <IndicatorPanel indicators={indicators} />
    </div>
  );
}
```

### Charting Engine
```typescript
// lib/charting/chart-engine.ts
import * as d3 from 'd3';
import { TechnicalIndicators } from 'technical-indicators';

export class ChartEngine {
  private svg: d3.Selection;
  private scales: { x: d3.ScaleTime, y: d3.ScaleLinear };
  private data: OHLC[];

  constructor(config: ChartConfig) {
    this.initializeSVG(config);
    this.setupScales();
    this.setupZoom();
  }

  renderCandlesticks(data: OHLC[]) {
    const candlesticks = this.svg.selectAll('.candlestick')
      .data(data);

    candlesticks.enter()
      .append('g')
      .attr('class', 'candlestick')
      .each(function(d) {
        const g = d3.select(this);

        // High-Low line
        g.append('line')
          .attr('class', 'high-low')
          .attr('x1', 0)
          .attr('x2', 0)
          .attr('y1', d => this.scales.y(d.high))
          .attr('y2', d => this.scales.y(d.low));

        // Open-Close rectangle
        g.append('rect')
          .attr('class', d => d.close > d.open ? 'bullish' : 'bearish')
          .attr('x', -this.candleWidth / 2)
          .attr('y', d => this.scales.y(Math.max(d.open, d.close)))
          .attr('width', this.candleWidth)
          .attr('height', d => Math.abs(this.scales.y(d.open) - this.scales.y(d.close)));
      });
  }

  addIndicator(type: string, params: any) {
    switch(type) {
      case 'SMA':
        const sma = TechnicalIndicators.SMA.calculate({
          period: params.period,
          values: this.data.map(d => d.close)
        });
        this.renderLine(sma, 'sma-line', params.color);
        break;

      case 'RSI':
        const rsi = TechnicalIndicators.RSI.calculate({
          period: params.period,
          values: this.data.map(d => d.close)
        });
        this.renderRSI(rsi);
        break;

      case 'MACD':
        const macd = TechnicalIndicators.MACD.calculate({
          fastPeriod: params.fast,
          slowPeriod: params.slow,
          signalPeriod: params.signal,
          values: this.data.map(d => d.close)
        });
        this.renderMACD(macd);
        break;
    }
  }

  addTradeMarkers(trades: Trade[]) {
    const markers = this.svg.selectAll('.trade-marker')
      .data(trades);

    markers.enter()
      .append('g')
      .attr('class', 'trade-marker')
      .attr('transform', d => `translate(${this.scales.x(d.time)}, ${this.scales.y(d.price)})`)
      .each(function(d) {
        const g = d3.select(this);

        // Arrow marker
        g.append('path')
          .attr('d', d => d.side === 'buy' ?
            'M 0,-10 L -5,0 L 5,0 Z' : 'M 0,10 L -5,0 L 5,0 Z')
          .attr('fill', d => d.pnl > 0 ? '#10b981' : '#ef4444');

        // Hover tooltip
        g.append('title')
          .text(d => `${d.side} @ ${d.price}\nPnL: ${d.pnl}`);
      });
  }
}
```

### Technical Indicators
```typescript
// lib/charting/indicators.ts
export class IndicatorManager {
  private indicators: Map<string, Indicator> = new Map();

  addIndicator(type: IndicatorType, params: IndicatorParams) {
    const indicator = this.createIndicator(type, params);
    this.indicators.set(indicator.id, indicator);
    return indicator;
  }

  private createIndicator(type: IndicatorType, params: IndicatorParams): Indicator {
    switch(type) {
      case 'SMA':
        return new SMAIndicator(params);
      case 'EMA':
        return new EMAIndicator(params);
      case 'BollingerBands':
        return new BollingerBandsIndicator(params);
      case 'RSI':
        return new RSIIndicator(params);
      case 'MACD':
        return new MACDIndicator(params);
      default:
        throw new Error(`Unknown indicator type: ${type}`);
    }
  }

  calculateAll(data: OHLC[]): IndicatorResults {
    const results: IndicatorResults = {};

    for (const [id, indicator] of this.indicators) {
      results[id] = indicator.calculate(data);
    }

    return results;
  }
}

// Specific indicator implementations
class SMAIndicator implements Indicator {
  constructor(private params: { period: number, source: 'close' | 'high' | 'low' }) {}

  calculate(data: OHLC[]): number[] {
    const values = data.map(d => d[this.params.source]);
    return this.movingAverage(values, this.params.period);
  }

  private movingAverage(values: number[], period: number): number[] {
    const result = [];
    for (let i = period - 1; i < values.length; i++) {
      const sum = values.slice(i - period + 1, i + 1).reduce((a, b) => a + b, 0);
      result.push(sum / period);
    }
    return result;
  }
}
```

### Drawing Tools
```typescript
// components/charts/DrawingTools.tsx
export function DrawingTools({ chart }: { chart: ChartEngine }) {
  const [activeTool, setActiveTool] = useState<DrawingTool | null>(null);

  const tools: DrawingTool[] = [
    { id: 'trendline', icon: TrendingUp, name: 'Trendline' },
    { id: 'channel', icon: Maximize2, name: 'Channel' },
    { id: 'fib', icon: Grid, name: 'Fibonacci' },
    { id: 'hline', icon: Minus, name: 'Horizontal Line' },
    { id: 'vline', icon: MoreVertical, name: 'Vertical Line' }
  ];

  const handleToolSelect = (tool: DrawingTool) => {
    setActiveTool(tool);
    chart.setDrawingMode(tool.id);
  };

  return (
    <div className="drawing-tools">
      {tools.map(tool => (
        <Button
          key={tool.id}
          variant={activeTool?.id === tool.id ? 'default' : 'ghost'}
          size="icon"
          onClick={() => handleToolSelect(tool)}
        >
          <tool.icon className="h-4 w-4" />
        </Button>
      ))}
    </div>
  );
}

// Drawing implementation
class DrawingManager {
  private drawings: Drawing[] = [];
  private activeDrawing: Drawing | null = null;

  startDrawing(type: string, startPoint: Point) {
    this.activeDrawing = this.createDrawing(type);
    this.activeDrawing.addPoint(startPoint);
  }

  updateDrawing(point: Point) {
    if (this.activeDrawing) {
      this.activeDrawing.updateLastPoint(point);
      this.render();
    }
  }

  completeDrawing() {
    if (this.activeDrawing) {
      this.drawings.push(this.activeDrawing);
      this.activeDrawing = null;
    }
  }
}
```

### Chart Comparison
```typescript
// components/charts/ChartComparison.tsx
export function ChartComparison({ strategies }: { strategies: Strategy[] }) {
  const [compareMode, setCompareMode] = useState<'overlay' | 'split'>('overlay');
  const [normalizeData, setNormalizeData] = useState(true);

  if (compareMode === 'overlay') {
    return (
      <div className="chart-overlay">
        <AdvancedChart
          data={mergeStrategyData(strategies, normalizeData)}
          config={{
            ...defaultConfig,
            series: strategies.map(s => ({
              name: s.name,
              color: s.color,
              data: s.results
            }))
          }}
        />
      </div>
    );
  }

  return (
    <div className="chart-grid grid grid-cols-2 gap-4">
      {strategies.map(strategy => (
        <AdvancedChart
          key={strategy.id}
          data={strategy.results}
          config={defaultConfig}
          title={strategy.name}
        />
      ))}
    </div>
  );
}
```

### Export Functionality
```typescript
// lib/charting/export.ts
export class ChartExporter {
  static async exportAsImage(chart: ChartEngine, format: 'png' | 'svg' = 'png') {
    const svg = chart.getSVGElement();

    if (format === 'svg') {
      const svgData = new XMLSerializer().serializeToString(svg);
      const blob = new Blob([svgData], { type: 'image/svg+xml' });
      downloadBlob(blob, `chart-${Date.now()}.svg`);
      return;
    }

    // Convert SVG to PNG
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    const img = new Image();

    img.onload = () => {
      canvas.width = img.width;
      canvas.height = img.height;
      ctx.drawImage(img, 0, 0);
      canvas.toBlob(blob => {
        downloadBlob(blob, `chart-${Date.now()}.png`);
      });
    };

    img.src = 'data:image/svg+xml;base64,' + btoa(svgData);
  }

  static exportAsCSV(data: OHLC[], indicators: IndicatorResults) {
    const headers = ['timestamp', 'open', 'high', 'low', 'close', 'volume'];
    const indicatorHeaders = Object.keys(indicators);

    const csv = [
      [...headers, ...indicatorHeaders].join(','),
      ...data.map((row, i) => [
        row.timestamp,
        row.open,
        row.high,
        row.low,
        row.close,
        row.volume,
        ...indicatorHeaders.map(ind => indicators[ind][i] || '')
      ].join(','))
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    downloadBlob(blob, `chart-data-${Date.now()}.csv`);
  }
}
```

## UI/UX Considerations
- Smooth zoom/pan interactions
- Keyboard shortcuts for common actions
- Responsive design for different screen sizes
- Dark mode optimized colors
- Loading states for large datasets
- Tooltips with detailed information

## Testing Requirements
1. Chart rendering performance tests
2. Indicator calculation accuracy
3. Drawing tool precision
4. Export functionality verification
5. Multi-timeframe data resampling
6. Memory usage with large datasets

## Dependencies
- UI_001: Next.js foundation
- UI_015: Basic results visualization
- UI_021: Interactive performance charts

## Story Points: 13

## Priority: High

## Implementation Notes
- Consider using WebGL for large datasets (e.g., Plotly.js)
- Implement data virtualization for performance
- Cache calculated indicators
- Use Web Workers for heavy calculations
