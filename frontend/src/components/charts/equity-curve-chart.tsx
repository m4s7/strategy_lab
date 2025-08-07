'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ChartContainer, ChartTooltip, ChartTooltipContent, ChartLegend, ChartLegendContent } from "@/components/ui/chart";
import { 
  LineChart, 
  Line, 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  ResponsiveContainer,
  Brush,
  ReferenceArea,
  ReferenceLine
} from 'recharts';
import { useState, useRef, useCallback, useMemo } from 'react';
import { format, parseISO } from 'date-fns';
import { 
  Download, 
  ZoomIn, 
  ZoomOut, 
  RotateCcw,
  Crosshair,
  TrendingUp,
  TrendingDown,
  BarChart3
} from 'lucide-react';
import html2canvas from 'html2canvas';

export interface EquityDataPoint {
  timestamp: string;
  equity: number;
  benchmark?: number;
  drawdown_pct: number;
  trade_pnl?: number;
  cumulative_pnl: number;
}

interface DrawdownPeriod {
  start: string;
  end: string;
  magnitude: number;
  duration: number;
}

interface EquityCurveChartProps {
  data: EquityDataPoint[];
  benchmarkData?: EquityDataPoint[];
  drawdownPeriods?: DrawdownPeriod[];
  initialCapital: number;
  title?: string;
  showDrawdown?: boolean;
  timeframe?: 'tick' | 'minute' | 'hour' | 'day';
  interactive?: boolean;
  synchronized?: boolean;
  exportable?: boolean;
  className?: string;
}

