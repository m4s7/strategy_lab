import { useState, useEffect } from "react";
import { useWebSocket } from "../lib/websocket/client";
import { API_URL } from "../lib/config";

export interface ExecutionProgress {
  percentage: number;
  current_tick: number;
  total_ticks: number;
  processed_trades: number;
  current_date?: string;
  stage: string;
  stage_progress: number;
}

export interface ResourceUsage {
  cpu_percent: number;
  memory_mb: number;
  peak_memory_mb: number;
  disk_io_mb: number;
}

export interface ExecutionError {
  timestamp: string;
  severity: string;
  message: string;
  details?: string;
  recoverable: boolean;
}

export interface BacktestMetrics {
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  total_pnl: number;
  max_drawdown: number;
  sharpe_ratio?: number;
  current_equity: number;
  last_trade_time?: string;
}

export interface BacktestExecution {
  id: string;
  backtest_id: string;
  status: string;
  progress: ExecutionProgress;
  start_time: string;
  end_time?: string;
  estimated_end_time?: string;
  current_stage: string;
  metrics: BacktestMetrics;
  resource_usage: ResourceUsage;
  errors: ExecutionError[];
  configuration: Record<string, any>;
}

export interface ExecutionRequest {
  strategy_id: string;
  strategy_parameters: Record<string, any>;
  data_configuration: Record<string, any>;
  priority?: number;
}

export const useBacktestExecution = () => {
  const [executions, setExecutions] = useState<BacktestExecution[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { subscribe, unsubscribe } = useWebSocket();

  const fetchExecutions = async () => {
    try {
      const response = await fetch(`${API_URL}/v1/execution`);
      if (!response.ok) throw new Error("Failed to fetch executions");
      const data = await response.json();
      setExecutions(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    }
  };

  const startExecution = async (request: ExecutionRequest) => {
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/v1/execution/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(request),
      });

      if (!response.ok) throw new Error("Failed to start execution");

      const result = await response.json();
      await fetchExecutions(); // Refresh list
      return result;
    } catch (err) {
      throw new Error(
        err instanceof Error ? err.message : "Failed to start execution"
      );
    } finally {
      setLoading(false);
    }
  };

  const controlExecution = async (
    executionId: string,
    action: string,
    priority?: number
  ) => {
    try {
      const response = await fetch(
        `${API_URL}/v1/execution/${executionId}/control`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ action, priority }),
        }
      );

      if (!response.ok) throw new Error("Failed to control execution");

      await fetchExecutions(); // Refresh list
      return await response.json();
    } catch (err) {
      throw new Error(
        err instanceof Error ? err.message : "Failed to control execution"
      );
    }
  };

  const deleteExecution = async (executionId: string) => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/execution/${executionId}`,
        { method: "DELETE" }
      );

      if (!response.ok) throw new Error("Failed to delete execution");

      await fetchExecutions(); // Refresh list
    } catch (err) {
      throw new Error(
        err instanceof Error ? err.message : "Failed to delete execution"
      );
    }
  };

  useEffect(() => {
    fetchExecutions();

    // Set up real-time updates
    const handleExecutionUpdate = (data: any) => {
      if (
        data.type === "execution_progress" ||
        data.type === "execution_status"
      ) {
        fetchExecutions(); // Refresh on updates
      }
    };

    subscribe("execution:all", handleExecutionUpdate);

    // Refresh every 5 seconds for active executions
    const interval = setInterval(() => {
      const hasActive = executions.some((e) =>
        [
          "queued",
          "initializing",
          "loading_data",
          "processing",
          "calculating_metrics",
        ].includes(e.status)
      );
      if (hasActive) {
        fetchExecutions();
      }
    }, 5000);

    return () => {
      unsubscribe("execution:all");
      clearInterval(interval);
    };
  }, [subscribe, unsubscribe, executions]);

  return {
    executions,
    loading,
    error,
    startExecution,
    controlExecution,
    deleteExecution,
    refresh: fetchExecutions,
  };
};
