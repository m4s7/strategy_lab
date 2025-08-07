"use client";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Play,
  Pause,
  Square,
  AlertTriangle,
  Cpu,
  MemoryStick,
  Clock,
  Zap,
  TrendingUp,
  TrendingDown,
  BarChart3,
  CheckCircle,
  XCircle,
} from "lucide-react";
import { useState, useEffect } from "react";
import { useWebSocketSubscription } from "@/lib/websocket/hooks";
import {
  format,
  formatDistanceToNow,
  differenceInMilliseconds,
} from "date-fns";

export interface BacktestMonitorData {
  backtestId: string;
  status: "running" | "paused" | "completed" | "aborted" | "failed" | "queued";
  progress: {
    currentTime: number;
    totalTime: number;
    eventsProcessed: number;
    eventsPerSecond: number;
    percentage: number;
    currentDate?: string;
    eta?: string;
  };
  resources: {
    cpuUsage: number;
    memoryUsage: number;
    memoryMB: number;
  };
  partialResults?: {
    pnl: number;
    trades: number;
    sharpe?: number;
    winRate?: number;
    currentDrawdown?: number;
  };
  startTime: string;
  endTime?: string;
  strategyName: string;
  configuration: Record<string, any>;
  errors: Array<{
    message: string;
    timestamp: string;
    level: "error" | "warning";
  }>;
}

interface BacktestMonitorProps {
  backtestId: string;
  initialData?: BacktestMonitorData;
  onAbort?: (backtestId: string) => void;
  onPause?: (backtestId: string) => void;
  onResume?: (backtestId: string) => void;
  compact?: boolean;
}

