import { useState, useEffect } from "react";
import { API_URL } from "../lib/config";

export interface EquityPoint {
  timestamp: string;
  equity: number;
  drawdown_pct: number;
  trade_pnl: number;
}

export interface TradeSummary {
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  largest_win: number;
  largest_loss: number;
  average_win: number;
  average_loss: number;
  average_trade: number;
  win_rate: number;
  profit_factor: number;
  consecutive_wins: number;
  consecutive_losses: number;
  avg_trade_duration_minutes: number;
}

export interface PerformanceMetrics {
  total_return: number;
  total_return_pct: number;
  sharpe_ratio: number;
  sortino_ratio: number;
  calmar_ratio: number;
  max_drawdown: number;
  max_drawdown_pct: number;
  volatility: number;
  var_95: number;
  cvar_95: number;
  beta?: number;
  alpha?: number;
  information_ratio?: number;
}

export interface PerformanceStatistics {
  returns: Record<string, number>;
  risk_metrics: Record<string, number>;
  trade_metrics: Record<string, number>;
  time_metrics: Record<string, number>;
}

export interface BacktestResult {
  id: string;
  backtest_id: string;
  start_date: string;
  end_date: string;
  strategy_name: string;
  initial_capital: number;
  final_capital: number;
  configuration: Record<string, any>;
  metrics: PerformanceMetrics;
  equity_curve: EquityPoint[];
  trade_summary: TradeSummary;
  statistics: PerformanceStatistics;
  created_at: string;
  execution_time_seconds: number;
}

export interface ResultSummary {
  id: string;
  backtest_id: string;
  strategy_name: string;
  start_date: string;
  end_date: string;
  total_return_pct: number;
  sharpe_ratio: number;
  max_drawdown_pct: number;
  total_trades: number;
  win_rate: number;
  created_at: string;
}

export const useResults = () => {
  const [results, setResults] = useState<ResultSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchResults = async () => {
      try {
        const response = await fetch(`${API_URL}/v1/results`);
        if (!response.ok) throw new Error("Failed to fetch results");
        const data = await response.json();
        setResults(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error");
      } finally {
        setLoading(false);
      }
    };

    fetchResults();
  }, []);

  return { results, loading, error, refresh: () => window.location.reload() };
};

export const useResult = (resultId: string) => {
  const [result, setResult] = useState<BacktestResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!resultId) {
      setLoading(false);
      return;
    }

    const fetchResult = async () => {
      try {
        const response = await fetch(`${API_URL}/v1/results/${resultId}`);
        if (!response.ok) {
          if (response.status === 404) {
            throw new Error("Result not found");
          }
          throw new Error("Failed to fetch result details");
        }
        const data = await response.json();
        setResult(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error");
      } finally {
        setLoading(false);
      }
    };

    fetchResult();
  }, [resultId]);

  const exportResult = async (format: "csv" | "json" | "pdf") => {
    if (!resultId) return;

    try {
      const response = await fetch(
        `${API_URL}/v1/results/${resultId}/export/${format}`
      );
      if (!response.ok) throw new Error("Failed to export result");

      const data = await response.json();

      if (format === "json") {
        // Download JSON
        const blob = new Blob([JSON.stringify(data, null, 2)], {
          type: "application/json",
        });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `${result?.strategy_name}_${resultId}.json`;
        a.click();
        URL.revokeObjectURL(url);
      } else {
        // Handle CSV and PDF exports (mock for now)
        console.log(`Exported ${format}:`, data);
      }
    } catch (err) {
      throw new Error(err instanceof Error ? err.message : "Failed to export");
    }
  };

  const generateMockResult = async (executionId: string) => {
    try {
      const response = await fetch(
        `${API_URL}/v1/results/generate/${executionId}`,
        { method: "POST" }
      );
      if (!response.ok) throw new Error("Failed to generate result");
      return await response.json();
    } catch (err) {
      throw new Error(
        err instanceof Error ? err.message : "Failed to generate result"
      );
    }
  };

  return {
    result,
    loading,
    error,
    exportResult,
    generateMockResult,
  };
};
