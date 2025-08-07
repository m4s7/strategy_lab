import { render, screen, waitFor } from "@testing-library/react";
import { RecentActivityPanel } from "../recent-activity-panel";
import { useRecentBacktests } from "@/hooks/useBacktests";
import { format } from "date-fns";

// Mock the hooks
jest.mock("@/hooks/useBacktests", () => ({
  useRecentBacktests: jest.fn(),
}));

jest.mock("next/link", () => ({
  __esModule: true,
  default: ({
    children,
    href,
  }: {
    children: React.ReactNode;
    href: string;
  }) => <a href={href}>{children}</a>,
}));

// Mock date-fns
jest.mock("date-fns", () => ({
  formatDistanceToNow: jest.fn((date) => "5 minutes ago"),
}));

describe("RecentActivityPanel", () => {
  const mockBacktests = [
    {
      id: "test-1",
      strategy_id: "Order Book Scalper",
      config: {},
      status: "completed" as const,
      created_at: "2024-01-15T10:00:00Z",
      updated_at: "2024-01-15T10:05:00Z",
    },
    {
      id: "test-2",
      strategy_id: "Momentum Breakout",
      config: {},
      status: "running" as const,
      created_at: "2024-01-15T09:30:00Z",
      updated_at: "2024-01-15T09:30:00Z",
    },
    {
      id: "test-3",
      strategy_id: "Mean Reversion",
      config: {},
      status: "failed" as const,
      created_at: "2024-01-15T09:00:00Z",
      updated_at: "2024-01-15T09:01:00Z",
      error_message: "Insufficient data",
    },
  ];

  beforeEach(() => {
    jest.clearAllMocks();
    // Mock fetch for metrics API
    global.fetch = jest.fn((url: string) => {
      if (url.includes("/api/v1/results")) {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve([
              {
                total_return_pct: 5.25,
                sharpe_ratio: 1.85,
                max_drawdown_pct: 2.5,
                win_rate: 65.5,
              },
            ]),
        });
      }
      return Promise.resolve({
        ok: false,
      });
    }) as jest.Mock;
  });

  it("renders loading state", () => {
    (useRecentBacktests as jest.Mock).mockReturnValue({
      backtests: [],
      loading: true,
      error: null,
    });

    render(<RecentActivityPanel />);
    expect(screen.getByText("Recent Activity")).toBeInTheDocument();
    expect(screen.getAllByTestId("skeleton-loader")).toHaveLength(5);
  });

  it("renders error state", () => {
    (useRecentBacktests as jest.Mock).mockReturnValue({
      backtests: [],
      loading: false,
      error: "Failed to load data",
    });

    render(<RecentActivityPanel />);
    expect(
      screen.getByText("Failed to load recent activity")
    ).toBeInTheDocument();
  });

  it("renders empty state", () => {
    (useRecentBacktests as jest.Mock).mockReturnValue({
      backtests: [],
      loading: false,
      error: null,
    });

    render(<RecentActivityPanel />);
    expect(screen.getByText("No recent backtests found")).toBeInTheDocument();
  });

  it("renders backtest list", async () => {
    (useRecentBacktests as jest.Mock).mockReturnValue({
      backtests: mockBacktests,
      loading: false,
      error: null,
    });

    render(<RecentActivityPanel />);

    // Check if backtests are rendered
    expect(screen.getByText("Order Book Scalper")).toBeInTheDocument();
    expect(screen.getByText("Momentum Breakout")).toBeInTheDocument();
    expect(screen.getByText("Mean Reversion")).toBeInTheDocument();

    // Check status badges
    expect(screen.getByText("completed")).toBeInTheDocument();
    expect(screen.getByText("running")).toBeInTheDocument();
    expect(screen.getByText("failed")).toBeInTheDocument();
  });

  it("fetches and displays metrics for completed backtests", async () => {
    (useRecentBacktests as jest.Mock).mockReturnValue({
      backtests: mockBacktests,
      loading: false,
      error: null,
    });

    render(<RecentActivityPanel />);

    // Wait for metrics to be fetched
    await waitFor(() => {
      expect(screen.getByText("5.25%")).toBeInTheDocument(); // Return
      expect(screen.getByText("1.85")).toBeInTheDocument(); // Sharpe
      expect(screen.getByText("2.5%")).toBeInTheDocument(); // Drawdown
      expect(screen.getByText("65.5%")).toBeInTheDocument(); // Win Rate
    });
  });

  it("does not show metrics for non-completed backtests", () => {
    (useRecentBacktests as jest.Mock).mockReturnValue({
      backtests: [mockBacktests[1]], // Only running backtest
      loading: false,
      error: null,
    });

    render(<RecentActivityPanel />);

    // Should not show metrics section
    expect(screen.queryByText("Return")).not.toBeInTheDocument();
    expect(screen.queryByText("Sharpe")).not.toBeInTheDocument();
  });

  it("renders view all button with correct link", () => {
    (useRecentBacktests as jest.Mock).mockReturnValue({
      backtests: mockBacktests,
      loading: false,
      error: null,
    });

    render(<RecentActivityPanel />);

    const viewAllButton = screen.getByRole("link", { name: /view all/i });
    expect(viewAllButton).toHaveAttribute("href", "/results");
  });

  it("renders individual backtest links", () => {
    (useRecentBacktests as jest.Mock).mockReturnValue({
      backtests: mockBacktests,
      loading: false,
      error: null,
    });

    render(<RecentActivityPanel />);

    // Check if individual links are rendered
    const links = screen
      .getAllByRole("link")
      .filter((link) => !link.textContent?.includes("View All"));
    expect(links).toHaveLength(3);
    expect(links[0]).toHaveAttribute("href", "/results/test-1");
    expect(links[1]).toHaveAttribute("href", "/results/test-2");
    expect(links[2]).toHaveAttribute("href", "/results/test-3");
  });

  it("applies correct color to metrics", async () => {
    (useRecentBacktests as jest.Mock).mockReturnValue({
      backtests: [mockBacktests[0]],
      loading: false,
      error: null,
    });

    render(<RecentActivityPanel />);

    await waitFor(() => {
      const returnElement = screen.getByText("5.25%");
      expect(returnElement).toHaveClass("text-green-600"); // Positive return
    });
  });

  it("handles fetch errors gracefully", async () => {
    const consoleError = jest.spyOn(console, "error").mockImplementation();

    global.fetch = jest.fn().mockRejectedValue(new Error("Network error"));

    (useRecentBacktests as jest.Mock).mockReturnValue({
      backtests: mockBacktests,
      loading: false,
      error: null,
    });

    render(<RecentActivityPanel />);

    await waitFor(() => {
      expect(consoleError).toHaveBeenCalledWith(
        expect.stringContaining("Failed to fetch metrics"),
        expect.any(Error)
      );
    });

    consoleError.mockRestore();
  });
});
