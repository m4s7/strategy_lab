'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart";
import { 
  BarChart, 
  Bar, 
  LineChart,
  Line,
  XAxis, 
  YAxis, 
  CartesianGrid, 
  ResponsiveContainer,
  Brush,
  ReferenceLine
} from 'recharts';
import { useState, useRef, useCallback, useMemo } from 'react';
import { 
  Download, 
  BarChart3,
  TrendingUp,
  Activity,
  Info
} from 'lucide-react';

export interface ReturnsDataPoint {
  tradeId: string;
  timestamp: string;
  return_pct: number;
  return_amount: number;
  duration: number;
  type: 'long' | 'short';
}

interface DistributionBin {
  bin: string;
  count: number;
  percentage: number;
  minValue: number;
  maxValue: number;
  cumulative: number;
}

interface DistributionStats {
  mean: number;
  median: number;
  std: number;
  skewness: number;
  kurtosis: number;
  min: number;
  max: number;
  percentiles: {
    p1: number;
    p5: number;
    p25: number;
    p75: number;
    p95: number;
    p99: number;
  };
}

interface ReturnsDistributionChartProps {
  data: ReturnsDataPoint[];
  bins?: number;
  showNormalDistribution?: boolean;
  interactive?: boolean;
  exportable?: boolean;
  className?: string;
}

const chartConfig = {
  returns: {
    label: "Returns",
    color: "hsl(var(--chart-1))",
  },
  normal: {
    label: "Normal Distribution",
    color: "hsl(var(--chart-2))",
  },
  cumulative: {
    label: "Cumulative %",
    color: "hsl(var(--chart-3))",
  },
};

