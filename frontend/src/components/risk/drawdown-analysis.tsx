"use client";

import { useState, useEffect, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  LineChart,
  Line,
} from "recharts";
import { TrendingDown, Clock, Calendar, Download, AlertCircle } from "lucide-react";
import { DrawdownPeriod } from "@/lib/risk/types";
import { generateMockDrawdowns, generateMockPortfolioSeries } from "@/lib/risk/mock-data";

interface DrawdownAnalysisProps {
  backtestId: string;
}

export function DrawdownAnalysis({ backtestId }: DrawdownAnalysisProps) {
  const [drawdowns, setDrawdowns] = useState<DrawdownPeriod[]>([]);
  const [selectedDrawdown, setSelectedDrawdown] = useState<DrawdownPeriod>();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadDrawdowns = async () => {
      setLoading(true);
      try {
        // Simulate API delay
        await new Promise(resolve => setTimeout(resolve, 800));
        const mockDrawdowns = generateMockDrawdowns();
        setDrawdowns(mockDrawdowns);
      } catch (error) {
        console.error("Failed to load drawdowns:", error);
      } finally {
        setLoading(false);
      }
    };

    loadDrawdowns();
  }, [backtestId]);

  // Generate drawdown chart data
  const drawdownChartData = useMemo(() => {
    const { dates, values } = generateMockPortfolioSeries(100000, 252);
    
    // Calculate running peak and drawdown
    const data = [];
    let peak = values[0];
    
    for (let i = 0; i < values.length; i++) {
      if (values[i] > peak) {
        peak = values[i];
      }
      
      const drawdown = (peak - values[i]) / peak;
      
      data.push({
        date: dates[i],
        value: values[i],
        peak,
        drawdown: -drawdown * 100, // Negative for proper chart display
        drawdownPercent: drawdown * 100
      });
    }
    
    return data;
  }, []);

  // Drawdown statistics
  const drawdownStats = useMemo(() => {
    if (!drawdowns.length) return null;

    const maxDrawdown = Math.max(...drawdowns.map(d => d.maxDrawdown));
    const avgDrawdown = drawdowns.reduce((sum, d) => sum + d.maxDrawdown, 0) / drawdowns.length;
    const avgDuration = drawdowns.reduce((sum, d) => sum + d.duration, 0) / drawdowns.length;
    
    const recoveredDrawdowns = drawdowns.filter(d => d.recovered);
    const avgRecovery = recoveredDrawdowns.length > 0 ?
      recoveredDrawdowns.reduce((sum, d) => sum + d.recoveryTime, 0) / recoveredDrawdowns.length : 0;
    
    const currentDrawdown = drawdowns.find(d => !d.recovered);

    return {
      count: drawdowns.length,
      maxDrawdown,
      avgDrawdown,
      avgDuration,
      avgRecovery,
      currentDrawdown: currentDrawdown?.maxDrawdown || 0,
      recoveryRate: recoveredDrawdowns.length / drawdowns.length
    };
  }, [drawdowns]);

  // Duration distribution data
  const durationDistribution = useMemo(() => {
    const bins = [
      { range: '0-7 days', count: 0, min: 0, max: 7 },
      { range: '1-2 weeks', count: 0, min: 8, max: 14 },
      { range: '2-4 weeks', count: 0, min: 15, max: 28 },
      { range: '1-2 months', count: 0, min: 29, max: 60 },
      { range: '2+ months', count: 0, min: 61, max: Infinity }
    ];

    drawdowns.forEach(dd => {
      const bin = bins.find(b => dd.duration >= b.min && dd.duration <= b.max);
      if (bin) bin.count++;
    });

    return bins.filter(b => b.count > 0);
  }, [drawdowns]);

  const handleExport = () => {
    const csvData = [
      ["Start Date", "End Date", "Trough Date", "Max Drawdown (%)", "Duration (Days)", "Recovery Time (Days)", "Status"],
      ...drawdowns.map(dd => [
        dd.start.split('T')[0],
        dd.end.split('T')[0],
        dd.trough.split('T')[0],
        (dd.maxDrawdown * 100).toFixed(2),
        dd.duration.toString(),
        dd.recoveryTime.toString(),
        dd.recovered ? "Recovered" : "Ongoing"
      ])
    ].map(row => row.join(",")).join("\\n");

    const blob = new Blob([csvData], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `drawdown-analysis-${backtestId}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  if (loading) {
    return (
      <div className="space-y-6">
        {[...Array(3)].map((_, i) => (
          <Card key={i}>
            <CardContent className="p-6">
              <div className="animate-pulse">
                <div className="h-4 bg-muted rounded w-1/4 mb-4"></div>
                <div className="h-48 bg-muted rounded"></div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Drawdown Chart */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center space-x-2">
              <TrendingDown className="h-5 w-5" />
              <span>Drawdown Timeline</span>
            </CardTitle>
            
            <Button variant="outline" size="sm" onClick={handleExport}>
              <Download className="h-4 w-4 mr-2" />
              Export
            </Button>
          </div>
        </CardHeader>
        
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={drawdownChartData}>
              <defs>
                <linearGradient id="drawdownGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#ef4444" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="#ef4444" stopOpacity={0.2}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="date" 
                tick={{ fontSize: 12 }}
                tickFormatter={(value) => new Date(value).toLocaleDateString()}
              />
              <YAxis 
                tick={{ fontSize: 12 }}
                tickFormatter={(value) => `${value.toFixed(1)}%`}
              />
              <Tooltip 
                formatter={(value) => [`${Number(value).toFixed(2)}%`, "Drawdown"]}
                labelFormatter={(value) => new Date(value).toLocaleDateString()}
              />
              <Area
                type="monotone"
                dataKey="drawdown"
                stroke="#ef4444"
                fillOpacity={1}
                fill="url(#drawdownGradient)"
              />
            </AreaChart>
          </ResponsiveContainer>

          {/* Drawdown Timeline/Navigator */}
          <div className="mt-4 space-y-2">
            <h4 className="text-sm font-medium">Major Drawdown Periods</h4>
            <div className="flex flex-wrap gap-2">
              {drawdowns
                .filter(dd => dd.maxDrawdown > 0.05) // Only show significant drawdowns
                .map((dd) => (
                <Button
                  key={dd.id}
                  variant={selectedDrawdown?.id === dd.id ? "default" : "outline"}
                  size="sm"
                  className="h-8 text-xs"
                  onClick={() => setSelectedDrawdown(dd)}
                >
                  {new Date(dd.start).toLocaleDateString()} 
                  <Badge variant="secondary" className="ml-2 text-xs">
                    -{(dd.maxDrawdown * 100).toFixed(1)}%
                  </Badge>
                </Button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Drawdown Table */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Drawdown Details</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Start</TableHead>
                  <TableHead>Max DD</TableHead>
                  <TableHead>Duration</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {drawdowns.map((dd) => (
                  <TableRow 
                    key={dd.id}
                    className={`cursor-pointer hover:bg-muted/50 ${
                      selectedDrawdown?.id === dd.id ? "bg-muted" : ""
                    }`}
                    onClick={() => setSelectedDrawdown(dd)}
                  >
                    <TableCell className="font-mono text-sm">
                      {new Date(dd.start).toLocaleDateString()}
                    </TableCell>
                    <TableCell>
                      <span className="text-red-600 font-medium">
                        -{(dd.maxDrawdown * 100).toFixed(2)}%
                      </span>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center space-x-1">
                        <Clock className="h-3 w-3 text-muted-foreground" />
                        <span className="text-sm">{dd.duration}d</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant={dd.recovered ? "default" : "destructive"}>
                        {dd.recovered ? "Recovered" : "Ongoing"}
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        {/* Selected Drawdown Details */}
        {selectedDrawdown && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2 text-base">
                <AlertCircle className="h-4 w-4" />
                <span>Drawdown Details</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs text-muted-foreground">Start Date</label>
                    <div className="font-medium">
                      {new Date(selectedDrawdown.start).toLocaleDateString()}
                    </div>
                  </div>
                  <div>
                    <label className="text-xs text-muted-foreground">End Date</label>
                    <div className="font-medium">
                      {selectedDrawdown.recovered ? 
                        new Date(selectedDrawdown.end).toLocaleDateString() : 
                        "Ongoing"
                      }
                    </div>
                  </div>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs text-muted-foreground">Trough Date</label>
                    <div className="font-medium">
                      {new Date(selectedDrawdown.trough).toLocaleDateString()}
                    </div>
                  </div>
                  <div>
                    <label className="text-xs text-muted-foreground">Max Drawdown</label>
                    <div className="font-bold text-red-600">
                      -{(selectedDrawdown.maxDrawdown * 100).toFixed(2)}%
                    </div>
                  </div>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs text-muted-foreground">Total Duration</label>
                    <div className="font-medium">{selectedDrawdown.duration} days</div>
                  </div>
                  <div>
                    <label className="text-xs text-muted-foreground">Recovery Time</label>
                    <div className="font-medium">
                      {selectedDrawdown.recovered ? 
                        `${selectedDrawdown.recoveryTime} days` : 
                        "N/A"
                      }
                    </div>
                  </div>
                </div>

                <div className="pt-4 border-t">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">Recovery Status</span>
                    <Badge variant={selectedDrawdown.recovered ? "default" : "destructive"}>
                      {selectedDrawdown.recovered ? "Fully Recovered" : "In Progress"}
                    </Badge>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Duration Distribution */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Duration Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={durationDistribution}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="range" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Bar dataKey="count" fill="#3b82f6" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Drawdown Statistics */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Summary Statistics</CardTitle>
          </CardHeader>
          <CardContent>
            {drawdownStats && (
              <div className="space-y-4">
                <div className="flex justify-between items-center py-2 border-b">
                  <span className="text-sm text-muted-foreground">Total Drawdowns</span>
                  <Badge variant="outline">{drawdownStats.count}</Badge>
                </div>
                
                <div className="flex justify-between items-center py-2 border-b">
                  <span className="text-sm text-muted-foreground">Maximum Drawdown</span>
                  <Badge variant="destructive">
                    -{(drawdownStats.maxDrawdown * 100).toFixed(2)}%
                  </Badge>
                </div>
                
                <div className="flex justify-between items-center py-2 border-b">
                  <span className="text-sm text-muted-foreground">Average Drawdown</span>
                  <span className="text-sm font-medium text-red-600">
                    -{(drawdownStats.avgDrawdown * 100).toFixed(2)}%
                  </span>
                </div>
                
                <div className="flex justify-between items-center py-2 border-b">
                  <span className="text-sm text-muted-foreground">Average Duration</span>
                  <span className="text-sm font-medium">
                    {Math.round(drawdownStats.avgDuration)} days
                  </span>
                </div>
                
                <div className="flex justify-between items-center py-2 border-b">
                  <span className="text-sm text-muted-foreground">Average Recovery</span>
                  <span className="text-sm font-medium">
                    {Math.round(drawdownStats.avgRecovery)} days
                  </span>
                </div>
                
                <div className="flex justify-between items-center py-2 border-b">
                  <span className="text-sm text-muted-foreground">Recovery Rate</span>
                  <Badge variant={drawdownStats.recoveryRate === 1 ? "default" : "secondary"}>
                    {(drawdownStats.recoveryRate * 100).toFixed(0)}%
                  </Badge>
                </div>
                
                {drawdownStats.currentDrawdown > 0 && (
                  <div className="flex justify-between items-center py-2">
                    <span className="text-sm text-muted-foreground">Current Drawdown</span>
                    <Badge variant="destructive">
                      -{(drawdownStats.currentDrawdown * 100).toFixed(2)}%
                    </Badge>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}