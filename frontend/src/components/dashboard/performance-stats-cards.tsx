'use client';

import { BarChart3, CheckCircle, Clock, AlertTriangle } from "lucide-react";
import { MetricCard } from "@/components/ui/metric-card";
import { useSystemStatus } from "@/hooks/useSystemStatus";

export function PerformanceStatsCards() {
  const { stats, loading, error } = useSystemStatus();

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

  if (error || !stats) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="Performance Stats"
          value="Error"
          description="Unable to load statistics"
          icon={AlertTriangle}
          status="error"
        />
      </div>
    );
  }

  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${Math.round(seconds)}s`;
    if (seconds < 3600) return `${Math.round(seconds / 60)}m`;
    return `${Math.round(seconds / 3600)}h`;
  };

  const formatNumber = (num: number) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  };

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">Today's Performance</h3>
      
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="Backtests Run"
          value={stats.today.backtests_run}
          description="Total executed today"
          icon={BarChart3}
          status="neutral"
        />
        
        <MetricCard
          title="Success Rate"
          value={`${stats.today.success_rate}%`}
          description={`${stats.today.completed} completed`}
          icon={CheckCircle}
          status={stats.today.success_rate > 90 ? 'healthy' : stats.today.success_rate > 70 ? 'warning' : 'error'}
        />
        
        <MetricCard
          title="Avg Duration"
          value={formatDuration(stats.today.average_duration)}
          description="Per backtest"
          icon={Clock}
          status="neutral"
        />
        
        <MetricCard
          title="Processing Speed"
          value={`${formatNumber(stats.data.processing_speed)}/s`}
          description="Records processed"
          icon={BarChart3}
          status="healthy"
        />
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <MetricCard
          title="Response Time"
          value={`${stats.performance.average_response_time}ms`}
          description="Average API response"
          icon={Clock}
          status={stats.performance.average_response_time < 200 ? 'healthy' : 'warning'}
        />
        
        <MetricCard
          title="Records Processed"
          value={formatNumber(stats.data.records_processed)}
          description="Total data points"
          icon={BarChart3}
          status="neutral"
        />
      </div>
    </div>
  );
}