export function ReturnsDistributionChart({
  data,
  bins = 30,
  showNormalDistribution = true,
  interactive = true,
  exportable = true,
  className
}: ReturnsDistributionChartProps) {
  const chartRef = useRef<HTMLDivElement>(null);
  const [activeBins, setActiveBins] = useState(bins);
  const [viewType, setViewType] = useState<'histogram' | 'boxplot' | 'qq-plot'>('histogram');
  const [selectedRange, setSelectedRange] = useState<[number, number] | null>(null);

  // Calculate statistics
  const stats = useMemo(() => {
    const returns = data.map(d => d.return_pct).sort((a, b) => a - b);
    const n = returns.length;
    
    if (n === 0) return null;

    const mean = returns.reduce((sum, val) => sum + val, 0) / n;
    const median = n % 2 === 0 ? 
      (returns[n / 2 - 1] + returns[n / 2]) / 2 : 
      returns[Math.floor(n / 2)];
    
    const variance = returns.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / (n - 1);
    const std = Math.sqrt(variance);
    
    const skewness = returns.reduce((sum, val) => sum + Math.pow((val - mean) / std, 3), 0) / n;
    const kurtosis = returns.reduce((sum, val) => sum + Math.pow((val - mean) / std, 4), 0) / n - 3;

    const getPercentile = (p: number) => {
      const index = Math.ceil((p / 100) * n) - 1;
      return returns[Math.max(0, Math.min(n - 1, index))];
    };

    return {
      mean,
      median,
      std,
      skewness,
      kurtosis,
      min: returns[0],
      max: returns[n - 1],
      percentiles: {
        p1: getPercentile(1),
        p5: getPercentile(5),
        p25: getPercentile(25),
        p75: getPercentile(75),
        p95: getPercentile(95),
        p99: getPercentile(99),
      }
    } as DistributionStats;
  }, [data]);

  // Create histogram bins
  const histogram = useMemo(() => {
    if (!stats) return [];
    
    const returns = data.map(d => d.return_pct);
    const { min, max } = stats;
    const binWidth = (max - min) / activeBins;
    
    const bins: DistributionBin[] = Array.from({ length: activeBins }, (_, i) => ({
      bin: `${(min + i * binWidth).toFixed(1)}%`,
      count: 0,
      percentage: 0,
      minValue: min + i * binWidth,
      maxValue: min + (i + 1) * binWidth,
      cumulative: 0
    }));

    returns.forEach(returnVal => {
      if (returnVal === max) {
        bins[activeBins - 1].count++;
      } else {
        const binIndex = Math.floor((returnVal - min) / binWidth);
        if (binIndex >= 0 && binIndex < activeBins) {
          bins[binIndex].count++;
        }
      }
    });

    let cumulative = 0;
    bins.forEach(bin => {
      bin.percentage = (bin.count / returns.length) * 100;
      cumulative += bin.percentage;
      bin.cumulative = cumulative;
    });

    return bins;
  }, [data, activeBins, stats]);

  // Normal distribution overlay data
  const normalDistribution = useMemo(() => {
    if (!stats || !showNormalDistribution) return [];
    
    const { mean, std } = stats;
    return histogram.map(bin => {
      const x = (bin.minValue + bin.maxValue) / 2;
      const normalDensity = (1 / (std * Math.sqrt(2 * Math.PI))) * 
        Math.exp(-0.5 * Math.pow((x - mean) / std, 2));
      
      return {
        ...bin,
        normalCount: normalDensity * data.length * ((bin.maxValue - bin.minValue)),
        normalPercentage: normalDensity * 100 * ((bin.maxValue - bin.minValue))
      };
    });
  }, [histogram, stats, showNormalDistribution, data.length]);

  // Box plot data
  const boxPlotData = useMemo(() => {
    if (!stats) return [];
    
    const { percentiles, min, max, mean, median } = stats;
    return [{
      category: 'Returns Distribution',
      min,
      q1: percentiles.p25,
      median,
      q3: percentiles.p75,
      max,
      mean,
      outliers: data.filter(d => 
        d.return_pct < percentiles.p5 || d.return_pct > percentiles.p95
      ).map(d => d.return_pct)
    }];
  }, [stats, data]);

  const formatPercent = (value: number) => `${value.toFixed(2)}%`;
  const formatDecimal = (value: number, decimals = 2) => value.toFixed(decimals);

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload || !payload.length) return null;

    const data = payload[0].payload;
    return (
      <div className="bg-background/95 border border-border rounded-lg p-3 shadow-lg">
        <p className="text-sm font-medium">{data.bin}</p>
        <div className="space-y-1 mt-2">
          <div className="flex items-center justify-between space-x-4">
            <span className="text-sm">Count:</span>
            <span className="text-sm font-medium">{data.count}</span>
          </div>
          <div className="flex items-center justify-between space-x-4">
            <span className="text-sm">Percentage:</span>
            <span className="text-sm font-medium">{formatPercent(data.percentage)}</span>
          </div>
          <div className="flex items-center justify-between space-x-4">
            <span className="text-sm">Cumulative:</span>
            <span className="text-sm font-medium">{formatPercent(data.cumulative)}</span>
          </div>
          {showNormalDistribution && (
            <div className="flex items-center justify-between space-x-4">
              <span className="text-sm">Expected (Normal):</span>
              <span className="text-sm font-medium">{data.normalCount?.toFixed(0) || 0}</span>
            </div>
          )}
        </div>
      </div>
    );
  };

  const handleBrushChange = useCallback((domain: any) => {
    if (domain && domain.startIndex !== undefined && domain.endIndex !== undefined) {
      const startBin = histogram[domain.startIndex];
      const endBin = histogram[domain.endIndex];
      if (startBin && endBin) {
        setSelectedRange([startBin.minValue, endBin.maxValue]);
      }
    }
  }, [histogram]);

  if (!stats) {
    return (
      <Card className={className}>
        <CardContent className="p-6">
          <div className="text-center text-muted-foreground">No data available</div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center space-x-2">
              <BarChart3 className="h-5 w-5" />
              <span>Returns Distribution Analysis</span>
            </CardTitle>
            <CardDescription>
              Statistical analysis of trade returns with distribution fitting
            </CardDescription>
          </div>
          <div className="flex items-center space-x-2">
            <Badge variant="outline">
              {data.length} trades
            </Badge>
            {exportable && (
              <Button variant="outline" size="sm">
                <Download className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {/* Statistics Summary */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div className="text-center p-3 bg-muted/30 rounded-lg">
            <div className={`text-lg font-medium ${stats.mean >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {formatPercent(stats.mean)}
            </div>
            <div className="text-xs text-muted-foreground">Mean Return</div>
          </div>
          <div className="text-center p-3 bg-muted/30 rounded-lg">
            <div className="text-lg font-medium">
              {formatPercent(stats.std)}
            </div>
            <div className="text-xs text-muted-foreground">Std Deviation</div>
          </div>
          <div className="text-center p-3 bg-muted/30 rounded-lg">
            <div className="text-lg font-medium">
              {formatDecimal(stats.skewness)}
            </div>
            <div className="text-xs text-muted-foreground">Skewness</div>
          </div>
          <div className="text-center p-3 bg-muted/30 rounded-lg">
            <div className="text-lg font-medium">
              {formatDecimal(stats.kurtosis)}
            </div>
            <div className="text-xs text-muted-foreground">Kurtosis</div>
          </div>
        </div>

        {/* Controls */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <Select value={activeBins.toString()} onValueChange={(value) => setActiveBins(parseInt(value))}>
              <SelectTrigger className="w-24">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="15">15</SelectItem>
                <SelectItem value="30">30</SelectItem>
                <SelectItem value="50">50</SelectItem>
                <SelectItem value="100">100</SelectItem>
              </SelectContent>
            </Select>
            
            <Button
              variant={showNormalDistribution ? "default" : "outline"}
              size="sm"
              onClick={() => setViewType(viewType === 'histogram' ? 'boxplot' : 'histogram')}
            >
              {viewType === 'histogram' ? 'Box Plot' : 'Histogram'}
            </Button>
          </div>

          <div className="flex items-center space-x-2">
            <Badge variant="outline">
              Range: {formatPercent(stats.min)} to {formatPercent(stats.max)}
            </Badge>
          </div>
        </div>

        {/* Chart Tabs */}
        <Tabs value={viewType} onValueChange={(value: any) => setViewType(value)}>
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="histogram">Histogram</TabsTrigger>
            <TabsTrigger value="boxplot">Box Plot</TabsTrigger>
            <TabsTrigger value="qq-plot">Q-Q Plot</TabsTrigger>
          </TabsList>

          <TabsContent value="histogram" className="space-y-4">
            <div ref={chartRef} className="h-96">
              <ChartContainer config={chartConfig} className="h-full w-full">
                <BarChart data={normalDistribution}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                  <XAxis 
                    dataKey="bin" 
                    tickFormatter={(value) => value.replace('%', '')}
                  />
                  <YAxis />
                  <ChartTooltip content={<CustomTooltip />} />
                  <Bar 
                    dataKey="count" 
                    fill="hsl(var(--chart-1))" 
                    fillOpacity={0.7}
                  />
                  {showNormalDistribution && (
                    <Line 
                      type="monotone" 
                      dataKey="normalCount" 
                      stroke="hsl(var(--chart-2))" 
                      strokeWidth={2}
                      dot={false}
                    />
                  )}
                  
                  {/* Percentile markers */}
                  <ReferenceLine 
                    x={`${stats.percentiles.p5.toFixed(1)}%`} 
                    stroke="hsl(var(--chart-3))" 
                    strokeDasharray="2 2" 
                    label="5th %" 
                  />
                  <ReferenceLine 
                    x={`${stats.percentiles.p95.toFixed(1)}%`} 
                    stroke="hsl(var(--chart-3))" 
                    strokeDasharray="2 2" 
                    label="95th %" 
                  />
                  
                  {interactive && (
                    <Brush
                      dataKey="bin"
                      height={30}
                      stroke="hsl(var(--chart-1))"
                      onChange={handleBrushChange}
                    />
                  )}
                </BarChart>
              </ChartContainer>
            </div>
          </TabsContent>

          <TabsContent value="boxplot" className="space-y-4">
            <div className="h-96 flex items-center justify-center">
              <div className="text-center space-y-4">
                <div className="text-6xl font-light text-muted-foreground">📊</div>
                <div className="text-lg font-medium">Box Plot Visualization</div>
                <div className="text-sm text-muted-foreground max-w-md">
                  Box plot would show quartiles, median, and outliers for the returns distribution
                </div>
                
                {/* Simple box plot representation */}
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span>Min:</span>
                    <span className="font-medium">{formatPercent(stats.min)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Q1 (25%):</span>
                    <span className="font-medium">{formatPercent(stats.percentiles.p25)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Median:</span>
                    <span className="font-medium">{formatPercent(stats.median)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Q3 (75%):</span>
                    <span className="font-medium">{formatPercent(stats.percentiles.p75)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Max:</span>
                    <span className="font-medium">{formatPercent(stats.max)}</span>
                  </div>
                </div>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="qq-plot" className="space-y-4">
            <div className="h-96 flex items-center justify-center">
              <div className="text-center space-y-4">
                <div className="text-6xl font-light text-muted-foreground">📈</div>
                <div className="text-lg font-medium">Q-Q Plot</div>
                <div className="text-sm text-muted-foreground max-w-md">
                  Quantile-quantile plot comparing sample quantiles against theoretical normal distribution
                </div>
                
                <div className="grid grid-cols-2 gap-4 text-sm max-w-sm">
                  <div className="text-center p-2 bg-muted/30 rounded">
                    <div className="font-medium">{formatDecimal(stats.skewness)}</div>
                    <div className="text-xs text-muted-foreground">Skewness</div>
                  </div>
                  <div className="text-center p-2 bg-muted/30 rounded">
                    <div className="font-medium">{formatDecimal(stats.kurtosis)}</div>
                    <div className="text-xs text-muted-foreground">Excess Kurtosis</div>
                  </div>
                </div>
              </div>
            </div>
          </TabsContent>
        </Tabs>

        {/* Percentile Information */}
        <div className="mt-6 p-4 bg-muted/20 rounded-lg">
          <div className="flex items-center space-x-2 mb-3">
            <Info className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm font-medium">Percentile Analysis</span>
          </div>
          <div className="grid grid-cols-3 lg:grid-cols-6 gap-3 text-xs">
            <div className="text-center">
              <div className="font-medium">{formatPercent(stats.percentiles.p1)}</div>
              <div className="text-muted-foreground">1st %</div>
            </div>
            <div className="text-center">
              <div className="font-medium">{formatPercent(stats.percentiles.p5)}</div>
              <div className="text-muted-foreground">5th %</div>
            </div>
            <div className="text-center">
              <div className="font-medium">{formatPercent(stats.percentiles.p25)}</div>
              <div className="text-muted-foreground">25th %</div>
            </div>
            <div className="text-center">
              <div className="font-medium">{formatPercent(stats.percentiles.p75)}</div>
              <div className="text-muted-foreground">75th %</div>
            </div>
            <div className="text-center">
              <div className="font-medium">{formatPercent(stats.percentiles.p95)}</div>
              <div className="text-muted-foreground">95th %</div>
            </div>
            <div className="text-center">
              <div className="font-medium">{formatPercent(stats.percentiles.p99)}</div>
              <div className="text-muted-foreground">99th %</div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}