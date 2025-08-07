'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart";
import { 
  LineChart, 
  Line, 
  AreaChart, 
  Area, 
  BarChart, 
  Bar,
  XAxis, 
  YAxis, 
  CartesianGrid,
  ResponsiveContainer,
  ReferenceLine,
  Brush
} from 'recharts';
import { useState, useRef, useCallback, useMemo } from 'react';
import { format, parseISO, differenceInDays } from 'date-fns';
import { 
  Download, 
  TrendingDown,
  Activity,
  Clock,
  AlertTriangle
} from 'lucide-react';

export interface DrawdownDataPoint {
  timestamp: string;
  equity: number;
  peak: number;
  drawdown: number;
  drawdown_pct: number;
  underwater: boolean;
}

interface DrawdownPeriod {
  start: string;
  end: string;
  peak: number;
  trough: number;
  recovery?: string;
  magnitude: number;
  duration: number;
  recoveryDuration?: number;
}

interface DrawdownChartProps {
  data: DrawdownDataPoint[];
  drawdownPeriods: DrawdownPeriod[];
  className?: string;
}

const chartConfig = {
  drawdown: {
    label: "Drawdown %",
    color: "hsl(var(--destructive))",
  },
  peak: {
    label: "Peak Value",
    color: "hsl(var(--chart-1))",
  },
  equity: {
    label: "Portfolio Value",
    color: "hsl(var(--chart-2))",
  },
};

