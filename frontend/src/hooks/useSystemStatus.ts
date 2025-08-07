import { useState, useEffect } from "react";
import { useWebSocket } from "../lib/websocket/client";

interface SystemMetrics {
  cpu: number;
  memory: {
    used_percent: number;
    available_gb: number;
    total_gb: number;
  };
  disk: {
    used_percent: number;
    free_gb: number;
    total_gb: number;
  };
  database: "healthy" | "warning" | "error";
  websocket: "connected" | "disconnected";
  uptime: number;
  timestamp: string;
}

interface SystemStats {
  today: {
    backtests_run: number;
    success_rate: number;
    average_duration: number;
    completed: number;
    failed: number;
  };
  performance: {
    average_response_time: number;
    uptime: number;
    requests_per_minute: number;
  };
  data: {
    records_processed: number;
    processing_speed: number;
    last_update: string;
  };
}

export const useSystemStatus = () => {
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const { connectionStatus, subscribe, unsubscribe } = useWebSocket();

  const fetchSystemStatus = async () => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/system/status`
      );
      if (!response.ok) throw new Error("Failed to fetch system status");
      const data = await response.json();
      setMetrics(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    }
  };

  const fetchSystemStats = async () => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/system/stats`
      );
      if (!response.ok) throw new Error("Failed to fetch system stats");
      const data = await response.json();
      setStats(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    }
  };

  useEffect(() => {
    const loadInitialData = async () => {
      setLoading(true);
      await Promise.all([fetchSystemStatus(), fetchSystemStats()]);
      setLoading(false);
    };

    loadInitialData();

    // Set up real-time updates
    const handleSystemUpdate = (data: any) => {
      if (data.type === "system_status") {
        setMetrics(data.payload);
      } else if (data.type === "system_stats") {
        setStats(data.payload);
      }
    };

    subscribe("system:status", handleSystemUpdate);
    subscribe("system:stats", handleSystemUpdate);

    // Fallback polling every 30 seconds
    const interval = setInterval(() => {
      fetchSystemStatus();
      fetchSystemStats();
    }, 30000);

    return () => {
      unsubscribe("system:status");
      unsubscribe("system:stats");
      clearInterval(interval);
    };
  }, [subscribe, unsubscribe]);

  return {
    metrics,
    stats,
    loading,
    error,
    connectionStatus,
    refresh: () => {
      fetchSystemStatus();
      fetchSystemStats();
    },
  };
};
