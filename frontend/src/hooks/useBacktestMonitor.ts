"use client";

import { useState, useEffect, useCallback } from "react";
import {
  useWebSocketSubscription,
  useWebSocketMultiSubscription,
} from "@/lib/websocket/hooks";
import { BacktestMonitorData } from "@/components/monitoring/backtest-monitor";

export interface MonitorState {
  [backtestId: string]: BacktestMonitorData;
}

export function useBacktestMonitor() {
  const [monitors, setMonitors] = useState<MonitorState>({});
  const [subscriptions, setSubscriptions] = useState<string[]>([]);

  // Subscribe to all active backtests updates
  const { data: allBacktestsData } = useWebSocketSubscription<{
    active_backtests: string[];
  }>("backtest:all_active");

  // Multi-subscription for individual backtest monitors
  const { data: monitorData } =
    useWebSocketMultiSubscription<BacktestMonitorData>(
      subscriptions.map((id) => `backtest:${id}:monitor`)
    );

  // Restore monitoring state from localStorage on mount
  useEffect(() => {
    const savedState = localStorage.getItem("backtest_monitors");
    if (savedState) {
      try {
        const parsed = JSON.parse(savedState);
        const activeMonitors: MonitorState = {};

        // Only restore running/paused backtests
        Object.entries(parsed).forEach(([id, monitor]) => {
          const monitorData = monitor as BacktestMonitorData;
          if (
            monitorData.status === "running" ||
            monitorData.status === "paused"
          ) {
            activeMonitors[id] = monitorData;
          }
        });

        if (Object.keys(activeMonitors).length > 0) {
          setMonitors(activeMonitors);
          setSubscriptions(Object.keys(activeMonitors));
        }
      } catch (error) {
        console.error("Failed to restore monitor state:", error);
        localStorage.removeItem("backtest_monitors");
      }
    }
  }, []);

  // Update subscriptions when active backtests change
  useEffect(() => {
    if (allBacktestsData?.active_backtests) {
      const activeIds = allBacktestsData.active_backtests;
      setSubscriptions(activeIds);
    }
  }, [allBacktestsData]);

  // Update monitors when individual data comes in
  useEffect(() => {
    if (monitorData) {
      setMonitors((prev) => {
        const updated = { ...prev };

        Object.entries(monitorData).forEach(([topicKey, data]) => {
          // Extract backtest ID from topic key like "backtest:123:monitor"
          const match = topicKey.match(/^backtest:([^:]+):monitor$/);
          if (match && data) {
            const backtestId = match[1];
            updated[backtestId] = data;
          }
        });

        return updated;
      });
    }
  }, [monitorData]);

  // Save state whenever monitors change
  useEffect(() => {
    if (Object.keys(monitors).length > 0) {
      localStorage.setItem("backtest_monitors", JSON.stringify(monitors));
    }
  }, [monitors]);

  // Add a monitor manually
  const addMonitor = useCallback(
    (backtestId: string, initialData?: BacktestMonitorData) => {
      if (initialData) {
        setMonitors((prev) => ({ ...prev, [backtestId]: initialData }));
      }

      setSubscriptions((prev) => {
        if (!prev.includes(backtestId)) {
          return [...prev, backtestId];
        }
        return prev;
      });
    },
    []
  );

  // Remove a monitor
  const removeMonitor = useCallback((backtestId: string) => {
    setMonitors((prev) => {
      const updated = { ...prev };
      delete updated[backtestId];
      return updated;
    });

    setSubscriptions((prev) => prev.filter((id) => id !== backtestId));

    // Clean up localStorage
    const saved = localStorage.getItem("backtest_monitors");
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        delete parsed[backtestId];
        localStorage.setItem("backtest_monitors", JSON.stringify(parsed));
      } catch (error) {
        console.error("Failed to update saved state:", error);
      }
    }
  }, []);

  // Update monitor data manually
  const updateMonitor = useCallback(
    (backtestId: string, updates: Partial<BacktestMonitorData>) => {
      setMonitors((prev) => ({
        ...prev,
        [backtestId]: {
          ...prev[backtestId],
          ...updates,
        } as BacktestMonitorData,
      }));
    },
    []
  );

  // Get monitors by status
  const getMonitorsByStatus = useCallback(
    (status: BacktestMonitorData["status"]) => {
      return Object.entries(monitors)
        .filter(([, monitor]) => monitor.status === status)
        .map(([id, monitor]) => ({ id, ...monitor }));
    },
    [monitors]
  );

  // Get active monitors (running or paused)
  const activeMonitors = useCallback(() => {
    return Object.entries(monitors)
      .filter(
        ([, monitor]) =>
          monitor.status === "running" || monitor.status === "paused"
      )
      .map(([id, monitor]) => ({ id, ...monitor }));
  }, [monitors]);

  // Clear completed monitors
  const clearCompleted = useCallback(() => {
    setMonitors((prev) => {
      const updated: MonitorState = {};
      Object.entries(prev).forEach(([id, monitor]) => {
        if (
          monitor.status !== "completed" &&
          monitor.status !== "aborted" &&
          monitor.status !== "failed"
        ) {
          updated[id] = monitor;
        }
      });
      return updated;
    });

    // Update subscriptions
    setSubscriptions((prev) =>
      prev.filter((id) => {
        const monitor = monitors[id];
        return (
          monitor &&
          monitor.status !== "completed" &&
          monitor.status !== "aborted" &&
          monitor.status !== "failed"
        );
      })
    );
  }, [monitors]);

  // Control functions that would interact with backend
  const abortBacktest = useCallback(
    async (backtestId: string) => {
      try {
        // This would be an actual API call
        const response = await fetch(`/api/backtests/${backtestId}/abort`, {
          method: "POST",
        });

        if (response.ok) {
          updateMonitor(backtestId, { status: "aborted" });
        }
      } catch (error) {
        console.error("Failed to abort backtest:", error);
      }
    },
    [updateMonitor]
  );

  const pauseBacktest = useCallback(
    async (backtestId: string) => {
      try {
        const response = await fetch(`/api/backtests/${backtestId}/pause`, {
          method: "POST",
        });

        if (response.ok) {
          updateMonitor(backtestId, { status: "paused" });
        }
      } catch (error) {
        console.error("Failed to pause backtest:", error);
      }
    },
    [updateMonitor]
  );

  const resumeBacktest = useCallback(
    async (backtestId: string) => {
      try {
        const response = await fetch(`/api/backtests/${backtestId}/resume`, {
          method: "POST",
        });

        if (response.ok) {
          updateMonitor(backtestId, { status: "running" });
        }
      } catch (error) {
        console.error("Failed to resume backtest:", error);
      }
    },
    [updateMonitor]
  );

  return {
    monitors: Object.entries(monitors).map(([id, monitor]) => ({
      id,
      ...monitor,
    })),
    activeMonitors: activeMonitors(),
    getMonitorsByStatus,
    addMonitor,
    removeMonitor,
    updateMonitor,
    clearCompleted,
    abortBacktest,
    pauseBacktest,
    resumeBacktest,
    subscriptionCount: subscriptions.length,
  };
}
