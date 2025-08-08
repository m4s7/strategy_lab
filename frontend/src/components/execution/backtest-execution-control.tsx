"use client";

import React, { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Play,
  Pause,
  Square,
  RefreshCw,
  AlertCircle,
  Clock,
  Activity,
  Cpu,
} from "lucide-react";
import { useWebSocket } from "@/hooks/use-websocket";
import { formatDistanceToNow } from "date-fns";

export enum ExecutionStatus {
  QUEUED = "queued",
  INITIALIZING = "initializing",
  LOADING_DATA = "loading_data",
  PROCESSING = "processing",
  CALCULATING_METRICS = "calculating_metrics",
  COMPLETED = "completed",
  FAILED = "failed",
  CANCELLED = "cancelled",
  PAUSED = "paused",
}

interface ExecutionProgress {
  percentage: number;
  currentTick: number;
  totalTicks: number;
  processedTrades: number;
  currentDate: string;
  stage: string;
  eta: string;
}

interface ResourceUsage {
  cpu: number;
  memory: number;
  disk: number;
}

interface BacktestExecution {
  id: string;
  configurationId: string;
  status: ExecutionStatus;
  progress: ExecutionProgress;
  startTime: string;
  estimatedEndTime?: string;
  currentStage: string;
  metrics: any;
  resourceUsage: ResourceUsage;
  errors: any[];
}

interface BacktestExecutionControlProps {
  executionId?: string;
  configurationId: string;
  onComplete?: (results: any) => void;
}

