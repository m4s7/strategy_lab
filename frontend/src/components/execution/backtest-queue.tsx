"use client";

import React, { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Play,
  Pause,
  Square,
  MoreVertical,
  ChevronUp,
  ChevronDown,
  Clock,
  AlertCircle,
} from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { ExecutionStatus } from "./backtest-execution-control";

interface QueuedBacktest {
  id: string;
  configurationId: string;
  strategyName: string;
  status: ExecutionStatus;
  priority: number;
  queuePosition: number;
  estimatedStartTime?: string;
  startTime?: string;
  progress?: number;
  error?: string;
}

interface BacktestQueueProps {
  onSelectBacktest?: (id: string) => void;
}

export function BacktestQueue({ onSelectBacktest }: BacktestQueueProps) {
  const [queue, setQueue] = useState<QueuedBacktest[]>([]);
  const [selectedJobs, setSelectedJobs] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchQueue();
    const interval = setInterval(fetchQueue, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchQueue = async () => {
    try {
      const response = await fetch("/api/backtests/queue");
      if (response.ok) {
        const data = await response.json();
        setQueue(data);
      }
    } catch (error) {
      console.error("Failed to fetch queue:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleBulkCancel = async () => {
    if (!confirm(`Cancel ${selectedJobs.length} selected backtests?`)) return;

    try {
      await Promise.all(
        selectedJobs.map((id) =>
          fetch(`/api/backtests/${id}/cancel`, { method: "POST" })
        )
      );
      setSelectedJobs([]);
      fetchQueue();
    } catch (error) {
      console.error("Failed to cancel backtests:", error);
    }
  };

  const handlePriorityChange = async (jobId: string, priority: number) => {
    try {
      await fetch(`/api/backtests/${jobId}/priority`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ priority }),
      });
      fetchQueue();
    } catch (error) {
      console.error("Failed to update priority:", error);
    }
  };

  const handleAction = async (jobId: string, action: string) => {
    try {
      await fetch(`/api/backtests/${jobId}/${action}`, { method: "POST" });
      fetchQueue();
    } catch (error) {
      console.error(`Failed to ${action} backtest:`, error);
    }
  };

  const toggleJobSelection = (jobId: string) => {
    setSelectedJobs((prev) =>
      prev.includes(jobId)
        ? prev.filter((id) => id !== jobId)
        : [...prev, jobId]
    );
  };

  const selectAll = () => {
    if (selectedJobs.length === queue.length) {
      setSelectedJobs([]);
    } else {
      setSelectedJobs(queue.map((job) => job.id));
    }
  };

  const getStatusIcon = (status: ExecutionStatus) => {
    switch (status) {
      case ExecutionStatus.PROCESSING:
        return <Play className="h-3 w-3" />;
      case ExecutionStatus.PAUSED:
        return <Pause className="h-3 w-3" />;
      case ExecutionStatus.QUEUED:
        return <Clock className="h-3 w-3" />;
      case ExecutionStatus.FAILED:
        return <AlertCircle className="h-3 w-3" />;
      default:
        return null;
    }
  };

  const getStatusColor = (status: ExecutionStatus) => {
    switch (status) {
      case ExecutionStatus.PROCESSING:
        return "default";
      case ExecutionStatus.PAUSED:
        return "secondary";
      case ExecutionStatus.QUEUED:
        return "outline";
      case ExecutionStatus.FAILED:
        return "destructive";
      default:
        return "outline";
    }
  };

  const runningCount = queue.filter(
    (j) => j.status === ExecutionStatus.PROCESSING
  ).length;
  const queuedCount = queue.filter(
    (j) => j.status === ExecutionStatus.QUEUED
  ).length;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Execution Queue</CardTitle>
            <p className="text-sm text-muted-foreground mt-1">
              {runningCount} running, {queuedCount} queued
            </p>
          </div>
          <div className="flex gap-2">
            {selectedJobs.length > 0 && (
              <>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setSelectedJobs([])}
                >
                  Clear Selection
                </Button>
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={handleBulkCancel}
                >
                  Cancel {selectedJobs.length} Selected
                </Button>
              </>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        ) : queue.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            No backtests in queue
          </div>
        ) : (
          <ScrollArea className="h-[400px]">
            <div className="space-y-2">
              <div className="flex items-center gap-2 pb-2 border-b">
                <Checkbox
                  checked={
                    selectedJobs.length === queue.length && queue.length > 0
                  }
                  onCheckedChange={selectAll}
                />
                <span className="text-sm font-medium">Select All</span>
              </div>

              {queue.map((job) => (
                <div
                  key={job.id}
                  className="flex items-center gap-3 p-3 rounded-lg border hover:bg-accent/50 transition-colors"
                >
                  <Checkbox
                    checked={selectedJobs.includes(job.id)}
                    onCheckedChange={() => toggleJobSelection(job.id)}
                  />

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <Badge variant={getStatusColor(job.status)}>
                        {getStatusIcon(job.status)}
                        <span className="ml-1">{job.status}</span>
                      </Badge>
                      <span className="font-medium truncate">
                        {job.strategyName}
                      </span>
                    </div>
                    <div className="flex items-center gap-4 mt-1 text-xs text-muted-foreground">
                      <span>Position: #{job.queuePosition}</span>
                      <span>Priority: {job.priority}</span>
                      {job.startTime && (
                        <span>
                          Started{" "}
                          {formatDistanceToNow(new Date(job.startTime), {
                            addSuffix: true,
                          })}
                        </span>
                      )}
                      {job.estimatedStartTime &&
                        job.status === ExecutionStatus.QUEUED && (
                          <span>
                            Est. start:{" "}
                            {formatDistanceToNow(
                              new Date(job.estimatedStartTime),
                              { addSuffix: true }
                            )}
                          </span>
                        )}
                      {job.progress !== undefined && (
                        <span>{job.progress.toFixed(1)}%</span>
                      )}
                    </div>
                    {job.error && (
                      <p className="text-xs text-destructive mt-1">
                        {job.error}
                      </p>
                    )}
                  </div>

                  <div className="flex items-center gap-2">
                    <div className="flex items-center gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() =>
                          handlePriorityChange(
                            job.id,
                            Math.min(job.priority + 1, 10)
                          )
                        }
                        disabled={job.status !== ExecutionStatus.QUEUED}
                      >
                        <ChevronUp className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() =>
                          handlePriorityChange(
                            job.id,
                            Math.max(job.priority - 1, 1)
                          )
                        }
                        disabled={job.status !== ExecutionStatus.QUEUED}
                      >
                        <ChevronDown className="h-4 w-4" />
                      </Button>
                    </div>

                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="sm">
                          <MoreVertical className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        {job.status === ExecutionStatus.PROCESSING && (
                          <DropdownMenuItem
                            onClick={() => handleAction(job.id, "pause")}
                          >
                            <Pause className="mr-2 h-4 w-4" />
                            Pause
                          </DropdownMenuItem>
                        )}
                        {job.status === ExecutionStatus.PAUSED && (
                          <DropdownMenuItem
                            onClick={() => handleAction(job.id, "resume")}
                          >
                            <Play className="mr-2 h-4 w-4" />
                            Resume
                          </DropdownMenuItem>
                        )}
                        <DropdownMenuItem
                          onClick={() => handleAction(job.id, "cancel")}
                          className="text-destructive"
                        >
                          <Square className="mr-2 h-4 w-4" />
                          Cancel
                        </DropdownMenuItem>
                        {onSelectBacktest && (
                          <DropdownMenuItem
                            onClick={() => onSelectBacktest(job.id)}
                          >
                            View Details
                          </DropdownMenuItem>
                        )}
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </div>
              ))}
            </div>
          </ScrollArea>
        )}
      </CardContent>
    </Card>
  );
}
