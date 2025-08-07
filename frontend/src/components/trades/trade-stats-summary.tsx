"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Activity,
  TrendingUp,
  TrendingDown,
  DollarSign,
  Plus,
  Minus,
  Calculator,
  Target,
  Clock,
} from "lucide-react";
import { useMemo } from "react";
import { Trade, TradeStats } from "@/lib/trades/types";
import { calculateTradeStats } from "@/lib/trades/calculations";

interface TradeStatsSummaryProps {
  trades: Trade[];
  className?: string;
}

interface StatCardProps {
  title: string;
  value: string | number;
  icon: React.ComponentType<{ className?: string }>;
  trend?: "up" | "down" | "neutral";
  className?: string;
  description?: string;
}

function StatCard({
  title,
  value,
  icon: Icon,
  trend = "neutral",
  className,
  description,
}: StatCardProps) {
  const trendColors = {
    up: "text-green-600 dark:text-green-400",
    down: "text-red-600 dark:text-red-400",
    neutral: "text-muted-foreground",
  };

  const bgColors = {
    up: "bg-green-50 dark:bg-green-950/20",
    down: "bg-red-50 dark:bg-red-950/20",
    neutral: "bg-muted/20",
  };

  return (
    <Card className={`${bgColors[trend]} ${className}`}>
      <CardContent className="p-4">
        <div className="flex items-center space-x-3">
          <div className={`p-2 rounded-lg ${bgColors[trend]}`}>
            <Icon className={`h-5 w-5 ${trendColors[trend]}`} />
          </div>
          <div className="flex-1">
            <p className="text-sm font-medium text-muted-foreground">{title}</p>
            <p className={`text-2xl font-bold ${trendColors[trend]}`}>
              {value}
            </p>
            {description && (
              <p className="text-xs text-muted-foreground mt-1">
                {description}
              </p>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export function TradeStatsSummary({
  trades,
  className,
}: TradeStatsSummaryProps) {
  const stats = useMemo(() => calculateTradeStats(trades), [trades]);

  if (trades.length === 0) {
    return (
      <Card className={className}>
        <CardContent className="p-6">
          <div className="text-center text-muted-foreground">
            No trades to analyze
          </div>
        </CardContent>
      </Card>
    );
  }

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
    }).format(value);
  };

  const formatDuration = (trades: Trade[]) => {
    if (trades.length === 0) return "0m";
    const avgDuration =
      trades.reduce((sum, t) => sum + t.duration, 0) / trades.length;
    const minutes = Math.round(avgDuration / 60000);
    if (minutes < 60) return `${minutes}m`;
    const hours = Math.round((minutes / 60) * 10) / 10;
    return `${hours}h`;
  };

  return (
    <div className={`space-y-4 ${className}`}>
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Trade Performance Overview</h3>
        <Badge variant="outline">{trades.length} trades analyzed</Badge>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
        <StatCard
          title="Total Trades"
          value={stats.totalTrades}
          icon={Activity}
          description="Executed positions"
        />

        <StatCard
          title="Win Rate"
          value={`${(stats.winRate * 100).toFixed(1)}%`}
          icon={TrendingUp}
          trend={stats.winRate > 0.5 ? "up" : "down"}
          description="Profitable trades"
        />

        <StatCard
          title="Profit Factor"
          value={stats.profitFactor.toFixed(2)}
          icon={Target}
          trend={stats.profitFactor > 1 ? "up" : "down"}
          description="Wins / Losses ratio"
        />

        <StatCard
          title="Avg Winner"
          value={formatCurrency(stats.avgWin)}
          icon={Plus}
          trend="up"
          className="border-green-200"
        />

        <StatCard
          title="Avg Loser"
          value={formatCurrency(stats.avgLoss)}
          icon={Minus}
          trend="down"
          className="border-red-200"
        />

        <StatCard
          title="Expectancy"
          value={formatCurrency(stats.expectancy)}
          icon={Calculator}
          trend={stats.expectancy > 0 ? "up" : "down"}
          description="Expected P&L per trade"
        />
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <Clock className="h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-sm text-muted-foreground">Avg Duration</p>
                <p className="text-lg font-bold">{formatDuration(trades)}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <TrendingUp className="h-4 w-4 text-green-600" />
              <div>
                <p className="text-sm text-muted-foreground">Best Trade</p>
                <p className="text-lg font-bold text-green-600">
                  {formatCurrency(stats.largestWin)}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <TrendingDown className="h-4 w-4 text-red-600" />
              <div>
                <p className="text-sm text-muted-foreground">Worst Trade</p>
                <p className="text-lg font-bold text-red-600">
                  {formatCurrency(stats.largestLoss)}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <Activity className="h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-sm text-muted-foreground">Max Streak</p>
                <div className="flex space-x-2">
                  <span className="text-sm font-medium text-green-600">
                    +{stats.maxConsecutiveWins}
                  </span>
                  <span className="text-sm font-medium text-red-600">
                    -{stats.maxConsecutiveLosses}
                  </span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Performance Insights */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Performance Insights</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {stats.winRate >= 0.6 && (
              <div className="flex items-center space-x-2 text-green-600">
                <TrendingUp className="h-4 w-4" />
                <span className="text-sm">
                  High win rate indicates good signal quality
                </span>
              </div>
            )}

            {stats.profitFactor >= 2 && (
              <div className="flex items-center space-x-2 text-green-600">
                <Target className="h-4 w-4" />
                <span className="text-sm">
                  Excellent risk management with strong profit factor
                </span>
              </div>
            )}

            {stats.avgWin / Math.abs(stats.avgLoss) >= 2 && (
              <div className="flex items-center space-x-2 text-blue-600">
                <DollarSign className="h-4 w-4" />
                <span className="text-sm">
                  Good reward-to-risk ratio on average
                </span>
              </div>
            )}

            {stats.winRate < 0.4 && (
              <div className="flex items-center space-x-2 text-orange-600">
                <TrendingDown className="h-4 w-4" />
                <span className="text-sm">
                  Low win rate - consider improving entry signals
                </span>
              </div>
            )}

            {stats.profitFactor < 1 && (
              <div className="flex items-center space-x-2 text-red-600">
                <Minus className="h-4 w-4" />
                <span className="text-sm">
                  Strategy is losing money - requires optimization
                </span>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