const chartConfig = {
  equity: {
    label: "Portfolio Value",
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
};

export function EquityCurveChart({
  data,
  benchmarkData,
  drawdownPeriods,
  initialCapital,
  title = "Equity Curve",
  showDrawdown = true,
  timeframe = 'day',
  interactive = true,
  synchronized = false,
  exportable = true,
  className
}: EquityCurveChartProps) {
  const chartRef = useRef<HTMLDivElement>(null);
  const [zoomDomain, setZoomDomain] = useState<[number, number] | null>(null);
  const [crosshairValue, setCrosshairValue] = useState<any>(null);
  const [selectedArea, setSelectedArea] = useState<any>(null);
  const [chartType, setChartType] = useState<'line' | 'area'>('line');
  const [showBenchmark, setShowBenchmark] = useState(!!benchmarkData);

  // Format data for display with proper time parsing
  const formattedData = useMemo(() => {
    return data.map(point => ({
      ...point,
      timestamp: new Date(point.timestamp).getTime(),
      tooltipTime: format(parseISO(point.timestamp), 'MMM dd, yyyy HH:mm'),
    }));
  }, [data]);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatPercent = (value: number) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  const handleMouseMove = useCallback((nextActiveLabel: any, activePayload: any) => {
    if (interactive && activePayload && activePayload.length > 0) {
      setCrosshairValue({
        label: nextActiveLabel,
        payload: activePayload,
      });
    }
  }, [interactive]);

  const handleBrushChange = useCallback((domain: any) => {
    if (domain && domain.startIndex !== undefined && domain.endIndex !== undefined) {
      const start = formattedData[domain.startIndex]?.timestamp;
      const end = formattedData[domain.endIndex]?.timestamp;
      if (start && end) {
        setZoomDomain([start, end]);
      }
    }
  }, [formattedData]);

  const resetZoom = useCallback(() => {
    setZoomDomain(null);
    setSelectedArea(null);
  }, []);

  const exportChart = useCallback(async (format: 'png' | 'svg' = 'png') => {
    if (!chartRef.current || !exportable) return;
    
    if (format === 'png') {
      const canvas = await html2canvas(chartRef.current);
      const url = canvas.toDataURL('image/png');
      const link = document.createElement('a');
      link.download = `equity-curve-${Date.now()}.png`;
      link.href = url;
      link.click();
    }
  }, [exportable]);

  // Calculate key statistics
  const currentEquity = formattedData[formattedData.length - 1]?.equity || initialCapital;
  const totalReturn = ((currentEquity - initialCapital) / initialCapital) * 100;
  const maxDrawdown = Math.min(...formattedData.map(d => d.drawdown_pct));

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload || !payload.length) return null;

    const data = payload[0].payload;
    return (
      <div className="bg-background/95 border border-border rounded-lg p-3 shadow-lg">
        <p className="text-sm font-medium">{data.tooltipTime}</p>
        <div className="space-y-1 mt-2">
          <div className="flex items-center justify-between space-x-4">
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 rounded-full bg-[--color-equity]" />
              <span className="text-sm">Portfolio Value:</span>
            </div>
            <span className="text-sm font-medium">{formatCurrency(data.equity)}</span>
          </div>
          {data.benchmark && (
            <div className="flex items-center justify-between space-x-4">
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 rounded-full bg-[--color-benchmark]" />
                <span className="text-sm">Benchmark:</span>
              </div>
              <span className="text-sm font-medium">{formatCurrency(data.benchmark)}</span>
            </div>
          )}
          <div className="flex items-center justify-between space-x-4">
            <span className="text-sm">Drawdown:</span>
            <span className={`text-sm font-medium ${data.drawdown_pct < 0 ? 'text-red-600' : 'text-green-600'}`}>
              {formatPercent(data.drawdown_pct)}
            </span>
          </div>
          {data.trade_pnl !== undefined && (
            <div className="flex items-center justify-between space-x-4">
              <span className="text-sm">Trade P&L:</span>
              <span className={`text-sm font-medium ${data.trade_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {formatCurrency(data.trade_pnl)}
              </span>
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center space-x-2">
              <BarChart3 className="h-5 w-5" />
              <span>{title}</span>
            </CardTitle>
            <CardDescription>
              Interactive equity curve showing portfolio performance over time
            </CardDescription>
          </div>
          <div className="flex items-center space-x-2">
            <Badge variant={totalReturn >= 0 ? 'default' : 'destructive'}>
              {formatPercent(totalReturn)}
            </Badge>
            {exportable && (
              <Button variant="outline" size="sm" onClick={() => exportChart('png')}>
                <Download className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {/* Chart Controls */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <Select value={chartType} onValueChange={(value: 'line' | 'area') => setChartType(value)}>
              <SelectTrigger className="w-24">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="line">Line</SelectItem>
                <SelectItem value="area">Area</SelectItem>
              </SelectContent>
            </Select>
            
            {benchmarkData && (
              <Button
                variant={showBenchmark ? "default" : "outline"}
                size="sm"
                onClick={() => setShowBenchmark(!showBenchmark)}
              >
                Benchmark
              </Button>
            )}
          </div>

          <div className="flex items-center space-x-2">
            {zoomDomain && (
              <Button variant="outline" size="sm" onClick={resetZoom}>
                <RotateCcw className="h-4 w-4" />
              </Button>
            )}
            <Button variant="outline" size="sm">
              <ZoomIn className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="text-center p-3 bg-muted/30 rounded-lg">
            <div className={`text-lg font-medium ${totalReturn >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {formatCurrency(currentEquity)}
            </div>
            <div className="text-xs text-muted-foreground">Current Value</div>
          </div>
          <div className="text-center p-3 bg-muted/30 rounded-lg">
            <div className={`text-lg font-medium ${totalReturn >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {formatPercent(totalReturn)}
            </div>
            <div className="text-xs text-muted-foreground">Total Return</div>
          </div>
          <div className="text-center p-3 bg-muted/30 rounded-lg">
            <div className="text-lg font-medium text-red-600">
              {formatPercent(maxDrawdown)}
            </div>
            <div className="text-xs text-muted-foreground">Max Drawdown</div>
          </div>
        </div>

        {/* Main Chart */}
        <div ref={chartRef} className="h-96">
          <ChartContainer config={chartConfig} className="h-full w-full">
            {chartType === 'area' ? (
              <AreaChart
                data={formattedData}
                onMouseMove={handleMouseMove}
                onMouseLeave={() => setCrosshairValue(null)}
              >
                <defs>
                  <linearGradient id="equityGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="hsl(var(--chart-1))" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="hsl(var(--chart-1))" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                <XAxis
                  dataKey="timestamp"
                  type="number"
                  scale="time"
                  domain={zoomDomain || ['dataMin', 'dataMax']}
                  tickFormatter={(value) => format(new Date(value), 'MMM dd')}
                />
                <YAxis
                  domain={['dataMin', 'dataMax']}
                  tickFormatter={(value) => formatCurrency(value)}
                />
                <ChartTooltip content={<CustomTooltip />} />
                <ChartLegend content={<ChartLegendContent />} />
                <Area
                  type="monotone"
                  dataKey="equity"
                  stroke="hsl(var(--chart-1))"
                  fill="url(#equityGradient)"
                  strokeWidth={2}
                />
                {showBenchmark && benchmarkData && (
                  <Area
                    type="monotone"
                    dataKey="benchmark"
                    stroke="hsl(var(--chart-2))"
                    fill="transparent"
                    strokeWidth={2}
                    strokeDasharray="5 5"
                  />
                )}
                {interactive && (
                  <Brush
                    dataKey="timestamp"
                    height={30}
                    stroke="hsl(var(--chart-1))"
                    onChange={handleBrushChange}
                  />
                )}
              </AreaChart>
            ) : (
              <LineChart
                data={formattedData}
                onMouseMove={handleMouseMove}
                onMouseLeave={() => setCrosshairValue(null)}
              >
                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                <XAxis
                  dataKey="timestamp"
                  type="number"
                  scale="time"
                  domain={zoomDomain || ['dataMin', 'dataMax']}
                  tickFormatter={(value) => format(new Date(value), 'MMM dd')}
                />
                <YAxis
                  domain={['dataMin', 'dataMax']}
                  tickFormatter={(value) => formatCurrency(value)}
                />
                <ChartTooltip content={<CustomTooltip />} />
                <ChartLegend content={<ChartLegendContent />} />
                <Line
                  type="monotone"
                  dataKey="equity"
                  stroke="hsl(var(--chart-1))"
                  strokeWidth={2}
                  dot={false}
                />
                {showBenchmark && benchmarkData && (
                  <Line
                    type="monotone"
                    dataKey="benchmark"
                    stroke="hsl(var(--chart-2))"
                    strokeWidth={2}
                    strokeDasharray="5 5"
                    dot={false}
                  />
                )}
                
                {/* Drawdown period shading */}
                {showDrawdown && drawdownPeriods && drawdownPeriods.map((period, index) => (
                  <ReferenceArea
                    key={index}
                    x1={new Date(period.start).getTime()}
                    x2={new Date(period.end).getTime()}
                    fill="hsl(var(--destructive))"
                    fillOpacity={0.1}
                  />
                ))}
                
                {interactive && (
                  <Brush
                    dataKey="timestamp"
                    height={30}
                    stroke="hsl(var(--chart-1))"
                    onChange={handleBrushChange}
                  />
                )}
              </LineChart>
            )}
          </ChartContainer>
        </div>

        {/* Crosshair Information */}
        {crosshairValue && (
          <div className="mt-4 p-3 bg-muted/50 rounded-lg">
            <div className="flex items-center space-x-2">
              <Crosshair className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm font-medium">Crosshair Data</span>
            </div>
            <div className="mt-2 text-sm text-muted-foreground">
              Click and drag to zoom into a specific time period
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}