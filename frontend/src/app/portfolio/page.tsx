'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { PortfolioSummary } from '@/components/portfolio/portfolio-summary';
import { CorrelationHeatmap } from '@/components/portfolio/correlation-heatmap';
import { RiskContributionChart } from '@/components/portfolio/risk-contribution-chart';
import { PortfolioAnalytics } from '@/lib/portfolio/analytics';
import { StrategyAllocation, PortfolioMetrics, OptimizationConstraints } from '@/lib/portfolio/types';
import { 
  BarChart3, 
  TrendingUp,
  Shield,
  Target,
  RefreshCw,
  Download,
  Settings,
  Play,
  Square
} from 'lucide-react';

// Generate sample strategy data
function generateSampleStrategies(): StrategyAllocation[] {
  const strategies = [
    {
      id: 'trend_following',
      name: 'Trend Following',
      weight: 0.25,
      enabled: true,
      volatility: 0.15,
      annualReturn: 0.12,
      maxDrawdown: -0.08,
      sharpeRatio: 0.8,
      calmarRatio: 1.5,
      color: '#2563eb'
    },
    {
      id: 'mean_reversion',
      name: 'Mean Reversion',
      weight: 0.20,
      enabled: true,
      volatility: 0.12,
      annualReturn: 0.10,
      maxDrawdown: -0.06,
      sharpeRatio: 0.83,
      calmarRatio: 1.67,
      color: '#dc2626'
    },
    {
      id: 'momentum',
      name: 'Momentum',
      weight: 0.30,
      enabled: true,
      volatility: 0.18,
      annualReturn: 0.14,
      maxDrawdown: -0.10,
      sharpeRatio: 0.67,
      calmarRatio: 1.4,
      color: '#059669'
    },
    {
      id: 'scalping',
      name: 'Scalping',
      weight: 0.15,
      enabled: true,
      volatility: 0.08,
      annualReturn: 0.08,
      maxDrawdown: -0.04,
      sharpeRatio: 0.75,
      calmarRatio: 2.0,
      color: '#7c3aed'
    },
    {
      id: 'breakout',
      name: 'Breakout',
      weight: 0.10,
      enabled: true,
      volatility: 0.20,
      annualReturn: 0.16,
      maxDrawdown: -0.12,
      sharpeRatio: 0.7,
      calmarRatio: 1.33,
      color: '#ea580c'
    }
  ];

  // Add synthetic returns data
  return strategies.map(strategy => ({
    ...strategy,
    returns: generateReturns(strategy.annualReturn, strategy.volatility, 252) // Daily returns for 1 year
  }));
}

// Generate synthetic daily returns
function generateReturns(annualReturn: number, volatility: number, days: number): number[] {
  const dailyReturn = annualReturn / days;
  const dailyVol = volatility / Math.sqrt(days);
  
  const returns: number[] = [];
  for (let i = 0; i < days; i++) {
    // Box-Muller transform for normal distribution
    const u = Math.random();
    const v = Math.random();
    const z = Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
    
    const dailyRet = dailyReturn + dailyVol * z;
    returns.push(dailyRet);
  }
  
  return returns;
}

