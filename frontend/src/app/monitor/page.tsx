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
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { BacktestMonitor } from "@/components/monitoring/backtest-monitor";
import { ResourceMonitor } from "@/components/monitoring/resource-monitor";
import { useBacktestMonitor } from "@/hooks/useBacktestMonitor";
import { useWebSocketStatus } from "@/lib/websocket/hooks";
import { useState, useEffect } from "react";
import { format } from "date-fns";
import {
  Activity,
  Wifi,
  WifiOff,
  Clock,
  AlertTriangle,
  CheckCircle,
  RefreshCw,
  BarChart3,
  Database,
  Trash2,
  Settings,
  Play,
  Pause,
  Square,
} from "lucide-react";

export default function MonitorPage() {
  const { 
    monitors, 
    activeMonitors, 
    abortBacktest, 
    pauseBacktest, 
    resumeBacktest,
    clearCompleted,
    subscriptionCount 
  } = useBacktestMonitor();
  
  const { status: wsStatus, isConnected, connect, disconnect } = useWebSocketStatus();
  const [currentTime, setCurrentTime] = useState(new Date());
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Update current time every second
  useEffect(() => {
    if (!autoRefresh) return;
    
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => clearInterval(timer);
  }, [autoRefresh]);

  // Auto-reconnect WebSocket if disconnected
  useEffect(() => {
    if (!isConnected && autoRefresh) {
      const reconnectTimer = setTimeout(() => {
        connect();
      }, 5000);
      
      return () => clearTimeout(reconnectTimer);
    }
  }, [isConnected, connect, autoRefresh]);

  const getConnectionStatus = () => {
    if (isConnected) {
      return (
        <Badge className="bg-green-500 text-white">
          <Wifi className="mr-1 h-3 w-3" />
          Connected
        </Badge>
      );
    }
    return (
      <Badge variant="destructive">
        <WifiOff className="mr-1 h-3 w-3" />
        Disconnected
      </Badge>
    );
  };

  const runningMonitors = monitors.filter(m => m.status === 'running');
  const pausedMonitors = monitors.filter(m => m.status === 'paused');
  const queuedMonitors = monitors.filter(m => m.status === 'queued');
  const completedMonitors = monitors.filter(m => 
    m.status === 'completed' || m.status === 'aborted' || m.status === 'failed'
  );

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
            Monitor system performance and active backtests in real-time
          </p>
        </div>
        <div className="flex items-center space-x-4">
          <div className="text-right">
            <div className="text-sm text-muted-foreground">Current Time</div>
            <div className="text-lg font-mono">
              {format(currentTime, "HH:mm:ss")}
            </div>
          </div>
          <Separator orientation="vertical" className="h-10" />
          <div className="flex items-center space-x-2">
            {getConnectionStatus()}
            <Button
              variant="outline"
              size="sm"
              onClick={() => setAutoRefresh(!autoRefresh)}
            >
              <RefreshCw className={`mr-2 h-4 w-4 ${autoRefresh ? 'animate-spin' : ''}`} />
              {autoRefresh ? 'Pause' : 'Resume'}
            </Button>
          </div>
        </div>
      </div>

      {/* Status Overview Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center space-x-2">
              <Play className="h-4 w-4 text-green-600" />
              <span>Running</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {runningMonitors.length}
            </div>
            <div className="text-sm text-muted-foreground">
              Active backtests
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center space-x-2">
              <Pause className="h-4 w-4 text-yellow-600" />
              <span>Paused</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">
              {pausedMonitors.length}
            </div>
            <div className="text-sm text-muted-foreground">
              Paused backtests
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center space-x-2">
              <Clock className="h-4 w-4 text-blue-600" />
              <span>Queued</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">
              {queuedMonitors.length}
            </div>
            <div className="text-sm text-muted-foreground">
              Waiting to start
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center space-x-2">
              <Database className="h-4 w-4" />
              <span>Subscriptions</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {subscriptionCount}
            </div>
            <div className="text-sm text-muted-foreground">
              WebSocket topics
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Tabs */}
      <Tabs defaultValue="active" className="space-y-6">
        <div className="flex items-center justify-between">
          <TabsList className="grid w-fit grid-cols-4">
            <TabsTrigger value="active">
              Active ({runningMonitors.length + pausedMonitors.length})
            </TabsTrigger>
            <TabsTrigger value="queue">Queue ({queuedMonitors.length})</TabsTrigger>
            <TabsTrigger value="completed">History ({completedMonitors.length})</TabsTrigger>
            <TabsTrigger value="system">System</TabsTrigger>
          </TabsList>

          <div className="flex items-center space-x-2">
            {completedMonitors.length > 0 && (
              <Button
                variant="outline"
                size="sm"
                onClick={clearCompleted}
              >
                <Trash2 className="mr-2 h-4 w-4" />
                Clear History
              </Button>
            )}
            <Button variant="outline" size="sm">
              <Settings className="mr-2 h-4 w-4" />
              Settings
            </Button>
          </div>
        </div>

        <TabsContent value="active" className="space-y-4">
          {runningMonitors.length === 0 && pausedMonitors.length === 0 ? (
            <Card>
              <CardContent className="pt-6">
                <div className="text-center py-8">
                  <BarChart3 className="mx-auto h-12 w-12 text-muted-foreground" />
                  <h3 className="mt-4 text-lg font-medium">No active backtests</h3>
                  <p className="text-muted-foreground mb-4">
                    Start a backtest to see real-time monitoring
                  </p>
                  <Button>Start New Backtest</Button>
                </div>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {/* Running Backtests */}
              {runningMonitors.map((monitor) => (
                <BacktestMonitor
                  key={monitor.id}
                  backtestId={monitor.id}
                  initialData={monitor}
                  onAbort={abortBacktest}
                  onPause={pauseBacktest}
                  onResume={resumeBacktest}
                />
              ))}

              {/* Paused Backtests */}
              {pausedMonitors.map((monitor) => (
                <BacktestMonitor
                  key={monitor.id}
                  backtestId={monitor.id}
                  initialData={monitor}
                  onAbort={abortBacktest}
                  onPause={pauseBacktest}
                  onResume={resumeBacktest}
                />
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="queue" className="space-y-4">
          {queuedMonitors.length === 0 ? (
            <Card>
              <CardContent className="pt-6">
                <div className="text-center py-8">
                  <Clock className="mx-auto h-12 w-12 text-muted-foreground" />
                  <h3 className="mt-4 text-lg font-medium">No queued backtests</h3>
                  <p className="text-muted-foreground">
                    All backtests are either running or completed
                  </p>
                </div>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {queuedMonitors.map((monitor) => (
                <BacktestMonitor
                  key={monitor.id}
                  backtestId={monitor.id}
                  initialData={monitor}
                  onAbort={abortBacktest}
                  compact={true}
                />
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="completed" className="space-y-4">
          {completedMonitors.length === 0 ? (
            <Card>
              <CardContent className="pt-6">
                <div className="text-center py-8">
                  <CheckCircle className="mx-auto h-12 w-12 text-muted-foreground" />
                  <h3 className="mt-4 text-lg font-medium">No completed backtests</h3>
                  <p className="text-muted-foreground">
                    Completed backtests will appear here
                  </p>
                </div>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {completedMonitors.map((monitor) => (
                <BacktestMonitor
                  key={monitor.id}
                  backtestId={monitor.id}
                  initialData={monitor}
                  compact={true}
                />
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="system" className="space-y-6">
          {/* System Resource Monitor */}
          <ResourceMonitor />

          {/* Connection Status */}
          <Card>
            <CardHeader>
              <CardTitle>Connection Status</CardTitle>
              <CardDescription>
                WebSocket connection and subscription details
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                <div className="space-y-2">
                  <div className="text-sm text-muted-foreground">WebSocket Status</div>
                  {getConnectionStatus()}
                </div>
                
                <div className="space-y-2">
                  <div className="text-sm text-muted-foreground">Active Subscriptions</div>
                  <div className="text-lg font-medium">{subscriptionCount}</div>
                </div>
                
                <div className="space-y-2">
                  <div className="text-sm text-muted-foreground">Auto Refresh</div>
                  <Badge variant={autoRefresh ? 'default' : 'secondary'}>
                    {autoRefresh ? 'Enabled' : 'Disabled'}
                  </Badge>
                </div>
              </div>

              <Separator className="my-4" />

              <div className="flex items-center space-x-2">
                {!isConnected && (
                  <Button onClick={connect} size="sm">
                    <Wifi className="mr-2 h-4 w-4" />
                    Reconnect
                  </Button>
                )}
                
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => setAutoRefresh(!autoRefresh)}
                >
                  {autoRefresh ? 'Disable' : 'Enable'} Auto Refresh
                </Button>
                
                <Button variant="outline" size="sm" onClick={() => window.location.reload()}>
                  <RefreshCw className="mr-2 h-4 w-4" />
                  Refresh Page
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* System Alerts */}
          <Card>
            <CardHeader>
              <CardTitle>System Alerts</CardTitle>
              <CardDescription>Recent warnings and notifications</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {isConnected ? (
                <div className="flex items-start space-x-3">
                  <CheckCircle className="h-5 w-5 text-green-600 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium">Real-time monitoring active</p>
                    <p className="text-xs text-muted-foreground">
                      {format(currentTime, "HH:mm:ss")}
                    </p>
                  </div>
                </div>
              ) : (
                <div className="flex items-start space-x-3">
                  <AlertTriangle className="h-5 w-5 text-red-600 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium">WebSocket disconnected</p>
                    <p className="text-xs text-muted-foreground">
                      Real-time updates unavailable
                    </p>
                  </div>
                </div>
              )}
              
              {runningMonitors.length > 3 && (
                <div className="flex items-start space-x-3">
                  <AlertTriangle className="h-5 w-5 text-yellow-600 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium">High concurrent backtest load</p>
                    <p className="text-xs text-muted-foreground">
                      {runningMonitors.length} backtests running simultaneously
                    </p>
                  </div>
                </div>
              )}
              
              <div className="flex items-start space-x-3">
                <CheckCircle className="h-5 w-5 text-green-600 mt-0.5" />
                <div>
                  <p className="text-sm font-medium">State persistence enabled</p>
                  <p className="text-xs text-muted-foreground">
                    Monitor state saved across page refreshes
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}