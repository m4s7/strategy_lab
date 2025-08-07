"use client";

import {
  Cpu,
  Database,
  HardDrive,
  MemoryStick,
  Activity,
  Wifi,
} from "lucide-react";
import { MetricCard } from "@/components/ui/metric-card";
import { StatusIndicator } from "@/components/ui/status-indicator";
import { ResourceMonitor } from "@/components/monitoring/resource-monitor";
import { useSystemStatus } from "@/hooks/useSystemStatus";
import { useWebSocketStatus } from "@/lib/websocket/hooks";
import { useBacktestMonitor } from "@/hooks/useBacktestMonitor";

export function SystemMetricsGrid() {
  const { metrics, loading, error } = useSystemStatus();
  const { isConnected } = useWebSocketStatus();
  const { activeMonitors } = useBacktestMonitor();

  if (loading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 4 }, (_, i) => (
          <div key={i} className="animate-pulse">
            <div className="h-32 bg-muted rounded-lg"></div>
          </div>
        ))}
      </div>
    );
  }

  if (error || !metrics) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="System Status"
          value="Error"
          description="Unable to load metrics"
          icon={Activity}
          status="error"
        />
      </div>
    );
  }

  const formatUptime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  const getCpuStatus = (usage: number) => {
    if (usage > 80) return "error";
    if (usage > 60) return "warning";
    return "healthy";
  };

  const getMemoryStatus = (usage: number) => {
    if (usage > 85) return "error";
    if (usage > 70) return "warning";
    return "healthy";
  };

  const getDiskStatus = (usage: number) => {
    if (usage > 90) return "error";
    if (usage > 80) return "warning";
    return "healthy";
  };

  return (
    <div className="space-y-4">
      {/* System Status Row */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">System Status</h3>
        <div className="flex items-center space-x-4">
          <StatusIndicator
            status={metrics.database === "healthy" ? "healthy" : "error"}
            label={`Database: ${metrics.database}`}
          />
          <StatusIndicator
            status={
              metrics.websocket === "connected" ? "connected" : "disconnected"
            }
            label={`WebSocket: ${metrics.websocket}`}
          />
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="CPU Usage"
          value={`${metrics.cpu}%`}
          description="Processor utilization"
          icon={Cpu}
          status={getCpuStatus(metrics.cpu)}
        />

        <MetricCard
          title="Memory Usage"
          value={`${metrics.memory.used_percent}%`}
          description={`${metrics.memory.available_gb}GB available`}
          icon={MemoryStick}
          status={getMemoryStatus(metrics.memory.used_percent)}
        />

        <MetricCard
          title="Disk Usage"
          value={`${metrics.disk.used_percent}%`}
          description={`${metrics.disk.free_gb}GB free`}
          icon={HardDrive}
          status={getDiskStatus(metrics.disk.used_percent)}
        />

        <MetricCard
          title="System Uptime"
          value={formatUptime(metrics.uptime)}
          description="System running time"
          icon={Activity}
          status="healthy"
        />
      </div>
    </div>
  );
}
