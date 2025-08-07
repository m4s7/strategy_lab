'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useState, useRef, useCallback, useMemo } from 'react';
import { format, parseISO, getDay, getHours, startOfWeek, startOfDay } from 'date-fns';
import { 
  Download, 
  Calendar,
  Clock,
  TrendingUp,
  TrendingDown,
  Filter,
  Info
} from 'lucide-react';

export interface TradeDataPoint {
  tradeId: string;
  timestamp: string;
  pnl: number;
  return_pct: number;
  duration: number;
  type: 'long' | 'short';
  entryPrice: number;
  exitPrice: number;
}

interface HeatmapCell {
  row: number;
  col: number;
  value: number;
  count: number;
  label: string;
  tooltip: string;
}

interface HeatmapData {
  cells: HeatmapCell[];
  rowLabels: string[];
  colLabels: string[];
  maxValue: number;
  minValue: number;
  title: string;
}

interface PerformanceHeatmapProps {
  data: TradeDataPoint[];
  aggregationType?: 'pnl' | 'return_pct' | 'count';
  timeFormat?: 'hourly' | 'daily' | 'weekly';
  viewType?: 'time-of-day' | 'day-of-week' | 'monthly' | 'combined';
  exportable?: boolean;
  className?: string;
}

const chartConfig = {
  positive: {
    label: "Positive P&L",
    color: "hsl(var(--color-bullish))",
  },
  negative: {
    label: "Negative P&L", 
    color: "hsl(var(--color-bearish))",
  },
  neutral: {
    label: "Neutral",
    color: "hsl(var(--muted))",
  },
};

