'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart";
import { 
  ComposedChart,
  Line,
  Bar,
  XAxis, 
  YAxis, 
  CartesianGrid,
  Brush,
  ReferenceLine,
  ResponsiveContainer
} from 'recharts';
import { useState, useMemo, useRef, useCallback } from 'react';
import { 
  TrendingUp, 
  TrendingDown,
  Download,
  Plus,
  Settings,
  Eye,
  EyeOff,
  RotateCcw,
  ZoomIn
} from 'lucide-react';
import { OHLC, Trade, IndicatorType, ChartConfig } from '@/lib/charting/types';
import { IndicatorManager } from '@/lib/charting/indicators';
import { DataResampler, TimeFormatter, PriceFormatter } from '@/lib/charting/data-utils';
import html2canvas from 'html2canvas';

interface AdvancedChartProps {
  data: OHLC[];
  trades?: Trade[];
  title?: string;
  initialTimeframe?: string;
  showVolume?: boolean;
  enableDrawing?: boolean;
  enableIndicators?: boolean;
  className?: string;
}

const chartConfig = {
  price: {
    label: "Price",
    color: "hsl(var(--chart-1))",
  },
  volume: {
    label: "Volume", 
    color: "hsl(var(--chart-2))",
  },
  bullish: {
    label: "Bullish",
    color: "hsl(var(--color-bullish))",
  },
  bearish: {
    label: "Bearish",
    color: "hsl(var(--color-bearish))",
  },
};

