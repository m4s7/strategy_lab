import { render, screen } from "@testing-library/react";
import { ActiveBacktestsMonitor } from "../active-backtests-monitor";
import { useBacktestMonitor } from "@/hooks/useBacktestMonitor";

// Mock the hooks
jest.mock("@/hooks/useBacktestMonitor", () => ({
  useBacktestMonitor: jest.fn(),
}));

jest.mock("@/components/monitoring/backtest-monitor", () => ({
  BacktestMonitor: ({
    backtestId,
    compact,
  }: {
    backtestId: string;
    compact?: boolean;
  }) => (
    <div data-testid={`backtest-monitor-${backtestId}`}>
      Backtest Monitor {backtestId} (compact: {compact ? "true" : "false"})
    </div>
  ),
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

describe("ActiveBacktestsMonitor", () => {
  const mockMonitors = [
    {
      id: "monitor-1",
      status: "running" as const,
      strategyName: "Order Book Scalper",
      progress: {
        percentage: 45.5,
        eta: "5 minutes",
      },
    },
    {
      id: "monitor-2",
      status: "running" as const,
      strategyName: "Momentum Breakout",
      progress: {
        percentage: 75.0,
        eta: "2 minutes",
      },
    },
    {
      id: "monitor-3",
      status: "paused" as const,
      strategyName: "Mean Reversion",
      progress: {
        percentage: 30.0,
        eta: null,
      },
    },
    {
      id: "monitor-4",
      status: "running" as const,
      strategyName: "Arbitrage Strategy",
      progress: {
        percentage: 10.0,
        eta: "15 minutes",
      },
    },
  ];

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders empty state when no active backtests", () => {
    (useBacktestMonitor as jest.Mock).mockReturnValue({
      monitors: [],
      activeMonitors: [],
    });

    render(<ActiveBacktestsMonitor />);

    expect(screen.getByText("No active backtests")).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Start New Backtest" })
    ).toHaveAttribute("href", "/backtests/new");
  });

  it("displays active backtest count badge", () => {
    (useBacktestMonitor as jest.Mock).mockReturnValue({
      monitors: mockMonitors,
      activeMonitors: mockMonitors.slice(0, 3),
    });

    render(<ActiveBacktestsMonitor />);

    const badge = screen.getByText("3");
    expect(badge).toHaveClass("ml-2");
    expect(badge.parentElement).toHaveTextContent("Active Backtests3");
  });

  it("renders up to 3 active monitors in compact mode", () => {
    (useBacktestMonitor as jest.Mock).mockReturnValue({
      monitors: mockMonitors,
      activeMonitors: mockMonitors.slice(0, 3),
    });

    render(<ActiveBacktestsMonitor />);

    // Check first 3 monitors are rendered
    expect(
      screen.getByTestId("backtest-monitor-monitor-1")
    ).toBeInTheDocument();
    expect(
      screen.getByTestId("backtest-monitor-monitor-2")
    ).toBeInTheDocument();
    expect(
      screen.getByTestId("backtest-monitor-monitor-3")
    ).toBeInTheDocument();

    // Check they are in compact mode
    expect(
      screen.getByText(/Backtest Monitor monitor-1.*compact: true/)
    ).toBeInTheDocument();
  });

  it("shows view all button when more than 3 active backtests", () => {
    (useBacktestMonitor as jest.Mock).mockReturnValue({
      monitors: mockMonitors,
      activeMonitors: mockMonitors,
    });

    render(<ActiveBacktestsMonitor />);

    const viewAllButton = screen.getByRole("link", {
      name: "View All 4 Active Backtests",
    });
    expect(viewAllButton).toHaveAttribute("href", "/monitor");
  });

  it("does not show view all button when 3 or fewer active backtests", () => {
    (useBacktestMonitor as jest.Mock).mockReturnValue({
      monitors: mockMonitors.slice(0, 3),
      activeMonitors: mockMonitors.slice(0, 3),
    });

    render(<ActiveBacktestsMonitor />);

    expect(
      screen.queryByText(/View All.*Active Backtests/)
    ).not.toBeInTheDocument();
  });

  it("renders view monitor button", () => {
    (useBacktestMonitor as jest.Mock).mockReturnValue({
      monitors: mockMonitors,
      activeMonitors: mockMonitors.slice(0, 2),
    });

    render(<ActiveBacktestsMonitor />);

    const viewMonitorButton = screen.getByRole("link", {
      name: /view monitor/i,
    });
    expect(viewMonitorButton).toHaveAttribute("href", "/monitor");
  });

  it("does not display badge when no active backtests", () => {
    (useBacktestMonitor as jest.Mock).mockReturnValue({
      monitors: [],
      activeMonitors: [],
    });

    render(<ActiveBacktestsMonitor />);

    // Should not show badge with 0
    expect(screen.queryByText("0")).not.toBeInTheDocument();
    expect(screen.getByText("Active Backtests")).not.toHaveTextContent(
      "Active Backtests0"
    );
  });

  it("filters to show only active monitors", () => {
    const allMonitors = [
      ...mockMonitors,
      {
        id: "monitor-5",
        status: "completed" as const,
        strategyName: "Completed Strategy",
        progress: { percentage: 100 },
      },
    ];

    (useBacktestMonitor as jest.Mock).mockReturnValue({
      monitors: allMonitors,
      activeMonitors: mockMonitors, // Only active ones
    });

    render(<ActiveBacktestsMonitor />);

    // Should not show completed monitor
    expect(
      screen.queryByTestId("backtest-monitor-monitor-5")
    ).not.toBeInTheDocument();

    // Should show active ones
    expect(
      screen.getByTestId("backtest-monitor-monitor-1")
    ).toBeInTheDocument();
  });

  it("passes correct props to BacktestMonitor component", () => {
    (useBacktestMonitor as jest.Mock).mockReturnValue({
      monitors: mockMonitors,
      activeMonitors: [mockMonitors[0]],
    });

    render(<ActiveBacktestsMonitor />);

    const monitor = screen.getByTestId("backtest-monitor-monitor-1");
    expect(monitor).toHaveTextContent("compact: true");
  });
});