export function PerformanceHeatmap({
  data,
  aggregationType = 'pnl',
  timeFormat = 'hourly',
  viewType = 'time-of-day',
  exportable = true,
  className
}: PerformanceHeatmapProps) {
  const heatmapRef = useRef<HTMLDivElement>(null);
  const [selectedCell, setSelectedCell] = useState<HeatmapCell | null>(null);
  const [activeView, setActiveView] = useState(viewType);
  const [activeAgg, setActiveAgg] = useState(aggregationType);

  // Generate time-of-day vs day-of-week heatmap
  const timeOfDayHeatmap = useMemo(() => {
    const dayLabels = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    const hourLabels = Array.from({ length: 24 }, (_, i) => `${i}:00`);
    
    // Initialize grid
    const grid: { [key: string]: { value: number; count: number } } = {};
    
    data.forEach(trade => {
      const date = parseISO(trade.timestamp);
      const day = getDay(date);
      const hour = getHours(date);
      const key = `${day}-${hour}`;
      
      if (!grid[key]) {
        grid[key] = { value: 0, count: 0 };
      }
      
      grid[key].count++;
      switch (activeAgg) {
        case 'pnl':
          grid[key].value += trade.pnl;
          break;
        case 'return_pct':
          grid[key].value += trade.return_pct;
          break;
        case 'count':
          grid[key].value = grid[key].count;
          break;
      }
    });

    // Convert to cells
    const cells: HeatmapCell[] = [];
    let maxValue = -Infinity;
    let minValue = Infinity;

    for (let day = 0; day < 7; day++) {
      for (let hour = 0; hour < 24; hour++) {
        const key = `${day}-${hour}`;
        const cellData = grid[key] || { value: 0, count: 0 };
        const avgValue = cellData.count > 0 && activeAgg !== 'count' ? 
          cellData.value / cellData.count : cellData.value;

        cells.push({
          row: day,
          col: hour,
          value: avgValue,
          count: cellData.count,
          label: `${dayLabels[day]} ${hourLabels[hour]}`,
          tooltip: `${dayLabels[day]} at ${hourLabels[hour]}: ${formatValue(avgValue, activeAgg)} (${cellData.count} trades)`
        });

        if (cellData.count > 0) {
          maxValue = Math.max(maxValue, avgValue);
          minValue = Math.min(minValue, avgValue);
        }
      }
    }

    return {
      cells,
      rowLabels: dayLabels,
      colLabels: hourLabels,
      maxValue: maxValue === -Infinity ? 0 : maxValue,
      minValue: minValue === Infinity ? 0 : minValue,
      title: `Performance by Time of Day and Day of Week`
    };
  }, [data, activeAgg]);

  // Generate monthly performance heatmap
  const monthlyHeatmap = useMemo(() => {
    const monthLabels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const yearSet = new Set(data.map(trade => parseISO(trade.timestamp).getFullYear()));
    const years = Array.from(yearSet).sort();
    
    const grid: { [key: string]: { value: number; count: number } } = {};
    
    data.forEach(trade => {
      const date = parseISO(trade.timestamp);
      const year = date.getFullYear();
      const month = date.getMonth();
      const key = `${year}-${month}`;
      
      if (!grid[key]) {
        grid[key] = { value: 0, count: 0 };
      }
      
      grid[key].count++;
      switch (activeAgg) {
        case 'pnl':
          grid[key].value += trade.pnl;
          break;
        case 'return_pct':
          grid[key].value += trade.return_pct;
          break;
        case 'count':
          grid[key].value = grid[key].count;
          break;
      }
    });

    const cells: HeatmapCell[] = [];
    let maxValue = -Infinity;
    let minValue = Infinity;

    years.forEach((year, yearIndex) => {
      for (let month = 0; month < 12; month++) {
        const key = `${year}-${month}`;
        const cellData = grid[key] || { value: 0, count: 0 };
        const totalValue = activeAgg === 'count' ? cellData.count : cellData.value;

        cells.push({
          row: yearIndex,
          col: month,
          value: totalValue,
          count: cellData.count,
          label: `${monthLabels[month]} ${year}`,
          tooltip: `${monthLabels[month]} ${year}: ${formatValue(totalValue, activeAgg)} (${cellData.count} trades)`
        });

        if (cellData.count > 0) {
          maxValue = Math.max(maxValue, totalValue);
          minValue = Math.min(minValue, totalValue);
        }
      }
    });

    return {
      cells,
      rowLabels: years.map(y => y.toString()),
      colLabels: monthLabels,
      maxValue: maxValue === -Infinity ? 0 : maxValue,
      minValue: minValue === Infinity ? 0 : minValue,
      title: `Monthly Performance by Year`
    };
  }, [data, activeAgg]);

  const currentHeatmap = activeView === 'monthly' ? monthlyHeatmap : timeOfDayHeatmap;

  const formatValue = (value: number, type: string) => {
    switch (type) {
      case 'pnl':
        return new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD',
          minimumFractionDigits: 0,
          maximumFractionDigits: 0,
        }).format(value);
      case 'return_pct':
        return `${value.toFixed(2)}%`;
      case 'count':
        return value.toString();
      default:
        return value.toFixed(2);
    }
  };

  const getCellColor = (value: number, min: number, max: number) => {
    if (value === 0) return 'hsl(var(--muted))';
    
    const absMax = Math.max(Math.abs(min), Math.abs(max));
    const normalizedValue = value / absMax;
    
    if (normalizedValue > 0) {
      const intensity = Math.min(normalizedValue, 1);
      return `hsl(var(--color-bullish) / ${0.2 + intensity * 0.8})`;
    } else {
      const intensity = Math.min(Math.abs(normalizedValue), 1);
      return `hsl(var(--color-bearish) / ${0.2 + intensity * 0.8})`;
    }
  };

  const exportHeatmap = useCallback(async () => {
    // Export functionality would be implemented here
    console.log('Exporting heatmap...');
  }, []);

  const handleCellHover = useCallback((cell: HeatmapCell) => {
    setSelectedCell(cell);
  }, []);

  const handleCellLeave = useCallback(() => {
    setSelectedCell(null);
  }, []);

  // Calculate summary statistics
  const summaryStats = useMemo(() => {
    const totalTrades = data.length;
    const totalPnL = data.reduce((sum, trade) => sum + trade.pnl, 0);
    const avgReturn = data.reduce((sum, trade) => sum + trade.return_pct, 0) / totalTrades;
    const winRate = (data.filter(trade => trade.pnl > 0).length / totalTrades) * 100;
    
    return {
      totalTrades,
      totalPnL,
      avgReturn,
      winRate
    };
  }, [data]);

  if (data.length === 0) {
    return (
      <Card className={className}>
        <CardContent className="p-6">
          <div className="text-center text-muted-foreground">No trade data available</div>
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
              <Calendar className="h-5 w-5" />
              <span>Performance Heatmap</span>
            </CardTitle>
            <CardDescription>
              {currentHeatmap.title}
            </CardDescription>
          </div>
          <div className="flex items-center space-x-2">
            <Badge variant="outline">
              {summaryStats.totalTrades} trades
            </Badge>
            {exportable && (
              <Button variant="outline" size="sm" onClick={exportHeatmap}>
                <Download className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {/* Summary Statistics */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div className="text-center p-3 bg-muted/30 rounded-lg">
            <div className={`text-lg font-medium ${summaryStats.totalPnL >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {formatValue(summaryStats.totalPnL, 'pnl')}
            </div>
            <div className="text-xs text-muted-foreground">Total P&L</div>
          </div>
          <div className="text-center p-3 bg-muted/30 rounded-lg">
            <div className={`text-lg font-medium ${summaryStats.avgReturn >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {formatValue(summaryStats.avgReturn, 'return_pct')}
            </div>
            <div className="text-xs text-muted-foreground">Avg Return</div>
          </div>
          <div className="text-center p-3 bg-muted/30 rounded-lg">
            <div className="text-lg font-medium">
              {summaryStats.winRate.toFixed(1)}%
            </div>
            <div className="text-xs text-muted-foreground">Win Rate</div>
          </div>
          <div className="text-center p-3 bg-muted/30 rounded-lg">
            <div className="text-lg font-medium">
              {summaryStats.totalTrades}
            </div>
            <div className="text-xs text-muted-foreground">Total Trades</div>
          </div>
        </div>

        {/* Controls */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-2">
            <Select value={activeView} onValueChange={(value: any) => setActiveView(value)}>
              <SelectTrigger className="w-40">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="time-of-day">Time of Day</SelectItem>
                <SelectItem value="monthly">Monthly</SelectItem>
              </SelectContent>
            </Select>
            
            <Select value={activeAgg} onValueChange={(value: any) => setActiveAgg(value)}>
              <SelectTrigger className="w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="pnl">P&L</SelectItem>
                <SelectItem value="return_pct">Returns %</SelectItem>
                <SelectItem value="count">Count</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-center space-x-2">
            <div className="flex items-center space-x-1 text-xs">
              <div className="w-3 h-3 rounded" style={{ backgroundColor: 'hsl(var(--color-bearish) / 0.7)' }} />
              <span>Loss</span>
            </div>
            <div className="flex items-center space-x-1 text-xs">
              <div className="w-3 h-3 rounded" style={{ backgroundColor: 'hsl(var(--muted))' }} />
              <span>Neutral</span>
            </div>
            <div className="flex items-center space-x-1 text-xs">
              <div className="w-3 h-3 rounded" style={{ backgroundColor: 'hsl(var(--color-bullish) / 0.7)' }} />
              <span>Profit</span>
            </div>
          </div>
        </div>

        {/* Heatmap Grid */}
        <div ref={heatmapRef} className="overflow-x-auto">
          <div className="inline-block min-w-full">
            {/* Column headers */}
            <div className="flex mb-1">
              <div className="w-16" /> {/* Empty corner */}
              {currentHeatmap.colLabels.map((label, index) => (
                <div 
                  key={index}
                  className="flex-none w-8 text-xs text-center text-muted-foreground p-1 font-mono"
                >
                  {label.length > 3 ? label.slice(0, 3) : label}
                </div>
              ))}
            </div>
            
            {/* Heatmap rows */}
            {currentHeatmap.rowLabels.map((rowLabel, rowIndex) => (
              <div key={rowIndex} className="flex mb-1">
                {/* Row header */}
                <div className="w-16 text-xs text-right text-muted-foreground p-1 pr-2">
                  {rowLabel}
                </div>
                
                {/* Row cells */}
                {currentHeatmap.colLabels.map((_, colIndex) => {
                  const cell = currentHeatmap.cells.find(c => c.row === rowIndex && c.col === colIndex);
                  const cellValue = cell?.value || 0;
                  const cellCount = cell?.count || 0;
                  
                  return (
                    <div
                      key={colIndex}
                      className="flex-none w-8 h-8 border border-border/50 cursor-pointer transition-all duration-150 hover:scale-110 hover:z-10 relative"
                      style={{
                        backgroundColor: getCellColor(cellValue, currentHeatmap.minValue, currentHeatmap.maxValue)
                      }}
                      onMouseEnter={() => cell && handleCellHover(cell)}
                      onMouseLeave={handleCellLeave}
                      title={cell?.tooltip}
                    >
                      {cellCount > 0 && (
                        <div className="absolute inset-0 flex items-center justify-center">
                          <div className="text-xs font-mono font-medium text-foreground/80">
                            {cellCount > 99 ? '99+' : cellCount || ''}
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            ))}
          </div>
        </div>

        {/* Selected Cell Details */}
        {selectedCell && (
          <div className="mt-6 p-4 bg-muted/20 rounded-lg">
            <div className="flex items-center space-x-2 mb-2">
              <Info className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm font-medium">Cell Details</span>
            </div>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-muted-foreground">Period: </span>
                <span className="font-medium">{selectedCell.label}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Value: </span>
                <span className="font-medium">{formatValue(selectedCell.value, activeAgg)}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Trades: </span>
                <span className="font-medium">{selectedCell.count}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Avg per Trade: </span>
                <span className="font-medium">
                  {selectedCell.count > 0 ? formatValue(selectedCell.value / selectedCell.count, activeAgg) : 'N/A'}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Legend and Summary */}
        <div className="mt-6 flex items-center justify-between text-xs text-muted-foreground">
          <div className="flex items-center space-x-4">
            <div>Min: {formatValue(currentHeatmap.minValue, activeAgg)}</div>
            <div>Max: {formatValue(currentHeatmap.maxValue, activeAgg)}</div>
          </div>
          <div>
            Hover over cells for detailed information
          </div>
        </div>
      </CardContent>
    </Card>
  );
}