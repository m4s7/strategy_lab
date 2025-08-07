"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { AlertTriangle, Shield, TrendingUp, Activity } from "lucide-react";
import { RiskMetrics } from "@/lib/risk/types";
import { generateMockRiskMetrics } from "@/lib/risk/mock-data";
import { RiskSummaryCards } from "./risk-summary-cards";
import { RiskOverview } from "./risk-overview";
import { ValueAtRiskAnalysis } from "./value-at-risk-analysis";
import { DrawdownAnalysis } from "./drawdown-analysis";
import { StressTesting } from "./stress-testing";
import { RiskRecommendations } from "./risk-recommendations";

interface RiskDashboardProps {
  backtestId: string;
  className?: string;
}

export function RiskDashboard({ backtestId, className }: RiskDashboardProps) {
  const [metrics, setMetrics] = useState<RiskMetrics>();
  const [timeframe, setTimeframe] = useState<"1M" | "3M" | "6M" | "1Y">("1Y");
  const [riskView, setRiskView] = useState<"overview" | "var" | "drawdown" | "stress">("overview");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // TODO: Replace with actual API call
    const loadRiskMetrics = async () => {
      setLoading(true);
      try {
        // Simulate API delay
        await new Promise(resolve => setTimeout(resolve, 1000));
        const mockMetrics = generateMockRiskMetrics();
        setMetrics(mockMetrics);
      } catch (error) {
        console.error("Failed to load risk metrics:", error);
      } finally {
        setLoading(false);
      }
    };

    loadRiskMetrics();
  }, [backtestId, timeframe]);

  const getRiskLevel = (metrics?: RiskMetrics): "low" | "medium" | "high" => {
    if (!metrics) return "medium";
    
    // Simple risk scoring based on key metrics
    let riskScore = 0;
    
    if (metrics.maxDrawdown > 0.20) riskScore += 3; // High drawdown
    else if (metrics.maxDrawdown > 0.10) riskScore += 2; // Medium drawdown
    else riskScore += 1; // Low drawdown
    
    if (metrics.var99 < -0.05) riskScore += 3; // High VaR
    else if (metrics.var99 < -0.03) riskScore += 2; // Medium VaR
    else riskScore += 1; // Low VaR
    
    if (metrics.calmarRatio < 0.5) riskScore += 3; // Poor risk-adjusted return
    else if (metrics.calmarRatio < 1.0) riskScore += 2; // Medium risk-adjusted return
    else riskScore += 1; // Good risk-adjusted return
    
    if (riskScore >= 7) return "high";
    if (riskScore >= 5) return "medium";
    return "low";
  };

  const riskLevel = getRiskLevel(metrics);
  const riskLevelConfig = {
    low: { color: "text-green-600", bgColor: "bg-green-100", icon: Shield },
    medium: { color: "text-yellow-600", bgColor: "bg-yellow-100", icon: Activity },
    high: { color: "text-red-600", bgColor: "bg-red-100", icon: AlertTriangle }
  };

  const RiskIcon = riskLevelConfig[riskLevel].icon;

  if (loading) {
    return (
      <div className={`space-y-6 ${className || ""}`}>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <Card key={i}>
              <CardContent className="p-6">
                <div className="animate-pulse">
                  <div className="h-4 bg-muted rounded w-3/4 mb-2"></div>
                  <div className="h-8 bg-muted rounded w-1/2"></div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
        <Card>
          <CardContent className="p-6">
            <div className="animate-pulse">
              <div className="h-64 bg-muted rounded"></div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className || ""}`}>
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <RiskIcon className={`h-6 w-6 ${riskLevelConfig[riskLevel].color}`} />
              <div>
                <CardTitle>Risk Analysis Dashboard</CardTitle>
                <div className="flex items-center space-x-2 mt-1">
                  <Badge 
                    variant="outline" 
                    className={`${riskLevelConfig[riskLevel].color} ${riskLevelConfig[riskLevel].bgColor}`}
                  >
                    {riskLevel.toUpperCase()} RISK
                  </Badge>
                  <span className="text-sm text-muted-foreground">
                    Backtest: {backtestId}
                  </span>
                </div>
              </div>
            </div>

            <div className="flex items-center space-x-4">
              <Select value={timeframe} onValueChange={(value: any) => setTimeframe(value)}>
                <SelectTrigger className="w-24">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1M">1M</SelectItem>
                  <SelectItem value="3M">3M</SelectItem>
                  <SelectItem value="6M">6M</SelectItem>
                  <SelectItem value="1Y">1Y</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Risk Summary Cards */}
      <RiskSummaryCards metrics={metrics} />

      {/* Main Risk Analysis Tabs */}
      <Tabs value={riskView} onValueChange={(value: any) => setRiskView(value)}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview" className="flex items-center space-x-2">
            <TrendingUp className="h-4 w-4" />
            <span>Overview</span>
          </TabsTrigger>
          <TabsTrigger value="var" className="flex items-center space-x-2">
            <Activity className="h-4 w-4" />
            <span>VaR/CVaR</span>
          </TabsTrigger>
          <TabsTrigger value="drawdown" className="flex items-center space-x-2">
            <AlertTriangle className="h-4 w-4" />
            <span>Drawdowns</span>
          </TabsTrigger>
          <TabsTrigger value="stress" className="flex items-center space-x-2">
            <Shield className="h-4 w-4" />
            <span>Stress Testing</span>
          </TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6 mt-6">
          <RiskOverview metrics={metrics} timeframe={timeframe} />
        </TabsContent>

        <TabsContent value="var" className="space-y-6 mt-6">
          <ValueAtRiskAnalysis backtestId={backtestId} />
        </TabsContent>

        <TabsContent value="drawdown" className="space-y-6 mt-6">
          <DrawdownAnalysis backtestId={backtestId} />
        </TabsContent>

        <TabsContent value="stress" className="space-y-6 mt-6">
          <StressTesting backtestId={backtestId} />
        </TabsContent>
      </Tabs>

      {/* Risk Recommendations */}
      <RiskRecommendations metrics={metrics} />
    </div>
  );
}