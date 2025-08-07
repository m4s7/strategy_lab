'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { AdvancedChart } from '@/components/charts/advanced-chart';
import { ChartComparison } from '@/components/charts/chart-comparison';
import { DataResampler } from '@/lib/charting/data-utils';
import { OHLC, Trade } from '@/lib/charting/types';
import { 
  TrendingUp, 
  BarChart3, 
  Layers,
  RefreshCw,
  Play,
  Square
} from 'lucide-react';

// Generate comprehensive sample data
function generateAdvancedSampleData() {
  const startDate = new Date('2024-01-01');
  const endDate = new Date('2024-12-31');
  
  // Generate base OHLC data
  const baseData = DataResampler.generateSampleData(startDate, endDate, '5m', 15000);
  const enhancedData = DataResampler.addRealisticNoise(baseData, 0.002);

  // Generate sample trades
  const trades: Trade[] = [];
  let tradeId = 1;

  for (let i = 0; i < enhancedData.length; i += Math.floor(Math.random() * 50) + 20) {
    if (i >= enhancedData.length) break;

    const candle = enhancedData[i];
    const isLong = Math.random() > 0.5;
    const entryPrice = candle.close;
    
    // Find exit a few candles later
    const exitIndex = Math.min(i + Math.floor(Math.random() * 20) + 5, enhancedData.length - 1);
    const exitCandle = enhancedData[exitIndex];
    const exitPrice = exitCandle.close;
    
    const quantity = Math.floor(Math.random() * 10) + 1;
    const pnl = isLong ? 
      (exitPrice - entryPrice) * quantity : 
      (entryPrice - exitPrice) * quantity;

    // Entry trade
    trades.push({
      id: `trade_${tradeId}_entry`,
      timestamp: candle.timestamp,
      price: entryPrice,
      side: isLong ? 'buy' : 'sell',
      quantity,
      pnl: 0,
      strategy: 'Sample Strategy',
      duration: 0
    });

    // Exit trade
    trades.push({
      id: `trade_${tradeId}_exit`,
      timestamp: exitCandle.timestamp,
      price: exitPrice,
      side: isLong ? 'sell' : 'buy',
      quantity,
      pnl,
      strategy: 'Sample Strategy',
      duration: exitCandle.timestamp - candle.timestamp
    });

    tradeId++;
  }

  return {
    ohlcData: enhancedData,
    trades: trades.sort((a, b) => a.timestamp - b.timestamp)
  };
}

// Generate multiple strategies for comparison
function generateComparisonStrategies() {
  const baseDate = new Date('2024-01-01');
  const endDate = new Date('2024-12-31');
  
  const strategies = [
    {
      id: 'trend_following',
      name: 'Trend Following',
      color: '#2563eb',
      visible: true,
      initialCapital: 100000
    },
    {
      id: 'mean_reversion',
      name: 'Mean Reversion', 
      color: '#dc2626',
      visible: true,
      initialCapital: 100000
    },
    {
      id: 'momentum',
      name: 'Momentum',
      color: '#059669',
      visible: true,
      initialCapital: 100000
    },
    {
      id: 'scalping',
      name: 'Scalping',
      color: '#7c3aed',
      visible: true,
      initialCapital: 100000
    }
  ];

  return strategies.map(strategy => {
    // Generate slightly different market conditions for each strategy
    const volatilityMultiplier = strategy.id === 'scalping' ? 0.5 : 
                                strategy.id === 'trend_following' ? 1.2 : 1.0;
    const trendBias = strategy.id === 'trend_following' ? 0.0005 : 
                     strategy.id === 'mean_reversion' ? -0.0002 : 0;
    
    const data = DataResampler.generateSampleData(
      baseDate, 
      endDate, 
      '1h', 
      15000 + Math.random() * 1000
    );

    // Apply strategy-specific characteristics
    const modifiedData = data.map((candle, index) => {
      if (index === 0) return candle;
      
      const prevCandle = data[index - 1];
      const trendAdjustment = trendBias * prevCandle.close;
      const volatilityAdjustment = (Math.random() - 0.5) * 0.01 * volatilityMultiplier * prevCandle.close;
      
      return {
        ...candle,
        open: candle.open + trendAdjustment,
        high: candle.high + trendAdjustment + Math.abs(volatilityAdjustment),
        low: candle.low + trendAdjustment - Math.abs(volatilityAdjustment),
        close: candle.close + trendAdjustment + volatilityAdjustment
      };
    });

    return {
      ...strategy,
      data: modifiedData
    };
  });
}

