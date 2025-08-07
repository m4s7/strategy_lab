"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Clock,
  ExternalLink,
  TrendingUp,
  TrendingDown,
  DollarSign,
  BarChart2,
} from "lucide-react";
import { useRecentBacktests, type Backtest } from "@/hooks/useBacktests";
import { formatDistanceToNow } from "date-fns";
import { useState, useEffect } from "react";
import Link from "next/link";

// Interface for backtest with result metrics
interface BacktestWithMetrics extends Backtest {
  metrics?: {
    total_return_pct?: number;
    sharpe_ratio?: number;
    max_drawdown_pct?: number;
    win_rate?: number;
  };
}

export function RecentActivityPanel() {
  const { backtests, loading, error } = useRecentBacktests();
  const [backtestsWithMetrics, setBacktestsWithMetrics] = useState<
    BacktestWithMetrics[]
  >([]);

  // Fetch metrics for completed backtests
  useEffect(() => {
    const fetchMetrics = async () => {
      const updatedBacktests: BacktestWithMetrics[] = [];

      for (const backtest of backtests) {
        const backtestWithMetrics: BacktestWithMetrics = { ...backtest };

        if (backtest.status === "completed") {
          try {
            const response = await fetch(
              `${process.env.NEXT_PUBLIC_API_URL}/api/v1/results?backtest_id=${backtest.id}`
            );
            if (response.ok) {
              const results = (await response.json()) as Array<{
                total_return_pct: number;
                sharpe_ratio: number;
                max_drawdown_pct: number;
                win_rate: number;
              }>;
              if (results.length > 0) {
                const result = results[0];
                backtestWithMetrics.metrics = {
                  total_return_pct: result.total_return_pct,
                  sharpe_ratio: result.sharpe_ratio,
                  max_drawdown_pct: result.max_drawdown_pct,
                  win_rate: result.win_rate,
                };
              }
            }
          } catch (err) {
            console.error(
              `Failed to fetch metrics for backtest ${backtest.id}`,
              err
            );
          }
        }

        updatedBacktests.push(backtestWithMetrics);
      }

      setBacktestsWithMetrics(updatedBacktests);
    };

    if (backtests.length > 0) {
      fetchMetrics();
    }
  }, [backtests]);

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {Array.from({ length: 5 }, (_, i) => (
              <div key={i} className="animate-pulse">
                <div className="h-16 bg-muted rounded-lg"></div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center text-muted-foreground py-8">
            Failed to load recent activity
          </div>
        </CardContent>
      </Card>
    );
  }

  const getStatusBadgeVariant = (status: Backtest["status"]) => {
    switch (status) {
      case "completed":
        return "default";
      case "running":
        return "secondary";
      case "failed":
        return "destructive";
      case "pending":
        return "outline";
      case "cancelled":
        return "secondary";
      default:
        return "outline";
    }
  };

  const getStatusIcon = (status: Backtest["status"]) => {
    switch (status) {
      case "completed":
        return <TrendingUp className="h-4 w-4 text-green-600" />;
      case "failed":
        return <TrendingDown className="h-4 w-4 text-red-600" />;
      default:
        return <Clock className="h-4 w-4 text-blue-600" />;
    }
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Recent Activity</CardTitle>
        <Link href="/results">
          <Button variant="outline" size="sm">
            <ExternalLink className="h-4 w-4 mr-2" />
            View All
          </Button>
        </Link>
      </CardHeader>
      <CardContent>
        {backtests.length === 0 ? (
          <div className="text-center text-muted-foreground py-8">
            No recent backtests found
          </div>
        ) : (
          <div className="space-y-4">
            {backtestsWithMetrics.map((backtest) => (
              <div
                key={backtest.id}
                className="flex flex-col p-3 bg-muted/50 rounded-lg hover:bg-muted/70 transition-colors"
              >
                {/* Header Row */}
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-3">
                    {getStatusIcon(backtest.status)}
                    <div>
                      <div className="font-medium text-sm">
                        {backtest.strategy_id}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {formatDistanceToNow(new Date(backtest.created_at), {
                          addSuffix: true,
                        })}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Badge variant={getStatusBadgeVariant(backtest.status)}>
                      {backtest.status}
                    </Badge>
                    <Link href={`/results/${backtest.id}`}>
                      <Button variant="ghost" size="sm">
                        <ExternalLink className="h-3 w-3" />
                      </Button>
                    </Link>
                  </div>
                </div>

                {/* Metrics Row - Only show for completed backtests with metrics */}
                {backtest.status === "completed" && backtest.metrics && (
                  <div className="grid grid-cols-4 gap-3 mt-2 pt-2 border-t border-border/50">
                    <div className="text-center">
                      <div className="flex items-center justify-center text-xs text-muted-foreground mb-1">
                        <DollarSign className="h-3 w-3 mr-1" />
                        Return
                      </div>
                      <div
                        className={`text-sm font-medium ${
                          backtest.metrics.total_return_pct &&
                          backtest.metrics.total_return_pct > 0
                            ? "text-green-600"
                            : "text-red-600"
                        }`}
                      >
                        {backtest.metrics.total_return_pct?.toFixed(2)}%
                      </div>
                    </div>
                    <div className="text-center">
                      <div className="flex items-center justify-center text-xs text-muted-foreground mb-1">
                        <BarChart2 className="h-3 w-3 mr-1" />
                        Sharpe
                      </div>
                      <div className="text-sm font-medium">
                        {backtest.metrics.sharpe_ratio?.toFixed(2) || "-"}
                      </div>
                    </div>
                    <div className="text-center">
                      <div className="flex items-center justify-center text-xs text-muted-foreground mb-1">
                        <TrendingDown className="h-3 w-3 mr-1" />
                        Drawdown
                      </div>
                      <div className="text-sm font-medium text-orange-600">
                        {backtest.metrics.max_drawdown_pct?.toFixed(1)}%
                      </div>
                    </div>
                    <div className="text-center">
                      <div className="flex items-center justify-center text-xs text-muted-foreground mb-1">
                        <TrendingUp className="h-3 w-3 mr-1" />
                        Win Rate
                      </div>
                      <div className="text-sm font-medium">
                        {backtest.metrics.win_rate?.toFixed(1)}%
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
