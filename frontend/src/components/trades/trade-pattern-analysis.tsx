'use client';

import { useState, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  Cell,
  PieChart,
  Pie
} from 'recharts';
import { 
  BarChart3, 
  TrendingUp, 
  TrendingDown, 
  Clock, 
  Target,
  Info,
  Download
} from 'lucide-react';
import { Trade, GroupingCriteria, GroupedData } from '@/lib/trades/types';
import { groupTrades } from '@/lib/trades/grouping';

interface TradePatternAnalysisProps {
  trades: Trade[];
  className?: string;
}

interface PatternInsightsProps {
  data: GroupedData[];
  groupBy: GroupingCriteria;
  metric: string;
}

const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7c7c', '#8dd1e1', '#d084d0'];

export function TradePatternAnalysis({ trades, className }: TradePatternAnalysisProps) {
  const [groupBy, setGroupBy] = useState<GroupingCriteria>('hourOfDay');
  const [metric, setMetric] = useState<'count' | 'pnl' | 'winRate' | 'avgReturn'>('pnl');
  const [chartType, setChartType] = useState<'bar' | 'pie'>('bar');

  const groupedData = useMemo(() => {
    return groupTrades(trades, groupBy, metric);
  }, [trades, groupBy, metric]);

  const handleExport = () => {
    const csv = [
      ['Group', 'Value', 'Trade Count', 'Win Rate', 'Avg P&L', 'Total P&L'],
      ...groupedData.map(row => [
        row.group,
        row.value,
        row.trades,
        (row.details.winRate * 100).toFixed(1) + '%',
        row.details.avgPnl.toFixed(2),
        row.details.totalPnl.toFixed(2)
      ])
    ].map(row => row.join(',')).join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `trade-patterns-${groupBy}-${metric}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const getMetricLabel = (metric: string) => {
    switch (metric) {
      case 'count': return 'Trade Count';
      case 'pnl': return 'Total P&L ($)';
      case 'winRate': return 'Win Rate (%)';
      case 'avgReturn': return 'Avg Return (%)';
      default: return 'Value';
    }
  };

  const formatValue = (value: number, metric: string) => {
    switch (metric) {
      case 'count': return value.toString();
      case 'pnl': return `$${value.toFixed(0)}`;
      case 'winRate': return `${(value * 100).toFixed(1)}%`;
      case 'avgReturn': return `${(value * 100).toFixed(2)}%`;
      default: return value.toString();
    }
  };

  const CustomBarLabel = ({ value, metric }: { value: number; metric: string }) => {
    return formatValue(value, metric);
  };

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center space-x-2">
            <BarChart3 className="h-5 w-5" />
            <span>Trade Patterns</span>
          </CardTitle>
          
          <Button variant="outline" size="sm" onClick={handleExport}>
            <Download className="h-4 w-4" />
          </Button>
        </div>
        
        <div className="flex flex-wrap gap-4">
          <div className="flex items-center space-x-2">
            <label className="text-sm text-muted-foreground">Group by:</label>
            <Select value={groupBy} onValueChange={(value: GroupingCriteria) => setGroupBy(value)}>
              <SelectTrigger className="w-40">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="hourOfDay">Hour of Day</SelectItem>
                <SelectItem value="dayOfWeek">Day of Week</SelectItem>
                <SelectItem value="month">Month</SelectItem>
                <SelectItem value="side">Trade Side</SelectItem>
                <SelectItem value="entryReason">Entry Reason</SelectItem>
                <SelectItem value="exitReason">Exit Reason</SelectItem>
                <SelectItem value="duration">Duration</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-center space-x-2">
            <label className="text-sm text-muted-foreground">Metric:</label>
            <Select value={metric} onValueChange={(value: any) => setMetric(value)}>
              <SelectTrigger className="w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="count">Count</SelectItem>
                <SelectItem value="pnl">Total P&L</SelectItem>
                <SelectItem value="winRate">Win Rate</SelectItem>
                <SelectItem value="avgReturn">Avg Return</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-center space-x-2">
            <label className="text-sm text-muted-foreground">Chart:</label>
            <Select value={chartType} onValueChange={(value: 'bar' | 'pie') => setChartType(value)}>
              <SelectTrigger className="w-24">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="bar">Bar</SelectItem>
                <SelectItem value="pie">Pie</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        {groupedData.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            No data available for the selected grouping
          </div>
        ) : (
          <>
            {/* Chart */}
            <div className="mb-6">
              <ResponsiveContainer width="100%" height={400}>
                {chartType === 'bar' ? (
                  <BarChart data={groupedData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="group" 
                      angle={-45}
                      textAnchor="end"
                      height={80}
                    />
                    <YAxis />
                    <Tooltip 
                      formatter={(value) => [formatValue(value as number, metric), getMetricLabel(metric)]}
                      labelFormatter={(label) => `${label}`}
                    />
                    <Bar 
                      dataKey="value" 
                      fill="#8884d8"
                      label={<CustomBarLabel metric={metric} />}
                    >
                      {groupedData.map((entry, index) => (
                        <Cell 
                          key={`cell-${index}`} 
                          fill={metric === 'pnl' && entry.value < 0 ? '#ff7c7c' : '#8884d8'} 
                        />
                      ))}
                    </Bar>
                  </BarChart>
                ) : (
                  <PieChart>
                    <Pie
                      data={groupedData.filter(d => d.value > 0)} // Only positive values for pie chart
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
                      outerRadius={120}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {groupedData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value) => [formatValue(value as number, metric), getMetricLabel(metric)]} />
                  </PieChart>
                )}
              </ResponsiveContainer>
            </div>

            {/* Pattern Insights */}
            <PatternInsights data={groupedData} groupBy={groupBy} metric={metric} />

            {/* Data Table */}
            <Card className="mt-6">
              <CardHeader>
                <CardTitle className="text-base">Detailed Breakdown</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left p-2">Group</th>
                        <th className="text-right p-2">Trades</th>
                        <th className="text-right p-2">Win Rate</th>
                        <th className="text-right p-2">Avg P&L</th>
                        <th className="text-right p-2">Total P&L</th>
                        <th className="text-right p-2">{getMetricLabel(metric)}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {groupedData.map((row, index) => (
                        <tr key={index} className="border-b hover:bg-muted/50">
                          <td className="p-2 font-medium">{row.group}</td>
                          <td className="p-2 text-right">{row.trades}</td>
                          <td className="p-2 text-right">
                            <span className={row.details.winRate > 0.5 ? 'text-green-600' : 'text-red-600'}>
                              {(row.details.winRate * 100).toFixed(1)}%
                            </span>
                          </td>
                          <td className="p-2 text-right font-mono">
                            <span className={row.details.avgPnl >= 0 ? 'text-green-600' : 'text-red-600'}>
                              ${row.details.avgPnl.toFixed(2)}
                            </span>
                          </td>
                          <td className="p-2 text-right font-mono">
                            <span className={row.details.totalPnl >= 0 ? 'text-green-600' : 'text-red-600'}>
                              ${row.details.totalPnl.toFixed(2)}
                            </span>
                          </td>
                          <td className="p-2 text-right font-mono">
                            {formatValue(row.value, metric)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </>
        )}
      </CardContent>
    </Card>
  );
}

function PatternInsights({ data, groupBy, metric }: PatternInsightsProps) {
  const insights = useMemo(() => {
    if (data.length === 0) return [];

    const sortedData = [...data].sort((a, b) => b.value - a.value);
    const best = sortedData[0];
    const worst = sortedData[sortedData.length - 1];
    
    const insights = [];

    // Best performing group
    if (best && best.value > 0) {
      insights.push({
        type: 'success',
        icon: TrendingUp,
        message: `Best ${groupBy}: ${best.group} with ${
          metric === 'count' ? `${best.value} trades` :
          metric === 'pnl' ? `$${best.value.toFixed(0)} total P&L` :
          metric === 'winRate' ? `${(best.value * 100).toFixed(1)}% win rate` :
          `${(best.value * 100).toFixed(2)}% avg return`
        }`
      });
    }

    // Worst performing group
    if (worst && worst !== best) {
      insights.push({
        type: 'warning',
        icon: TrendingDown,
        message: `Worst ${groupBy}: ${worst.group} with ${
          metric === 'count' ? `${worst.value} trades` :
          metric === 'pnl' ? `$${worst.value.toFixed(0)} total P&L` :
          metric === 'winRate' ? `${(worst.value * 100).toFixed(1)}% win rate` :
          `${(worst.value * 100).toFixed(2)}% avg return`
        }`
      });
    }

    // Time-based insights
    if (groupBy === 'hourOfDay') {
      const marketHours = data.filter(d => {
        const hour = parseInt(d.group.split(':')[0]);
        return hour >= 9 && hour <= 16; // Market hours
      });
      const afterHours = data.filter(d => {
        const hour = parseInt(d.group.split(':')[0]);
        return hour < 9 || hour > 16;
      });

      if (marketHours.length > 0 && afterHours.length > 0) {
        const marketTotal = marketHours.reduce((sum, d) => sum + d.details.totalPnl, 0);
        const afterTotal = afterHours.reduce((sum, d) => sum + d.details.totalPnl, 0);
        
        insights.push({
          type: 'info',
          icon: Clock,
          message: `Market hours: $${marketTotal.toFixed(0)} vs After hours: $${afterTotal.toFixed(0)}`
        });
      }
    }

    // Side-based insights
    if (groupBy === 'side') {
      const longData = data.find(d => d.group === 'Long');
      const shortData = data.find(d => d.group === 'Short');
      
      if (longData && shortData) {
        const longWinRate = longData.details.winRate;
        const shortWinRate = shortData.details.winRate;
        
        if (Math.abs(longWinRate - shortWinRate) > 0.1) {
          insights.push({
            type: longWinRate > shortWinRate ? 'info' : 'info',
            icon: Target,
            message: `${longWinRate > shortWinRate ? 'Long' : 'Short'} trades perform better: ${
              ((longWinRate > shortWinRate ? longWinRate : shortWinRate) * 100).toFixed(1)
            }% win rate vs ${
              ((longWinRate > shortWinRate ? shortWinRate : longWinRate) * 100).toFixed(1)
            }%`
          });
        }
      }
    }

    return insights;
  }, [data, groupBy, metric]);

  if (insights.length === 0) return null;

  return (
    <Card className="bg-muted/20">
      <CardHeader>
        <CardTitle className="text-base flex items-center space-x-2">
          <Info className="h-4 w-4" />
          <span>Pattern Insights</span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {insights.map((insight, index) => {
            const IconComponent = insight.icon;
            return (
              <div key={index} className="flex items-center space-x-3">
                <div className={`p-2 rounded-lg ${
                  insight.type === 'success' ? 'bg-green-100 text-green-600 dark:bg-green-950/20' :
                  insight.type === 'warning' ? 'bg-orange-100 text-orange-600 dark:bg-orange-950/20' :
                  'bg-blue-100 text-blue-600 dark:bg-blue-950/20'
                }`}>
                  <IconComponent className="h-4 w-4" />
                </div>
                <p className="text-sm">{insight.message}</p>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}