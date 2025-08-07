'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { ChartContainer, ChartTooltip, ChartTooltipContent, ChartLegend, ChartLegendContent } from "@/components/ui/chart";
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid,
  ResponsiveContainer,
  Brush,
  ReferenceLine
} from 'recharts';
import { useState, useMemo, useCallback } from 'react';
import { 
  TrendingUp, 
  BarChart3,
  Download,
  Grid3X3,
  Layers,
  Eye,
  Settings
} from 'lucide-react';
import { OHLC } from '@/lib/charting/types';
import { DataResampler, TimeFormatter, PriceFormatter } from '@/lib/charting/data-utils';
import { AdvancedChart } from './advanced-chart';

interface Strategy {
  id: string;
  name: string;
  data: OHLC[];
  color: string;
  visible: boolean;
  initialCapital?: number;
}

interface ChartComparisonProps {
  strategies: Strategy[];
  title?: string;
  className?: string;
}

const comparisonColors = [
  '#2563eb', // Blue
  '#dc2626', // Red
  '#059669', // Green
  '#7c3aed', // Purple
  '#ea580c', // Orange
  '#0891b2', // Cyan
  '#be185d', // Pink
  '#65a30d'  // Lime
];

export function ChartComparison({ 
  strategies, 
  title = "Strategy Comparison",
  className 
}: ChartComparisonProps) {
  const [compareMode, setCompareMode] = useState<'overlay' | 'normalized' | 'grid'>('overlay');
  const [normalizeData, setNormalizeData] = useState(true);
  const [timeframe, setTimeframe] = useState('1h');
  const [showStats, setShowStats] = useState(true);
  const [selectedStrategies, setSelectedStrategies] = useState<string[]>(
    strategies.map(s => s.id)
  );

  // Filter visible strategies
  const visibleStrategies = useMemo(() => {
    return strategies.filter(s => selectedStrategies.includes(s.id));
  }, [strategies, selectedStrategies]);

  // Prepare comparison data
  const comparisonData = useMemo(() => {
    if (!visibleStrategies.length) return [];

    // Resample all strategies to the same timeframe
    const resampledStrategies = visibleStrategies.map(strategy => ({
      ...strategy,
      data: DataResampler.resample(strategy.data, timeframe)
    }));

    // Find common time range
    const minLength = Math.min(...resampledStrategies.map(s => s.data.length));
    const maxTimestamp = Math.max(...resampledStrategies.map(s => 
      s.data.length > 0 ? s.data[s.data.length - 1].timestamp : 0
    ));

    // Create combined dataset
    const combinedData: any[] = [];
    const maxDataLength = Math.max(...resampledStrategies.map(s => s.data.length));

    for (let i = 0; i < maxDataLength; i++) {
      const dataPoint: any = {
        index: i,
        timestamp: 0,
        time: ''
      };

      resampledStrategies.forEach((strategy, strategyIndex) => {
        const candle = strategy.data[i];
        if (candle) {
          const timestamp = typeof candle.timestamp === 'number' ? candle.timestamp : new Date(candle.timestamp).getTime();
          
          if (dataPoint.timestamp === 0) {
            dataPoint.timestamp = timestamp;
            dataPoint.time = TimeFormatter.formatTimestamp(timestamp, timeframe);
          }

          // Calculate equity curve (cumulative returns)
          const price = candle.close;
          let equityValue = price;

          if (normalizeData) {
            // Normalize to percentage returns from first price
            const firstPrice = strategy.data[0]?.close || price;
            equityValue = ((price - firstPrice) / firstPrice) * 100 + 100; // Start at 100%
          } else if (strategy.initialCapital) {
            // Convert to portfolio value
            const firstPrice = strategy.data[0]?.close || price;
            equityValue = strategy.initialCapital * (price / firstPrice);
          }

          dataPoint[`${strategy.id}_equity`] = equityValue;
          dataPoint[`${strategy.id}_price`] = price;
          dataPoint[`${strategy.id}_volume`] = candle.volume || 0;
        }
      });

      if (dataPoint.timestamp > 0) {
        combinedData.push(dataPoint);
      }
    }

    return combinedData;
  }, [visibleStrategies, timeframe, normalizeData]);

  // Calculate strategy statistics
  const strategyStats = useMemo(() => {
    return visibleStrategies.map(strategy => {
      const stats = DataResampler.getStatistics(strategy.data);
      if (!stats) return null;

      const equityData = comparisonData.map(d => d[`${strategy.id}_equity`]).filter(v => v !== undefined);
      const maxEquity = Math.max(...equityData);
      const minEquity = Math.min(...equityData);
      const finalEquity = equityData[equityData.length - 1] || 0;
      const maxDrawdown = normalizeData ? 
        ((minEquity - maxEquity) / maxEquity) * 100 :
        minEquity - maxEquity;

      return {
        id: strategy.id,
        name: strategy.name,
        color: strategy.color,
        finalReturn: normalizeData ? finalEquity - 100 : ((finalEquity - (strategy.initialCapital || 100000)) / (strategy.initialCapital || 100000)) * 100,
        maxDrawdown,
        volatility: stats.volatility * 100,
        sharpeRatio: stats.avgReturn / stats.volatility, // Simplified Sharpe ratio
        totalTrades: strategy.data.length,
        winRate: 0 // Would need actual trade data to calculate
      };
    }).filter(Boolean);
  }, [visibleStrategies, comparisonData, normalizeData]);

  // Toggle strategy visibility
  const toggleStrategy = useCallback((strategyId: string) => {
    setSelectedStrategies(prev => 
      prev.includes(strategyId) 
        ? prev.filter(id => id !== strategyId)
        : [...prev, strategyId]
    );
  }, []);

  // Custom tooltip for comparison
  const ComparisonTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload || !payload.length) return null;

    const dataPoint = payload[0].payload;

    return (
      <div className="bg-background/95 border border-border rounded-lg p-3 shadow-lg min-w-48">
        <p className="text-sm font-medium mb-2">{dataPoint.time}</p>
        
        <div className="space-y-1">
          {visibleStrategies.map(strategy => {
            const equityValue = dataPoint[`${strategy.id}_equity`];
            const priceValue = dataPoint[`${strategy.id}_price`];
            
            if (equityValue === undefined) return null;

            return (
              <div key={strategy.id} className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <div 
                    className="w-3 h-3 rounded-full" 
                    style={{ backgroundColor: strategy.color }}
                  />
                  <span className="text-xs">{strategy.name}</span>
                </div>
                <div className="text-xs font-mono">
                  {normalizeData ? 
                    `${equityValue.toFixed(2)}%` : 
                    PriceFormatter.formatPrice(equityValue)
                  }
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  if (!strategies.length) {
    return (
      <Card className={className}>
        <CardContent className="p-6">
          <div className="text-center text-muted-foreground">No strategies to compare</div>
        </CardContent>
      </Card>
    );
  }

  // Overlay mode - single chart with multiple lines
  if (compareMode === 'overlay' || compareMode === 'normalized') {
    return (
      <Card className={className}>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center space-x-2">
                <Layers className="h-5 w-5" />
                <span>{title}</span>
              </CardTitle>
              <CardDescription>
                Compare multiple strategies on a single chart
              </CardDescription>
            </div>
            
            <div className="flex items-center space-x-2">
              <Badge variant="outline">
                {visibleStrategies.length} strategies
              </Badge>
              <Button variant="outline" size="sm">
                <Download className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardHeader>

        <CardContent>
          {/* Controls */}
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <Label htmlFor="normalize">Normalize:</Label>
                <Switch 
                  id="normalize"
                  checked={normalizeData} 
                  onCheckedChange={setNormalizeData} 
                />
              </div>

              <Select value={timeframe} onValueChange={setTimeframe}>
                <SelectTrigger className="w-32">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1m">1 Minute</SelectItem>
                  <SelectItem value="5m">5 Minutes</SelectItem>
                  <SelectItem value="15m">15 Minutes</SelectItem>
                  <SelectItem value="1h">1 Hour</SelectItem>
                  <SelectItem value="4h">4 Hours</SelectItem>
                  <SelectItem value="1d">1 Day</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-center space-x-2">
              <Button
                variant={compareMode === 'overlay' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setCompareMode('overlay')}
              >
                <Layers className="h-4 w-4" />
              </Button>
              <Button
                variant={(compareMode as any) === 'grid' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setCompareMode('grid' as any)}
              >
                <Grid3X3 className="h-4 w-4" />
              </Button>
            </div>
          </div>

          {/* Strategy Selection */}
          <div className="flex flex-wrap gap-2 mb-4">
            {strategies.map(strategy => (
              <Button
                key={strategy.id}
                variant={selectedStrategies.includes(strategy.id) ? 'default' : 'outline'}
                size="sm"
                onClick={() => toggleStrategy(strategy.id)}
                className="text-xs"
              >
                <div 
                  className="w-3 h-3 rounded-full mr-2" 
                  style={{ backgroundColor: strategy.color }}
                />
                {strategy.name}
              </Button>
            ))}
          </div>

          {/* Comparison Chart */}
          <div className="h-96">
            <ChartContainer config={{}} className="h-full w-full">
              <LineChart data={comparisonData}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-muted/50" />
                
                <XAxis 
                  dataKey="timestamp"
                  type="number"
                  scale="time"
                  tickFormatter={(value) => TimeFormatter.formatTimestamp(value, timeframe)}
                />
                
                <YAxis 
                  tickFormatter={(value) => 
                    normalizeData ? `${value.toFixed(1)}%` : PriceFormatter.formatPrice(value)
                  }
                />

                <ChartTooltip content={<ComparisonTooltip />} />
                <ChartLegend content={<ChartLegendContent />} />

                {/* Strategy lines */}
                {visibleStrategies.map((strategy, index) => (
                  <Line
                    key={strategy.id}
                    type="monotone"
                    dataKey={`${strategy.id}_equity`}
                    stroke={strategy.color}
                    strokeWidth={2}
                    dot={false}
                    name={strategy.name}
                  />
                ))}

                <Brush
                  dataKey="timestamp"
                  height={30}
                  stroke="hsl(var(--muted-foreground))"
                />
              </LineChart>
            </ChartContainer>
          </div>

          {/* Strategy Statistics */}
          {showStats && (
            <div className="mt-6">
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-sm font-medium">Performance Statistics</h4>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowStats(!showStats)}
                >
                  <Eye className="h-4 w-4" />
                </Button>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left p-2">Strategy</th>
                      <th className="text-right p-2">Return</th>
                      <th className="text-right p-2">Max DD</th>
                      <th className="text-right p-2">Volatility</th>
                      <th className="text-right p-2">Sharpe</th>
                      <th className="text-right p-2">Trades</th>
                    </tr>
                  </thead>
                  <tbody>
                    {strategyStats.filter(stat => stat !== null).map(stat => (
                      <tr key={stat!.id} className="border-b">
                        <td className="p-2">
                          <div className="flex items-center space-x-2">
                            <div 
                              className="w-3 h-3 rounded-full" 
                              style={{ backgroundColor: stat.color }}
                            />
                            <span>{stat.name}</span>
                          </div>
                        </td>
                        <td className={`text-right p-2 font-mono ${stat.finalReturn >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {PriceFormatter.formatPercent(stat.finalReturn)}
                        </td>
                        <td className="text-right p-2 font-mono text-red-600">
                          {PriceFormatter.formatPercent(stat.maxDrawdown)}
                        </td>
                        <td className="text-right p-2 font-mono">
                          {stat.volatility.toFixed(2)}%
                        </td>
                        <td className="text-right p-2 font-mono">
                          {stat.sharpeRatio.toFixed(2)}
                        </td>
                        <td className="text-right p-2 font-mono">
                          {stat.totalTrades}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    );
  }

  // Grid mode - separate charts
  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center space-x-2">
              <Grid3X3 className="h-5 w-5" />
              <span>{title} - Grid View</span>
            </CardTitle>
            <CardDescription>
              Individual charts for each strategy comparison
            </CardDescription>
          </div>
          
          <div className="flex items-center space-x-2">
            <Button
              variant={(compareMode as any) === 'overlay' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setCompareMode('overlay' as any)}
            >
              <Layers className="h-4 w-4" />
            </Button>
            <Button
              variant={(compareMode as any) === 'grid' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setCompareMode('grid' as any)}
            >
              <Grid3X3 className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {visibleStrategies.map(strategy => (
            <AdvancedChart
              key={strategy.id}
              data={strategy.data}
              title={strategy.name}
              initialTimeframe={timeframe}
              enableIndicators={false}
              showVolume={false}
            />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}