"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  TrendingDown,
  AlertCircle,
  Shield,
  Target,
  Activity,
  Zap,
  BarChart3,
  TrendingUp,
} from "lucide-react";
import { RiskMetrics } from "@/lib/risk/types";

interface RiskSummaryCardsProps {
  metrics?: RiskMetrics;
}

export function RiskSummaryCards({ metrics }: RiskSummaryCardsProps) {
  if (!metrics) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(8)].map((_, i) => (
          <Card key={i}>
            <CardContent className="p-4">
              <div className="animate-pulse">
                <div className="h-4 bg-muted rounded w-3/4 mb-2"></div>
                <div className="h-6 bg-muted rounded w-1/2"></div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  const formatPercentage = (value: number, decimals: number = 2) => {
    return `${(value * 100).toFixed(decimals)}%`;
  };

  const formatRatio = (value: number, decimals: number = 2) => {
    return value.toFixed(decimals);
  };

  const getVaRSeverity = (var95: number): "low" | "medium" | "high" => {
    const absVar = Math.abs(var95);
    if (absVar > 0.05) return "high";
    if (absVar > 0.03) return "medium";
    return "low";
  };

  const getDrawdownSeverity = (maxDrawdown: number): "low" | "medium" | "high" => {
    if (maxDrawdown > 0.20) return "high";
    if (maxDrawdown > 0.10) return "medium";
    return "low";
  };

  const getRatioQuality = (ratio: number, goodThreshold: number): "poor" | "fair" | "good" => {
    if (ratio >= goodThreshold * 1.5) return "good";
    if (ratio >= goodThreshold) return "fair";
    return "poor";
  };

  const varSeverity = getVaRSeverity(metrics.var95);
  const drawdownSeverity = getDrawdownSeverity(metrics.maxDrawdown);
  const calmarQuality = getRatioQuality(metrics.calmarRatio, 1.0);
  const sortinoQuality = getRatioQuality(metrics.sortinoRatio, 1.0);

  const severityColors = {
    low: "text-green-600 bg-green-50",
    medium: "text-yellow-600 bg-yellow-50",
    high: "text-red-600 bg-red-50",
    poor: "text-red-600 bg-red-50",
    fair: "text-yellow-600 bg-yellow-50",
    good: "text-green-600 bg-green-50",
  };

  const cards = [
    {
      title: "Value at Risk (95%)",
      value: formatPercentage(metrics.var95),
      description: "1-day VaR at 95% confidence",
      icon: TrendingDown,
      severity: varSeverity,
      trend: metrics.var95 > -0.02 ? "improving" : "declining",
    },
    {
      title: "Expected Shortfall",
      value: formatPercentage(metrics.cvar95),
      description: "CVaR (95%) - tail risk",
      icon: AlertCircle,
      severity: getVaRSeverity(metrics.cvar95),
      trend: metrics.cvar95 > metrics.var95 * 1.2 ? "declining" : "stable",
    },
    {
      title: "Maximum Drawdown",
      value: formatPercentage(metrics.maxDrawdown),
      description: "Largest peak-to-trough decline",
      icon: TrendingDown,
      severity: drawdownSeverity,
      trend: metrics.maxDrawdown < 0.15 ? "improving" : "concerning",
    },
    {
      title: "Average Drawdown",
      value: formatPercentage(metrics.avgDrawdown),
      description: "Mean of all drawdown periods",
      icon: BarChart3,
      severity: getDrawdownSeverity(metrics.avgDrawdown * 2), // Scale for avg vs max
      trend: metrics.avgDrawdown < metrics.maxDrawdown * 0.3 ? "stable" : "volatile",
    },
    {
      title: "Calmar Ratio",
      value: formatRatio(metrics.calmarRatio),
      description: "Return / Max Drawdown",
      icon: Target,
      severity: calmarQuality,
      trend: metrics.calmarRatio > 1.0 ? "strong" : "weak",
    },
    {
      title: "Sortino Ratio",
      value: formatRatio(metrics.sortinoRatio),
      description: "Return / Downside deviation",
      icon: Shield,
      severity: sortinoQuality,
      trend: metrics.sortinoRatio > metrics.calmarRatio ? "outperforming" : "underperforming",
    },
    {
      title: "Omega Ratio",
      value: formatRatio(metrics.omega),
      description: "Gains over losses ratio",
      icon: Activity,
      severity: getRatioQuality(metrics.omega, 1.0),
      trend: metrics.omega > 1.2 ? "strong" : metrics.omega < 0.8 ? "weak" : "neutral",
    },
    {
      title: "Tail Ratio",
      value: formatRatio(metrics.tailRatio),
      description: "Right vs left tail ratio",
      icon: Zap,
      severity: metrics.tailRatio > 0.5 ? "good" : metrics.tailRatio > 0.3 ? "fair" : "poor",
      trend: metrics.tailRatio > 0.5 ? "positive" : "negative",
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card, index) => {
        const IconComponent = card.icon;
        const trendIcon = 
          card.trend === "improving" || card.trend === "strong" || card.trend === "positive" ? 
          TrendingUp : TrendingDown;
        
        return (
          <Card key={index} className="relative">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {card.title}
              </CardTitle>
              <div className="flex items-center space-x-1">
                <IconComponent className="h-4 w-4 text-muted-foreground" />
                <Badge 
                  variant="outline" 
                  className={`text-xs px-1.5 py-0.5 ${severityColors[card.severity]}`}
                >
                  {card.severity.toUpperCase()}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-1">
                <div className="flex items-center space-x-2">
                  <div className="text-2xl font-bold">
                    {card.value}
                  </div>
                  <div className="flex items-center">
                    <trendIcon className={`h-3 w-3 ${
                      card.trend === "improving" || card.trend === "strong" || card.trend === "positive" ? 
                      "text-green-500" : 
                      card.trend === "declining" || card.trend === "weak" || card.trend === "negative" ?
                      "text-red-500" : "text-muted-foreground"
                    }`} />
                  </div>
                </div>
                <p className="text-xs text-muted-foreground">
                  {card.description}
                </p>
                <p className="text-xs text-muted-foreground capitalize">
                  Trend: {card.trend}
                </p>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}