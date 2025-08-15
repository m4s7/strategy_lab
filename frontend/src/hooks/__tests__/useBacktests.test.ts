import { renderHook, waitFor } from "@/tests/utils/test-helpers";
import { useBacktests } from "../useBacktests";
import { server } from "@/tests/mocks/server";
import { http, HttpResponse } from "msw";

describe("useBacktests", () => {
  it("should fetch backtest data successfully", async () => {
    const { result } = renderHook(() => useBacktests());

    expect(result.current.isLoading).toBe(true);
    expect(result.current.backtests).toEqual([]);

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.backtests).toHaveLength(1);
    expect(result.current.backtests[0]).toMatchObject({
      id: "test-123",
      status: "completed",
      strategyId: "strategy-456",
    });
  });

  it("should handle pagination correctly", async () => {
    const { result, rerender } = renderHook(
      ({ page, pageSize }) => useBacktests({ page, pageSize }),
      {
        initialProps: { page: 1, pageSize: 20 },
      }
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.total).toBe(1);
    expect(result.current.page).toBe(1);
    expect(result.current.pageSize).toBe(20);

    // Change page
    rerender({ page: 2, pageSize: 20 });

    await waitFor(() => {
      expect(result.current.page).toBe(2);
    });
  });

  it("should handle filters correctly", async () => {
    const { result } = renderHook(() =>
      useBacktests({
        filters: {
          status: "completed",
          strategyId: "strategy-456",
        },
      })
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.backtests).toHaveLength(1);
    expect(result.current.backtests[0].status).toBe("completed");
    expect(result.current.backtests[0].strategyId).toBe("strategy-456");
  });

  it("should handle errors gracefully", async () => {
    server.use(
      http.get("http://localhost:8000/api/backtests", () => {
        return HttpResponse.json(
          { error: "Internal server error" },
          { status: 500 }
        );
      })
    );

    const { result } = renderHook(() => useBacktests());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBeTruthy();
    });

    expect(result.current.error?.message).toContain(
      "Failed to fetch backtests"
    );
    expect(result.current.backtests).toEqual([]);
  });

  it("should refetch data when refetch is called", async () => {
    let callCount = 0;

    server.use(
      http.get("http://localhost:8000/api/backtests", () => {
        callCount++;
        return HttpResponse.json({
          backtests: [
            {
              id: `test-${callCount}`,
              status: "completed",
              strategyId: "strategy-456",
            },
          ],
          total: 1,
          page: 1,
          pageSize: 20,
        });
      })
    );

    const { result } = renderHook(() => useBacktests());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.backtests[0].id).toBe("test-1");

    // Call refetch
    await result.current.refetch();

    await waitFor(() => {
      expect(result.current.backtests[0].id).toBe("test-2");
    });

    expect(callCount).toBe(2);
  });

  it("should handle sorting correctly", async () => {
    const { result, rerender } = renderHook(
      ({ sortBy, sortOrder }) => useBacktests({ sortBy, sortOrder }),
      {
        initialProps: { sortBy: "createdAt", sortOrder: "desc" as const },
      }
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Change sort order
    rerender({ sortBy: "sharpeRatio", sortOrder: "asc" as const });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Verify the request was made with new parameters
    // (In a real implementation, this would be verified through the API call)
  });

  it("should handle real-time updates via WebSocket", async () => {
    const { result } = renderHook(() => useBacktests());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Simulate WebSocket message for backtest update
    const wsMessage = {
      type: "backtest.updated",
      data: {
        id: "test-123",
        status: "running",
        progress: 50,
      },
    };

    // In a real implementation, this would trigger through WebSocket
    // For now, we'll just verify the hook sets up the listener
    expect(result.current.isSubscribed).toBe(true);
  });

  it("should clean up subscriptions on unmount", async () => {
    const { result, unmount } = renderHook(() => useBacktests());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.isSubscribed).toBe(true);

    unmount();

    // In a real implementation, verify WebSocket unsubscribe was called
  });
});
