'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { 
  Clock, 
  Zap, 
  TrendingUp, 
  TrendingDown, 
  Activity,
  Calculator
} from "lucide-react";
import { formatDistanceToNow, differenceInMilliseconds, addMilliseconds } from "date-fns";

interface PerformanceMetricsProps {
  eventsProcessed: number;
  totalEvents: number;
  eventsPerSecond: number;
  startTime: string;
  currentTime?: string;
  estimatedEndTime?: string;
}

export function PerformanceMetrics({
  eventsProcessed,
  totalEvents,
  eventsPerSecond,
  startTime,
  currentTime,
  estimatedEndTime
}: PerformanceMetricsProps) {
  
  const calculateETA = () => {
    if (eventsPerSecond === 0) return null;
    
    const remaining = totalEvents - eventsProcessed;
    const secondsRemaining = remaining / eventsPerSecond;
    
    if (secondsRemaining <= 0) return null;
    
    const estimatedEnd = addMilliseconds(new Date(), secondsRemaining * 1000);
    return estimatedEnd;
  };

  const getPerformanceRating = (eps: number) => {
    if (eps >= 10000) return { label: 'Excellent', color: 'bg-green-500', text: 'text-green-600' };
    if (eps >= 5000) return { label: 'Good', color: 'bg-blue-500', text: 'text-blue-600' };
    if (eps >= 1000) return { label: 'Fair', color: 'bg-yellow-500', text: 'text-yellow-600' };
    return { label: 'Slow', color: 'bg-red-500', text: 'text-red-600' };
  };

  const getProgressColor = (percentage: number) => {
    if (percentage >= 90) return 'bg-green-500';
    if (percentage >= 50) return 'bg-blue-500';
    if (percentage >= 25) return 'bg-yellow-500';
    return 'bg-gray-500';
  };

  const formatNumber = (num: number) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toLocaleString();
  };

  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${seconds.toFixed(0)}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${(seconds % 60).toFixed(0)}s`;
    return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
  };

  const progress = totalEvents > 0 ? (eventsProcessed / totalEvents) * 100 : 0;
  const eta = calculateETA();
  const runtime = differenceInMilliseconds(new Date(), new Date(startTime)) / 1000;
  const performanceRating = getPerformanceRating(eventsPerSecond);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <Activity className="h-5 w-5" />
          <span>Performance Metrics</span>
        </CardTitle>
        <CardDescription>
          Real-time execution performance and timing estimates
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Progress Overview */}
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span>Overall Progress</span>
            <span className="font-medium">{progress.toFixed(1)}%</span>
          </div>
          <Progress value={progress} className="h-3" />
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>{formatNumber(eventsProcessed)} / {formatNumber(totalEvents)} events</span>
            {eta && (
              <span>ETA: {formatDistanceToNow(eta, { addSuffix: true })}</span>
            )}
          </div>
        </div>

        {/* Performance Metrics Grid */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <div className="text-center p-3 bg-muted/30 rounded-lg">
            <div className="flex items-center justify-center space-x-1 mb-1">
              <Zap className="h-4 w-4 text-blue-600" />
              <span className="text-xs text-muted-foreground">Speed</span>
            </div>
            <div className={`text-lg font-medium ${performanceRating.text}`}>
              {formatNumber(eventsPerSecond)}/sec
            </div>
            <Badge 
              className={`${performanceRating.color} text-white text-xs mt-1`}
            >
              {performanceRating.label}
            </Badge>
          </div>

          <div className="text-center p-3 bg-muted/30 rounded-lg">
            <div className="flex items-center justify-center space-x-1 mb-1">
              <Clock className="h-4 w-4 text-green-600" />
              <span className="text-xs text-muted-foreground">Runtime</span>
            </div>
            <div className="text-lg font-medium">
              {formatDuration(runtime)}
            </div>
            <div className="text-xs text-muted-foreground mt-1">
              Since {new Date(startTime).toLocaleTimeString()}
            </div>
          </div>

          {eta && (
            <div className="text-center p-3 bg-muted/30 rounded-lg">
              <div className="flex items-center justify-center space-x-1 mb-1">
                <Calculator className="h-4 w-4 text-purple-600" />
                <span className="text-xs text-muted-foreground">ETA</span>
              </div>
              <div className="text-lg font-medium">
                {formatDistanceToNow(eta, { addSuffix: false })}
              </div>
              <div className="text-xs text-muted-foreground mt-1">
                {eta.toLocaleTimeString()}
              </div>
            </div>
          )}

          <div className="text-center p-3 bg-muted/30 rounded-lg">
            <div className="flex items-center justify-center space-x-1 mb-1">
              <TrendingUp className="h-4 w-4 text-orange-600" />
              <span className="text-xs text-muted-foreground">Remaining</span>
            </div>
            <div className="text-lg font-medium">
              {formatNumber(totalEvents - eventsProcessed)}
            </div>
            <div className="text-xs text-muted-foreground mt-1">
              events left
            </div>
          </div>
        </div>

        {/* Detailed Timing Information */}
        <div className="pt-2 border-t space-y-2">
          <h4 className="text-sm font-medium">Timing Details</h4>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Average per event:</span>
              <span className="font-mono">
                {eventsPerSecond > 0 ? (1000 / eventsPerSecond).toFixed(2) : '0'}ms
              </span>
            </div>
            
            <div className="flex justify-between">
              <span className="text-muted-foreground">Completion rate:</span>
              <span className="font-mono">
                {totalEvents > 0 ? ((eventsProcessed / totalEvents) * 100).toFixed(2) : '0'}%
              </span>
            </div>
            
            {currentTime && (
              <div className="flex justify-between">
                <span className="text-muted-foreground">Current time:</span>
                <span className="font-mono">{currentTime}</span>
              </div>
            )}
            
            {eta && (
              <div className="flex justify-between">
                <span className="text-muted-foreground">Estimated finish:</span>
                <span className="font-mono">{eta.toLocaleString()}</span>
              </div>
            )}
          </div>
        </div>

        {/* Performance Insights */}
        {eventsPerSecond > 0 && (
          <div className="pt-2 border-t">
            <h4 className="text-sm font-medium mb-2">Performance Insights</h4>
            <div className="text-xs text-muted-foreground space-y-1">
              {eventsPerSecond < 1000 && (
                <p>• Processing speed is below optimal. Consider reducing concurrent backtests.</p>
              )}
              {progress > 50 && eta && (
                <p>• More than halfway complete. Estimated completion: {formatDistanceToNow(eta, { addSuffix: true })}</p>
              )}
              {eventsPerSecond > 10000 && (
                <p>• Excellent processing speed! System is performing optimally.</p>
              )}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}