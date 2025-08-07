"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { BacktestMonitor } from "@/components/monitoring/backtest-monitor";
import { useBacktestMonitor } from "@/hooks/useBacktestMonitor";
import { Play, ExternalLink, BarChart3 } from "lucide-react";
import Link from "next/link";

export function ActiveBacktestsMonitor() {
  const { monitors, activeMonitors } = useBacktestMonitor();

  const runningMonitors = monitors.filter((m) => m.status === "running");
  const totalActive = activeMonitors.length;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>
          Active Backtests
          {totalActive > 0 && (
            <Badge variant="secondary" className="ml-2">
              {totalActive}
            </Badge>
          )}
        </CardTitle>
        <Button variant="outline" size="sm" asChild>
          <Link href="/monitor">
            <ExternalLink className="h-4 w-4 mr-2" />
            View Monitor
          </Link>
        </Button>
      </CardHeader>
      <CardContent>
        {totalActive === 0 ? (
          <div className="text-center text-muted-foreground py-8">
            <BarChart3 className="h-8 w-8 mx-auto mb-2 opacity-50" />
            <p>No active backtests</p>
            <Button variant="outline" size="sm" className="mt-2" asChild>
              <Link href="/backtests/new">Start New Backtest</Link>
            </Button>
          </div>
        ) : (
          <div className="space-y-3">
            {/* Show compact version of active monitors */}
            {activeMonitors
              .slice(0, 3)
              .map((monitor) => (
                <BacktestMonitor
                  key={monitor.id}
                  backtestId={monitor.id}
                  initialData={monitor}
                  compact={true}
                />
              ))}

            {activeMonitors.length > 3 && (
              <div className="text-center pt-2">
                <Button variant="outline" size="sm" asChild>
                  <Link href="/monitor">
                    View All {activeMonitors.length} Active Backtests
                  </Link>
                </Button>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
