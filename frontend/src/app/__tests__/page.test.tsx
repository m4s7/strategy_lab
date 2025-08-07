import { render, screen } from "@testing-library/react";
import Dashboard from "../page";

// Mock all the dashboard components
jest.mock("@/components/dashboard/system-metrics-grid", () => ({
  SystemMetricsGrid: () => (
    <div data-testid="system-metrics-grid">System Metrics Grid</div>
  ),
}));

jest.mock("@/components/dashboard/recent-activity-panel", () => ({
  RecentActivityPanel: () => (
    <div data-testid="recent-activity-panel">Recent Activity Panel</div>
  ),
}));

jest.mock("@/components/dashboard/performance-stats-cards", () => ({
  PerformanceStatsCards: () => (
    <div data-testid="performance-stats-cards">Performance Stats Cards</div>
  ),
}));

jest.mock("@/components/dashboard/active-backtests-monitor", () => ({
  ActiveBacktestsMonitor: () => (
    <div data-testid="active-backtests-monitor">Active Backtests Monitor</div>
  ),
}));

jest.mock("@/components/dashboard/quick-actions-panel", () => ({
  QuickActionsPanel: () => (
    <div data-testid="quick-actions-panel">Quick Actions Panel</div>
  ),
}));

describe("Dashboard Page", () => {
  it("renders the dashboard header", () => {
    render(<Dashboard />);

    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(
      "Strategy Lab Dashboard"
    );
    expect(
      screen.getByText(
        "Monitor your backtesting environment and manage trading strategies"
      )
    ).toBeInTheDocument();
  });

  it("renders all dashboard components", () => {
    render(<Dashboard />);

    // Check all components are rendered
    expect(screen.getByTestId("system-metrics-grid")).toBeInTheDocument();
    expect(screen.getByTestId("performance-stats-cards")).toBeInTheDocument();
    expect(screen.getByTestId("recent-activity-panel")).toBeInTheDocument();
    expect(screen.getByTestId("active-backtests-monitor")).toBeInTheDocument();
    expect(screen.getByTestId("quick-actions-panel")).toBeInTheDocument();
  });

  it("applies correct layout structure", () => {
    const { container } = render(<Dashboard />);

    // Check main container spacing
    const mainContainer = container.firstChild;
    expect(mainContainer).toHaveClass("space-y-8");

    // Check grid layout for bottom section
    const gridContainer = container.querySelector(
      ".grid.gap-6.lg\\:grid-cols-2"
    );
    expect(gridContainer).toBeInTheDocument();

    // Check left column
    const leftColumn = gridContainer?.children[0];
    expect(leftColumn).toHaveClass("space-y-6");
    expect(leftColumn?.children).toHaveLength(2); // Recent Activity + Quick Actions

    // Check right column
    const rightColumn = gridContainer?.children[1];
    expect(rightColumn).toHaveClass("space-y-6");
    expect(rightColumn?.children).toHaveLength(1); // Active Backtests Monitor
  });

  it("renders components in correct order", () => {
    const { container } = render(<Dashboard />);

    const sections = container.querySelectorAll("section");

    // First section should be System Metrics
    expect(sections[0]).toContainElement(
      screen.getByTestId("system-metrics-grid")
    );

    // Second section should be Performance Stats
    expect(sections[1]).toContainElement(
      screen.getByTestId("performance-stats-cards")
    );
  });

  it("has responsive grid classes", () => {
    const { container } = render(<Dashboard />);

    const gridElement = container.querySelector(".grid");
    expect(gridElement).toHaveClass("lg:grid-cols-2");
    expect(gridElement).toHaveClass("gap-6");
  });

  it("groups components correctly in layout", () => {
    const { container } = render(<Dashboard />);

    // Find the grid container
    const grid = container.querySelector(".grid.gap-6.lg\\:grid-cols-2");

    // Left column should have Recent Activity and Quick Actions
    const leftColumn = grid?.children[0];
    expect(leftColumn).toContainElement(
      screen.getByTestId("recent-activity-panel")
    );
    expect(leftColumn).toContainElement(
      screen.getByTestId("quick-actions-panel")
    );

    // Right column should have Active Backtests Monitor
    const rightColumn = grid?.children[1];
    expect(rightColumn).toContainElement(
      screen.getByTestId("active-backtests-monitor")
    );
  });
});
