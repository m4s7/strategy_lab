import { createTestQueryClient } from "../utils/test-helpers";
import { mockBacktestData, mockStrategyData } from "../fixtures/backtest";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

describe("Backtest API Integration", () => {
  let queryClient: ReturnType<typeof createTestQueryClient>;

  beforeEach(() => {
    queryClient = createTestQueryClient();
  });

  describe("GET /api/backtests", () => {
    it("should fetch backtests list", async () => {
      const response = await fetch(`${API_URL}/api/backtests`);
      const data = await response.json();

      expect(response.status).toBe(200);
      expect(data).toHaveProperty("backtests");
      expect(data).toHaveProperty("total");
      expect(Array.isArray(data.backtests)).toBe(true);
    });

    it("should support pagination", async () => {
      const response = await fetch(
        `${API_URL}/api/backtests?page=2&pageSize=10`
      );
      const data = await response.json();

      expect(response.status).toBe(200);
      expect(data.page).toBe(2);
      expect(data.pageSize).toBe(10);
    });

    it("should support filtering by status", async () => {
      const response = await fetch(`${API_URL}/api/backtests?status=completed`);
      const data = await response.json();

      expect(response.status).toBe(200);
      data.backtests.forEach((backtest: any) => {
        expect(backtest.status).toBe("completed");
      });
    });
  });

  describe("POST /api/backtests", () => {
    it("should create a new backtest", async () => {
      const payload = {
        strategyId: "strategy-456",
        config: {
          startDate: "2023-01-01",
          endDate: "2023-12-31",
          initialCapital: 100000,
          dataLevel: "level1",
          contracts: ["03-24", "06-24"],
        },
      };

      const response = await fetch(`${API_URL}/api/backtests`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      const data = await response.json();

      expect(response.status).toBe(201);
      expect(data).toHaveProperty("id");
      expect(data.status).toBe("pending");
      expect(data.strategyId).toBe(payload.strategyId);
    });

    it("should validate required fields", async () => {
      const invalidPayload = {
        // Missing strategyId
        config: {
          startDate: "2023-01-01",
          endDate: "2023-12-31",
        },
      };

      const response = await fetch(`${API_URL}/api/backtests`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(invalidPayload),
      });

      expect(response.status).toBe(400);
      const error = await response.json();
      expect(error).toHaveProperty("error");
    });

    it("should validate date ranges", async () => {
      const payload = {
        strategyId: "strategy-456",
        config: {
          startDate: "2023-12-31",
          endDate: "2023-01-01", // End before start
          initialCapital: 100000,
        },
      };

      const response = await fetch(`${API_URL}/api/backtests`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      expect(response.status).toBe(400);
      const error = await response.json();
      expect(error.error).toContain("end date");
    });
  });

  describe("GET /api/backtests/:id", () => {
    it("should fetch a specific backtest", async () => {
      const response = await fetch(`${API_URL}/api/backtests/test-123`);
      const data = await response.json();

      expect(response.status).toBe(200);
      expect(data.id).toBe("test-123");
      expect(data).toHaveProperty("status");
      expect(data).toHaveProperty("results");
    });

    it("should return 404 for non-existent backtest", async () => {
      const response = await fetch(`${API_URL}/api/backtests/non-existent`);

      expect(response.status).toBe(404);
    });
  });

  describe("GET /api/backtests/:id/trades", () => {
    it("should fetch trades for a backtest", async () => {
      const response = await fetch(`${API_URL}/api/backtests/test-123/trades`);
      const data = await response.json();

      expect(response.status).toBe(200);
      expect(data).toHaveProperty("trades");
      expect(Array.isArray(data.trades)).toBe(true);
      expect(data).toHaveProperty("total");
    });

    it("should support trade filtering", async () => {
      const response = await fetch(
        `${API_URL}/api/backtests/test-123/trades?direction=long&minPnl=0`
      );
      const data = await response.json();

      expect(response.status).toBe(200);
      data.trades.forEach((trade: any) => {
        expect(trade.direction).toBe("long");
        expect(trade.pnl).toBeGreaterThanOrEqual(0);
      });
    });
  });

  describe("DELETE /api/backtests/:id", () => {
    it("should delete a backtest", async () => {
      const response = await fetch(`${API_URL}/api/backtests/test-123`, {
        method: "DELETE",
      });

      expect(response.status).toBe(204);
    });

    it("should return 404 when deleting non-existent backtest", async () => {
      const response = await fetch(`${API_URL}/api/backtests/non-existent`, {
        method: "DELETE",
      });

      expect(response.status).toBe(404);
    });
  });

  describe("POST /api/backtests/:id/stop", () => {
    it("should stop a running backtest", async () => {
      const response = await fetch(`${API_URL}/api/backtests/test-123/stop`, {
        method: "POST",
      });

      expect(response.status).toBe(200);
      const data = await response.json();
      expect(data.status).toBe("stopped");
    });
  });

  describe("Error Handling", () => {
    it("should handle server errors gracefully", async () => {
      // This would need to be mocked in a real test
      const response = await fetch(`${API_URL}/api/backtests`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: "invalid json",
      });

      expect(response.status).toBeGreaterThanOrEqual(400);
    });

    it("should handle network timeouts", async () => {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 100);

      try {
        await fetch(`${API_URL}/api/backtests`, {
          signal: controller.signal,
        });
      } catch (error: any) {
        expect(error.name).toBe("AbortError");
      } finally {
        clearTimeout(timeoutId);
      }
    });
  });

  describe("Concurrent Requests", () => {
    it("should handle multiple concurrent requests", async () => {
      const requests = Array.from({ length: 10 }, (_, i) =>
        fetch(`${API_URL}/api/backtests/test-${i}`)
      );

      const responses = await Promise.all(requests);

      responses.forEach((response) => {
        expect([200, 404]).toContain(response.status);
      });
    });
  });
});