export default function AdvancedChartsPage() {
  const [sampleData, setSampleData] = useState<any>(null);
  const [comparisonStrategies, setComparisonStrategies] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState('single');
  const [autoRefresh, setAutoRefresh] = useState(false);

  useEffect(() => {
    setSampleData(generateAdvancedSampleData());
    setComparisonStrategies(generateComparisonStrategies());
  }, []);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (autoRefresh) {
      interval = setInterval(() => {
        setSampleData(generateAdvancedSampleData());
        setComparisonStrategies(generateComparisonStrategies());
      }, 10000); // Refresh every 10 seconds
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [autoRefresh]);

  const handleRegenerateData = () => {
    setSampleData(generateAdvancedSampleData());
    setComparisonStrategies(generateComparisonStrategies());
  };

  if (!sampleData || !comparisonStrategies.length) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-lg text-muted-foreground">Loading advanced charts...</div>
        </div>
      </div>
    );
  }

  const { ohlcData, trades } = sampleData;

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Advanced Trading Charts</h1>
          <p className="text-muted-foreground mt-1">
            Professional trading charts with technical indicators, timeframe analysis, and strategy comparison
          </p>
        </div>
        
        <div className="flex items-center space-x-2">
          <Badge variant="outline">
            {ohlcData.length} candles
          </Badge>
          <Badge variant="outline">
            {trades.length} trades
          </Badge>
          <Badge variant="outline">
            {comparisonStrategies.length} strategies
          </Badge>
        </div>
      </div>

      {/* Controls */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <RefreshCw className="h-5 w-5" />
            <span>Chart Controls</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Button 
                variant="outline" 
                size="sm" 
                onClick={handleRegenerateData}
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Generate New Data
              </Button>
              
              <Button 
                variant={autoRefresh ? "destructive" : "outline"} 
                size="sm" 
                onClick={() => setAutoRefresh(!autoRefresh)}
              >
                {autoRefresh ? (
                  <><Square className="h-4 w-4 mr-2" />Stop Auto-refresh</>
                ) : (
                  <><Play className="h-4 w-4 mr-2" />Start Auto-refresh</>
                )}
              </Button>
            </div>

            <div className="flex items-center space-x-2">
              <Badge variant={activeTab === 'single' ? 'default' : 'outline'}>
                Single Chart Analysis
              </Badge>
              <Badge variant={activeTab === 'comparison' ? 'default' : 'outline'}>
                Strategy Comparison
              </Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Chart Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="single">Single Chart Analysis</TabsTrigger>
          <TabsTrigger value="comparison">Strategy Comparison</TabsTrigger>
        </TabsList>

        <TabsContent value="single" className="space-y-6">
          {/* Advanced Single Chart */}
          <AdvancedChart
            data={ohlcData}
            trades={trades}
            title="Advanced Trading Chart with Technical Analysis"
            initialTimeframe="1h"
            showVolume={true}
            enableIndicators={true}
            enableDrawing={false}
          />

          {/* Different timeframes */}
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
            <AdvancedChart
              data={ohlcData}
              trades={trades.slice(0, 20)} // Limit trades for cleaner view
              title="5-Minute Chart"
              initialTimeframe="5m"
              showVolume={false}
              enableIndicators={true}
            />

            <AdvancedChart
              data={ohlcData}
              trades={trades.slice(0, 20)}
              title="Daily Chart"
              initialTimeframe="1d" 
              showVolume={true}
              enableIndicators={true}
            />
          </div>
        </TabsContent>

        <TabsContent value="comparison" className="space-y-6">
          {/* Strategy Comparison Chart */}
          <ChartComparison
            strategies={comparisonStrategies}
            title="Multi-Strategy Performance Comparison"
          />

          {/* Individual Strategy Charts in Grid */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <BarChart3 className="h-5 w-5" />
                <span>Individual Strategy Analysis</span>
              </CardTitle>
              <CardDescription>
                Detailed view of each strategy with technical indicators
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                {comparisonStrategies.slice(0, 4).map(strategy => (
                  <AdvancedChart
                    key={strategy.id}
                    data={strategy.data.slice(0, 500)} // Limit data for performance
                    title={`${strategy.name} Strategy`}
                    initialTimeframe="4h"
                    showVolume={false}
                    enableIndicators={true}
                    className="h-96"
                  />
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Feature Information */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <TrendingUp className="h-5 w-5" />
            <span>Advanced Chart Features</span>
          </CardTitle>
          <CardDescription>
            Professional-grade trading chart capabilities
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div className="space-y-2">
              <h4 className="font-medium">Technical Indicators</h4>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>• Simple Moving Average (SMA)</li>
                <li>• Exponential Moving Average (EMA)</li>
                <li>• Bollinger Bands</li>
                <li>• Relative Strength Index (RSI)</li>
                <li>• MACD (Moving Average Convergence Divergence)</li>
                <li>• Average True Range (ATR)</li>
              </ul>
            </div>
            
            <div className="space-y-2">
              <h4 className="font-medium">Chart Features</h4>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>• Multiple timeframe support (1m to 1d)</li>
                <li>• OHLC candlestick visualization</li>
                <li>• Volume analysis panel</li>
                <li>• Trade entry/exit markers</li>
                <li>• Interactive zoom and pan</li>
                <li>• Brush selection for detailed analysis</li>
              </ul>
            </div>
            
            <div className="space-y-2">
              <h4 className="font-medium">Analysis Tools</h4>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>• Strategy performance comparison</li>
                <li>• Normalized return analysis</li>
                <li>• Statistical performance metrics</li>
                <li>• Real-time data updates</li>
                <li>• Export functionality (PNG/SVG)</li>
                <li>• Responsive design for all devices</li>
              </ul>
            </div>

            <div className="space-y-2">
              <h4 className="font-medium">Data Processing</h4>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>• Automatic timeframe resampling</li>
                <li>• Price normalization for comparison</li>
                <li>• Statistical calculations (volatility, Sharpe ratio)</li>
                <li>• Realistic market data simulation</li>
                <li>• Trade correlation analysis</li>
                <li>• Performance optimization for large datasets</li>
              </ul>
            </div>
            
            <div className="space-y-2">
              <h4 className="font-medium">User Experience</h4>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>• Intuitive indicator management</li>
                <li>• Real-time tooltip information</li>
                <li>• Theme-aware color schemes</li>
                <li>• Keyboard shortcuts support</li>
                <li>• Mobile-responsive interface</li>
                <li>• Accessibility features (WCAG compliant)</li>
              </ul>
            </div>
            
            <div className="space-y-2">
              <h4 className="font-medium">Performance</h4>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>• Optimized rendering for 100K+ data points</li>
                <li>• Smooth 60fps interactions</li>
                <li>• Memory-efficient data handling</li>
                <li>• Progressive loading for large datasets</li>
                <li>• Web Workers for heavy calculations</li>
                <li>• Cached indicator calculations</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}