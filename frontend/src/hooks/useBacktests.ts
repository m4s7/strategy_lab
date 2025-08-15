import { useState, useEffect } from "react";
import { useWebSocketSubscription } from "../lib/websocket/hooks";
import { API_URL } from "../lib/config";

export interface Backtest {
  id: string;
  strategy_id: string;
  config: Record<string, any>;
  status: "pending" | "running" | "completed" | "failed" | "cancelled";
  error_message?: string;
  created_at: string;
  updated_at: string;
}

export const useRecentBacktests = (limit = 10) => {
  const [backtests, setBacktests] = useState<Backtest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Use WebSocket subscription for real-time updates
  const { data: wsBacktestUpdates } = useWebSocketSubscription("backtest:all");

  const fetchRecentBacktests = async () => {
    try {
      const response = await fetch(
        `${API_URL}/v1/backtests/recent?limit=${limit}`
      );
      if (!response.ok) throw new Error("Failed to fetch recent backtests");
      const data = await response.json();
      setBacktests(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    }
  };

  useEffect(() => {
    const loadInitialData = async () => {
      setLoading(true);
      await fetchRecentBacktests();
      setLoading(false);
    };

    loadInitialData();
  }, [limit]);

  // Handle WebSocket updates
  useEffect(() => {
    if (wsBacktestUpdates) {
      // Refetch when we get WebSocket updates
      fetchRecentBacktests();
    }
  }, [wsBacktestUpdates]);

  return {
    backtests,
    loading,
    error,
    refresh: fetchRecentBacktests,
  };
};

export const useActiveBacktests = () => {
  const [backtests, setBacktests] = useState<Backtest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Use WebSocket subscription for real-time updates
  const { data: wsActiveUpdates } = useWebSocketSubscription("backtest:active");

  const fetchActiveBacktests = async () => {
    try {
      const response = await fetch(`${API_URL}/v1/backtests/active`);
      if (!response.ok) throw new Error("Failed to fetch active backtests");
      const data = await response.json();
      setBacktests(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    }
  };

  useEffect(() => {
    const loadInitialData = async () => {
      setLoading(true);
      await fetchActiveBacktests();
      setLoading(false);
    };

    loadInitialData();

    // Refresh active backtests more frequently
    const interval = setInterval(fetchActiveBacktests, 10000);

    return () => {
      clearInterval(interval);
    };
  }, []);

  // Handle WebSocket updates
  useEffect(() => {
    if (wsActiveUpdates) {
      fetchActiveBacktests();
    }
  }, [wsActiveUpdates]);

  return {
    backtests,
    loading,
    error,
    refresh: fetchActiveBacktests,
  };
};
