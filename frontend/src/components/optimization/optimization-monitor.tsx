"use client";

import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Play,
  Pause,
  Square,
  RefreshCw,
  Clock,
  Activity,
  Cpu,
  BarChart3,
  Zap,
} from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { useWebSocket } from "@/hooks/use-websocket";

enum OptimizationStatus {
  QUEUED = "queued",
  INITIALIZING = "initializing",
  RUNNING = "running",
  PAUSED = "paused",
  COMPLETED = "completed",
  FAILED = "failed",
  CANCELLED = "cancelled",
}

interface OptimizationProgress {
  completed: number;
  total: number;
  percentage: number;
  currentCombination: Record<string, any>;
  bestResult: {
    parameters: Record<string, any>;
    sharpeRatio: number;
    totalReturn: number;
  } | null;
  eta: string;
  throughput: number; // combinations per minute
}

interface ResourceUsage {
  cpuPercent: number;
  memoryPercent: number;
  activeWorkers: number;
  maxWorkers: number;
}

interface OptimizationJob {
  id: string;
  strategyId: string;
  status: OptimizationStatus;
  progress: OptimizationProgress;
  resourceUsage: ResourceUsage;
  startTime: string;
  estimatedEndTime?: string;
  errors: string[];
}

interface OptimizationMonitorProps {
  optimizationId: string;
  onComplete?: (results: any) => void;
}

