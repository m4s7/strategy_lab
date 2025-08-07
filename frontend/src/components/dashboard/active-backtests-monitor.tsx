'use client';

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Play, Square, ExternalLink, Clock } from "lucide-react";
import { useActiveBacktests, type Backtest } from "@/hooks/useBacktests";
import { formatDistanceToNow } from "date-fns";

export function ActiveBacktestsMonitor() {
  const { backtests, loading, error } = useActiveBacktests();

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Active Backtests</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {Array.from({ length: 3 }, (_, i) => (
              <div key={i} className="animate-pulse">
                <div className="h-20 bg-muted rounded-lg"></div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Active Backtests</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center text-muted-foreground py-8">
            Failed to load active backtests
          </div>
        </CardContent>
      </Card>
    );
  }

  const runningBacktests = backtests.filter(bt => bt.status === 'running');
  const pendingBacktests = backtests.filter(bt => bt.status === 'pending');

  // Mock progress data - in real implementation this would come from WebSocket updates
  const getProgress = (backtest: Backtest) => {
    if (backtest.status === 'pending') return 0;
    if (backtest.status === 'running') {
      // Mock progress based on how long it's been running
      const elapsed = Date.now() - new Date(backtest.created_at).getTime();
      const estimatedDuration = 5 * 60 * 1000; // 5 minutes
      return Math.min(95, Math.round((elapsed / estimatedDuration) * 100));
    }
    return 100;
  };

  const getStatusIcon = (status: Backtest['status']) => {
    switch (status) {
      case 'running':
        return <Play className="h-4 w-4 text-green-600" />;
      case 'pending':
        return <Clock className="h-4 w-4 text-yellow-600" />;
      default:
        return <Square className="h-4 w-4 text-gray-600" />;
    }
  };

  const getEstimatedCompletion = (backtest: Backtest) => {
    if (backtest.status === 'pending') return 'Queued';
    if (backtest.status === 'running') {
      const progress = getProgress(backtest);
      if (progress < 10) return 'Starting...';
      const remaining = Math.round((100 - progress) * 3); // Mock: ~3 seconds per percent
      if (remaining < 60) return `~${remaining}s`;
      return `~${Math.round(remaining / 60)}m`;
    }
    return 'Complete';
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>
          Active Backtests
          {backtests.length > 0 && (
            <Badge variant="secondary" className="ml-2">
              {backtests.length}
            </Badge>
          )}
        </CardTitle>
        <Button variant="outline" size="sm">
          <ExternalLink className="h-4 w-4 mr-2" />
          View Queue
        </Button>
      </CardHeader>
      <CardContent>
        {backtests.length === 0 ? (
          <div className="text-center text-muted-foreground py-8">
            <Play className="h-8 w-8 mx-auto mb-2 opacity-50" />
            <p>No active backtests</p>
            <Button variant="outline" size="sm" className="mt-2">
              Start New Backtest
            </Button>
          </div>
        ) : (
          <div className="space-y-4">
            {/* Running Backtests */}
            {runningBacktests.map((backtest) => (
              <div
                key={backtest.id}
                className="p-4 bg-green-50/50 border border-green-200 rounded-lg"
              >
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center space-x-2">
                    {getStatusIcon(backtest.status)}
                    <div>
                      <div className="font-medium text-sm">
                        {backtest.strategy_id}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        Started {formatDistanceToNow(new Date(backtest.created_at), { 
                          addSuffix: true 
                        })}
                      </div>
                    </div>
                  </div>
                  <Badge variant="secondary">
                    {backtest.status}
                  </Badge>
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between text-xs">
                    <span>Progress</span>
                    <span>{getProgress(backtest)}%</span>
                  </div>
                  <Progress value={getProgress(backtest)} className="h-2" />
                  <div className="flex justify-between text-xs text-muted-foreground">
                    <span>ETA: {getEstimatedCompletion(backtest)}</span>
                    <Button variant="ghost" size="sm">
                      <ExternalLink className="h-3 w-3" />
                    </Button>
                  </div>
                </div>
              </div>
            ))}

            {/* Pending Backtests */}
            {pendingBacktests.map((backtest) => (
              <div
                key={backtest.id}
                className="p-4 bg-yellow-50/50 border border-yellow-200 rounded-lg"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    {getStatusIcon(backtest.status)}
                    <div>
                      <div className="font-medium text-sm">
                        {backtest.strategy_id}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        Queued {formatDistanceToNow(new Date(backtest.created_at), { 
                          addSuffix: true 
                        })}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Badge variant="outline">
                      {backtest.status}
                    </Badge>
                    <Button variant="ghost" size="sm">
                      <ExternalLink className="h-3 w-3" />
                    </Button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}