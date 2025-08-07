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
import { Separator } from "@/components/ui/separator";
import { useBacktestExecution } from "@/hooks/useBacktestExecution";
import { useSystemStatus } from "@/hooks/useSystemStatus";
import { useState, useEffect } from "react";
import { format } from "date-fns";
import {
  Activity,
  Cpu,
  HardDrive,
  Zap,
  Clock,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle,
  Pause,
  Play,
  Square,
  RefreshCw,
  BarChart3,
  Users,
  Database,
} from "lucide-react";

export default function MonitorPage() {
  const { executions, loading: executionsLoading } = useBacktestExecution();
  const { status: systemStatus, loading: systemLoading } = useSystemStatus();
  const [currentTime, setCurrentTime] = useState(new Date());

  // Update current time every second
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatPercent = (value: number) => {
    return `${value >= 0 ? "+" : ""}${value.toFixed(2)}%`;
  };

  const getExecutionStatusBadge = (status: string) => {
    switch (status) {
      case "running":
        return (
          <Badge variant="default" className="bg-blue-500 text-white">
            Running
          </Badge>
        );
      case "completed":
        return (
          <Badge variant="default" className="bg-green-500 text-white">
            Completed
          </Badge>
        );
      case "failed":
        return <Badge variant="destructive">Failed</Badge>;
      case "paused":
        return <Badge variant="secondary">Paused</Badge>;
      case "queued":
        return <Badge variant="outline">Queued</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const getSystemHealthColor = (value: number, threshold: number = 80) => {
    if (value >= threshold) return "text-red-600";
    if (value >= threshold * 0.7) return "text-yellow-600";
    return "text-green-600";
  };

  const runningExecutions = executions.filter(
    (e) => e.status === "running" || e.status === "paused"
  );
  const queuedExecutions = executions.filter((e) => e.status === "queued");

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center space-x-2">
            <Activity className="h-8 w-8" />
            <span>Real-time Monitor</span>
          </h1>
          <p className="text-muted-foreground">
            Monitor system performance and active executions
          </p>
        </div>
        <div className="text-right">
          <div className="text-sm text-muted-foreground">Current Time</div>
          <div className="text-lg font-mono">
            {format(currentTime, "HH:mm:ss")}
          </div>
        </div>
      </div>

      {/* System Status Overview */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center space-x-2">
              <Cpu className="h-4 w-4" />
              <span>CPU Usage</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div
              className={`text-2xl font-bold ${getSystemHealthColor(
                systemStatus?.cpu_usage || 0
              )}`}
            >
              {systemStatus?.cpu_usage?.toFixed(1) || "0.0"}%
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all"
                style={{ width: `${systemStatus?.cpu_usage || 0}%` }}
              ></div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center space-x-2">
              <HardDrive className="h-4 w-4" />
              <span>Memory Usage</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div
              className={`text-2xl font-bold ${getSystemHealthColor(
                systemStatus?.memory_usage || 0
              )}`}
            >
              {systemStatus?.memory_usage?.toFixed(1) || "0.0"}%
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
              <div
                className="bg-green-600 h-2 rounded-full transition-all"
                style={{ width: `${systemStatus?.memory_usage || 0}%` }}
              ></div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center space-x-2">
              <BarChart3 className="h-4 w-4" />
              <span>Active Executions</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">
              {runningExecutions.length}
            </div>
            <div className="text-sm text-muted-foreground">
              {queuedExecutions.length} queued
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center space-x-2">
              <Database className="h-4 w-4" />
              <span>Data Status</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">Online</div>
            <div className="text-sm text-muted-foreground">
              All data sources available
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Active Executions */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Active Executions</CardTitle>
              <CardDescription>
                Currently running and queued backtests
              </CardDescription>
            </div>
            <Button variant="outline" size="sm">
              <RefreshCw className="mr-2 h-4 w-4" />
              Refresh
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {executionsLoading ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto"></div>
              <p className="mt-2 text-sm text-muted-foreground">
                Loading executions...
              </p>
            </div>
          ) : runningExecutions.length === 0 &&
            queuedExecutions.length === 0 ? (
            <div className="text-center py-8">
              <BarChart3 className="mx-auto h-12 w-12 text-muted-foreground" />
              <h3 className="mt-4 text-lg font-medium">No active executions</h3>
              <p className="text-muted-foreground">
                Start a backtest to see real-time monitoring
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Running Executions */}
              {runningExecutions.map((execution) => (
                <Card key={execution.id} className="border-blue-200">
                  <CardContent className="pt-6">
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center space-x-3">
                        <div className="relative">
                          <Activity className="h-6 w-6 text-blue-600" />
                          <div className="absolute -top-1 -right-1 w-3 h-3 bg-blue-600 rounded-full animate-pulse"></div>
                        </div>
                        <div>
                          <h4 className="font-medium">
                            {execution.strategy_name}
                          </h4>
                          <p className="text-sm text-muted-foreground">
                            Started{" "}
                            {format(new Date(execution.started_at), "HH:mm:ss")}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        {getExecutionStatusBadge(execution.status)}
                        <Button variant="outline" size="sm">
                          {execution.status === "paused" ? (
                            <Play className="h-4 w-4" />
                          ) : (
                            <Pause className="h-4 w-4" />
                          )}
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          className="text-red-600"
                        >
                          <Square className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>

                    {/* Progress Bar */}
                    <div className="mb-4">
                      <div className="flex justify-between text-sm mb-2">
                        <span>Progress</span>
                        <span>{execution.progress}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full transition-all"
                          style={{ width: `${execution.progress}%` }}
                        ></div>
                      </div>
                    </div>

                    {/* Real-time Metrics */}
                    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                      <div>
                        <p className="text-sm text-muted-foreground">
                          Current Equity
                        </p>
                        <p className="text-lg font-semibold">
                          {formatCurrency(
                            execution.current_equity ||
                              execution.initial_capital
                          )}
                        </p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">
                          Unrealized P&L
                        </p>
                        <p
                          className={`text-lg font-semibold ${
                            (execution.unrealized_pnl || 0) >= 0
                              ? "text-green-600"
                              : "text-red-600"
                          }`}
                        >
                          {formatPercent(execution.unrealized_pnl || 0)}
                        </p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">
                          Trades Executed
                        </p>
                        <p className="text-lg font-semibold">
                          {execution.trades_completed || 0}
                        </p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">
                          Est. Time Left
                        </p>
                        <p className="text-lg font-semibold">
                          {execution.estimated_completion || "Calculating..."}
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}

              {/* Queued Executions */}
              {queuedExecutions.map((execution) => (
                <Card key={execution.id} className="border-orange-200">
                  <CardContent className="pt-6">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <Clock className="h-6 w-6 text-orange-600" />
                        <div>
                          <h4 className="font-medium">
                            {execution.strategy_name}
                          </h4>
                          <p className="text-sm text-muted-foreground">
                            Queued at{" "}
                            {format(new Date(execution.created_at), "HH:mm:ss")}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        {getExecutionStatusBadge(execution.status)}
                        <span className="text-sm text-muted-foreground">
                          Priority: {execution.priority || "Normal"}
                        </span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Recent Activity */}
      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>System Alerts</CardTitle>
            <CardDescription>Recent warnings and notifications</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-start space-x-3">
              <CheckCircle className="h-5 w-5 text-green-600 mt-0.5" />
              <div>
                <p className="text-sm font-medium">All systems operational</p>
                <p className="text-xs text-muted-foreground">
                  {format(currentTime, "HH:mm:ss")}
                </p>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <AlertTriangle className="h-5 w-5 text-yellow-600 mt-0.5" />
              <div>
                <p className="text-sm font-medium">High CPU usage detected</p>
                <p className="text-xs text-muted-foreground">5 minutes ago</p>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <CheckCircle className="h-5 w-5 text-green-600 mt-0.5" />
              <div>
                <p className="text-sm font-medium">
                  Data feed connection restored
                </p>
                <p className="text-xs text-muted-foreground">15 minutes ago</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Performance Summary</CardTitle>
            <CardDescription>Today's execution statistics</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex justify-between">
              <span className="text-muted-foreground">
                Executions Completed:
              </span>
              <span className="font-medium">
                {executions.filter((e) => e.status === "completed").length}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Average Duration:</span>
              <span className="font-medium">2m 34s</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Success Rate:</span>
              <span className="font-medium text-green-600">98.5%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">
                Total Data Processed:
              </span>
              <span className="font-medium">1.2M ticks</span>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
