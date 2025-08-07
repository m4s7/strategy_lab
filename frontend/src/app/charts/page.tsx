'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { useResults } from "@/hooks/useResults";
import { useState, useMemo } from "react";
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  ComposedChart,
  Bar,
  Area,
  AreaChart,
  ReferenceLine,
  Brush,
  Legend
} from 'recharts';
import { format, subDays } from "date-fns";
import { 
  TrendingUp,
  TrendingDown,
  BarChart3,
  Settings,
  Download,
  Maximize2,
  RefreshCw,
  Filter,
  Calendar
} from "lucide-react";

// Mock advanced chart data
const generateMockChartData = () => {
  const baseDate = new Date('2024-01-01');
  const data = [];
  let equity = 100000;
  let drawdown = 0;
  let maxEquity = equity;
  
  for (let i = 0; i < 252; i++) { // Trading days in a year
    const date = new Date(baseDate);
    date.setDate(date.getDate() + i);
    
    // Generate realistic trading data
    const dailyReturn = (Math.random() - 0.48) * 0.02; // Slight positive bias
    const volume = Math.floor(Math.random() * 1000) + 100;
    const trades = Math.floor(Math.random() * 20) + 1;
    
    equity *= (1 + dailyReturn);
    maxEquity = Math.max(maxEquity, equity);
    drawdown = ((maxEquity - equity) / maxEquity) * 100;
    
    data.push({
      date: date.toISOString().split('T')[0],
      timestamp: date.toISOString(),
      equity: Math.round(equity),
      dailyReturn: dailyReturn * 100,
      volume,
      trades,
      drawdown,
      vwap: equity * (0.995 + Math.random() * 0.01),
      sharpe: Math.random() * 3,
      volatility: Math.random() * 0.3 + 0.1,
      beta: 0.8 + Math.random() * 0.4
    });
  }
  
  return data;
};

