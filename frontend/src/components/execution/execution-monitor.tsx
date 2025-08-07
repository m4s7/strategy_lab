"use client";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { BacktestExecution } from "@/hooks/useBacktestExecution";
import {
  Play,
  Pause,
  Square,
  Trash2,
  Clock,
  Cpu,
  MemoryStick,
  TrendingUp,
  AlertTriangle,
} from "lucide-react";
import { formatDistanceToNow } from "date-fns";

interface ExecutionMonitorProps {
  execution: BacktestExecution;
  onControl: (action: string) => void;
  onDelete: () => void;
}

export function ExecutionMonitor({
  execution,
  onControl,
  onDelete,
}: ExecutionMonitorProps) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "bg-green-500";
      case "failed":
      case "cancelled":
        return "bg-red-500";
      case "processing":
      case "loading_data":
      case "calculating_metrics":
        return "bg-blue-500";
      case "paused":
        return "bg-yellow-500";
      case "queued":
      case "initializing":
        return "bg-gray-500";
      default:
        return "bg-gray-500";
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "completed":
        return "default";
      case "failed":
      case "cancelled":
        return "destructive";
      case "processing":
      case "loading_data":
      case "calculating_metrics":
        return "secondary";
      case "paused":
        return "outline";
      default:
        return "outline";
    }
  };

  const formatDuration = (startTime: string, endTime?: string) => {
    const start = new Date(startTime);
    const end = endTime ? new Date(endTime) : new Date();
    return formatDistanceToNow(start, { addSuffix: false });
  };

  const formatNumber = (num: number) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(0)}K`;
    return num.toString();
  };

  const canPause = [
    "processing",
    "loading_data",
    "calculating_metrics",
  ].includes(execution.status);
  const canResume = execution.status === "paused";
  const canCancel = !["completed", "failed", "cancelled"].includes(
    execution.status
  );
  const canDelete = ["completed", "failed", "cancelled"].includes(
    execution.status
  );

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div
              className={`w-3 h-3 rounded-full ${getStatusColor(
                execution.status
              )}`}
            />
            <div>
              <CardTitle className="text-lg">
                {execution.configuration.strategy_id || "Unnamed Strategy"}
              </CardTitle>
              <CardDescription>
                Execution ID: {execution.id.slice(0, 8)}...
              </CardDescription>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <Badge variant={getStatusBadge(execution.status)}>
              {execution.status.replace("_", " ")}
            </Badge>
            <div className="flex space-x-1">
              {canPause && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onControl("pause")}
                >
                  <Pause className="h-4 w-4" />
                </Button>
              )}
              {canResume && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onControl("resume")}
                >
                  <Play className="h-4 w-4" />
                </Button>
              )}
              {canCancel && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onControl("cancel")}
                >
                  <Square className="h-4 w-4" />
                </Button>
              )}
              {canDelete && (
                <Button variant="outline" size="sm" onClick={onDelete}>
                  <Trash2 className="h-4 w-4" />
                </Button>
              )}
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Progress Section */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">
              {execution.progress.stage || execution.current_stage}
            </span>
            <span className="font-medium">
              {execution.progress.percentage.toFixed(1)}%
            </span>
          </div>
          <Progress value={execution.progress.percentage} className="h-2" />

          {execution.progress.current_tick > 0 && (
            <div className="text-xs text-muted-foreground">
              Processed {formatNumber(execution.progress.current_tick)} of{" "}
              {formatNumber(execution.progress.total_ticks)} ticks
              {execution.progress.current_date && (
                <span> • Current date: {execution.progress.current_date}</span>
              )}
            </div>
          )}
        </div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <div className="text-center p-2 bg-muted/50 rounded">
            <div className="text-lg font-medium">
              {execution.metrics.total_trades}
            </div>
            <div className="text-xs text-muted-foreground">Total Trades</div>
          </div>

          <div className="text-center p-2 bg-muted/50 rounded">
            <div className="text-lg font-medium">
              {execution.metrics.win_rate.toFixed(1)}%
            </div>
            <div className="text-xs text-muted-foreground">Win Rate</div>
          </div>

          <div className="text-center p-2 bg-muted/50 rounded">
            <div
              className={`text-lg font-medium ${
                execution.metrics.total_pnl >= 0
                  ? "text-green-600"
                  : "text-red-600"
              }`}
            >
              ${execution.metrics.total_pnl.toFixed(0)}
            </div>
            <div className="text-xs text-muted-foreground">Total P&L</div>
          </div>

          <div className="text-center p-2 bg-muted/50 rounded">
            <div className="text-lg font-medium text-red-600">
              -{execution.metrics.max_drawdown.toFixed(1)}%
            </div>
            <div className="text-xs text-muted-foreground">Max Drawdown</div>
          </div>
        </div>

        {/* Resource Usage */}
        <div className="grid grid-cols-3 gap-3 text-sm">
          <div className="flex items-center space-x-2">
            <Cpu className="h-4 w-4 text-muted-foreground" />
            <span>CPU: {execution.resource_usage.cpu_percent.toFixed(1)}%</span>
          </div>

          <div className="flex items-center space-x-2">
            <MemoryStick className="h-4 w-4 text-muted-foreground" />
            <span>RAM: {execution.resource_usage.memory_mb.toFixed(0)}MB</span>
          </div>

          <div className="flex items-center space-x-2">
            <Clock className="h-4 w-4 text-muted-foreground" />
            <span>
              Runtime:{" "}
              {formatDuration(execution.start_time, execution.end_time)}
            </span>
          </div>
        </div>

        {/* Errors */}
        {execution.errors.length > 0 && (
          <div className="p-3 bg-red-50 dark:bg-red-950 rounded-lg">
            <div className="flex items-center space-x-2 text-sm font-medium text-red-800 dark:text-red-200 mb-2">
              <AlertTriangle className="h-4 w-4" />
              <span>Errors ({execution.errors.length})</span>
            </div>
            <div className="space-y-1">
              {execution.errors.slice(0, 2).map((error, i) => (
                <div key={i} className="text-xs text-red-700 dark:text-red-300">
                  {error.message}
                </div>
              ))}
              {execution.errors.length > 2 && (
                <div className="text-xs text-red-600 dark:text-red-400">
                  +{execution.errors.length - 2} more errors...
                </div>
              )}
            </div>
          </div>
        )}

        {/* Estimated Completion */}
        {execution.estimated_end_time && execution.status === "processing" && (
          <div className="text-sm text-muted-foreground">
            <Clock className="inline h-4 w-4 mr-1" />
            Estimated completion:{" "}
            {formatDistanceToNow(new Date(execution.estimated_end_time), {
              addSuffix: true,
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
