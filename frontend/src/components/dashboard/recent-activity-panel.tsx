'use client';

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Clock, ExternalLink, TrendingUp, TrendingDown } from "lucide-react";
import { useRecentBacktests, type Backtest } from "@/hooks/useBacktests";
import { formatDistanceToNow } from "date-fns";

export function RecentActivityPanel() {
  const { backtests, loading, error } = useRecentBacktests();

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {Array.from({ length: 5 }, (_, i) => (
              <div key={i} className="animate-pulse">
                <div className="h-16 bg-muted rounded-lg"></div>
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
          <CardTitle>Recent Activity</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center text-muted-foreground py-8">
            Failed to load recent activity
          </div>
        </CardContent>
      </Card>
    );
  }

  const getStatusBadgeVariant = (status: Backtest['status']) => {
    switch (status) {
      case 'completed':
        return 'default';
      case 'running':
        return 'secondary';
      case 'failed':
        return 'destructive';
      case 'pending':
        return 'outline';
      case 'cancelled':
        return 'secondary';
      default:
        return 'outline';
    }
  };

  const getStatusIcon = (status: Backtest['status']) => {
    switch (status) {
      case 'completed':
        return <TrendingUp className="h-4 w-4 text-green-600" />;
      case 'failed':
        return <TrendingDown className="h-4 w-4 text-red-600" />;
      default:
        return <Clock className="h-4 w-4 text-blue-600" />;
    }
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Recent Activity</CardTitle>
        <Button variant="outline" size="sm">
          <ExternalLink className="h-4 w-4 mr-2" />
          View All
        </Button>
      </CardHeader>
      <CardContent>
        {backtests.length === 0 ? (
          <div className="text-center text-muted-foreground py-8">
            No recent backtests found
          </div>
        ) : (
          <div className="space-y-4">
            {backtests.map((backtest) => (
              <div
                key={backtest.id}
                className="flex items-center justify-between p-3 bg-muted/50 rounded-lg"
              >
                <div className="flex items-center space-x-3">
                  {getStatusIcon(backtest.status)}
                  <div>
                    <div className="font-medium text-sm">
                      {backtest.strategy_id}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {formatDistanceToNow(new Date(backtest.created_at), { 
                        addSuffix: true 
                      })}
                    </div>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <Badge variant={getStatusBadgeVariant(backtest.status)}>
                    {backtest.status}
                  </Badge>
                  <Button variant="ghost" size="sm">
                    <ExternalLink className="h-3 w-3" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}