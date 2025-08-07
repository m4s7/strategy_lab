"use client";

import { SystemMetricsGrid } from "@/components/dashboard/system-metrics-grid";
import { RecentActivityPanel } from "@/components/dashboard/recent-activity-panel";
import { PerformanceStatsCards } from "@/components/dashboard/performance-stats-cards";
import { ActiveBacktestsMonitor } from "@/components/dashboard/active-backtests-monitor";
import { QuickActionsPanel } from "@/components/dashboard/quick-actions-panel";

export default function Dashboard() {
  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Strategy Lab Dashboard</h1>
        <p className="text-muted-foreground mt-2">
          Monitor your backtesting environment and manage trading strategies
        </p>
      </div>

      {/* System Status */}
      <section>
        <SystemMetricsGrid />
      </section>

      {/* Performance Statistics */}
      <section>
        <PerformanceStatsCards />
      </section>

      {/* Main Dashboard Grid */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Left Column */}
        <div className="space-y-6">
          <RecentActivityPanel />
          <QuickActionsPanel />
        </div>

        {/* Right Column */}
        <div className="space-y-6">
          <ActiveBacktestsMonitor />
        </div>
      </div>
    </div>
  );
}