export function BacktestMonitor({
  backtestId,
  initialData,
  onAbort,
  onPause,
  onResume,
  compact = false,
}: BacktestMonitorProps) {
  const [showAbortDialog, setShowAbortDialog] = useState(false);
  const [localData, setLocalData] = useState<BacktestMonitorData | undefined>(
    initialData
  );

  // Subscribe to real-time updates
  const { data: realtimeData } = useWebSocketSubscription<BacktestMonitorData>(
    `backtest:${backtestId}:monitor`,
    initialData
  );

  // Use realtime data if available, otherwise use local data
  const data = realtimeData || localData;

  // Persist state to localStorage
  useEffect(() => {
    if (data && data.status === "running") {
      const saved = localStorage.getItem("backtest_monitors");
      const monitors = saved ? JSON.parse(saved) : {};
      monitors[backtestId] = data;
      localStorage.setItem("backtest_monitors", JSON.stringify(monitors));
    }
  }, [backtestId, data]);

  if (!data) {
    return (
      <Card className="animate-pulse">
        <CardHeader>
          <div className="h-6 bg-muted rounded w-2/3"></div>
          <div className="h-4 bg-muted rounded w-1/2"></div>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="h-4 bg-muted rounded"></div>
            <div className="h-8 bg-muted rounded"></div>
            <div className="grid grid-cols-3 gap-3">
              <div className="h-16 bg-muted rounded"></div>
              <div className="h-16 bg-muted rounded"></div>
              <div className="h-16 bg-muted rounded"></div>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  const getStatusIcon = () => {
    switch (data.status) {
      case "running":
        return <Play className="h-4 w-4 text-green-600" />;
      case "paused":
        return <Pause className="h-4 w-4 text-yellow-600" />;
      case "completed":
        return <CheckCircle className="h-4 w-4 text-green-600" />;
      case "aborted":
      case "failed":
        return <XCircle className="h-4 w-4 text-red-600" />;
      case "queued":
        return <Clock className="h-4 w-4 text-blue-600" />;
      default:
        return <Square className="h-4 w-4 text-gray-600" />;
    }
  };

  const getStatusBadge = () => {
    switch (data.status) {
      case "running":
        return <Badge className="bg-green-500 text-white">Running</Badge>;
      case "paused":
        return <Badge className="bg-yellow-500 text-white">Paused</Badge>;
      case "completed":
        return <Badge className="bg-green-500 text-white">Completed</Badge>;
      case "aborted":
        return <Badge className="bg-orange-500 text-white">Aborted</Badge>;
      case "failed":
        return <Badge className="bg-red-500 text-white">Failed</Badge>;
      case "queued":
        return <Badge className="bg-blue-500 text-white">Queued</Badge>;
      default:
        return <Badge variant="secondary">{data.status}</Badge>;
    }
  };

  const formatNumber = (num: number) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toLocaleString();
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const calculateRuntime = () => {
    const start = new Date(data.startTime);
    const end = data.endTime ? new Date(data.endTime) : new Date();
    return formatDistanceToNow(start, { addSuffix: false });
  };

  const getProgressColor = () => {
    if (data.status === "completed") return "bg-green-500";
    if (data.status === "failed" || data.status === "aborted")
      return "bg-red-500";
    if (data.status === "paused") return "bg-yellow-500";
    return "bg-blue-500";
  };

  const canPause = data.status === "running";
  const canResume = data.status === "paused";
  const canAbort =
    data.status === "running" ||
    data.status === "paused" ||
    data.status === "queued";

  if (compact) {
    return (
      <Card className="border-l-4 border-l-blue-500">
        <CardContent className="pt-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-2">
              {getStatusIcon()}
              <span className="font-medium text-sm">{data.strategyName}</span>
            </div>
            {getStatusBadge()}
          </div>
          <div className="space-y-2">
            <div className="flex justify-between text-xs">
              <span>Progress</span>
              <span>{data.progress.percentage.toFixed(1)}%</span>
            </div>
            <Progress value={data.progress.percentage} className="h-2" />
            {data.progress.eta && (
              <div className="text-xs text-muted-foreground">
                ETA: {data.progress.eta}
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            {getStatusIcon()}
            <div>
              <CardTitle className="text-lg">{data.strategyName}</CardTitle>
              <CardDescription>
                ID: {backtestId.slice(0, 8)}... • Started{" "}
                {formatDistanceToNow(new Date(data.startTime), {
                  addSuffix: true,
                })}
              </CardDescription>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            {getStatusBadge()}
            <div className="flex space-x-1">
              {canPause && onPause && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onPause(backtestId)}
                >
                  <Pause className="h-4 w-4" />
                </Button>
              )}
              {canResume && onResume && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onResume(backtestId)}
                >
                  <Play className="h-4 w-4" />
                </Button>
              )}
              {canAbort && onAbort && (
                <Dialog
                  open={showAbortDialog}
                  onOpenChange={setShowAbortDialog}
                >
                  <DialogTrigger asChild>
                    <Button variant="outline" size="sm">
                      <Square className="h-4 w-4" />
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>Abort Backtest</DialogTitle>
                      <DialogDescription>
                        Are you sure you want to abort this backtest? This
                        action cannot be undone, but partial results will be
                        saved.
                      </DialogDescription>
                    </DialogHeader>
                    <div className="py-4">
                      <div className="space-y-2 text-sm">
                        <div>
                          <strong>Strategy:</strong> {data.strategyName}
                        </div>
                        <div>
                          <strong>Progress:</strong>{" "}
                          {data.progress.percentage.toFixed(1)}%
                        </div>
                        <div>
                          <strong>Runtime:</strong> {calculateRuntime()}
                        </div>
                        {data.partialResults && (
                          <div>
                            <strong>Current P&L:</strong>{" "}
                            {formatCurrency(data.partialResults.pnl)}
                          </div>
                        )}
                      </div>
                    </div>
                    <DialogFooter>
                      <Button
                        variant="outline"
                        onClick={() => setShowAbortDialog(false)}
                      >
                        Cancel
                      </Button>
                      <Button
                        variant="destructive"
                        onClick={() => {
                          onAbort(backtestId);
                          setShowAbortDialog(false);
                        }}
                      >
                        Abort Backtest
                      </Button>
                    </DialogFooter>
                  </DialogContent>
                </Dialog>
              )}
            </div>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Progress Section */}
        <div className="space-y-3">
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center space-x-2">
              <span className="text-muted-foreground">Progress</span>
              {data.progress.currentDate && (
                <Badge variant="outline" className="text-xs">
                  {data.progress.currentDate}
                </Badge>
              )}
            </div>
            <span className="font-medium">
              {data.progress.percentage.toFixed(1)}%
            </span>
          </div>

          <Progress value={data.progress.percentage} className="h-3" />

          <div className="grid grid-cols-2 lg:grid-cols-4 gap-2 text-xs text-muted-foreground">
            <div>
              Events: {formatNumber(data.progress.eventsProcessed)} /{" "}
              {formatNumber(data.progress.totalTime)}
            </div>
            <div className="flex items-center space-x-1">
              <Zap className="h-3 w-3" />
              <span>{formatNumber(data.progress.eventsPerSecond)}/sec</span>
            </div>
            <div className="flex items-center space-x-1">
              <Clock className="h-3 w-3" />
              <span>Runtime: {calculateRuntime()}</span>
            </div>
            {data.progress.eta && (
              <div className="flex items-center space-x-1">
                <Clock className="h-3 w-3" />
                <span>ETA: {data.progress.eta}</span>
              </div>
            )}
          </div>
        </div>

        {/* Partial Results */}
        {data.partialResults && (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            <div className="text-center p-3 bg-muted/50 rounded-lg">
              <div
                className={`text-lg font-medium ${
                  data.partialResults.pnl >= 0
                    ? "text-green-600"
                    : "text-red-600"
                }`}
              >
                {formatCurrency(data.partialResults.pnl)}
              </div>
              <div className="text-xs text-muted-foreground">Current P&L</div>
            </div>

            <div className="text-center p-3 bg-muted/50 rounded-lg">
              <div className="text-lg font-medium">
                {data.partialResults.trades}
              </div>
              <div className="text-xs text-muted-foreground">Trades</div>
            </div>

            {data.partialResults.winRate !== undefined && (
              <div className="text-center p-3 bg-muted/50 rounded-lg">
                <div className="text-lg font-medium">
                  {data.partialResults.winRate.toFixed(1)}%
                </div>
                <div className="text-xs text-muted-foreground">Win Rate</div>
              </div>
            )}

            {data.partialResults.currentDrawdown !== undefined && (
              <div className="text-center p-3 bg-muted/50 rounded-lg">
                <div className="text-lg font-medium text-red-600">
                  -{data.partialResults.currentDrawdown.toFixed(1)}%
                </div>
                <div className="text-xs text-muted-foreground">Drawdown</div>
              </div>
            )}
          </div>
        )}

        {/* Resource Usage */}
        <div className="grid grid-cols-3 gap-4 p-3 bg-muted/30 rounded-lg">
          <div className="flex items-center space-x-2 text-sm">
            <Cpu className="h-4 w-4 text-blue-600" />
            <span>CPU: {data.resources.cpuUsage.toFixed(1)}%</span>
          </div>
          <div className="flex items-center space-x-2 text-sm">
            <MemoryStick className="h-4 w-4 text-green-600" />
            <span>RAM: {data.resources.memoryUsage.toFixed(1)}%</span>
          </div>
          <div className="flex items-center space-x-2 text-sm">
            <MemoryStick className="h-4 w-4 text-purple-600" />
            <span>{data.resources.memoryMB.toFixed(0)}MB</span>
          </div>
        </div>

        {/* Errors */}
        {data.errors.length > 0 && (
          <div className="p-3 bg-red-50 dark:bg-red-950 rounded-lg">
            <div className="flex items-center space-x-2 text-sm font-medium text-red-800 dark:text-red-200 mb-2">
              <AlertTriangle className="h-4 w-4" />
              <span>Issues ({data.errors.length})</span>
            </div>
            <div className="space-y-1 max-h-20 overflow-y-auto">
              {data.errors.slice(0, 3).map((error, i) => (
                <div key={i} className="text-xs text-red-700 dark:text-red-300">
                  {error.message}
                </div>
              ))}
              {data.errors.length > 3 && (
                <div className="text-xs text-red-600 dark:text-red-400">
                  +{data.errors.length - 3} more issues...
                </div>
              )}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
