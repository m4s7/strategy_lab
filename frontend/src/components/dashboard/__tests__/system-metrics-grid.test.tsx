import {
  renderWithProviders,
  screen,
  waitFor,
} from "@/tests/utils/test-helpers";
import { SystemMetricsGrid } from "../system-metrics-grid";
import { server } from "@/tests/mocks/server";
import { http, HttpResponse } from "msw";

describe("SystemMetricsGrid", () => {
  it("should render loading state initially", () => {
    renderWithProviders(<SystemMetricsGrid />);

    expect(screen.getByText("CPU Usage")).toBeInTheDocument();
    expect(screen.getByText("Memory Usage")).toBeInTheDocument();
    expect(screen.getByText("Disk Usage")).toBeInTheDocument();
    expect(screen.getByText("Active Backtests")).toBeInTheDocument();
  });

  it("should display system metrics when loaded", async () => {
    renderWithProviders(<SystemMetricsGrid />);

    await waitFor(() => {
      expect(screen.getByText("45.2%")).toBeInTheDocument();
      expect(screen.getByText("62.8%")).toBeInTheDocument();
      expect(screen.getByText("35.4%")).toBeInTheDocument();
      expect(screen.getByText("2")).toBeInTheDocument();
    });
  });

  it("should update metrics periodically", async () => {
    renderWithProviders(<SystemMetricsGrid />);

    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByText("45.2%")).toBeInTheDocument();
    });

    // Mock updated values
    server.use(
      http.get("http://localhost:8000/api/system/status", () => {
        return HttpResponse.json({
          cpuUsage: 55.5,
          memoryUsage: 70.1,
          diskUsage: 35.4,
          activeBacktests: 3,
          queuedBacktests: 5,
          completedToday: 12,
          averageExecutionTime: 180,
          systemHealth: "healthy",
          services: {
            api: "running",
            database: "running",
            redis: "running",
            websocket: "running",
          },
        });
      })
    );

    // Wait for refresh (component refreshes every 5 seconds in test mode)
    await waitFor(
      () => {
        expect(screen.getByText("55.5%")).toBeInTheDocument();
        expect(screen.getByText("70.1%")).toBeInTheDocument();
        expect(screen.getByText("3")).toBeInTheDocument();
      },
      { timeout: 10000 }
    );
  });

  it("should handle error states gracefully", async () => {
    // Mock API error
    server.use(
      http.get("http://localhost:8000/api/system/status", () => {
        return HttpResponse.json({ error: "Server error" }, { status: 500 });
      })
    );

    renderWithProviders(<SystemMetricsGrid />);

    await waitFor(() => {
      expect(
        screen.getByText(/Unable to load system metrics/)
      ).toBeInTheDocument();
    });
  });

  it("should show appropriate icons for different metric levels", async () => {
    renderWithProviders(<SystemMetricsGrid />);

    await waitFor(() => {
      // CPU at 45.2% should show normal icon
      const cpuCard = screen.getByTestId("metric-cpu");
      expect(cpuCard).toHaveClass("border-blue-500/20");

      // Memory at 62.8% should show warning
      const memoryCard = screen.getByTestId("metric-memory");
      expect(memoryCard).toHaveClass("border-yellow-500/20");
    });
  });

  it("should be accessible", async () => {
    const { container } = renderWithProviders(<SystemMetricsGrid />);

    await waitFor(() => {
      expect(screen.getByText("45.2%")).toBeInTheDocument();
    });

    // Check for proper ARIA labels
    expect(
      screen.getByRole("region", { name: /system metrics/i })
    ).toBeInTheDocument();

    // Check that all metric cards have proper structure
    const metricCards = screen.getAllByRole("article");
    expect(metricCards).toHaveLength(4);

    metricCards.forEach((card) => {
      expect(card).toHaveAttribute("aria-label");
    });
  });
});
