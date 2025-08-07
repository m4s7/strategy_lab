'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { EquityCurveChart } from '@/components/charts/equity-curve-chart';
import { DrawdownChart } from '@/components/charts/drawdown-chart';
import { ReturnsDistributionChart } from '@/components/charts/returns-distribution-chart';
import { PerformanceHeatmap } from '@/components/charts/performance-heatmap';
import { useChartSync } from '@/lib/chart-sync-manager';
import { 
  TrendingUp, 
  BarChart3, 
  Calendar,
  RefreshCw,
  Play,
  Square
} from 'lucide-react';

// Generate sample data for demonstration
function generateSampleData() {
  const startDate = new Date('2024-01-01');
  const endDate = new Date('2024-12-31');
  const dayMs = 24 * 60 * 60 * 1000;
  const totalDays = Math.floor((endDate.getTime() - startDate.getTime()) / dayMs);
  
  let equity = 100000;
  let peak = equity;
  const equityData: any[] = [];
  const trades: any[] = [];
  const drawdownPeriods: any[] = [];
  
  let inDrawdown = false;
  let drawdownStart = '';
  let drawdownPeak = 0;

  for (let day = 0; day <= totalDays; day++) {
    const currentDate = new Date(startDate.getTime() + day * dayMs);
    const timestamp = currentDate.toISOString();
    
    // Simulate trading activity (more active during weekdays)
    const isWeekend = currentDate.getDay() === 0 || currentDate.getDay() === 6;
    const tradesPerDay = isWeekend ? Math.floor(Math.random() * 3) : Math.floor(Math.random() * 8) + 2;
    
    let dailyPnL = 0;
    
    for (let trade = 0; trade < tradesPerDay; trade++) {
      const hour = 9 + Math.floor(Math.random() * 7); // Trading hours 9-16
      const minute = Math.floor(Math.random() * 60);
      const tradeTime = new Date(currentDate);
      tradeTime.setHours(hour, minute, 0, 0);
      
      // Generate realistic returns with slight positive bias and occasional large moves
      let returnPct = (Math.random() - 0.48) * 4; // Slight positive bias
      if (Math.random() < 0.05) {
        returnPct *= 4; // Occasional large moves
      }
      
      const returnAmount = equity * (returnPct / 100);
      const newEquity = equity + returnAmount;
      
      trades.push({
        tradeId: `trade_${day}_${trade}`,
        timestamp: tradeTime.toISOString(),
        pnl: returnAmount,
        return_pct: returnPct,
        duration: Math.floor(Math.random() * 300) + 60, // 1-5 minutes
        type: Math.random() > 0.5 ? 'long' : 'short',
        entryPrice: 15000 + Math.random() * 1000,
        exitPrice: 15000 + Math.random() * 1000
      });
      
      equity = newEquity;
      dailyPnL += returnAmount;
    }
    
    // Update peak
    if (equity > peak) {
      peak = equity;
      
      // End drawdown period if we were in one
      if (inDrawdown) {
        const lastPeriod = drawdownPeriods[drawdownPeriods.length - 1];
        if (lastPeriod) {
          lastPeriod.end = equityData[equityData.length - 1]?.timestamp || timestamp;
          lastPeriod.recovery = timestamp;
          lastPeriod.duration = Math.floor((new Date(timestamp).getTime() - new Date(lastPeriod.start).getTime()) / dayMs);
          lastPeriod.recoveryDuration = Math.floor((new Date(timestamp).getTime() - new Date(lastPeriod.end).getTime()) / dayMs);
        }
        inDrawdown = false;
      }
    }
    
    const drawdown = equity - peak;
    const drawdown_pct = peak > 0 ? (drawdown / peak) * 100 : 0;
    
    // Start new drawdown period if we drop below peak
    if (drawdown < 0 && !inDrawdown) {
      inDrawdown = true;
      drawdownStart = timestamp;
      drawdownPeak = peak;
    }
    
    // Record drawdown periods that exceed 5%
    if (inDrawdown && drawdown_pct < -5 && 
        !drawdownPeriods.some(p => p.start === drawdownStart)) {
      drawdownPeriods.push({
        start: drawdownStart,
        end: timestamp,
        peak: drawdownPeak,
        trough: equity,
        magnitude: drawdown_pct,
        duration: 0,
        recoveryDuration: undefined
      });
    }

    equityData.push({
      timestamp,
      equity,
      benchmark: 100000 * (1 + 0.08 * (day / totalDays)), // Simple 8% annual benchmark
      drawdown_pct,
      trade_pnl: dailyPnL,
      cumulative_pnl: equity - 100000
    });
  }

  return {
    equityData: equityData.filter((_, i) => i % 1 === 0), // Use all data points
    drawdownData: equityData.map(point => ({
      timestamp: point.timestamp,
      equity: point.equity,
      peak,
      drawdown: point.equity - peak,
      drawdown_pct: point.drawdown_pct,
      underwater: point.drawdown_pct < 0
    })),
    trades,
    drawdownPeriods: drawdownPeriods.filter(p => p.magnitude < -5) // Only significant drawdowns
  };
}