export function OptimizationMonitor({
  optimizationId,
  onComplete,
}: OptimizationMonitorProps) {
  const [optimization, setOptimization] = useState<OptimizationJob | null>(
    null
  );
  const [isLoading, setIsLoading] = useState(true);
  const { subscribe, unsubscribe, sendMessage } = useWebSocket();

  useEffect(() => {
    fetchOptimization();

    // Subscribe to real-time updates
    const handleProgressUpdate = (data: any) => {
      setOptimization((prev) =>
        prev ? { ...prev, progress: data.progress } : null
      );
    };

    const handleStatusUpdate = (data: any) => {
      setOptimization((prev) =>
        prev ? { ...prev, status: data.status } : null
      );
      if (data.status === OptimizationStatus.COMPLETED && onComplete) {
        onComplete(data.results);
      }
    };

    const handleResourceUpdate = (data: any) => {
      setOptimization((prev) =>
        prev ? { ...prev, resourceUsage: data.resourceUsage } : null
      );
    };

    subscribe(`optimization:${optimizationId}:progress`, handleProgressUpdate);
    subscribe(`optimization:${optimizationId}:status`, handleStatusUpdate);
    subscribe(`optimization:${optimizationId}:resources`, handleResourceUpdate);

    return () => {
      unsubscribe(`optimization:${optimizationId}:progress`);
      unsubscribe(`optimization:${optimizationId}:status`);
      unsubscribe(`optimization:${optimizationId}:resources`);
    };
  }, [optimizationId]);

  const fetchOptimization = async () => {
    try {
      const response = await fetch(`/api/optimization/${optimizationId}`);
      if (response.ok) {
        const data = await response.json();
        setOptimization(data);
      }
    } catch (error) {
      console.error("Failed to fetch optimization:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAction = (action: "pause" | "resume" | "cancel") => {
    sendMessage("optimization:control", {
      optimizationId,
      action,
    });
  };

  const getStatusColor = (status: OptimizationStatus) => {
    switch (status) {
      case OptimizationStatus.RUNNING:
        return "default";
      case OptimizationStatus.COMPLETED:
        return "success";
      case OptimizationStatus.FAILED:
        return "destructive";
      case OptimizationStatus.PAUSED:
        return "secondary";
      default:
        return "outline";
    }
  };

  const getStatusIcon = (status: OptimizationStatus) => {
    switch (status) {
      case OptimizationStatus.RUNNING:
        return <Activity className="h-4 w-4 animate-pulse" />;
      case OptimizationStatus.COMPLETED:
        return <RefreshCw className="h-4 w-4" />;
      case OptimizationStatus.PAUSED:
        return <Pause className="h-4 w-4" />;
      default:
        return <Clock className="h-4 w-4" />;
    }
  };

  if (isLoading) {
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

  if (!optimization) {
    return (
      <Card>
        <CardContent className="py-8">
          <div className="text-center text-muted-foreground">
            Optimization not found
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Optimization Monitor</CardTitle>
            <div className="flex items-center gap-2">
              <Badge variant={getStatusColor(optimization.status)}>
                {getStatusIcon(optimization.status)}
                <span className="ml-1 capitalize">{optimization.status}</span>
              </Badge>
              <div className="flex gap-2">
                {optimization.status === OptimizationStatus.RUNNING && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleAction("pause")}
                  >
                    <Pause className="h-4 w-4" />
                  </Button>
                )}
                {optimization.status === OptimizationStatus.PAUSED && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleAction("resume")}
                  >
                    <Play className="h-4 w-4" />
                  </Button>
                )}
                {![
                  OptimizationStatus.COMPLETED,
                  OptimizationStatus.FAILED,
                ].includes(optimization.status) && (
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={() => handleAction("cancel")}
                  >
                    <Square className="h-4 w-4" />
                  </Button>
                )}
              </div>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Progress Section */}
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium">Progress</span>
              <span className="text-sm text-muted-foreground">
                {optimization.progress.completed.toLocaleString()} /{" "}
                {optimization.progress.total.toLocaleString()}
              </span>
            </div>
            <Progress
              value={optimization.progress.percentage}
              className="h-3"
            />
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>
                {optimization.progress.percentage.toFixed(1)}% complete
              </span>
              <span>ETA: {optimization.progress.eta}</span>
            </div>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <Clock className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm font-medium">Runtime</span>
              </div>
              <div className="text-xl font-bold">
                {formatDistanceToNow(new Date(optimization.startTime))}
              </div>
            </div>

            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <Zap className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm font-medium">Throughput</span>
              </div>
              <div className="text-xl font-bold">
                {optimization.progress.throughput.toFixed(1)}/min
              </div>
            </div>

            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <Activity className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm font-medium">Workers</span>
              </div>
              <div className="text-xl font-bold">
                {optimization.resourceUsage.activeWorkers}/
                {optimization.resourceUsage.maxWorkers}
              </div>
            </div>

            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <Cpu className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm font-medium">CPU</span>
              </div>
              <div className="text-xl font-bold">
                {optimization.resourceUsage.cpuPercent.toFixed(0)}%
              </div>
            </div>
          </div>

          {/* Resource Usage */}
          <div className="space-y-3">
            <h4 className="font-medium">Resource Usage</h4>
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span>CPU Usage</span>
                <span>{optimization.resourceUsage.cpuPercent.toFixed(1)}%</span>
              </div>
              <Progress value={optimization.resourceUsage.cpuPercent} />
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span>Memory Usage</span>
                <span>
                  {optimization.resourceUsage.memoryPercent.toFixed(1)}%
                </span>
              </div>
              <Progress value={optimization.resourceUsage.memoryPercent} />
            </div>
          </div>

          {/* Current Combination */}
          {optimization.progress.currentCombination && (
            <div className="space-y-2">
              <h4 className="font-medium">Current Parameters</h4>
              <div className="bg-muted p-3 rounded">
                <div className="grid grid-cols-2 md:grid-cols-3 gap-2 text-sm">
                  {Object.entries(optimization.progress.currentCombination).map(
                    ([key, value]) => (
                      <div key={key} className="flex justify-between">
                        <span className="text-muted-foreground">{key}:</span>
                        <span className="font-mono">{value}</span>
                      </div>
                    )
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Best Result So Far */}
          {optimization.progress.bestResult && (
            <div className="space-y-2">
              <h4 className="font-medium flex items-center gap-2">
                <BarChart3 className="h-4 w-4" />
                Best Result So Far
              </h4>
              <div className="bg-green-50 dark:bg-green-950 p-4 rounded border border-green-200 dark:border-green-800">
                <div className="grid grid-cols-2 gap-4 mb-3">
                  <div className="space-y-1">
                    <span className="text-sm text-muted-foreground">
                      Sharpe Ratio
                    </span>
                    <div className="text-xl font-bold text-green-700 dark:text-green-300">
                      {optimization.progress.bestResult.sharpeRatio.toFixed(3)}
                    </div>
                  </div>
                  <div className="space-y-1">
                    <span className="text-sm text-muted-foreground">
                      Total Return
                    </span>
                    <div className="text-xl font-bold text-green-700 dark:text-green-300">
                      {(
                        optimization.progress.bestResult.totalReturn * 100
                      ).toFixed(1)}
                      %
                    </div>
                  </div>
                </div>
                <div className="text-xs text-muted-foreground">
                  <strong>Parameters:</strong>{" "}
                  {JSON.stringify(
                    optimization.progress.bestResult.parameters,
                    null,
                    0
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Errors */}
          {optimization.errors.length > 0 && (
            <Alert variant="destructive">
              <AlertDescription>
                <div className="space-y-1">
                  {optimization.errors.map((error, index) => (
                    <div key={index} className="text-sm">
                      {error}
                    </div>
                  ))}
                </div>
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
