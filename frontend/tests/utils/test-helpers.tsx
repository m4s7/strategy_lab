import { ReactElement } from "react";
import { render, RenderOptions } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ThemeProvider } from "next-themes";

// Create a custom render function with providers
interface CustomRenderOptions extends Omit<RenderOptions, "wrapper"> {
  initialRoute?: string;
}

export function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        staleTime: 0,
        gcTime: 0, // Previously cacheTime
      },
      mutations: {
        retry: false,
      },
    },
    logger: {
      log: () => {},
      warn: () => {},
      error: () => {},
    },
  });
}

export function renderWithProviders(
  ui: ReactElement,
  options: CustomRenderOptions = {}
) {
  const { initialRoute = "/", ...renderOptions } = options;

  // Set the initial route
  window.history.pushState({}, "Test page", initialRoute);

  const queryClient = createTestQueryClient();

  function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        <ThemeProvider attribute="class" defaultTheme="light">
          {children}
        </ThemeProvider>
      </QueryClientProvider>
    );
  }

  const result = render(ui, { wrapper: Wrapper, ...renderOptions });

  return {
    ...result,
    queryClient,
  };
}

// Test data factories
export const createMockBacktest = (overrides = {}) => ({
  id: "test-123",
  status: "completed",
  strategyId: "strategy-456",
  config: {
    startDate: "2023-01-01",
    endDate: "2023-12-31",
    initialCapital: 100000,
    dataLevel: "level1",
    contracts: ["03-24", "06-24"],
  },
  results: {
    totalReturn: 0.125,
    sharpeRatio: 1.8,
    maxDrawdown: 0.08,
    winRate: 0.65,
    totalTrades: 150,
    profitFactor: 1.8,
    averageWin: 25.5,
    averageLoss: -12.3,
    expectancy: 8.2,
  },
  ...overrides,
});

export const createMockStrategy = (overrides = {}) => ({
  id: "strategy-456",
  name: "Test Strategy",
  type: "scalping",
  description: "A test strategy",
  parameters: {
    stopLoss: 10,
    takeProfit: 20,
    positionSize: 1,
  },
  ...overrides,
});

// Helper to wait for async updates
export const waitForLoadingToFinish = () =>
  waitFor(() => {
    const loaders = [
      ...screen.queryAllByTestId(/loading/i),
      ...screen.queryAllByText(/loading/i),
      ...screen.queryAllByRole("progressbar"),
    ];
    loaders.forEach((loader) => {
      expect(loader).not.toBeInTheDocument();
    });
  });

// Re-export everything from testing library
export * from "@testing-library/react";
export { default as userEvent } from "@testing-library/user-event";

// Helper for async component testing
import { act, screen, waitFor } from "@testing-library/react";

export async function waitForElement(
  callback: () => HTMLElement | null | Promise<HTMLElement | null>,
  options = {}
) {
  let element: HTMLElement | null = null;

  await waitFor(async () => {
    element = await callback();
    expect(element).toBeInTheDocument();
  }, options);

  return element!;
}

// Mock next/router if needed
export const mockRouter = {
  push: jest.fn(),
  replace: jest.fn(),
  prefetch: jest.fn(),
  back: jest.fn(),
  pathname: "/",
  query: {},
  asPath: "/",
  events: {
    on: jest.fn(),
    off: jest.fn(),
    emit: jest.fn(),
  },
};
