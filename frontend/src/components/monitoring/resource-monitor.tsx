'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { 
  Cpu, 
  MemoryStick, 
  HardDrive,
  Activity,
  AlertTriangle,
  CheckCircle,
  Server
} from "lucide-react";
import { useWebSocketSubscription } from "@/lib/websocket/hooks";
import { useState, useEffect } from "react";

interface ResourceData {
  cpu: number;
  memory: number;
  disk: number;
  activeBacktests: number;
  timestamp: string;
  networkRx?: number;
  networkTx?: number;
}

interface ResourceMonitorProps {
  compact?: boolean;
  showDetails?: boolean;
}

export function ResourceMonitor({ compact = false, showDetails = true }: ResourceMonitorProps) {
  const { data: resourceData, lastUpdate } = useWebSocketSubscription<ResourceData>('system:resources');
  const [history, setHistory] = useState<ResourceData[]>([]);

  // Keep history for trending
  useEffect(() => {
    if (resourceData) {
      setHistory(prev => {
        const newHistory = [...prev, resourceData].slice(-60); // Keep last 60 data points (1 minute at 1s intervals)
        return newHistory;
      });
    }
  }, [resourceData]);

  if (!resourceData) {
    return (
      <Card className="animate-pulse">
        <CardHeader>
          <div className="h-6 bg-muted rounded w-2/3"></div>
          <div className="h-4 bg-muted rounded w-1/2"></div>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {Array.from({ length: 3 }, (_, i) => (
              <div key={i} className="space-y-2">
                <div className="h-4 bg-muted rounded w-1/4"></div>
                <div className="h-2 bg-muted rounded"></div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  const getResourceStatus = (value: number) => {
    if (value >= 90) return { level: 'critical', color: 'text-red-600', bg: 'bg-red-500' };
    if (value >= 75) return { level: 'warning', color: 'text-yellow-600', bg: 'bg-yellow-500' };
    if (value >= 50) return { level: 'moderate', color: 'text-blue-600', bg: 'bg-blue-500' };
    return { level: 'good', color: 'text-green-600', bg: 'bg-green-500' };
  };

  const formatBytes = (bytes: number) => {
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    if (bytes === 0) return '0 B';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  };

  const getOverallHealthStatus = () => {
    const maxUsage = Math.max(resourceData.cpu, resourceData.memory, resourceData.disk);
    if (maxUsage >= 90) return { icon: AlertTriangle, color: 'text-red-600', label: 'Critical' };
    if (maxUsage >= 75) return { icon: AlertTriangle, color: 'text-yellow-600', label: 'Warning' };
    return { icon: CheckCircle, color: 'text-green-600', label: 'Good' };
  };

  const cpuStatus = getResourceStatus(resourceData.cpu);
  const memoryStatus = getResourceStatus(resourceData.memory);
  const diskStatus = getResourceStatus(resourceData.disk);
  const healthStatus = getOverallHealthStatus();

  if (compact) {
    return (
      <Card>
        <CardContent className="pt-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-2">
              <Server className="h-4 w-4 text-muted-foreground" />
              <span className="font-medium text-sm">System Resources</span>
            </div>
            <Badge 
              variant={healthStatus.label === 'Good' ? 'default' : 'destructive'}
              className="text-xs"
            >
              {healthStatus.label}
            </Badge>
          </div>
          
          <div className="grid grid-cols-3 gap-3 text-xs">
            <div className="text-center">
              <div className={`font-medium ${cpuStatus.color}`}>
                {resourceData.cpu.toFixed(0)}%
              </div>
              <div className="text-muted-foreground">CPU</div>
            </div>
            <div className="text-center">
              <div className={`font-medium ${memoryStatus.color}`}>
                {resourceData.memory.toFixed(0)}%
              </div>
              <div className="text-muted-foreground">RAM</div>
            </div>
            <div className="text-center">
              <div className={`font-medium ${diskStatus.color}`}>
                {resourceData.disk.toFixed(0)}%
              </div>
              <div className="text-muted-foreground">Disk</div>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Server className="h-5 w-5 text-muted-foreground" />
            <div>
              <CardTitle className="text-lg">System Resources</CardTitle>
              <CardDescription>
                Real-time system monitoring
                {lastUpdate && (
                  <span className="ml-2 text-xs">
                    Updated {new Date(lastUpdate).toLocaleTimeString()}
                  </span>
                )}
              </CardDescription>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <healthStatus.icon className={`h-5 w-5 ${healthStatus.color}`} />
            <Badge 
              variant={healthStatus.label === 'Good' ? 'default' : 'destructive'}
            >
              {healthStatus.label}
            </Badge>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* CPU Usage */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center space-x-2">
              <Cpu className="h-4 w-4 text-blue-600" />
              <span>CPU Usage</span>
            </div>
            <span className={`font-medium ${cpuStatus.color}`}>
              {resourceData.cpu.toFixed(1)}%
            </span>
          </div>
          <Progress value={resourceData.cpu} className="h-2" />
        </div>

        {/* Memory Usage */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center space-x-2">
              <MemoryStick className="h-4 w-4 text-green-600" />
              <span>Memory Usage</span>
            </div>
            <span className={`font-medium ${memoryStatus.color}`}>
              {resourceData.memory.toFixed(1)}%
            </span>
          </div>
          <Progress value={resourceData.memory} className="h-2" />
        </div>

        {/* Disk Usage */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center space-x-2">
              <HardDrive className="h-4 w-4 text-purple-600" />
              <span>Disk Usage</span>
            </div>
            <span className={`font-medium ${diskStatus.color}`}>
              {resourceData.disk.toFixed(1)}%
            </span>
          </div>
          <Progress value={resourceData.disk} className="h-2" />
        </div>

        {showDetails && (
          <>
            {/* Activity Summary */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 pt-2 border-t">
              <div className="text-center p-2 bg-muted/30 rounded-lg">
                <div className="text-lg font-medium text-blue-600">
                  {resourceData.activeBacktests}
                </div>
                <div className="text-xs text-muted-foreground">Active Tests</div>
              </div>
              
              <div className="text-center p-2 bg-muted/30 rounded-lg">
                <div className="text-lg font-medium">
                  {history.length > 1 ? 
                    ((resourceData.cpu - history[history.length - 2].cpu) >= 0 ? '+' : '') +
                    (resourceData.cpu - history[history.length - 2].cpu).toFixed(1) + '%'
                    : '—'
                  }
                </div>
                <div className="text-xs text-muted-foreground">CPU Δ</div>
              </div>
              
              <div className="text-center p-2 bg-muted/30 rounded-lg">
                <div className="text-lg font-medium">
                  {history.length > 1 ? 
                    ((resourceData.memory - history[history.length - 2].memory) >= 0 ? '+' : '') +
                    (resourceData.memory - history[history.length - 2].memory).toFixed(1) + '%'
                    : '—'
                  }
                </div>
                <div className="text-xs text-muted-foreground">RAM Δ</div>
              </div>

              <div className="text-center p-2 bg-muted/30 rounded-lg">
                <div className="text-lg font-medium">
                  {history.length}
                </div>
                <div className="text-xs text-muted-foreground">Samples</div>
              </div>
            </div>

            {/* Network Activity */}
            {(resourceData.networkRx !== undefined || resourceData.networkTx !== undefined) && (
              <div className="grid grid-cols-2 gap-3 pt-2 border-t">
                <div className="flex items-center space-x-2 text-sm">
                  <Activity className="h-4 w-4 text-green-600" />
                  <span>RX: {formatBytes(resourceData.networkRx || 0)}/s</span>
                </div>
                <div className="flex items-center space-x-2 text-sm">
                  <Activity className="h-4 w-4 text-blue-600" />
                  <span>TX: {formatBytes(resourceData.networkTx || 0)}/s</span>
                </div>
              </div>
            )}

            {/* Warning Messages */}
            {(resourceData.cpu >= 90 || resourceData.memory >= 90 || resourceData.disk >= 90) && (
              <div className="p-3 bg-red-50 dark:bg-red-950 rounded-lg">
                <div className="flex items-center space-x-2 text-sm font-medium text-red-800 dark:text-red-200 mb-1">
                  <AlertTriangle className="h-4 w-4" />
                  <span>Resource Warning</span>
                </div>
                <div className="text-xs text-red-700 dark:text-red-300">
                  System resources are critically high. Consider pausing non-essential backtests.
                </div>
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}