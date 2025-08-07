import { useState, useEffect } from 'react';
import { useWebSocket } from '../lib/websocket/client';

export interface Backtest {
  id: string;
  strategy_id: string;
  config: Record<string, any>;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  error_message?: string;
  created_at: string;
  updated_at: string;
}

export const useRecentBacktests = (limit = 10) => {
  const [backtests, setBacktests] = useState<Backtest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const { subscribe, unsubscribe } = useWebSocket();

  const fetchRecentBacktests = async () => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/backtests/recent?limit=${limit}`
      );
      if (!response.ok) throw new Error('Failed to fetch recent backtests');
      const data = await response.json();
      setBacktests(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    }
  };

  useEffect(() => {
    const loadInitialData = async () => {
      setLoading(true);
      await fetchRecentBacktests();
      setLoading(false);
    };

    loadInitialData();

    // Set up real-time updates
    const handleBacktestUpdate = (data: any) => {
      if (data.type === 'backtest_created' || data.type === 'backtest_updated') {
        // Refetch recent backtests when there are updates
        fetchRecentBacktests();
      }
    };

    subscribe('backtest:all', handleBacktestUpdate);

    return () => {
      unsubscribe('backtest:all');
    };
  }, [limit, subscribe, unsubscribe]);

  return {
    backtests,
    loading,
    error,
    refresh: fetchRecentBacktests
  };
};

export const useActiveBacktests = () => {
  const [backtests, setBacktests] = useState<Backtest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const { subscribe, unsubscribe } = useWebSocket();

  const fetchActiveBacktests = async () => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/backtests/active`
      );
      if (!response.ok) throw new Error('Failed to fetch active backtests');
      const data = await response.json();
      setBacktests(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    }
  };

  useEffect(() => {
    const loadInitialData = async () => {
      setLoading(true);
      await fetchActiveBacktests();
      setLoading(false);
    };

    loadInitialData();

    // Set up real-time updates for active backtests
    const handleBacktestUpdate = (data: any) => {
      if (data.type === 'backtest_updated' || data.type === 'backtest_progress') {
        fetchActiveBacktests();
      }
    };

    subscribe('backtest:active', handleBacktestUpdate);

    // Refresh active backtests more frequently
    const interval = setInterval(fetchActiveBacktests, 10000);

    return () => {
      unsubscribe('backtest:active');
      clearInterval(interval);
    };
  }, [subscribe, unsubscribe]);

  return {
    backtests,
    loading,
    error,
    refresh: fetchActiveBacktests
  };
};