export function AdvancedChart({
  data,
  trades = [],
  title = "Advanced Trading Chart",
  initialTimeframe = '1h',
  showVolume = true,
  enableIndicators = true,
  className
}: AdvancedChartProps) {
  const chartRef = useRef<HTMLDivElement>(null);
  const [timeframe, setTimeframe] = useState(initialTimeframe);
  const [showVolumePanel, setShowVolumePanel] = useState(showVolume);
  const [indicatorManager] = useState(() => new IndicatorManager());
  const [indicators, setIndicators] = useState<any[]>([]);
  const [selectedIndicator, setSelectedIndicator] = useState<IndicatorType>('SMA');
  const [zoomDomain, setZoomDomain] = useState<[number, number] | null>(null);

  // Resample data based on timeframe
  const resampledData = useMemo(() => {
    if (!data?.length) return [];
    return DataResampler.resample(data, timeframe);
  }, [data, timeframe]);

  // Format data for chart display
  const chartData = useMemo(() => {
    return resampledData.map((candle, index) => {
      const timestamp = typeof candle.timestamp === 'number' ? candle.timestamp : new Date(candle.timestamp).getTime();
      
      return {
        timestamp,
        time: TimeFormatter.formatTimestamp(timestamp, timeframe),
        open: candle.open,
        high: candle.high,
        low: candle.low,
        close: candle.close,
        volume: candle.volume || 0,
        // Simple candlestick representation using high-low as line and open-close as body
        bodyTop: Math.max(candle.open, candle.close),
        bodyBottom: Math.min(candle.open, candle.close),
        bodyHeight: Math.abs(candle.close - candle.open),
        isBullish: candle.close > candle.open,
        wickTop: candle.high - Math.max(candle.open, candle.close),
        wickBottom: Math.min(candle.open, candle.close) - candle.low,
        index
      };
    });
  }, [resampledData, timeframe]);

  // Calculate indicators
  const indicatorResults = useMemo(() => {
    if (!enableIndicators || !resampledData.length) return {};
    return indicatorManager.calculateAll(resampledData);
  }, [resampledData, indicators, indicatorManager, enableIndicators]);

  // Merge indicator data with chart data
  const enrichedData = useMemo(() => {
    return chartData.map((point, index) => {
      const enriched = { ...point };
      
      // Add indicator values
      Object.entries(indicatorResults).forEach(([id, result]) => {
        if (Array.isArray(result.values)) {
          (enriched as any)[id] = result.values[index];
        } else if (typeof result.values === 'object') {
          Object.entries(result.values).forEach(([key, values]) => {
            (enriched as any)[`${id}_${key}`] = values[index];
          });
        }
      });
      
      return enriched;
    });
  }, [chartData, indicatorResults]);

  // Get price statistics
  const priceStats = useMemo(() => {
    return DataResampler.getStatistics(resampledData);
  }, [resampledData]);

  // Add indicator
  const handleAddIndicator = useCallback((type: IndicatorType) => {
    let params = {};
    
    switch (type) {
      case 'SMA':
      case 'EMA':
        params = { period: 20, color: '#2563eb' };
        break;
      case 'BollingerBands':
        params = { period: 20, multiplier: 2, color: '#6366f1' };
        break;
      case 'RSI':
        params = { period: 14, color: '#7c3aed' };
        break;
      case 'MACD':
        params = { fast: 12, slow: 26, signal: 9, color: '#059669' };
        break;
      case 'ATR':
        params = { period: 14, color: '#ea580c' };
        break;
    }

    const indicator = indicatorManager.addIndicator(type, params);
    setIndicators(prev => [...prev, indicator]);
  }, [indicatorManager]);

  // Remove indicator
  const handleRemoveIndicator = useCallback((id: string) => {
    indicatorManager.removeIndicator(id);
    setIndicators(prev => prev.filter(ind => ind.id !== id));
  }, [indicatorManager]);

  // Toggle indicator visibility
  const handleToggleIndicator = useCallback((id: string) => {
    const indicator = indicatorManager.getIndicator(id);
    if (indicator) {
      indicator.visible = !indicator.visible;
      setIndicators(prev => [...prev]); // Force re-render
    }
  }, [indicatorManager]);

  // Export chart
  const handleExport = useCallback(async (format: 'png' | 'svg' = 'png') => {
    if (!chartRef.current) return;

    if (format === 'png') {
      const canvas = await html2canvas(chartRef.current);
      const url = canvas.toDataURL('image/png');
      const link = document.createElement('a');
      link.download = `advanced-chart-${Date.now()}.png`;
      link.href = url;
      link.click();
    }
  }, []);

  // Reset zoom
  const handleResetZoom = useCallback(() => {
    setZoomDomain(null);
  }, []);

  // Brush change handler
  const handleBrushChange = useCallback((domain: any) => {
    if (domain && domain.startIndex !== undefined && domain.endIndex !== undefined) {
      const start = enrichedData[domain.startIndex]?.timestamp;
      const end = enrichedData[domain.endIndex]?.timestamp;
      if (start && end) {
        setZoomDomain([start, end]);
      }
    }
  }, [enrichedData]);

  // Custom tooltip
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload || !payload.length) return null;

    const data = payload[0].payload;
    if (!data) return null;

    return (
      <div className="bg-background/95 border border-border rounded-lg p-3 shadow-lg min-w-48">
        <p className="text-sm font-medium mb-2">{data.time}</p>
        
        {/* OHLC Data */}
        <div className="space-y-1 text-xs">
          <div className="flex justify-between">
            <span>Open:</span>
            <span className="font-mono">{PriceFormatter.formatPrice(data.open)}</span>
          </div>
          <div className="flex justify-between">
            <span>High:</span>
            <span className="font-mono text-green-600">{PriceFormatter.formatPrice(data.high)}</span>
          </div>
          <div className="flex justify-between">
            <span>Low:</span>
            <span className="font-mono text-red-600">{PriceFormatter.formatPrice(data.low)}</span>
          </div>
          <div className="flex justify-between">
            <span>Close:</span>
            <span className={`font-mono ${data.isBullish ? 'text-green-600' : 'text-red-600'}`}>
              {PriceFormatter.formatPrice(data.close)}
            </span>
          </div>
          <div className="flex justify-between">
            <span>Volume:</span>
            <span className="font-mono">{PriceFormatter.formatVolume(data.volume)}</span>
          </div>

          {/* Indicator values */}
          {Object.entries(indicatorResults).map(([id, result]) => {
            const indicator = indicatorManager.getIndicator(id);
            if (!indicator || !indicator.visible) return null;

            return (
              <div key={id} className="border-t pt-1 mt-1">
                <div className="font-medium text-xs mb-1" style={{ color: result.color }}>
                  {result.name}
                </div>
                {Array.isArray(result.values) ? (
                  <div className="flex justify-between">
                    <span>Value:</span>
                    <span className="font-mono">{data[id]?.toFixed(2) || 'N/A'}</span>
                  </div>
                ) : (
                  Object.keys(result.values).map(key => (
                    <div key={key} className="flex justify-between">
                      <span>{key}:</span>
                      <span className="font-mono">{data[`${id}_${key}`]?.toFixed(2) || 'N/A'}</span>
                    </div>
                  ))
                )}
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  if (!data?.length) {
    return (
      <Card className={className}>
        <CardContent className="p-6">
          <div className="text-center text-muted-foreground">No chart data available</div>
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
              <TrendingUp className="h-5 w-5" />
              <span>{title}</span>
            </CardTitle>
            <CardDescription>
              Advanced trading chart with technical indicators and timeframe analysis
            </CardDescription>
          </div>
          
          <div className="flex items-center space-x-2">
            {priceStats && (
              <Badge variant={priceStats.changePercent >= 0 ? 'default' : 'destructive'}>
                {PriceFormatter.formatPercent(priceStats.changePercent)}
              </Badge>
            )}
            
            <Button variant="outline" size="sm" onClick={() => handleExport('png')}>
              <Download className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        {/* Chart Controls */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
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

            <Button
              variant={showVolumePanel ? "default" : "outline"}
              size="sm"
              onClick={() => setShowVolumePanel(!showVolumePanel)}
            >
              Volume
            </Button>
          </div>

          <div className="flex items-center space-x-2">
            {zoomDomain && (
              <Button variant="outline" size="sm" onClick={handleResetZoom}>
                <RotateCcw className="h-4 w-4" />
              </Button>
            )}
            <Button variant="outline" size="sm">
              <ZoomIn className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Indicators Panel */}
        {enableIndicators && (
          <div className="mb-4 p-3 bg-muted/20 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium">Technical Indicators</span>
              <div className="flex items-center space-x-2">
                <Select value={selectedIndicator} onValueChange={(value: IndicatorType) => setSelectedIndicator(value)}>
                  <SelectTrigger className="w-32">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="SMA">SMA</SelectItem>
                    <SelectItem value="EMA">EMA</SelectItem>
                    <SelectItem value="BollingerBands">Bollinger Bands</SelectItem>
                    <SelectItem value="RSI">RSI</SelectItem>
                    <SelectItem value="MACD">MACD</SelectItem>
                    <SelectItem value="ATR">ATR</SelectItem>
                  </SelectContent>
                </Select>
                <Button 
                  size="sm" 
                  onClick={() => handleAddIndicator(selectedIndicator)}
                >
                  <Plus className="h-4 w-4" />
                </Button>
              </div>
            </div>

            {/* Active Indicators */}
            <div className="flex flex-wrap gap-2">
              {indicators.map(indicator => {
                const result = indicatorResults[indicator.id];
                if (!result) return null;

                return (
                  <div 
                    key={indicator.id}
                    className="flex items-center space-x-2 px-2 py-1 bg-background rounded text-xs"
                  >
                    <div 
                      className="w-3 h-3 rounded-full" 
                      style={{ backgroundColor: result.color }}
                    />
                    <span>{result.name}</span>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-4 w-4 p-0"
                      onClick={() => handleToggleIndicator(indicator.id)}
                    >
                      {indicator.visible ? <Eye className="h-3 w-3" /> : <EyeOff className="h-3 w-3" />}
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-4 w-4 p-0 text-red-600"
                      onClick={() => handleRemoveIndicator(indicator.id)}
                    >
                      ×
                    </Button>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Main Chart */}
        <div ref={chartRef} className={showVolumePanel ? "h-96" : "h-80"}>
          <ChartContainer config={chartConfig} className="h-full w-full">
            <ComposedChart data={enrichedData}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted/50" />
              
              <XAxis 
                dataKey="timestamp"
                type="number"
                scale="time"
                domain={zoomDomain || ['dataMin', 'dataMax']}
                tickFormatter={(value) => TimeFormatter.formatTimestamp(value, timeframe)}
              />
              
              <YAxis 
                yAxisId="price"
                domain={['dataMin', 'dataMax']}
                tickFormatter={(value) => PriceFormatter.formatPrice(value)}
              />
              
              {showVolumePanel && (
                <YAxis 
                  yAxisId="volume"
                  orientation="right"
                  domain={[0, 'dataMax']}
                  tickFormatter={PriceFormatter.formatVolume}
                />
              )}

              <ChartTooltip content={<CustomTooltip />} />

              {/* Price Lines (simplified candlestick representation) */}
              <Line
                yAxisId="price"
                type="monotone"
                dataKey="high"
                stroke="hsl(var(--muted-foreground))"
                strokeWidth={1}
                dot={false}
                connectNulls={false}
              />
              
              <Line
                yAxisId="price"
                type="monotone"
                dataKey="low"
                stroke="hsl(var(--muted-foreground))"
                strokeWidth={1}
                dot={false}
                connectNulls={false}
              />

              <Line
                yAxisId="price"
                type="monotone"
                dataKey="close"
                stroke="hsl(var(--chart-1))"
                strokeWidth={2}
                dot={false}
              />

              {/* Volume bars */}
              {showVolumePanel && (
                <Bar
                  yAxisId="volume"
                  dataKey="volume"
                  fill="hsl(var(--chart-2))"
                  fillOpacity={0.3}
                />
              )}

              {/* Indicator lines */}
              {Object.entries(indicatorResults).map(([id, result]) => {
                const indicator = indicatorManager.getIndicator(id);
                if (!indicator || !indicator.visible || result.panel !== 'main') return null;

                if (Array.isArray(result.values)) {
                  return (
                    <Line
                      key={id}
                      yAxisId="price"
                      type="monotone"
                      dataKey={id}
                      stroke={result.color}
                      strokeWidth={2}
                      dot={false}
                      connectNulls={false}
                    />
                  );
                }

                // Handle multi-line indicators like Bollinger Bands
                if (typeof result.values === 'object') {
                  return Object.keys(result.values).map(key => (
                    <Line
                      key={`${id}_${key}`}
                      yAxisId="price"
                      type="monotone"
                      dataKey={`${id}_${key}`}
                      stroke={result.color}
                      strokeWidth={key === 'middle' ? 2 : 1}
                      strokeDasharray={key !== 'middle' ? "5 5" : undefined}
                      dot={false}
                      connectNulls={false}
                    />
                  ));
                }

                return null;
              })}

              {/* Trade markers as reference lines */}
              {trades.map((trade, index) => {
                const tradeTime = typeof trade.timestamp === 'number' ? trade.timestamp : new Date(trade.timestamp).getTime();
                return (
                  <ReferenceLine
                    key={`trade-${index}`}
                    yAxisId="price"
                    x={tradeTime}
                    stroke={trade.pnl >= 0 ? 'hsl(var(--color-bullish))' : 'hsl(var(--color-bearish))'}
                    strokeDasharray="3 3"
                    label={{
                      value: trade.side === 'buy' ? '▲' : '▼',
                      position: 'top',
                      fill: trade.pnl >= 0 ? 'hsl(var(--color-bullish))' : 'hsl(var(--color-bearish))'
                    }}
                  />
                );
              })}

              {/* Brush for zooming */}
              <Brush
                dataKey="timestamp"
                height={30}
                stroke="hsl(var(--chart-1))"
                onChange={handleBrushChange}
              />
            </ComposedChart>
          </ChartContainer>
        </div>

        {/* Statistics */}
        {priceStats && (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mt-4">
            <div className="text-center p-2 bg-muted/30 rounded">
              <div className="text-sm font-medium">{PriceFormatter.formatPrice(priceStats.last)}</div>
              <div className="text-xs text-muted-foreground">Last Price</div>
            </div>
            <div className="text-center p-2 bg-muted/30 rounded">
              <div className={`text-sm font-medium ${priceStats.changePercent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {PriceFormatter.formatPercent(priceStats.changePercent)}
              </div>
              <div className="text-xs text-muted-foreground">Change</div>
            </div>
            <div className="text-center p-2 bg-muted/30 rounded">
              <div className="text-sm font-medium">{PriceFormatter.formatVolume(priceStats.totalVolume)}</div>
              <div className="text-xs text-muted-foreground">Volume</div>
            </div>
            <div className="text-center p-2 bg-muted/30 rounded">
              <div className="text-sm font-medium">{PriceFormatter.formatPercent(priceStats.volatility * 100)}</div>
              <div className="text-xs text-muted-foreground">Volatility</div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}