export function BacktestExecutionControl({
  executionId: initialExecutionId,
  configurationId,
  onComplete,
}: BacktestExecutionControlProps) {
  const [executionId, setExecutionId] = useState<string | undefined>(
    initialExecutionId
  );
  const [execution, setExecution] = useState<BacktestExecution | null>(null);
  const [isStarting, setIsStarting] = useState(false);
  const { subscribe, unsubscribe, sendMessage } = useWebSocket();

  useEffect(() => {
    if (!executionId) return;

    const handleProgressUpdate = (data: any) => {
      setExecution((prev) => ({
        ...prev!,
        progress: data.progress,
        metrics: { ...prev?.metrics, ...data.metrics },
      }));
    };

    const handleStatusUpdate = (data: any) => {
      setExecution((prev) => ({
        ...prev!,
        status: data.status,
        currentStage: data.stage,
      }));

      if (data.status === ExecutionStatus.COMPLETED && onComplete) {
        onComplete(data.results);
      }
    };

    const handleResourceUpdate = (data: any) => {
      setExecution((prev) => ({
        ...prev!,
        resourceUsage: data.resourceUsage,
      }));
    };

    subscribe(`backtest:${executionId}:progress`, handleProgressUpdate);
    subscribe(`backtest:${executionId}:status`, handleStatusUpdate);
    subscribe(`backtest:${executionId}:resources`, handleResourceUpdate);

    return () => {
      unsubscribe(`backtest:${executionId}:progress`);
      unsubscribe(`backtest:${executionId}:status`);
      unsubscribe(`backtest:${executionId}:resources`);
    };
  }, [executionId, subscribe, unsubscribe, onComplete]);

  const startBacktest = async () => {
    setIsStarting(true);
    try {
      const response = await fetch("/api/backtests/execute", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ configurationId }),
      });

      if (!response.ok) throw new Error("Failed to start backtest");

      const data = await response.json();
      setExecutionId(data.id);
      setExecution(data);
    } catch (error) {
      console.error("Failed to start backtest:", error);
    } finally {
      setIsStarting(false);
    }
  };

  const pauseBacktest = async () => {
    if (!executionId) return;

    sendMessage("backtest:control", {
      executionId,
      action: "pause",
    });
  };

  const resumeBacktest = async () => {
    if (!executionId) return;

    sendMessage("backtest:control", {
      executionId,
      action: "resume",
    });
  };

  const cancelBacktest = async () => {
    if (!executionId) return;

    if (
      confirm(
        "Are you sure you want to cancel this backtest? Progress will be lost."
      )
    ) {
      sendMessage("backtest:control", {
        executionId,
        action: "cancel",
      });
    }
  };

  const getStatusColor = (status: ExecutionStatus) => {
    switch (status) {
      case ExecutionStatus.COMPLETED:
        return "success";
      case ExecutionStatus.FAILED:
        return "destructive";
      case ExecutionStatus.PROCESSING:
      case ExecutionStatus.LOADING_DATA:
        return "default";
      case ExecutionStatus.PAUSED:
        return "secondary";
      default:
        return "outline";
    }
  };

  const getStatusIcon = (status: ExecutionStatus) => {
    switch (status) {
      case ExecutionStatus.PROCESSING:
        return <Activity className="h-4 w-4 animate-pulse" />;
      case ExecutionStatus.COMPLETED:
        return <RefreshCw className="h-4 w-4" />;
      case ExecutionStatus.FAILED:
        return <AlertCircle className="h-4 w-4" />;
      case ExecutionStatus.PAUSED:
        return <Pause className="h-4 w-4" />;
      default:
        return <Clock className="h-4 w-4" />;
    }
  };

  if (!execution && !executionId) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Backtest Execution</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col gap-4">
            <Alert>
              <AlertDescription>
                Review your configuration and click Start to begin the backtest.
              </AlertDescription>
            </Alert>
            <Button
              onClick={startBacktest}
              disabled={isStarting}
              className="w-full"
              size="lg"
            >
              {isStarting ? (
                <>
                  <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                  Starting...
                </>
              ) : (
                <>
                  <Play className="mr-2 h-4 w-4" />
                  Start Backtest
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!execution) {
    return (
      <Card>
        <CardContent className="py-8">
          <div className="flex items-center justify-center">
            <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Backtest Execution</CardTitle>
          <div className="flex items-center gap-2">
            <Badge variant={getStatusColor(execution.status)}>
              {getStatusIcon(execution.status)}
              <span className="ml-1">{execution.status}</span>
            </Badge>
            <div className="flex gap-2">
              {execution.status === ExecutionStatus.PROCESSING && (
                <Button variant="outline" size="sm" onClick={pauseBacktest}>
                  <Pause className="h-4 w-4" />
                </Button>
              )}
              {execution.status === ExecutionStatus.PAUSED && (
                <Button variant="outline" size="sm" onClick={resumeBacktest}>
                  <Play className="h-4 w-4" />
                </Button>
              )}
              {![
                ExecutionStatus.COMPLETED,
                ExecutionStatus.FAILED,
                ExecutionStatus.CANCELLED,
              ].includes(execution.status) && (
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={cancelBacktest}
                >
                  <Square className="h-4 w-4" />
                </Button>
              )}
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="progress">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="progress">Progress</TabsTrigger>
            <TabsTrigger value="metrics">Live Metrics</TabsTrigger>
            <TabsTrigger value="resources">Resources</TabsTrigger>
          </TabsList>

          <TabsContent value="progress" className="space-y-4">
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>{execution.progress?.stage || "Initializing"}</span>
                <span>{execution.progress?.percentage.toFixed(1)}%</span>
              </div>
              <Progress value={execution.progress?.percentage || 0} />
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>
                  {execution.progress?.currentTick.toLocaleString()} /{" "}
                  {execution.progress?.totalTicks.toLocaleString()} ticks
                </span>
                <span>ETA: {execution.progress?.eta || "Calculating..."}</span>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <p className="text-sm font-medium">Started</p>
                <p className="text-xs text-muted-foreground">
                  {formatDistanceToNow(new Date(execution.startTime), {
                    addSuffix: true,
                  })}
                </p>
              </div>
              <div className="space-y-1">
                <p className="text-sm font-medium">Current Date</p>
                <p className="text-xs text-muted-foreground">
                  {execution.progress?.currentDate || "N/A"}
                </p>
              </div>
              <div className="space-y-1">
                <p className="text-sm font-medium">Trades Processed</p>
                <p className="text-xs text-muted-foreground">
                  {execution.progress?.processedTrades.toLocaleString() || 0}
                </p>
              </div>
              <div className="space-y-1">
                <p className="text-sm font-medium">Processing Speed</p>
                <p className="text-xs text-muted-foreground">
                  {execution.progress
                    ? `${Math.round(
                        execution.progress.currentTick /
                          ((Date.now() -
                            new Date(execution.startTime).getTime()) /
                            1000)
                      )} ticks/sec`
                    : "N/A"}
                </p>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="metrics" className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <Card>
                <CardContent className="pt-6">
                  <div className="text-2xl font-bold">
                    {execution.metrics?.totalPnl
                      ? `$${execution.metrics.totalPnl.toLocaleString()}`
                      : "$0"}
                  </div>
                  <p className="text-xs text-muted-foreground">Total P&L</p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-6">
                  <div className="text-2xl font-bold">
                    {execution.metrics?.winRate
                      ? `${execution.metrics.winRate.toFixed(1)}%`
                      : "0%"}
                  </div>
                  <p className="text-xs text-muted-foreground">Win Rate</p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-6">
                  <div className="text-2xl font-bold">
                    {execution.metrics?.sharpeRatio?.toFixed(2) || "0.00"}
                  </div>
                  <p className="text-xs text-muted-foreground">Sharpe Ratio</p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-6">
                  <div className="text-2xl font-bold">
                    {execution.metrics?.maxDrawdown
                      ? `${(execution.metrics.maxDrawdown * 100).toFixed(1)}%`
                      : "0%"}
                  </div>
                  <p className="text-xs text-muted-foreground">Max Drawdown</p>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="resources" className="space-y-4">
            <div className="space-y-4">
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="flex items-center gap-2">
                    <Cpu className="h-4 w-4" />
                    CPU Usage
                  </span>
                  <span>{execution.resourceUsage?.cpu.toFixed(1)}%</span>
                </div>
                <Progress value={execution.resourceUsage?.cpu || 0} />
              </div>

              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Memory Usage</span>
                  <span>{execution.resourceUsage?.memory.toFixed(1)}%</span>
                </div>
                <Progress value={execution.resourceUsage?.memory || 0} />
              </div>

              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Disk I/O</span>
                  <span>{execution.resourceUsage?.disk.toFixed(1)}%</span>
                </div>
                <Progress value={execution.resourceUsage?.disk || 0} />
              </div>
            </div>
          </TabsContent>
        </Tabs>

        {execution.errors && execution.errors.length > 0 && (
          <Alert variant="destructive" className="mt-4">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              {execution.errors[execution.errors.length - 1]}
            </AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  );
}
