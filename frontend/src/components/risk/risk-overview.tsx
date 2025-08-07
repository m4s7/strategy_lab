"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
} from "recharts";
import { TrendingUp, AlertTriangle, Shield, Activity } from "lucide-react";
import { RiskMetrics } from "@/lib/risk/types";
import { generateMockPortfolioSeries } from "@/lib/risk/mock-data";
import { useMemo } from "react";

interface RiskOverviewProps {
  metrics?: RiskMetrics;
  timeframe: "1M" | "3M" | "6M" | "1Y";
}

export function RiskOverview({ metrics, timeframe }: RiskOverviewProps) {
  // Generate mock time series data
  const timeSeriesData = useMemo(() => {
    const length = timeframe === "1M" ? 30 : timeframe === "3M" ? 90 : timeframe === "6M" ? 180 : 252;
    const { dates, values, returns } = generateMockPortfolioSeries(100000, length);
    
    // Calculate rolling metrics
    const rollingData = [];
    const window = 30; // 30-day rolling window
    
    for (let i = window; i < returns.length; i++) {
      const windowReturns = returns.slice(i - window, i);
      const windowValues = values.slice(i - window, i + 1);
      
      // Calculate rolling VaR
      const sortedReturns = [...windowReturns].sort((a, b) => a - b);
      const var95Index = Math.ceil(0.05 * sortedReturns.length) - 1;
      const rollingVar95 = sortedReturns[Math.max(0, var95Index)];
      
      // Calculate rolling max drawdown
      let maxDrawdown = 0;
      let peak = windowValues[0];
      for (const value of windowValues) {
        if (value > peak) peak = value;
        const drawdown = (peak - value) / peak;
        if (drawdown > maxDrawdown) maxDrawdown = drawdown;
      }
      
      // Calculate rolling volatility
      const mean = windowReturns.reduce((sum, r) => sum + r, 0) / windowReturns.length;
      const variance = windowReturns.reduce((sum, r) => sum + Math.pow(r - mean, 2), 0) / windowReturns.length;
      const volatility = Math.sqrt(variance * 252); // Annualized
      
      rollingData.push({
        date: dates[i],
        value: values[i + 1],
        var95: rollingVar95 * 100, // Convert to percentage
        maxDrawdown: maxDrawdown * 100,
        volatility: volatility * 100,
        return: windowReturns[windowReturns.length - 1] * 100
      });
    }
    
    return rollingData;
  }, [timeframe]);

  // Risk distribution data
  const riskDistribution = useMemo(() => {
    if (!metrics) return [];
    
    return [
      { name: 'Low Risk', value: 60, color: '#10b981' },
      { name: 'Medium Risk', value: 30, color: '#f59e0b' },
      { name: 'High Risk', value: 10, color: '#ef4444' },
    ];
  }, [metrics]);

  // VaR confidence levels comparison
  const varComparison = useMemo(() => {
    if (!metrics) return [];
    
    return [
      { confidence: '90%', var: Math.abs(metrics.var95 * 0.8) * 100, cvar: Math.abs(metrics.cvar95 * 0.8) * 100 },
      { confidence: '95%', var: Math.abs(metrics.var95) * 100, cvar: Math.abs(metrics.cvar95) * 100 },
      { confidence: '99%', var: Math.abs(metrics.var99) * 100, cvar: Math.abs(metrics.cvar99) * 100 },
    ];
  }, [metrics]);

  if (!metrics) {
    return (
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {[...Array(4)].map((_, i) => (
          <Card key={i}>
            <CardContent className="p-6">
              <div className="animate-pulse">
                <div className="h-4 bg-muted rounded w-3/4 mb-4"></div>
                <div className="h-48 bg-muted rounded"></div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  const formatTooltipValue = (value: number, name: string) => {
    if (name.includes('%') || name.includes('var') || name.includes('volatility') || name.includes('Drawdown')) {
      return [`${value.toFixed(2)}%`, name];
    }
    return [value.toLocaleString(), name];
  };

  return (
    <div className="space-y-6">
      {/* Portfolio Value & Risk Timeline */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <TrendingUp className="h-5 w-5" />
            <span>Portfolio Value & Risk Timeline ({timeframe})</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={timeSeriesData}>
              <defs>
                <linearGradient id="valueGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.1}/>
                </linearGradient>
                <linearGradient id="drawdownGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#ef4444" stopOpacity={0.1}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="date" 
                tick={{ fontSize: 12 }}
                tickFormatter={(value) => new Date(value).toLocaleDateString()}
              />
              <YAxis yAxisId="value" orientation="left" tick={{ fontSize: 12 }} />
              <YAxis yAxisId="risk" orientation="right" tick={{ fontSize: 12 }} />
              <Tooltip formatter={formatTooltipValue} />
              
              <Area
                yAxisId="value"
                type="monotone"
                dataKey="value"
                stroke="#3b82f6"
                fillOpacity={1}
                fill="url(#valueGradient)"
                name="Portfolio Value"
              />
              
              <Area
                yAxisId="risk"
                type="monotone"
                dataKey="maxDrawdown"
                stroke="#ef4444"
                fillOpacity={1}
                fill="url(#drawdownGradient)"
                name="Max Drawdown (%)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Rolling Risk Metrics */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Activity className="h-5 w-5" />
              <span>Rolling Risk Metrics</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={timeSeriesData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="date" 
                  tick={{ fontSize: 12 }}
                  tickFormatter={(value) => new Date(value).toLocaleDateString()}
                />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip formatter={formatTooltipValue} />
                
                <Line
                  type="monotone"
                  dataKey="var95"
                  stroke="#ef4444"
                  strokeWidth={2}
                  dot={false}
                  name="VaR 95% (%)"
                />
                
                <Line
                  type="monotone"
                  dataKey="volatility"
                  stroke="#f59e0b"
                  strokeWidth={2}
                  dot={false}
                  name="Volatility (%)"
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* VaR vs CVaR Comparison */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <AlertTriangle className="h-5 w-5" />
              <span>VaR vs CVaR Comparison</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={varComparison}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="confidence" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip formatter={(value) => [`${Number(value).toFixed(2)}%`, '']} />
                
                <Bar dataKey="var" fill="#3b82f6" name="VaR" />
                <Bar dataKey="cvar" fill="#ef4444" name="CVaR" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Risk Distribution */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Shield className="h-5 w-5" />
              <span>Risk Distribution</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={riskDistribution}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {riskDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Key Risk Statistics */}
        <Card>
          <CardHeader>
            <CardTitle>Key Risk Statistics</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex justify-between items-center py-2 border-b">
                <span className="text-sm text-muted-foreground">Max Drawdown Duration</span>
                <Badge variant="outline">
                  {metrics.maxDrawdownDuration} days
                </Badge>
              </div>
              
              <div className="flex justify-between items-center py-2 border-b">
                <span className="text-sm text-muted-foreground">Risk-Adjusted Return</span>
                <Badge variant={metrics.calmarRatio > 1 ? "default" : "secondary"}>
                  {metrics.calmarRatio.toFixed(2)}
                </Badge>
              </div>
              
              <div className="flex justify-between items-center py-2 border-b">
                <span className="text-sm text-muted-foreground">Downside Protection</span>
                <Badge variant={metrics.sortinoRatio > 1 ? "default" : "secondary"}>
                  {metrics.sortinoRatio.toFixed(2)}
                </Badge>
              </div>
              
              <div className="flex justify-between items-center py-2 border-b">
                <span className="text-sm text-muted-foreground">Tail Risk Balance</span>
                <Badge variant={metrics.tailRatio > 0.5 ? "default" : "destructive"}>
                  {metrics.tailRatio.toFixed(2)}
                </Badge>
              </div>
              
              <div className="flex justify-between items-center py-2">
                <span className="text-sm text-muted-foreground">Gains/Losses Ratio</span>
                <Badge variant={metrics.omega > 1 ? "default" : "destructive"}>
                  {metrics.omega.toFixed(2)}
                </Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}