'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { useResults } from "@/hooks/useResults";
import { useState } from "react";
import { format } from "date-fns";
import Link from "next/link";
import {
  Search,
  FileText,
  Calendar,
  TrendingUp,
  TrendingDown,
  Target,
  BarChart3,
  Download,
  Filter
} from "lucide-react";

export default function ResultsPage() {
  const { results, loading, error, refresh } = useResults();
  const [searchTerm, setSearchTerm] = useState("");
  const [sortBy, setSortBy] = useState<'date' | 'return' | 'sharpe'>('date');

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

  const getReturnColor = (value: number) => {
    return value >= 0 ? 'text-green-600' : 'text-red-600';
  };

  const getPerformanceBadge = (sharpe: number) => {
    if (sharpe >= 2) return { label: 'Excellent', color: 'bg-green-500' };
    if (sharpe >= 1) return { label: 'Good', color: 'bg-blue-500' };
    if (sharpe >= 0.5) return { label: 'Fair', color: 'bg-yellow-500' };
    return { label: 'Poor', color: 'bg-red-500' };
  };

  const filteredResults = results
    .filter(result =>
      result.strategy_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      result.id.toLowerCase().includes(searchTerm.toLowerCase())
    )
    .sort((a, b) => {
      switch (sortBy) {
        case 'return':
          return b.total_return_pct - a.total_return_pct;
        case 'sharpe':
          return b.sharpe_ratio - a.sharpe_ratio;
        default:
          return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      }
    });

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto"></div>
            <p className="mt-2 text-sm text-muted-foreground">Loading results...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto p-6">
        <Card>
          <CardContent className="pt-6">
            <div className="text-center">
              <p className="text-red-600 mb-4">Error: {error}</p>
              <Button onClick={refresh}>Retry</Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Backtest Results</h1>
          <p className="text-muted-foreground">
            View and analyze your backtesting results
          </p>
        </div>
        <Button onClick={refresh}>
          <FileText className="mr-2 h-4 w-4" />
          Refresh
        </Button>
      </div>

      {/* Stats Overview */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Results
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{results.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Best Return
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${getReturnColor(Math.max(...results.map(r => r.total_return_pct)))}`}>
              {results.length > 0 ? formatPercent(Math.max(...results.map(r => r.total_return_pct))) : 'N/A'}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Best Sharpe
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">
              {results.length > 0 ? Math.max(...results.map(r => r.sharpe_ratio)).toFixed(2) : 'N/A'}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Profitable Results
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {results.length > 0 ? Math.round((results.filter(r => r.total_return_pct > 0).length / results.length) * 100) : 0}%
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters and Search */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col space-y-4 md:flex-row md:space-y-0 md:space-x-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search by strategy name or result ID..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <div className="flex space-x-2">
              <Button
                variant={sortBy === 'date' ? 'default' : 'outline'}
                onClick={() => setSortBy('date')}
                size="sm"
              >
                <Calendar className="mr-2 h-4 w-4" />
                Date
              </Button>
              <Button
                variant={sortBy === 'return' ? 'default' : 'outline'}
                onClick={() => setSortBy('return')}
                size="sm"
              >
                <TrendingUp className="mr-2 h-4 w-4" />
                Return
              </Button>
              <Button
                variant={sortBy === 'sharpe' ? 'default' : 'outline'}
                onClick={() => setSortBy('sharpe')}
                size="sm"
              >
                <Target className="mr-2 h-4 w-4" />
                Sharpe
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Results Grid */}
      {filteredResults.length === 0 ? (
        <Card>
          <CardContent className="pt-6">
            <div className="text-center py-8">
              <BarChart3 className="mx-auto h-12 w-12 text-muted-foreground" />
              <h3 className="mt-4 text-lg font-medium">No results found</h3>
              <p className="text-muted-foreground">
                {searchTerm ? 'Try adjusting your search terms' : 'Run some backtests to see results here'}
              </p>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {filteredResults.map((result) => {
            const performanceBadge = getPerformanceBadge(result.sharpe_ratio);

            return (
              <Card key={result.id} className="hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="space-y-1">
                      <CardTitle className="text-lg">{result.strategy_name}</CardTitle>
                      <CardDescription>
                        {format(new Date(result.start_date), 'MMM dd')} - {format(new Date(result.end_date), 'MMM dd, yyyy')}
                      </CardDescription>
                    </div>
                    <Badge
                      className={`${performanceBadge.color} text-white`}
                      variant="secondary"
                    >
                      {performanceBadge.label}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Key Metrics */}
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-muted-foreground">Total Return</p>
                      <p className={`text-lg font-semibold ${getReturnColor(result.total_return_pct)}`}>
                        {formatPercent(result.total_return_pct)}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Sharpe Ratio</p>
                      <p className="text-lg font-semibold">{result.sharpe_ratio.toFixed(2)}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Max Drawdown</p>
                      <p className="text-lg font-semibold text-red-600">
                        -{result.max_drawdown_pct.toFixed(2)}%
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Win Rate</p>
                      <p className="text-lg font-semibold">{result.win_rate.toFixed(1)}%</p>
                    </div>
                  </div>

                  <Separator />

                  {/* Metadata */}
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Total Trades:</span>
                      <span>{result.total_trades}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Created:</span>
                      <span>{format(new Date(result.created_at), 'MMM dd, HH:mm')}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Result ID:</span>
                      <span className="font-mono text-xs">{result.id.substring(0, 8)}...</span>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex space-x-2 pt-2">
                    <Button asChild className="flex-1">
                      <Link href={`/results/${result.id}`}>
                        View Details
                      </Link>
                    </Button>
                    <Button variant="outline" size="sm">
                      <Download className="h-4 w-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
