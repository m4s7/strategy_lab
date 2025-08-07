'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { 
  TrendingUp, 
  TrendingDown,
  Shield,
  Target,
  BarChart3,
  Download,
  AlertTriangle
} from 'lucide-react';
import { PortfolioMetrics } from '@/lib/portfolio/types';
import { Progress } from "@/components/ui/progress";

interface PortfolioSummaryProps {
  metrics: PortfolioMetrics | null;
  onExport?: () => void;
  className?: string;
}

export function PortfolioSummary({ metrics, onExport, className }: PortfolioSummaryProps) {
  if (!metrics) {
    return (
      <Card className={className}>
        <CardContent className="p-6">
          <div className="text-center text-muted-foreground">Loading portfolio metrics...</div>
        </CardContent>
      </Card>
    );
  }

  const formatPercent = (value: number, decimals: number = 2) => {
    const sign = value >= 0 ? '+' : '';
    return `${sign}${value.toFixed(decimals)}%`;
  };

  const formatNumber = (value: number, decimals: number = 2) => {
    return value.toFixed(decimals);
  };

  const getRiskLevel = (sharpe: number) => {
    if (sharpe > 1.5) return { level: 'Excellent', color: 'text-green-600', bg: 'bg-green-100' };
    if (sharpe > 1.0) return { level: 'Good', color: 'text-blue-600', bg: 'bg-blue-100' };
    if (sharpe > 0.5) return { level: 'Fair', color: 'text-yellow-600', bg: 'bg-yellow-100' };
    return { level: 'Poor', color: 'text-red-600', bg: 'bg-red-100' };
  };

  const getDiversificationLevel = (ratio: number) => {
    if (ratio > 1.5) return { level: 'High', color: 'text-green-600', progress: 80 };
    if (ratio > 1.2) return { level: 'Medium', color: 'text-yellow-600', progress: 60 };
    return { level: 'Low', color: 'text-red-600', progress: 40 };
  };

  const riskLevel = getRiskLevel(metrics.sharpeRatio);
  const diversificationLevel = getDiversificationLevel(metrics.diversificationRatio);

  return (
    <div className={className}>
      {/* Header */}
      <Card className="mb-6">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center space-x-2">
                <BarChart3 className="h-6 w-6" />
                <span>Portfolio Overview</span>
              </CardTitle>
              <CardDescription>
                Comprehensive portfolio performance and risk analysis
              </CardDescription>
            </div>
            <div className="flex items-center space-x-2">
              <Badge variant="outline">
                {metrics.strategies.filter(s => s.enabled).length} Active Strategies
              </Badge>
              {onExport && (
                <Button variant="outline" size="sm" onClick={onExport}>
                  <Download className="h-4 w-4" />
                </Button>
              )}
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {/* Total Return */}
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total Return</p>
                <p className={`text-2xl font-bold ${metrics.totalReturn >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {formatPercent(metrics.totalReturn)}
                </p>
              </div>
              <div className={`p-2 rounded-full ${metrics.totalReturn >= 0 ? 'bg-green-100' : 'bg-red-100'}`}>
                {metrics.totalReturn >= 0 ? (
                  <TrendingUp className="h-6 w-6 text-green-600" />
                ) : (
                  <TrendingDown className="h-6 w-6 text-red-600" />
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Sharpe Ratio */}
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Sharpe Ratio</p>
                <p className="text-2xl font-bold">{formatNumber(metrics.sharpeRatio)}</p>
                <Badge variant="outline" className={`text-xs ${riskLevel.color}`}>
                  {riskLevel.level}
                </Badge>
              </div>
              <div className="p-2 rounded-full bg-blue-100">
                <Target className="h-6 w-6 text-blue-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Volatility */}
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Volatility</p>
                <p className="text-2xl font-bold">{formatPercent(metrics.volatility)}</p>
                <p className="text-xs text-muted-foreground">Annualized</p>
              </div>
              <div className="p-2 rounded-full bg-purple-100">
                <AlertTriangle className="h-6 w-6 text-purple-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Max Drawdown */}
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Max Drawdown</p>
                <p className="text-2xl font-bold text-red-600">
                  {formatPercent(Math.abs(metrics.maxDrawdown))}
                </p>
                <p className="text-xs text-muted-foreground">Worst case</p>
              </div>
              <div className="p-2 rounded-full bg-red-100">
                <Shield className="h-6 w-6 text-red-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Advanced Metrics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Risk-Adjusted Returns */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Risk-Adjusted Performance</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-sm text-muted-foreground">Calmar Ratio</span>
                <span className="font-medium">{formatNumber(metrics.calmarRatio)}</span>
              </div>
              
              <div className="flex justify-between items-center">
                <span className="text-sm text-muted-foreground">Sortino Ratio</span>
                <span className="font-medium">{formatNumber(metrics.sortinoRatio)}</span>
              </div>
              
              <div className="flex justify-between items-center">
                <span className="text-sm text-muted-foreground">Information Ratio</span>
                <span className="font-medium">{formatNumber(metrics.informationRatio)}</span>
              </div>

              <div className="pt-2 border-t">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">Annualized Return</span>
                  <span className={`font-medium ${metrics.annualizedReturn >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {formatPercent(metrics.annualizedReturn)}
                  </span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Risk Metrics */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Risk Analysis</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-sm text-muted-foreground">Value at Risk (95%)</span>
                <span className="font-medium text-red-600">{formatPercent(Math.abs(metrics.valueAtRisk))}</span>
              </div>
              
              <div className="flex justify-between items-center">
                <span className="text-sm text-muted-foreground">Conditional VaR</span>
                <span className="font-medium text-red-600">{formatPercent(Math.abs(metrics.conditionalVaR))}</span>
              </div>
              
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">Diversification</span>
                  <span className={`font-medium ${diversificationLevel.color}`}>
                    {diversificationLevel.level}
                  </span>
                </div>
                <Progress value={diversificationLevel.progress} className="h-2" />
                <p className="text-xs text-muted-foreground">
                  Ratio: {formatNumber(metrics.diversificationRatio)} 
                  (Higher is better diversified)
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Strategy Allocation Summary */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Strategy Allocation</CardTitle>
          <CardDescription>
            Current portfolio weights and individual strategy performance
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {metrics.strategies.map((strategy, index) => (
              <div key={strategy.id} className="flex items-center justify-between p-3 bg-muted/20 rounded-lg">
                <div className="flex items-center space-x-3">
                  <div 
                    className="w-4 h-4 rounded-full" 
                    style={{ 
                      backgroundColor: strategy.color || `hsl(${index * 360 / metrics.strategies.length}, 70%, 50%)` 
                    }}
                  />
                  <div>
                    <p className="font-medium">{strategy.name}</p>
                    <p className="text-xs text-muted-foreground">
                      Sharpe: {formatNumber(strategy.sharpeRatio)}
                    </p>
                  </div>
                </div>
                
                <div className="text-right">
                  <p className="font-medium">{formatPercent(strategy.weight * 100, 1)}</p>
                  <p className={`text-xs ${strategy.annualReturn >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {formatPercent(strategy.annualReturn)}
                  </p>
                </div>
              </div>
            ))}
          </div>

          {/* Quick stats */}
          <div className="grid grid-cols-3 gap-4 mt-6 pt-4 border-t">
            <div className="text-center">
              <p className="text-sm text-muted-foreground">Strategies</p>
              <p className="text-lg font-medium">{metrics.strategies.length}</p>
            </div>
            <div className="text-center">
              <p className="text-sm text-muted-foreground">Avg. Weight</p>
              <p className="text-lg font-medium">
                {formatPercent((100 / metrics.strategies.length), 0)}
              </p>
            </div>
            <div className="text-center">
              <p className="text-sm text-muted-foreground">Best Performer</p>
              <p className="text-lg font-medium">
                {metrics.strategies.reduce((best, current) => 
                  current.annualReturn > best.annualReturn ? current : best
                ).name.substring(0, 8)}...
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}