export default function PortfolioPage() {
  const [strategies, setStrategies] = useState<StrategyAllocation[]>([]);
  const [portfolioMetrics, setPortfolioMetrics] = useState<PortfolioMetrics | null>(null);
  const [timeframe, setTimeframe] = useState<'1M' | '3M' | '6M' | '1Y' | '2Y'>('1Y');
  const [optimizationTarget, setOptimizationTarget] = useState<'sharpe' | 'return' | 'risk'>('sharpe');
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  // Initialize with sample data
  useEffect(() => {
    const sampleStrategies = generateSampleStrategies();
    setStrategies(sampleStrategies);
    calculatePortfolioMetrics(sampleStrategies);
  }, []);

  // Auto-refresh
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (autoRefresh) {
      interval = setInterval(() => {
        regenerateData();
      }, 30000); // Refresh every 30 seconds
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [autoRefresh]);

  // Calculate portfolio metrics
  const calculatePortfolioMetrics = (strategiesData: StrategyAllocation[]) => {
    setIsLoading(true);
    try {
      const metrics = PortfolioAnalytics.calculatePortfolioMetrics(strategiesData);
      setPortfolioMetrics(metrics);
    } catch (error) {
      console.error('Error calculating portfolio metrics:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Regenerate sample data
  const regenerateData = () => {
    const newStrategies = generateSampleStrategies();
    setStrategies(newStrategies);
    calculatePortfolioMetrics(newStrategies);
  };

  // Handle strategy weight changes
  const updateStrategyWeight = (strategyId: string, newWeight: number) => {
    const updatedStrategies = strategies.map(strategy =>
      strategy.id === strategyId 
        ? { ...strategy, weight: newWeight / 100 } 
        : strategy
    );
    setStrategies(updatedStrategies);
    calculatePortfolioMetrics(updatedStrategies);
  };

  // Toggle strategy enabled/disabled
  const toggleStrategy = (strategyId: string) => {
    const updatedStrategies = strategies.map(strategy =>
      strategy.id === strategyId 
        ? { ...strategy, enabled: !strategy.enabled } 
        : strategy
    );
    setStrategies(updatedStrategies);
    calculatePortfolioMetrics(updatedStrategies);
  };

  // Run optimization
  const runOptimization = () => {
    const constraints: OptimizationConstraints = {
      minWeight: 0.05,
      maxWeight: 0.50,
      sumToOne: true,
      longOnly: true
    };

    const result = PortfolioAnalytics.optimizePortfolio(strategies, optimizationTarget, constraints);
    
    const optimizedStrategies = strategies.map((strategy, index) => ({
      ...strategy,
      weight: result.weights[index]
    }));

    setStrategies(optimizedStrategies);
    calculatePortfolioMetrics(optimizedStrategies);
  };

  // Export portfolio report
  const exportReport = () => {
    // In a real implementation, this would generate and download a report
    console.log('Exporting portfolio report...', portfolioMetrics);
  };

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Portfolio Analysis</h1>
          <p className="text-muted-foreground mt-1">
            Comprehensive portfolio analytics, risk analysis, and optimization
          </p>
        </div>
        
        <div className="flex items-center space-x-2">
          <Badge variant="outline">
            {strategies.filter(s => s.enabled).length} Active Strategies
          </Badge>
          <Badge variant="outline">
            {timeframe} Analysis
          </Badge>
        </div>
      </div>

      {/* Controls */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Settings className="h-5 w-5" />
            <span>Portfolio Controls</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <label className="text-sm text-muted-foreground">Timeframe:</label>
                <Select value={timeframe} onValueChange={(value: any) => setTimeframe(value)}>
                  <SelectTrigger className="w-24">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="1M">1M</SelectItem>
                    <SelectItem value="3M">3M</SelectItem>
                    <SelectItem value="6M">6M</SelectItem>
                    <SelectItem value="1Y">1Y</SelectItem>
                    <SelectItem value="2Y">2Y</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="flex items-center space-x-2">
                <label className="text-sm text-muted-foreground">Optimization:</label>
                <Select value={optimizationTarget} onValueChange={(value: any) => setOptimizationTarget(value)}>
                  <SelectTrigger className="w-32">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="sharpe">Max Sharpe</SelectItem>
                    <SelectItem value="return">Max Return</SelectItem>
                    <SelectItem value="risk">Min Risk</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <Button variant="outline" size="sm" onClick={runOptimization}>
                <Target className="h-4 w-4 mr-2" />
                Optimize
              </Button>
            </div>

            <div className="flex items-center space-x-2">
              <Button 
                variant="outline" 
                size="sm" 
                onClick={regenerateData}
                disabled={isLoading}
              >
                <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
              
              <Button 
                variant={autoRefresh ? "destructive" : "outline"} 
                size="sm" 
                onClick={() => setAutoRefresh(!autoRefresh)}
              >
                {autoRefresh ? (
                  <><Square className="h-4 w-4 mr-2" />Stop Auto-refresh</>
                ) : (
                  <><Play className="h-4 w-4 mr-2" />Auto-refresh</>
                )}
              </Button>

              <Button variant="outline" size="sm" onClick={exportReport}>
                <Download className="h-4 w-4 mr-2" />
                Export
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Portfolio Summary */}
      <PortfolioSummary 
        metrics={portfolioMetrics} 
        onExport={exportReport}
      />

      {/* Analysis Tabs */}
      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="correlations">Correlations</TabsTrigger>
          <TabsTrigger value="risk">Risk Analysis</TabsTrigger>
          <TabsTrigger value="optimization">Optimization</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
            {/* Correlation Heatmap */}
            <CorrelationHeatmap 
              data={portfolioMetrics?.correlations || null}
              onExport={exportReport}
            />

            {/* Risk Contributions */}
            <RiskContributionChart 
              data={portfolioMetrics?.riskContributions || null}
              onExport={exportReport}
            />
          </div>
        </TabsContent>

        <TabsContent value="correlations" className="space-y-6">
          <CorrelationHeatmap 
            data={portfolioMetrics?.correlations || null}
            onExport={exportReport}
            className="w-full"
          />
        </TabsContent>

        <TabsContent value="risk" className="space-y-6">
          <RiskContributionChart 
            data={portfolioMetrics?.riskContributions || null}
            onExport={exportReport}
            className="w-full"
          />
        </TabsContent>

        <TabsContent value="optimization" className="space-y-6">
          {/* Optimization Panel */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Target className="h-5 w-5" />
                <span>Portfolio Optimization</span>
              </CardTitle>
              <CardDescription>
                Optimize portfolio weights based on risk-return objectives
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {/* Current vs Optimal Allocation */}
                <div>
                  <h4 className="font-medium mb-4">Strategy Allocations</h4>
                  <div className="space-y-3">
                    {strategies.map((strategy, index) => (
                      <div key={strategy.id} className="flex items-center justify-between p-4 border rounded-lg">
                        <div className="flex items-center space-x-3">
                          <div 
                            className="w-4 h-4 rounded-full" 
                            style={{ backgroundColor: strategy.color }}
                          />
                          <div>
                            <p className="font-medium">{strategy.name}</p>
                            <p className="text-xs text-muted-foreground">
                              Sharpe: {strategy.sharpeRatio.toFixed(2)} | 
                              Vol: {(strategy.volatility * 100).toFixed(1)}%
                            </p>
                          </div>
                        </div>
                        
                        <div className="flex items-center space-x-4">
                          <div className="text-right">
                            <p className="font-medium">{(strategy.weight * 100).toFixed(1)}%</p>
                            <p className="text-xs text-muted-foreground">Current</p>
                          </div>
                          
                          <Button
                            variant={strategy.enabled ? "default" : "outline"}
                            size="sm"
                            onClick={() => toggleStrategy(strategy.id)}
                          >
                            {strategy.enabled ? 'Enabled' : 'Disabled'}
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Optimization Results */}
                {portfolioMetrics && (
                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                    <Card>
                      <CardContent className="p-4">
                        <div className="text-center">
                          <p className="text-sm text-muted-foreground">Current Sharpe</p>
                          <p className="text-2xl font-bold">{portfolioMetrics.sharpeRatio.toFixed(3)}</p>
                        </div>
                      </CardContent>
                    </Card>
                    
                    <Card>
                      <CardContent className="p-4">
                        <div className="text-center">
                          <p className="text-sm text-muted-foreground">Portfolio Risk</p>
                          <p className="text-2xl font-bold">{portfolioMetrics.volatility.toFixed(2)}%</p>
                        </div>
                      </CardContent>
                    </Card>
                    
                    <Card>
                      <CardContent className="p-4">
                        <div className="text-center">
                          <p className="text-sm text-muted-foreground">Expected Return</p>
                          <p className="text-2xl font-bold">{portfolioMetrics.annualizedReturn.toFixed(2)}%</p>
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                )}

                {/* Optimization Actions */}
                <div className="flex items-center justify-between pt-4 border-t">
                  <div className="text-sm text-muted-foreground">
                    Optimize portfolio weights to maximize {optimizationTarget === 'sharpe' ? 'Sharpe ratio' : optimizationTarget === 'return' ? 'returns' : 'minimize risk'}
                  </div>
                  
                  <Button onClick={runOptimization}>
                    <Target className="h-4 w-4 mr-2" />
                    Run Optimization
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Feature Information */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <BarChart3 className="h-5 w-5" />
            <span>Portfolio Analysis Features</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div className="space-y-2">
              <h4 className="font-medium flex items-center">
                <TrendingUp className="h-4 w-4 mr-2" />
                Performance Metrics
              </h4>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>• Total return and annualized performance</li>
                <li>• Risk-adjusted returns (Sharpe, Calmar, Sortino)</li>
                <li>• Maximum drawdown analysis</li>
                <li>• Value at Risk (VaR) and Conditional VaR</li>
                <li>• Rolling performance windows</li>
              </ul>
            </div>
            
            <div className="space-y-2">
              <h4 className="font-medium flex items-center">
                <Shield className="h-4 w-4 mr-2" />
                Risk Analysis
              </h4>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>• Strategy correlation matrix</li>
                <li>• Risk contribution decomposition</li>
                <li>• Marginal risk analysis</li>
                <li>• Diversification benefits</li>
                <li>• Concentration risk monitoring</li>
              </ul>
            </div>
            
            <div className="space-y-2">
              <h4 className="font-medium flex items-center">
                <Target className="h-4 w-4 mr-2" />
                Optimization
              </h4>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>• Mean-variance optimization</li>
                <li>• Multiple objective functions</li>
                <li>• Weight constraints and bounds</li>
                <li>• Scenario analysis and what-if modeling</li>
                <li>• Efficient frontier generation</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}