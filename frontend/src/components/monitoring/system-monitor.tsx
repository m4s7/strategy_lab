"use client";

import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Activity,
  Cpu,
  HardDrive,
  Wifi,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Database,
  Server,
  TrendingUp,
  TrendingDown,
} from "lucide-react";
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  ResponsiveContainer,
} from "recharts";
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";

interface SystemMetrics {
  cpu: {
    usage: number;
    cores: number;
    temperature?: number;
  };
  memory: {
    used: number;
    total: number;
    percentage: number;
  };
  disk: {
    used: number;
    total: number;
    percentage: number;
    iops: number;
  };
  network: {
    in: number;
    out: number;
    latency: number;
    errors: number;
  };
  services: {
    api: "healthy" | "degraded" | "down";
    database: "healthy" | "degraded" | "down";
    websocket: "healthy" | "degraded" | "down";
    cache: "healthy" | "degraded" | "down";
  };
}

interface PerformanceLog {
  timestamp: number;
  cpu: number;
  memory: number;
  requestsPerSecond: number;
  responseTime: number;
}

export function SystemMonitor() {
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [performanceLogs, setPerformanceLogs] = useState<PerformanceLog[]>([]);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 5000); // Update every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchMetrics = async () => {
    try {
      const response = await fetch("/api/system/metrics");
      if (response.ok) {
        const data = await response.json();
        setMetrics(data.current);

        // Add to performance logs
        setPerformanceLogs((prev) => {
          const newLog: PerformanceLog = {
            timestamp: Date.now(),
            cpu: data.current.cpu.usage,
            memory: data.current.memory.percentage,
            requestsPerSecond: data.requestsPerSecond || 0,
            responseTime: data.averageResponseTime || 0,
          };

          // Keep last 60 data points (5 minutes of data)
          const logs = [...prev, newLog].slice(-60);
          return logs;
        });

        setAlerts(data.alerts || []);
      }
    } catch (error) {
      console.error("Failed to fetch metrics:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const getServiceStatusIcon = (status: string) => {
    switch (status) {
      case "healthy":
        return <CheckCircle2 className="h-4 w-4 text-green-500" />;
      case "degraded":
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      case "down":
        return <AlertTriangle className="h-4 w-4 text-red-500" />;
      default:
        return null;
    }
  };

  const getServiceStatusColor = (status: string) => {
    switch (status) {
      case "healthy":
        return "outline";
      case "degraded":
        return "secondary";
      case "down":
        return "destructive";
      default:
        return "outline";
    }
  };

  if (isLoading || !metrics) {
    return (
      <Card>
        <CardContent className="py-8">
          <div className="flex items-center justify-center">
            <Activity className="h-8 w-8 animate-pulse text-muted-foreground" />
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* System Health Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Cpu className="h-4 w-4" />
              CPU Usage
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {metrics.cpu.usage.toFixed(1)}%
            </div>
            <Progress value={metrics.cpu.usage} className="mt-2" />
            <p className="text-xs text-muted-foreground mt-1">
              {metrics.cpu.cores} cores
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Server className="h-4 w-4" />
              Memory
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {metrics.memory.percentage.toFixed(1)}%
            </div>
            <Progress value={metrics.memory.percentage} className="mt-2" />
            <p className="text-xs text-muted-foreground mt-1">
              {(metrics.memory.used / 1024 / 1024 / 1024).toFixed(1)} /
              {(metrics.memory.total / 1024 / 1024 / 1024).toFixed(1)} GB
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <HardDrive className="h-4 w-4" />
              Disk
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {metrics.disk.percentage.toFixed(1)}%
            </div>
            <Progress value={metrics.disk.percentage} className="mt-2" />
            <p className="text-xs text-muted-foreground mt-1">
              {metrics.disk.iops} IOPS
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Wifi className="h-4 w-4" />
              Network
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {metrics.network.latency}ms
            </div>
            <div className="flex items-center gap-2 mt-2">
              <TrendingDown className="h-3 w-3 text-blue-500" />
              <span className="text-xs">
                {(metrics.network.in / 1024).toFixed(1)} MB/s
              </span>
            </div>
            <div className="flex items-center gap-2">
              <TrendingUp className="h-3 w-3 text-green-500" />
              <span className="text-xs">
                {(metrics.network.out / 1024).toFixed(1)} MB/s
              </span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Service Status */}
      <Card>
        <CardHeader>
          <CardTitle>Service Status</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(metrics.services).map(([service, status]) => (
              <div
                key={service}
                className="flex items-center justify-between p-3 border rounded"
              >
                <div className="flex items-center gap-2">
                  <Database className="h-4 w-4 text-muted-foreground" />
                  <span className="font-medium capitalize">{service}</span>
                </div>
                <Badge variant={getServiceStatusColor(status)}>
                  {getServiceStatusIcon(status)}
                  <span className="ml-1">{status}</span>
                </Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Performance Charts */}
      <Tabs defaultValue="cpu" className="space-y-4">
        <TabsList>
          <TabsTrigger value="cpu">CPU</TabsTrigger>
          <TabsTrigger value="memory">Memory</TabsTrigger>
          <TabsTrigger value="requests">Requests</TabsTrigger>
          <TabsTrigger value="response">Response Time</TabsTrigger>
        </TabsList>

        <TabsContent value="cpu">
          <Card>
            <CardHeader>
              <CardTitle>CPU Usage Over Time</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={200}>
                <AreaChart data={performanceLogs}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="timestamp"
                    tickFormatter={(value) =>
                      new Date(value).toLocaleTimeString()
                    }
                  />
                  <YAxis domain={[0, 100]} />
                  <ChartTooltip
                    content={
                      <ChartTooltipContent
                        labelFormatter={(value) =>
                          new Date(value).toLocaleTimeString()
                        }
                      />
                    }
                  />
                  <Area
                    type="monotone"
                    dataKey="cpu"
                    stroke="hsl(var(--chart-1))"
                    fill="hsl(var(--chart-1))"
                    fillOpacity={0.3}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="memory">
          <Card>
            <CardHeader>
              <CardTitle>Memory Usage Over Time</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={200}>
                <AreaChart data={performanceLogs}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="timestamp"
                    tickFormatter={(value) =>
                      new Date(value).toLocaleTimeString()
                    }
                  />
                  <YAxis domain={[0, 100]} />
                  <ChartTooltip
                    content={
                      <ChartTooltipContent
                        labelFormatter={(value) =>
                          new Date(value).toLocaleTimeString()
                        }
                      />
                    }
                  />
                  <Area
                    type="monotone"
                    dataKey="memory"
                    stroke="hsl(var(--chart-2))"
                    fill="hsl(var(--chart-2))"
                    fillOpacity={0.3}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Alerts */}
      {alerts.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Active Alerts</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {alerts.map((alert, index) => (
              <Alert
                key={index}
                variant={
                  alert.severity === "critical" ? "destructive" : "default"
                }
              >
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>
                  <div className="flex items-center justify-between">
                    <span>{alert.message}</span>
                    <span className="text-xs text-muted-foreground">
                      {formatDistanceToNow(new Date(alert.timestamp))} ago
                    </span>
                  </div>
                </AlertDescription>
              </Alert>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function formatDistanceToNow(date: Date): string {
  const seconds = Math.floor((Date.now() - date.getTime()) / 1000);
  if (seconds < 60) return `${seconds}s`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m`;
  const hours = Math.floor(minutes / 60);
  return `${hours}h`;
}