export function DrawdownChart({ data, drawdownPeriods, className }: DrawdownChartProps) {
  const chartRef = useRef<HTMLDivElement>(null);
  const [activeView, setActiveView] = useState<'underwater' | 'rolling' | 'distribution' | 'periods'>('underwater');

  const formattedData = useMemo(() => {
    return data.map(point => ({
      ...point,
      timestamp: new Date(point.timestamp).getTime(),
      tooltipTime: format(parseISO(point.timestamp), 'MMM dd, yyyy'),
    }));
  }, [data]);

  // Calculate drawdown distribution for histogram
  const drawdownDistribution = useMemo(() => {
    const bins = 20;
    const maxDrawdown = Math.min(...data.map(d => d.drawdown_pct));
    const binSize = Math.abs(maxDrawdown) / bins;
    
    const histogram = Array.from({ length: bins }, (_, i) => ({
      range: `${(-binSize * (i + 1)).toFixed(1)}%`,
      count: 0,
      bin: -binSize * (i + 1)
    }));
    
    data.forEach(point => {
      if (point.drawdown_pct < 0) {
        const binIndex = Math.min(Math.floor(Math.abs(point.drawdown_pct) / binSize), bins - 1);
        histogram[binIndex].count++;
      }
    });
    
    return histogram.filter(bin => bin.count > 0);
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
    return `${value.toFixed(2)}%`;
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload || !payload.length) return null;

    const data = payload[0].payload;
    return (
      <div className="bg-background/95 border border-border rounded-lg p-3 shadow-lg">
        <p className="text-sm font-medium">{data.tooltipTime}</p>
        <div className="space-y-1 mt-2">
          <div className="flex items-center justify-between space-x-4">
            <span className="text-sm">Equity:</span>
            <span className="text-sm font-medium">{formatCurrency(data.equity)}</span>
          </div>
          <div className="flex items-center justify-between space-x-4">
            <span className="text-sm">Peak:</span>
            <span className="text-sm font-medium">{formatCurrency(data.peak)}</span>
          </div>
          <div className="flex items-center justify-between space-x-4">
            <span className="text-sm">Drawdown:</span>
            <span className="text-sm font-medium text-red-600">{formatPercent(data.drawdown_pct)}</span>
          </div>
          <div className="flex items-center justify-between space-x-4">
            <span className="text-sm">Amount:</span>
            <span className="text-sm font-medium text-red-600">{formatCurrency(data.drawdown)}</span>
          </div>
        </div>
      </div>
    );
  };

  // Calculate key statistics
  const maxDrawdownPeriod = drawdownPeriods.reduce((max, period) => 
    Math.abs(period.magnitude) > Math.abs(max.magnitude) ? period : max
  );
  
  const avgDrawdownDuration = drawdownPeriods.reduce((sum, p) => sum + p.duration, 0) / drawdownPeriods.length;
  const avgRecoveryTime = drawdownPeriods
    .filter(p => p.recoveryDuration)
    .reduce((sum, p) => sum + (p.recoveryDuration || 0), 0) / drawdownPeriods.filter(p => p.recoveryDuration).length;

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <TrendingDown className="h-5 w-5" />
          <span>Drawdown Analysis</span>
        </CardTitle>
        <CardDescription>
          Comprehensive analysis of portfolio drawdown periods and recovery patterns
        </CardDescription>
      </CardHeader>
      <CardContent>
        {/* Key Statistics */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div className="text-center p-3 bg-red-50 dark:bg-red-950/20 rounded-lg">
            <div className="text-lg font-medium text-red-600">
              {formatPercent(maxDrawdownPeriod.magnitude)}
            </div>
            <div className="text-xs text-muted-foreground">Max Drawdown</div>
          </div>
          <div className="text-center p-3 bg-muted/30 rounded-lg">
            <div className="text-lg font-medium">
              {drawdownPeriods.length}
            </div>
            <div className="text-xs text-muted-foreground">Drawdown Periods</div>
          </div>
          <div className="text-center p-3 bg-muted/30 rounded-lg">
            <div className="text-lg font-medium">
              {Math.round(avgDrawdownDuration)} days
            </div>
            <div className="text-xs text-muted-foreground">Avg Duration</div>
          </div>
          <div className="text-center p-3 bg-muted/30 rounded-lg">
            <div className="text-lg font-medium">
              {isNaN(avgRecoveryTime) ? 'N/A' : `${Math.round(avgRecoveryTime)} days`}
            </div>
            <div className="text-xs text-muted-foreground">Avg Recovery</div>
          </div>
        </div>

        {/* Chart Tabs */}
        <Tabs value={activeView} onValueChange={(value: any) => setActiveView(value)}>
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="underwater">Underwater</TabsTrigger>
            <TabsTrigger value="rolling">Rolling DD</TabsTrigger>
            <TabsTrigger value="distribution">Distribution</TabsTrigger>
            <TabsTrigger value="periods">Periods</TabsTrigger>
          </TabsList>

          <TabsContent value="underwater" className="space-y-4">
            <div className="h-80">
              <ChartContainer config={chartConfig} className="h-full w-full">
                <AreaChart data={formattedData}>
                  <defs>
                    <linearGradient id="drawdownGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="hsl(var(--destructive))" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="hsl(var(--destructive))" stopOpacity={0.0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                  <XAxis
                    dataKey="timestamp"
                    type="number"
                    scale="time"
                    tickFormatter={(value) => format(new Date(value), 'MMM dd')}
                  />
                  <YAxis
                    tickFormatter={(value) => `${value.toFixed(1)}%`}
                  />
                  <ChartTooltip content={<CustomTooltip />} />
                  <Area
                    type="monotone"
                    dataKey="drawdown_pct"
                    stroke="hsl(var(--destructive))"
                    fill="url(#drawdownGradient)"
                    strokeWidth={2}
                  />
                  <ReferenceLine y={0} stroke="hsl(var(--muted-foreground))" strokeDasharray="2 2" />
                </AreaChart>
              </ChartContainer>
            </div>
          </TabsContent>

          <TabsContent value="rolling" className="space-y-4">
            <div className="h-80">
              <ChartContainer config={chartConfig} className="h-full w-full">
                <LineChart data={formattedData}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                  <XAxis
                    dataKey="timestamp"
                    type="number"
                    scale="time"
                    tickFormatter={(value) => format(new Date(value), 'MMM dd')}
                  />
                  <YAxis
                    tickFormatter={(value) => `${value.toFixed(1)}%`}
                  />
                  <ChartTooltip content={<CustomTooltip />} />
                  <Line
                    type="monotone"
                    dataKey="drawdown_pct"
                    stroke="hsl(var(--destructive))"
                    strokeWidth={2}
                    dot={false}
                  />
                  <ReferenceLine y={0} stroke="hsl(var(--muted-foreground))" strokeDasharray="2 2" />
                  <ReferenceLine y={maxDrawdownPeriod.magnitude} stroke="hsl(var(--destructive))" strokeDasharray="5 5" />
                </LineChart>
              </ChartContainer>
            </div>
          </TabsContent>

          <TabsContent value="distribution" className="space-y-4">
            <div className="h-80">
              <ChartContainer config={chartConfig} className="h-full w-full">
                <BarChart data={drawdownDistribution}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                  <XAxis dataKey="range" />
                  <YAxis />
                  <ChartTooltip 
                    content={({ active, payload }: any) => {
                      if (!active || !payload?.[0]) return null;
                      return (
                        <div className="bg-background/95 border border-border rounded-lg p-3 shadow-lg">
                          <p className="text-sm">Drawdown Range: {payload[0].payload.range}</p>
                          <p className="text-sm">Count: {payload[0].value} occurrences</p>
                        </div>
                      );
                    }} 
                  />
                  <Bar dataKey="count" fill="hsl(var(--destructive))" />
                </BarChart>
              </ChartContainer>
            </div>
          </TabsContent>

          <TabsContent value="periods" className="space-y-4">
            {/* Drawdown Periods Table */}
            <div className="rounded-md border">
              <div className="p-4">
                <h4 className="text-sm font-medium mb-3">Drawdown Periods Detail</h4>
                <div className="space-y-3 max-h-64 overflow-y-auto">
                  {drawdownPeriods.map((period, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-muted/30 rounded-lg">
                      <div className="space-y-1">
                        <div className="flex items-center space-x-2">
                          <AlertTriangle className="h-4 w-4 text-red-600" />
                          <span className="text-sm font-medium">
                            {format(parseISO(period.start), 'MMM dd, yyyy')} - {format(parseISO(period.end), 'MMM dd, yyyy')}
                          </span>
                        </div>
                        <div className="flex items-center space-x-4 text-xs text-muted-foreground">
                          <div className="flex items-center space-x-1">
                            <TrendingDown className="h-3 w-3" />
                            <span>Magnitude: {formatPercent(period.magnitude)}</span>
                          </div>
                          <div className="flex items-center space-x-1">
                            <Clock className="h-3 w-3" />
                            <span>Duration: {period.duration} days</span>
                          </div>
                          {period.recoveryDuration && (
                            <div className="flex items-center space-x-1">
                              <Activity className="h-3 w-3" />
                              <span>Recovery: {period.recoveryDuration} days</span>
                            </div>
                          )}
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-sm font-medium text-red-600">
                          {formatCurrency(period.trough - period.peak)}
                        </div>
                        <div className="text-xs text-muted-foreground">Loss Amount</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}