export default function ChartsPage() {
  const { results, loading } = useResults();
  const [selectedTimeframe, setSelectedTimeframe] = useState('1Y');
  const [selectedMetric, setSelectedMetric] = useState('equity');
  const [showDrawdown, setShowDrawdown] = useState(false);
  const [showVolume, setShowVolume] = useState(true);
  const [zoomRange, setZoomRange] = useState([0, 100]);
  const [selectedResults, setSelectedResults] = useState<string[]>([]);

  const chartData = useMemo(() => generateMockChartData(), []);
  
  const getTimeframeData = (data: any[], timeframe: string) => {
    const now = new Date();
    let startDate = new Date();
    
    switch (timeframe) {
      case '1M':
        startDate = subDays(now, 30);
        break;
      case '3M':
        startDate = subDays(now, 90);
        break;
      case '6M':
        startDate = subDays(now, 180);
        break;
      case '1Y':
        startDate = subDays(now, 365);
        break;
      default:
        return data;
    }
    
    return data.filter(d => new Date(d.timestamp) >= startDate);
  };

  const filteredData = getTimeframeData(chartData, selectedTimeframe);
  
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

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-card border rounded-lg p-3 shadow-lg">
          <p className="text-sm font-medium">{format(new Date(label), 'MMM dd, yyyy')}</p>
          <div className="space-y-1 mt-2">
            {payload.map((entry: any, index: number) => (
              <div key={index} className="flex justify-between space-x-4">
                <span className="text-sm" style={{ color: entry.color }}>
                  {entry.name}:
                </span>
                <span className="text-sm font-medium">
                  {entry.dataKey === 'equity' || entry.dataKey === 'vwap' ? 
                    formatCurrency(entry.value) : 
                    entry.dataKey === 'dailyReturn' || entry.dataKey === 'drawdown' ?
                    formatPercent(entry.value) :
                    entry.value
                  }
                </span>
              </div>
            ))}
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center space-x-2">
            <BarChart3 className="h-8 w-8" />
            <span>Interactive Charts</span>
          </h1>
          <p className="text-muted-foreground">
            Advanced visualization and analysis tools
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline" size="sm">
            <Download className="mr-2 h-4 w-4" />
            Export
          </Button>
          <Button variant="outline" size="sm">
            <Maximize2 className="mr-2 h-4 w-4" />
            Fullscreen
          </Button>
          <Button variant="outline" size="sm">
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Chart Controls */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid gap-4 md:grid-cols-4 lg:grid-cols-6">
            <div className="space-y-2">
              <Label>Timeframe</Label>
              <Select value={selectedTimeframe} onValueChange={setSelectedTimeframe}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1M">1 Month</SelectItem>
                  <SelectItem value="3M">3 Months</SelectItem>
                  <SelectItem value="6M">6 Months</SelectItem>
                  <SelectItem value="1Y">1 Year</SelectItem>
                  <SelectItem value="ALL">All Time</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Primary Metric</Label>
              <Select value={selectedMetric} onValueChange={setSelectedMetric}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="equity">Equity Curve</SelectItem>
                  <SelectItem value="dailyReturn">Daily Returns</SelectItem>
                  <SelectItem value="drawdown">Drawdown</SelectItem>
                  <SelectItem value="sharpe">Sharpe Ratio</SelectItem>
                  <SelectItem value="volatility">Volatility</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-center space-x-2">
              <Switch 
                id="drawdown-overlay" 
                checked={showDrawdown}
                onCheckedChange={setShowDrawdown}
              />
              <Label htmlFor="drawdown-overlay">Show Drawdown</Label>
            </div>
            <div className="flex items-center space-x-2">
              <Switch 
                id="volume-bars" 
                checked={showVolume}
                onCheckedChange={setShowVolume}
              />
              <Label htmlFor="volume-bars">Show Volume</Label>
            </div>
            <div className="space-y-2">
              <Label>Zoom Range</Label>
              <Slider
                value={zoomRange}
                onValueChange={setZoomRange}
                max={100}
                step={1}
                className="w-full"
              />
            </div>
            <div className="space-y-2">
              <Label>Compare Results</Label>
              <Button variant="outline" size="sm" className="w-full">
                <Filter className="mr-2 h-4 w-4" />
                Select ({selectedResults.length})
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Main Charts */}
      <Tabs defaultValue="equity" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="equity">Equity Analysis</TabsTrigger>
          <TabsTrigger value="performance">Performance Metrics</TabsTrigger>
          <TabsTrigger value="risk">Risk Analysis</TabsTrigger>
          <TabsTrigger value="comparison">Multi-Strategy</TabsTrigger>
        </TabsList>

        <TabsContent value="equity" className="space-y-6">
          {/* Primary Equity Chart */}
          <Card>
            <CardHeader>
              <CardTitle>Equity Curve with Volume</CardTitle>
              <CardDescription>
                Interactive equity progression with trading volume overlay
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[500px]">
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart data={filteredData}>
                    <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
                    <XAxis 
                      dataKey="timestamp"
                      tickFormatter={(value) => format(new Date(value), 'MMM dd')}
                      className="text-xs"
                    />
                    <YAxis yAxisId="equity" orientation="left" tickFormatter={formatCurrency} className="text-xs" />
                    {showVolume && (
                      <YAxis yAxisId="volume" orientation="right" className="text-xs" />
                    )}
                    <Tooltip content={<CustomTooltip />} />
                    <Legend />
                    
                    {showVolume && (
                      <Bar 
                        yAxisId="volume"
                        dataKey="volume" 
                        fill="#8884d8" 
                        opacity={0.3}
                        name="Volume"
                      />
                    )}
                    
                    <Line
                      yAxisId="equity"
                      type="monotone"
                      dataKey="equity"
                      stroke="#10b981"
                      strokeWidth={2}
                      dot={false}
                      name="Equity"
                    />
                    
                    <Line
                      yAxisId="equity"
                      type="monotone"
                      dataKey="vwap"
                      stroke="#f59e0b"
                      strokeWidth={1}
                      strokeDasharray="5 5"
                      dot={false}
                      name="VWAP"
                    />
                    
                    {showDrawdown && (
                      <Area
                        yAxisId="equity"
                        dataKey="drawdown"
                        stroke="#ef4444"
                        fill="#ef4444"
                        fillOpacity={0.2}
                        name="Drawdown %"
                      />
                    )}

                    <Brush dataKey="timestamp" height={30} />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          {/* Secondary Charts */}
          <div className="grid gap-6 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Daily Returns Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-[300px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <ScatterChart data={filteredData}>
                      <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
                      <XAxis 
                        dataKey="timestamp"
                        tickFormatter={(value) => format(new Date(value), 'MMM')}
                        className="text-xs"
                      />
                      <YAxis 
                        tickFormatter={(value) => `${value.toFixed(2)}%`}
                        className="text-xs"
                      />
                      <Tooltip 
                        formatter={(value: number) => [`${value.toFixed(2)}%`, 'Daily Return']}
                        labelFormatter={(value) => format(new Date(value), 'MMM dd, yyyy')}
                      />
                      <Scatter 
                        dataKey="dailyReturn" 
                        fill="#8884d8"
                        fillOpacity={0.6}
                      />
                      <ReferenceLine y={0} stroke="#666" strokeDasharray="2 2" />
                    </ScatterChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Rolling Drawdown</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-[300px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={filteredData}>
                      <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
                      <XAxis 
                        dataKey="timestamp"
                        tickFormatter={(value) => format(new Date(value), 'MMM')}
                        className="text-xs"
                      />
                      <YAxis 
                        tickFormatter={(value) => `-${value.toFixed(1)}%`}
                        className="text-xs"
                      />
                      <Tooltip 
                        formatter={(value: number) => [`-${value.toFixed(2)}%`, 'Drawdown']}
                        labelFormatter={(value) => format(new Date(value), 'MMM dd, yyyy')}
                      />
                      <Area
                        dataKey="drawdown"
                        stroke="#ef4444"
                        fill="url(#drawdownGradient)"
                      />
                      <defs>
                        <linearGradient id="drawdownGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#ef4444" stopOpacity={0.8}/>
                          <stop offset="95%" stopColor="#ef4444" stopOpacity={0.1}/>
                        </linearGradient>
                      </defs>
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="performance" className="space-y-6">
          <div className="grid gap-6 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Risk-Adjusted Returns</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-[400px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={filteredData}>
                      <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
                      <XAxis 
                        dataKey="timestamp"
                        tickFormatter={(value) => format(new Date(value), 'MMM')}
                        className="text-xs"
                      />
                      <YAxis className="text-xs" />
                      <Tooltip content={<CustomTooltip />} />
                      <Legend />
                      <Line
                        type="monotone"
                        dataKey="sharpe"
                        stroke="#10b981"
                        strokeWidth={2}
                        dot={false}
                        name="Sharpe Ratio"
                      />
                      <Line
                        type="monotone"
                        dataKey="volatility"
                        stroke="#f59e0b"
                        strokeWidth={2}
                        dot={false}
                        name="Volatility"
                      />
                      <ReferenceLine y={1} stroke="#666" strokeDasharray="2 2" />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Beta Analysis</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-[400px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <ScatterChart data={filteredData}>
                      <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
                      <XAxis 
                        dataKey="volatility"
                        name="Volatility"
                        tickFormatter={(value) => `${(value * 100).toFixed(1)}%`}
                        className="text-xs"
                      />
                      <YAxis 
                        dataKey="sharpe"
                        name="Sharpe"
                        className="text-xs"
                      />
                      <Tooltip 
                        formatter={(value: number, name: string) => [
                          name === 'sharpe' ? value.toFixed(2) : `${(value * 100).toFixed(1)}%`,
                          name === 'sharpe' ? 'Sharpe Ratio' : 'Volatility'
                        ]}
                        labelFormatter={() => 'Risk-Return Profile'}
                      />
                      <Scatter 
                        dataKey="sharpe" 
                        fill="#8884d8"
                        fillOpacity={0.6}
                      />
                      <ReferenceLine x={0.2} stroke="#666" strokeDasharray="2 2" />
                      <ReferenceLine y={1} stroke="#666" strokeDasharray="2 2" />
                    </ScatterChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="risk" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Risk Metrics Over Time</CardTitle>
              <CardDescription>
                Comprehensive risk analysis with multiple metrics
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[400px]">
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart data={filteredData}>
                    <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
                    <XAxis 
                      dataKey="timestamp"
                      tickFormatter={(value) => format(new Date(value), 'MMM')}
                      className="text-xs"
                    />
                    <YAxis yAxisId="left" className="text-xs" />
                    <YAxis yAxisId="right" orientation="right" className="text-xs" />
                    <Tooltip content={<CustomTooltip />} />
                    <Legend />
                    
                    <Bar 
                      yAxisId="right"
                      dataKey="trades" 
                      fill="#8884d8" 
                      opacity={0.3}
                      name="Daily Trades"
                    />
                    
                    <Line
                      yAxisId="left"
                      type="monotone"
                      dataKey="volatility"
                      stroke="#ef4444"
                      strokeWidth={2}
                      dot={false}
                      name="Volatility"
                    />
                    
                    <Line
                      yAxisId="left"
                      type="monotone"
                      dataKey="beta"
                      stroke="#10b981"
                      strokeWidth={2}
                      dot={false}
                      name="Beta"
                    />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="comparison" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Multi-Strategy Comparison</CardTitle>
              <CardDescription>
                Compare performance across different strategies
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-12">
                <BarChart3 className="mx-auto h-16 w-16 text-muted-foreground" />
                <h3 className="mt-4 text-lg font-medium">Strategy Comparison</h3>
                <p className="text-muted-foreground mt-2">
                  Select multiple results to compare their performance side by side
                </p>
                <Button className="mt-4" variant="outline">
                  <Filter className="mr-2 h-4 w-4" />
                  Select Strategies to Compare
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}