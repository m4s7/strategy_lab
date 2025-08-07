'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useState, useMemo, useCallback } from 'react';
import { 
  Download,
  Grid3X3,
  Info,
  Eye,
  Maximize2
} from 'lucide-react';
import { CorrelationMatrix } from '@/lib/portfolio/types';

interface CorrelationHeatmapProps {
  data: CorrelationMatrix | null;
  onExport?: () => void;
  className?: string;
}

interface CorrelationCell {
  row: number;
  col: number;
  value: number;
  strategy1: string;
  strategy2: string;
  color: string;
  intensity: number;
}

export function CorrelationHeatmap({ data, onExport, className }: CorrelationHeatmapProps) {
  const [selectedPair, setSelectedPair] = useState<[string, string] | null>(null);
  const [colorScheme, setColorScheme] = useState<'diverging' | 'sequential'>('diverging');
  const [showValues, setShowValues] = useState(true);

  // Generate heatmap cells
  const heatmapCells = useMemo(() => {
    if (!data) return [];

    const cells: CorrelationCell[] = [];
    const n = data.strategies.length;

    for (let i = 0; i < n; i++) {
      for (let j = 0; j < n; j++) {
        const value = data.values[i][j];
        const intensity = Math.abs(value);
        
        let color: string;
        if (colorScheme === 'diverging') {
          // Red-White-Blue diverging scale
          if (value > 0) {
            const alpha = value;
            color = `rgba(59, 130, 246, ${alpha})`; // Blue for positive
          } else {
            const alpha = Math.abs(value);
            color = `rgba(239, 68, 68, ${alpha})`; // Red for negative
          }
        } else {
          // Sequential blue scale
          const alpha = intensity * 0.8 + 0.1;
          color = `rgba(59, 130, 246, ${alpha})`;
        }

        cells.push({
          row: i,
          col: j,
          value,
          strategy1: data.strategies[i],
          strategy2: data.strategies[j],
          color,
          intensity
        });
      }
    }

    return cells;
  }, [data, colorScheme]);

  // Handle cell click
  const handleCellClick = useCallback((strategy1: string, strategy2: string) => {
    if (strategy1 === strategy2) return; // Skip diagonal cells
    setSelectedPair([strategy1, strategy2]);
  }, []);

  // Get correlation interpretation
  const getCorrelationInterpretation = (correlation: number) => {
    const abs = Math.abs(correlation);
    if (abs >= 0.8) return { level: 'Very Strong', color: 'text-red-600' };
    if (abs >= 0.6) return { level: 'Strong', color: 'text-orange-600' };
    if (abs >= 0.4) return { level: 'Moderate', color: 'text-yellow-600' };
    if (abs >= 0.2) return { level: 'Weak', color: 'text-blue-600' };
    return { level: 'Very Weak', color: 'text-green-600' };
  };

  // Calculate correlation statistics
  const correlationStats = useMemo(() => {
    if (!data) return null;

    const values = data.values.flat().filter((v, i, arr) => {
      const row = Math.floor(i / data.strategies.length);
      const col = i % data.strategies.length;
      return row !== col; // Exclude diagonal (perfect correlation = 1)
    });

    const avgCorrelation = values.reduce((sum, v) => sum + v, 0) / values.length;
    const maxCorrelation = Math.max(...values);
    const minCorrelation = Math.min(...values);
    
    // Find pairs with highest and lowest correlations
    let maxPair = ['', ''];
    let minPair = ['', ''];
    let maxValue = -2;
    let minValue = 2;

    for (let i = 0; i < data.strategies.length; i++) {
      for (let j = i + 1; j < data.strategies.length; j++) {
        const value = data.values[i][j];
        if (value > maxValue) {
          maxValue = value;
          maxPair = [data.strategies[i], data.strategies[j]];
        }
        if (value < minValue) {
          minValue = value;
          minPair = [data.strategies[i], data.strategies[j]];
        }
      }
    }

    return {
      avgCorrelation,
      maxCorrelation: maxValue,
      minCorrelation: minValue,
      maxPair,
      minPair,
      pairsAbove60: values.filter(v => Math.abs(v) > 0.6).length,
      totalPairs: values.length
    };
  }, [data]);

  if (!data) {
    return (
      <Card className={className}>
        <CardContent className="p-6">
          <div className="text-center text-muted-foreground">Loading correlation data...</div>
        </CardContent>
      </Card>
    );
  }

  const selectedCorrelation = selectedPair ? 
    data.values[data.strategies.indexOf(selectedPair[0])][data.strategies.indexOf(selectedPair[1])] : 
    null;

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center space-x-2">
              <Grid3X3 className="h-5 w-5" />
              <span>Strategy Correlations</span>
            </CardTitle>
            <CardDescription>
              Correlation matrix showing relationships between strategy returns
            </CardDescription>
          </div>
          
          <div className="flex items-center space-x-2">
            <Badge variant="outline">
              {data.strategies.length}×{data.strategies.length} Matrix
            </Badge>
            {onExport && (
              <Button variant="outline" size="sm" onClick={onExport}>
                <Download className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent>
        {/* Controls */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <label className="text-sm text-muted-foreground">Color Scheme:</label>
              <Select value={colorScheme} onValueChange={(value: 'diverging' | 'sequential') => setColorScheme(value)}>
                <SelectTrigger className="w-32">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="diverging">Diverging</SelectItem>
                  <SelectItem value="sequential">Sequential</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <Button
              variant={showValues ? "default" : "outline"}
              size="sm"
              onClick={() => setShowValues(!showValues)}
            >
              <Eye className="h-4 w-4 mr-2" />
              Values
            </Button>
          </div>

          <Button variant="outline" size="sm">
            <Maximize2 className="h-4 w-4" />
          </Button>
        </div>

        {/* Heatmap Grid */}
        <div className="mb-6 overflow-x-auto">
          <div className="inline-block min-w-full">
            <div className="relative">
              {/* Column headers */}
              <div className="flex mb-2">
                <div className="w-24" /> {/* Empty corner */}
                {data.strategies.map((strategy, index) => (
                  <div 
                    key={index}
                    className="flex-none w-20 text-xs text-center text-muted-foreground p-1 font-medium"
                    style={{ writingMode: 'vertical-rl', textOrientation: 'mixed' }}
                  >
                    {strategy.length > 8 ? `${strategy.substring(0, 8)}...` : strategy}
                  </div>
                ))}
              </div>
              
              {/* Heatmap rows */}
              {data.strategies.map((rowStrategy, rowIndex) => (
                <div key={rowIndex} className="flex mb-1">
                  {/* Row header */}
                  <div className="w-24 text-xs text-right text-muted-foreground p-2 pr-3 font-medium">
                    {rowStrategy.length > 10 ? `${rowStrategy.substring(0, 10)}...` : rowStrategy}
                  </div>
                  
                  {/* Row cells */}
                  {data.strategies.map((colStrategy, colIndex) => {
                    const cell = heatmapCells.find(c => c.row === rowIndex && c.col === colIndex);
                    if (!cell) return null;

                    const isDiagonal = rowIndex === colIndex;
                    const isSelected = selectedPair && 
                      ((selectedPair[0] === rowStrategy && selectedPair[1] === colStrategy) ||
                       (selectedPair[1] === rowStrategy && selectedPair[0] === colStrategy));

                    return (
                      <div
                        key={colIndex}
                        className={`flex-none w-20 h-12 border border-border/50 cursor-pointer transition-all duration-150 hover:scale-105 hover:z-10 relative flex items-center justify-center ${
                          isDiagonal ? 'border-2 border-primary/30' : ''
                        } ${isSelected ? 'ring-2 ring-primary ring-offset-2' : ''}`}
                        style={{
                          backgroundColor: isDiagonal ? 'hsl(var(--muted))' : cell.color
                        }}
                        onClick={() => handleCellClick(rowStrategy, colStrategy)}
                        title={`${rowStrategy} vs ${colStrategy}: ${cell.value.toFixed(3)}`}
                      >
                        {showValues && (
                          <span className={`text-xs font-mono font-medium ${
                            isDiagonal ? 'text-muted-foreground' : 
                            cell.intensity > 0.5 ? 'text-white' : 'text-foreground'
                          }`}>
                            {isDiagonal ? '1.0' : cell.value.toFixed(2)}
                          </span>
                        )}
                      </div>
                    );
                  })}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Legend */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 bg-red-500 rounded" />
              <span className="text-xs text-muted-foreground">Negative</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 bg-gray-200 rounded" />
              <span className="text-xs text-muted-foreground">Zero</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 bg-blue-500 rounded" />
              <span className="text-xs text-muted-foreground">Positive</span>
            </div>
          </div>
          
          <div className="text-xs text-muted-foreground">
            Range: -1.00 to +1.00 | Click cells for details
          </div>
        </div>

        {/* Selected Pair Details */}
        {selectedPair && selectedCorrelation !== null && (
          <Card className="mb-6 bg-muted/20">
            <CardContent className="p-4">
              <div className="flex items-center space-x-2 mb-3">
                <Info className="h-4 w-4 text-muted-foreground" />
                <span className="font-medium">Correlation Detail</span>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-muted-foreground">Strategy Pair</p>
                  <p className="font-medium">{selectedPair[0]} × {selectedPair[1]}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Correlation</p>
                  <div className="flex items-center space-x-2">
                    <p className="font-medium font-mono">{selectedCorrelation.toFixed(4)}</p>
                    <Badge 
                      variant="outline" 
                      className={getCorrelationInterpretation(selectedCorrelation).color}
                    >
                      {getCorrelationInterpretation(selectedCorrelation).level}
                    </Badge>
                  </div>
                </div>
              </div>

              <div className="mt-3 p-3 bg-background rounded border">
                <p className="text-xs text-muted-foreground">
                  <strong>Interpretation:</strong> {
                    Math.abs(selectedCorrelation) > 0.7 
                      ? "High correlation indicates these strategies move together strongly. Consider reducing allocation to improve diversification."
                      : Math.abs(selectedCorrelation) < 0.3
                      ? "Low correlation is good for diversification. These strategies provide complementary risk characteristics."
                      : "Moderate correlation provides some diversification benefit while maintaining reasonable coherence."
                  }
                </p>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Correlation Statistics */}
        {correlationStats && (
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Correlation Analysis</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="text-center">
                  <p className="text-sm text-muted-foreground">Average</p>
                  <p className="text-lg font-medium">{correlationStats.avgCorrelation.toFixed(3)}</p>
                </div>
                <div className="text-center">
                  <p className="text-sm text-muted-foreground">Highest</p>
                  <p className="text-lg font-medium text-blue-600">{correlationStats.maxCorrelation.toFixed(3)}</p>
                  <p className="text-xs text-muted-foreground">
                    {correlationStats.maxPair[0]} × {correlationStats.maxPair[1]}
                  </p>
                </div>
                <div className="text-center">
                  <p className="text-sm text-muted-foreground">Lowest</p>
                  <p className="text-lg font-medium text-red-600">{correlationStats.minCorrelation.toFixed(3)}</p>
                  <p className="text-xs text-muted-foreground">
                    {correlationStats.minPair[0]} × {correlationStats.minPair[1]}
                  </p>
                </div>
                <div className="text-center">
                  <p className="text-sm text-muted-foreground">High Correlation</p>
                  <p className="text-lg font-medium">{correlationStats.pairsAbove60}</p>
                  <p className="text-xs text-muted-foreground">
                    of {correlationStats.totalPairs} pairs &gt; 0.6
                  </p>
                </div>
              </div>

              {/* Diversification Insight */}
              <div className="mt-4 p-3 bg-muted/20 rounded">
                <p className="text-sm">
                  <strong>Portfolio Insight:</strong> {
                    correlationStats.pairsAbove60 / correlationStats.totalPairs > 0.3
                      ? "⚠️ High correlation concentration detected. Consider rebalancing to improve diversification."
                      : correlationStats.avgCorrelation < 0.3
                      ? "✅ Well-diversified portfolio with good correlation structure."
                      : "📊 Moderate diversification. Room for improvement in strategy selection."
                  }
                </p>
              </div>
            </CardContent>
          </Card>
        )}
      </CardContent>
    </Card>
  );
}