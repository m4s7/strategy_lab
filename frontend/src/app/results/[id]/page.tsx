'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Separator } from "@/components/ui/separator";
import { Breadcrumb, BreadcrumbItem, BreadcrumbLink, BreadcrumbList, BreadcrumbPage, BreadcrumbSeparator } from "@/components/ui/breadcrumb";
import { useResult } from "@/hooks/useResults";
import { EquityCurveChart } from "@/components/results/equity-curve-chart";
import { PerformanceMetrics } from "@/components/results/performance-metrics";
import { TradeDistributionChart } from "@/components/results/trade-distribution-chart";
import { PerformanceStatisticsTable } from "@/components/results/performance-statistics-table";
import { TradeSummaryPanel } from "@/components/results/trade-summary-panel";
import { ResultsSharing } from "@/components/results/results-sharing";
import { useState } from "react";
import { format } from "date-fns";
import Link from "next/link";
import { 
  ArrowLeft, 
  Download, 
  Share2, 
  Calendar,
  Clock,
  BarChart3,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  LineChart,
  Target,
  Users,
  Home,
  ExternalLink
} from "lucide-react";

interface ResultDetailPageProps {
  params: Promise<{
    id: string;
  }>;
}

export default async function ResultDetailPage({ params }: ResultDetailPageProps) {
  const { id } = await params;
  const { result, loading, error, exportResult } = useResult(id);
  const [exportLoading, setExportLoading] = useState<string | null>(null);

  const handleExport = async (format: 'csv' | 'json' | 'pdf') => {
    try {
      setExportLoading(format);
      await exportResult(format);
    } catch (err) {
      console.error('Export failed:', err);
    } finally {
      setExportLoading(null);
    }
  };

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

  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${seconds}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
    return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
  };

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto"></div>
            <p className="mt-2 text-sm text-muted-foreground">Loading result...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error || !result) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center mb-6">
          <Button variant="ghost" asChild>
            <Link href="/results">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Results
            </Link>
          </Button>
        </div>
        <Card>
          <CardContent className="pt-6">
            <div className="text-center">
              <AlertTriangle className="mx-auto h-12 w-12 text-red-500" />
              <h3 className="mt-4 text-lg font-medium">Result not found</h3>
              <p className="text-muted-foreground mb-4">
                {error || 'The requested result could not be loaded.'}
              </p>
              <Button asChild>
                <Link href="/results">Back to Results</Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  const getRiskRating = (sharpe: number) => {
    if (sharpe >= 2) return { label: 'Excellent', color: 'bg-green-500' };
    if (sharpe >= 1) return { label: 'Good', color: 'bg-blue-500' };
    if (sharpe >= 0.5) return { label: 'Fair', color: 'bg-yellow-500' };
    return { label: 'Poor', color: 'bg-red-500' };
  };

  const riskRating = getRiskRating(result.metrics.sharpe_ratio);
  const isProfit = result.final_capital > result.initial_capital;

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Breadcrumb Navigation */}
      <Breadcrumb>
        <BreadcrumbList>
          <BreadcrumbItem>
            <BreadcrumbLink asChild>
              <Link href="/" className="flex items-center">
                <Home className="mr-2 h-4 w-4" />
                Home
              </Link>
            </BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbSeparator />
          <BreadcrumbItem>
            <BreadcrumbLink asChild>
              <Link href="/results">Results</Link>
            </BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbSeparator />
          <BreadcrumbItem>
            <BreadcrumbPage>{result.strategy_name}</BreadcrumbPage>
          </BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>

      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Button variant="ghost" asChild>
            <Link href="/results">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Results
            </Link>
          </Button>
          <Separator orientation="vertical" className="h-6" />
          <div>
            <h1 className="text-2xl font-bold flex items-center space-x-2">
              <span>{result.strategy_name}</span>
              {isProfit ? (
                <CheckCircle className="h-6 w-6 text-green-600" />
              ) : (
                <AlertTriangle className="h-6 w-6 text-red-600" />
              )}
            </h1>
            <p className="text-muted-foreground">
              {format(new Date(result.start_date), 'MMM dd, yyyy')} - {format(new Date(result.end_date), 'MMM dd, yyyy')}
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <Badge 
            className={`${riskRating.color} text-white`}
            variant="secondary"
          >
            {riskRating.label}
          </Badge>
          <ResultsSharing result={result} />
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Return
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${isProfit ? 'text-green-600' : 'text-red-600'}`}>
              {formatCurrency(result.final_capital - result.initial_capital)}
            </div>
            <div className="text-sm text-muted-foreground">
              {formatPercent(result.metrics.total_return_pct)}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Risk Score
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{result.metrics.sharpe_ratio.toFixed(2)}</div>
            <div className="text-sm text-muted-foreground">Sharpe Ratio</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Max Drawdown
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              -{result.metrics.max_drawdown_pct.toFixed(2)}%
            </div>
            <div className="text-sm text-muted-foreground">
              {formatCurrency(result.metrics.max_drawdown)}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Execution Time
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatDuration(result.execution_time_seconds)}</div>
            <div className="text-sm text-muted-foreground">
              {format(new Date(result.created_at), 'MMM dd, HH:mm')}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Tabs */}
      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
          <TabsTrigger value="statistics">Statistics</TabsTrigger>
          <TabsTrigger value="trades">Trade Analysis</TabsTrigger>
          <TabsTrigger value="navigation">Advanced Tools</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          {/* Equity Curve with enhanced features */}
          <EquityCurveChart
            data={result.equity_curve}
            initialCapital={result.initial_capital}
            title="Interactive Equity Curve"
            showDrawdown={true}
            benchmarkData={undefined} // Could add benchmark data here
          />

          {/* Configuration */}
          <Card>
            <CardHeader>
              <CardTitle>Strategy Configuration</CardTitle>
              <CardDescription>
                Parameters and settings used for this backtest
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <h4 className="font-medium mb-2">Basic Settings</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Initial Capital:</span>
                      <span>{formatCurrency(result.initial_capital)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Final Capital:</span>
                      <span className={isProfit ? 'text-green-600' : 'text-red-600'}>
                        {formatCurrency(result.final_capital)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Execution Time:</span>
                      <span>{formatDuration(result.execution_time_seconds)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Backtest ID:</span>
                      <span className="font-mono text-xs">{result.backtest_id.substring(0, 8)}...</span>
                    </div>
                  </div>
                </div>
                <div>
                  <h4 className="font-medium mb-2">Strategy Parameters</h4>
                  <div className="space-y-2 text-sm">
                    {Object.entries(result.configuration).map(([key, value]) => (
                      <div key={key} className="flex justify-between">
                        <span className="text-muted-foreground">{key}:</span>
                        <span>{String(value)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="performance" className="space-y-6">
          <PerformanceMetrics
            metrics={result.metrics}
            tradeSummary={result.trade_summary}
            initialCapital={result.initial_capital}
          />
        </TabsContent>

        <TabsContent value="statistics" className="space-y-6">
          <PerformanceStatisticsTable
            metrics={result.metrics}
            tradeSummary={result.trade_summary}
            statistics={result.statistics}
            exportable={true}
          />
        </TabsContent>

        <TabsContent value="trades" className="space-y-6">
          <TradeSummaryPanel
            tradeSummary={result.trade_summary}
            onDetailClick={() => {
              // Navigate to trade explorer (UI_022)
              console.log('Navigate to trade explorer');
            }}
          />
          
          <TradeDistributionChart
            tradeSummary={result.trade_summary}
            initialCapital={result.initial_capital}
          />
        </TabsContent>

        <TabsContent value="navigation" className="space-y-6">
          {/* Quick Actions Panel - Links to Advanced Analysis */}
          <Card>
            <CardHeader>
              <CardTitle>Advanced Analysis Tools</CardTitle>
              <CardDescription>
                Explore deeper insights and advanced analysis capabilities
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                <Card className="p-4 hover:shadow-md transition-shadow cursor-pointer">
                  <div className="flex items-center space-x-3">
                    <LineChart className="h-8 w-8 text-blue-600" />
                    <div>
                      <h4 className="font-medium">Interactive Charts</h4>
                      <p className="text-sm text-muted-foreground">Advanced visualization suite</p>
                    </div>
                  </div>
                  <Button variant="outline" className="w-full mt-3" asChild>
                    <Link href="/charts">
                      Open Charts
                      <ExternalLink className="ml-2 h-4 w-4" />
                    </Link>
                  </Button>
                </Card>

                <Card className="p-4 hover:shadow-md transition-shadow cursor-pointer">
                  <div className="flex items-center space-x-3">
                    <BarChart3 className="h-8 w-8 text-green-600" />
                    <div>
                      <h4 className="font-medium">Trade Analysis</h4>
                      <p className="text-sm text-muted-foreground">Trade-by-trade detailed analysis</p>
                    </div>
                  </div>
                  <Button variant="outline" className="w-full mt-3" asChild>
                    <Link href={`/results/${id}/trades`}>
                      Analyze Trades
                      <ExternalLink className="ml-2 h-4 w-4" />
                    </Link>
                  </Button>
                </Card>

                <Card className="p-4 hover:shadow-md transition-shadow cursor-pointer">
                  <div className="flex items-center space-x-3">
                    <Users className="h-8 w-8 text-purple-600" />
                    <div>
                      <h4 className="font-medium">Compare Results</h4>
                      <p className="text-sm text-muted-foreground">Multi-strategy comparison</p>
                    </div>
                  </div>
                  <Button variant="outline" className="w-full mt-3" disabled>
                    Coming Soon
                  </Button>
                </Card>

                <Card className="p-4 hover:shadow-md transition-shadow cursor-pointer">
                  <div className="flex items-center space-x-3">
                    <Target className="h-8 w-8 text-orange-600" />
                    <div>
                      <h4 className="font-medium">Optimization</h4>
                      <p className="text-sm text-muted-foreground">Parameter optimization tools</p>
                    </div>
                  </div>
                  <Button variant="outline" className="w-full mt-3" disabled>
                    Coming Soon
                  </Button>
                </Card>
              </div>
            </CardContent>
          </Card>

          {/* Related Results Recommendations */}
          <Card>
            <CardHeader>
              <CardTitle>Related Results</CardTitle>
              <CardDescription>
                Similar strategies and time periods you might be interested in
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="p-4 border rounded-lg hover:bg-muted/10 transition-colors">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="font-medium">Similar Strategy - Different Period</h4>
                      <p className="text-sm text-muted-foreground">Same parameters, 2023 data</p>
                    </div>
                    <Button variant="ghost" size="sm">View</Button>
                  </div>
                </div>
                <div className="p-4 border rounded-lg hover:bg-muted/10 transition-colors">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="font-medium">Parameter Variation</h4>
                      <p className="text-sm text-muted-foreground">Modified stop loss settings</p>
                    </div>
                    <Button variant="ghost" size="sm">View</Button>
                  </div>
                </div>
                <div className="p-4 border rounded-lg hover:bg-muted/10 transition-colors">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="font-medium">Market Regime Analysis</h4>
                      <p className="text-sm text-muted-foreground">Bull vs Bear market performance</p>
                    </div>
                    <Button variant="ghost" size="sm" disabled>Coming Soon</Button>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}