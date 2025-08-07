"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import {
  TrendingUp,
  TrendingDown,
  Clock,
  Target,
  AlertTriangle,
  Activity,
  BarChart3,
  Download,
  Info,
} from "lucide-react";
import { Trade, TimelineEvent } from "@/lib/trades/types";
import {
  calculateEntryEfficiency,
  calculateExitEfficiency,
  calculateRiskReward,
  calculateTradeDrawdown,
} from "@/lib/trades/calculations";

interface TradeDetailsProps {
  trade: Trade;
  onClose?: () => void;
  className?: string;
}

export function TradeDetails({ trade, onClose, className }: TradeDetailsProps) {
  const [activeTab, setActiveTab] = useState("overview");

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
    }).format(value);
  };

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  };

  const formatDuration = (duration: number) => {
    const totalMinutes = Math.floor(duration / 60000);
    const hours = Math.floor(totalMinutes / 60);
    const minutes = totalMinutes % 60;
    const seconds = Math.floor((duration % 60000) / 1000);

    if (hours > 0) {
      return `${hours}h ${minutes}m ${seconds}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${seconds}s`;
    } else {
      return `${seconds}s`;
    }
  };

  const entryEfficiency = calculateEntryEfficiency(trade);
  const exitEfficiency = calculateExitEfficiency(trade);
  const riskReward = calculateRiskReward(trade);
  const drawdown = calculateTradeDrawdown(trade);

  return (
    <Card className={`h-full ${className}`}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center space-x-2">
              <Activity className="h-5 w-5" />
              <span>Trade Analysis</span>
            </CardTitle>
            <p className="text-sm text-muted-foreground mt-1">
              Trade {trade.id.slice(-8)}
            </p>
          </div>

          <div className="flex items-center space-x-2">
            <Badge
              variant={trade.pnl >= 0 ? "default" : "destructive"}
              className="text-lg px-3 py-1"
            >
              {formatCurrency(trade.pnl)}
            </Badge>
            {onClose && (
              <Button variant="ghost" size="sm" onClick={onClose}>
                ×
              </Button>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent>
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="lifecycle">Lifecycle</TabsTrigger>
            <TabsTrigger value="market">Market</TabsTrigger>
            <TabsTrigger value="analysis">Analysis</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-4">
            <TradeOverview trade={trade} />
          </TabsContent>

          <TabsContent value="lifecycle" className="space-y-4">
            <TradeLifecycle trade={trade} />
          </TabsContent>

          <TabsContent value="market" className="space-y-4">
            <MarketContext trade={trade} />
          </TabsContent>

          <TabsContent value="analysis" className="space-y-4">
            <TradeAnalysis
              trade={trade}
              entryEfficiency={entryEfficiency}
              exitEfficiency={exitEfficiency}
              riskReward={riskReward}
              drawdown={drawdown}
            />
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}

function TradeOverview({ trade }: { trade: Trade }) {
  const formatCurrency = (value: number) => formatCurrency(value);
  const formatPrice = (value: number) => value.toFixed(2);

  return (
    <div className="space-y-6">
      {/* Key Metrics */}
      <div className="grid grid-cols-2 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-sm text-muted-foreground">Side & Size</p>
                <p className="text-lg font-bold">
                  {trade.side.toUpperCase()} {trade.quantity}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <Clock className="h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-sm text-muted-foreground">Duration</p>
                <p className="text-lg font-bold">
                  {Math.round(trade.duration / 60000)}m
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Price Information */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Price Details</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center">
              <p className="text-sm text-muted-foreground">Signal Price</p>
              <p className="text-lg font-mono">
                {formatPrice(trade.signalPrice)}
              </p>
            </div>
            <div className="text-center">
              <p className="text-sm text-muted-foreground">Entry Price</p>
              <p className="text-lg font-mono">
                {formatPrice(trade.entryPrice)}
              </p>
              <p className="text-xs text-muted-foreground">
                Slippage: {trade.entrySlippage.toFixed(2)}
              </p>
            </div>
            <div className="text-center">
              <p className="text-sm text-muted-foreground">Exit Price</p>
              <p className="text-lg font-mono">
                {formatPrice(trade.exitPrice)}
              </p>
              <p className="text-xs text-muted-foreground">
                Slippage: {trade.exitSlippage.toFixed(2)}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Performance Summary */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Performance</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-muted-foreground">Total P&L</p>
              <p
                className={`text-2xl font-bold ${
                  trade.pnl >= 0 ? "text-green-600" : "text-red-600"
                }`}
              >
                {formatCurrency(trade.pnl)}
              </p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Return %</p>
              <p
                className={`text-2xl font-bold ${
                  trade.returnPct >= 0 ? "text-green-600" : "text-red-600"
                }`}
              >
                {(trade.returnPct * 100).toFixed(2)}%
              </p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Max Profit</p>
              <p className="text-lg font-bold text-green-600">
                {formatCurrency(trade.maxProfit)}
              </p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Max Loss</p>
              <p className="text-lg font-bold text-red-600">
                {formatCurrency(trade.maxLoss)}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Trade Reasons */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Trade Rationale</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div>
            <p className="text-sm text-muted-foreground">Signal Type</p>
            <Badge variant="outline">{trade.signalType}</Badge>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Entry Reason</p>
            <p className="text-sm">{trade.entryReason}</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Exit Reason</p>
            <p className="text-sm">{trade.exitReason}</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function TradeLifecycle({ trade }: { trade: Trade }) {
  // Create timeline events
  const events: TimelineEvent[] = [
    {
      type: "signal",
      time: trade.signalTime,
      price: trade.signalPrice,
      description: `${trade.signalType} signal generated`,
    },
    {
      type: "entry",
      time: trade.entryTime,
      price: trade.entryPrice,
      description: `Entered ${trade.side} position`,
      slippage: trade.entrySlippage,
    },
    {
      type: "exit",
      time: trade.exitTime,
      price: trade.exitPrice,
      description: `Exited: ${trade.exitReason}`,
      slippage: trade.exitSlippage,
    },
  ];

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Trade Timeline</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {events.map((event, index) => (
              <div key={index} className="flex items-start space-x-3">
                <div
                  className={`w-3 h-3 rounded-full mt-2 ${
                    event.type === "signal"
                      ? "bg-blue-500"
                      : event.type === "entry"
                      ? "bg-green-500"
                      : "bg-red-500"
                  }`}
                />
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <p className="font-medium">{event.description}</p>
                    <p className="text-sm text-muted-foreground">
                      {new Date(event.time).toLocaleTimeString()}
                    </p>
                  </div>
                  {event.price && (
                    <p className="text-sm text-muted-foreground">
                      Price: {event.price.toFixed(2)}
                      {event.slippage &&
                        ` (Slippage: ${event.slippage.toFixed(2)})`}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Execution Efficiency */}
      <div className="grid grid-cols-2 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">
                  Entry Efficiency
                </span>
                <span className="text-sm font-medium">
                  {(calculateEntryEfficiency(trade) * 100).toFixed(1)}%
                </span>
              </div>
              <Progress value={calculateEntryEfficiency(trade) * 100} />
              <p className="text-xs text-muted-foreground">
                How close entry was to signal price
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">
                  Exit Efficiency
                </span>
                <span className="text-sm font-medium">
                  {(calculateExitEfficiency(trade) * 100).toFixed(1)}%
                </span>
              </div>
              <Progress value={calculateExitEfficiency(trade) * 100} />
              <p className="text-xs text-muted-foreground">
                Capture of favorable move
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function MarketContext({ trade }: { trade: Trade }) {
  const context = trade.marketContext;

  if (!context) {
    return (
      <Card>
        <CardContent className="p-6 text-center text-muted-foreground">
          No market context data available
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <BarChart3 className="h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-sm text-muted-foreground">Volatility</p>
                <p className="text-lg font-bold">
                  {(context.volatility * 100).toFixed(2)}%
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
                <p className="text-sm text-muted-foreground">Volume Rank</p>
                <p className="text-lg font-bold">
                  {(context.volumeRank * 100).toFixed(0)}%
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-sm text-muted-foreground">Trend Strength</p>
                <p className="text-lg font-bold">
                  {context.trendStrength.toFixed(1)}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <Target className="h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-sm text-muted-foreground">Regime</p>
                <p className="text-lg font-bold capitalize">{context.regime}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {context.conditions && context.conditions.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Market Conditions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {context.conditions.map((condition, index) => (
                <Badge key={index} variant="secondary">
                  {condition}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function TradeAnalysis({
  trade,
  entryEfficiency,
  exitEfficiency,
  riskReward,
  drawdown,
}: {
  trade: Trade;
  entryEfficiency: number;
  exitEfficiency: number;
  riskReward: number;
  drawdown: number;
}) {
  return (
    <div className="space-y-6">
      {/* Efficiency Metrics */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Execution Analysis</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm">Entry Efficiency</span>
                <span className="text-sm font-medium">
                  {(entryEfficiency * 100).toFixed(1)}%
                </span>
              </div>
              <Progress value={entryEfficiency * 100} />
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm">Exit Efficiency</span>
                <span className="text-sm font-medium">
                  {(exitEfficiency * 100).toFixed(1)}%
                </span>
              </div>
              <Progress value={exitEfficiency * 100} />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Risk Metrics */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Risk Analysis</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-muted-foreground">Risk/Reward Ratio</p>
              <p className="text-2xl font-bold">{riskReward.toFixed(2)}:1</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Max Drawdown</p>
              <p className="text-2xl font-bold text-red-600">
                {(drawdown * 100).toFixed(2)}%
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Trade Quality Assessment */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center space-x-2">
            <Info className="h-4 w-4" />
            <span>Trade Quality</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {entryEfficiency > 0.8 && (
            <div className="flex items-center space-x-2 text-green-600">
              <TrendingUp className="h-4 w-4" />
              <span className="text-sm">Excellent entry execution</span>
            </div>
          )}

          {exitEfficiency > 0.7 && (
            <div className="flex items-center space-x-2 text-green-600">
              <Target className="h-4 w-4" />
              <span className="text-sm">Good profit capture</span>
            </div>
          )}

          {riskReward > 2 && (
            <div className="flex items-center space-x-2 text-blue-600">
              <BarChart3 className="h-4 w-4" />
              <span className="text-sm">Favorable risk/reward profile</span>
            </div>
          )}

          {drawdown > 0.05 && (
            <div className="flex items-center space-x-2 text-orange-600">
              <AlertTriangle className="h-4 w-4" />
              <span className="text-sm">High drawdown experienced</span>
            </div>
          )}

          {Math.abs(trade.entrySlippage) > 1 && (
            <div className="flex items-center space-x-2 text-orange-600">
              <AlertTriangle className="h-4 w-4" />
              <span className="text-sm">Significant entry slippage</span>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