export default function ChartsDemo() {
  const [sampleData, setSampleData] = useState<any>(null);
  const [synchronized, setSynchronized] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(false);

  const { subscribe, resetZoom, clearAll } = useChartSync('demo-page');

  useEffect(() => {
    setSampleData(generateSampleData());
  }, []);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (autoRefresh) {
      interval = setInterval(() => {
        setSampleData(generateSampleData());
      }, 5000); // Refresh every 5 seconds
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [autoRefresh]);

  const handleRegenerateData = () => {
    setSampleData(generateSampleData());
  };

  const handleResetZoom = () => {
    resetZoom();
  };

  const handleClearSync = () => {
    clearAll();
  };

  if (!sampleData) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-lg text-muted-foreground">Loading chart demo...</div>
        </div>
      </div>
    );
  }

  const { equityData, drawdownData, trades, drawdownPeriods } = sampleData;

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Interactive Charts Demo</h1>
          <p className="text-muted-foreground mt-1">
            Demonstration of synchronized interactive charts with sample trading data
          </p>
        </div>
        
        <div className="flex items-center space-x-2">
          <Badge variant="outline">
            {trades.length} trades
          </Badge>
          <Badge variant="outline">
            {synchronized ? 'Synchronized' : 'Independent'}
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
                variant={synchronized ? "default" : "outline"} 
                size="sm" 
                onClick={() => setSynchronized(!synchronized)}
              >
                {synchronized ? 'Synchronized' : 'Independent'}
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
              <Button variant="outline" size="sm" onClick={handleResetZoom}>
                Reset Zoom
              </Button>
              <Button variant="outline" size="sm" onClick={handleClearSync}>
                Clear Sync
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Chart Grid */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* Equity Curve */}
        <EquityCurveChart
          data={equityData}
          benchmarkData={equityData}
          drawdownPeriods={drawdownPeriods}
          initialCapital={100000}
          title="Portfolio Equity Curve"
          synchronized={synchronized}
          interactive={true}
          exportable={true}
          className="xl:col-span-2"
        />

        {/* Drawdown Analysis */}
        <DrawdownChart
          data={drawdownData}
          drawdownPeriods={drawdownPeriods}
        />

        {/* Returns Distribution */}
        <ReturnsDistributionChart
          data={trades}
          bins={30}
          showNormalDistribution={true}
          interactive={true}
          exportable={true}
        />
      </div>

      {/* Performance Heatmap */}
      <div className="grid grid-cols-1 gap-6">
        <PerformanceHeatmap
          data={trades}
          aggregationType="pnl"
          timeFormat="hourly"
          viewType="time-of-day"
          exportable={true}
        />
      </div>

      {/* Chart Information */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <BarChart3 className="h-5 w-5" />
            <span>Chart Features</span>
          </CardTitle>
          <CardDescription>
            Interactive features available in this chart suite
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div className="space-y-2">
              <h4 className="font-medium">Equity Curve</h4>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>• Interactive zoom and pan</li>
                <li>• Crosshair with precise values</li>
                <li>• Benchmark overlay</li>
                <li>• Drawdown period highlighting</li>
                <li>• Chart type switching (line/area)</li>
              </ul>
            </div>
            
            <div className="space-y-2">
              <h4 className="font-medium">Drawdown Analysis</h4>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>• Underwater chart</li>
                <li>• Rolling drawdown view</li>
                <li>• Distribution histogram</li>
                <li>• Detailed period table</li>
                <li>• Recovery time analysis</li>
              </ul>
            </div>
            
            <div className="space-y-2">
              <h4 className="font-medium">Returns Distribution</h4>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>• Configurable bin sizes</li>
                <li>• Normal distribution overlay</li>
                <li>• Statistical annotations</li>
                <li>• Percentile markers</li>
                <li>• Interactive brushing</li>
              </ul>
            </div>

            <div className="space-y-2">
              <h4 className="font-medium">Performance Heatmap</h4>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>• Time-based performance analysis</li>
                <li>• Interactive cell hover</li>
                <li>• Multiple aggregation types</li>
                <li>• Color-coded visualization</li>
                <li>• Export functionality</li>
              </ul>
            </div>
            
            <div className="space-y-2">
              <h4 className="font-medium">Synchronization</h4>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>• Coordinated zoom/pan</li>
                <li>• Linked brushing</li>
                <li>• Crosshair synchronization</li>
                <li>• Consistent time axis</li>
                <li>• Shared color schemes</li>
              </ul>
            </div>
            
            <div className="space-y-2">
              <h4 className="font-medium">Export Options</h4>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>• PNG image export</li>
                <li>• SVG vector export</li>
                <li>• Data export (CSV/JSON)</li>
                <li>• Print-friendly layouts</li>
                <li>• Custom sizing</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}