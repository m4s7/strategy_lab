# UI_044: Comprehensive Testing Suite

**Status:** Not Started

## Story
As a developer, I want a comprehensive testing suite that covers unit, integration, and end-to-end tests so that I can ensure the application works correctly and prevent regressions.

## Acceptance Criteria
1. Set up unit testing for all components and utilities
2. Implement integration tests for API endpoints
3. Create end-to-end tests for critical user flows
4. Add visual regression testing for UI consistency
5. Implement performance testing benchmarks
6. Set up continuous integration with test automation
7. Achieve 80%+ code coverage
8. Add accessibility testing automation

## Technical Requirements

### Unit Testing Setup
```typescript
// jest.config.js
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/tests/setup.ts'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy',
  },
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80
    }
  },
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
    '!src/**/*.stories.tsx',
    '!src/**/index.ts'
  ],
  testMatch: [
    '**/__tests__/**/*.(test|spec).(ts|tsx)',
    '**/*.(test|spec).(ts|tsx)'
  ]
};

// tests/setup.ts
import '@testing-library/jest-dom';
import { cleanup } from '@testing-library/react';
import { server } from './mocks/server';

// Enable API mocking
beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));
afterEach(() => {
  cleanup();
  server.resetHandlers();
});
afterAll(() => server.close());

// Mock IntersectionObserver
global.IntersectionObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn()
}));

// Mock WebSocket
global.WebSocket = jest.fn().mockImplementation(() => ({
  send: jest.fn(),
  close: jest.fn(),
  addEventListener: jest.fn(),
  removeEventListener: jest.fn()
}));
```

### Component Testing
```typescript
// components/__tests__/BacktestResults.test.tsx
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BacktestResults } from '../BacktestResults';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { mockBacktestData } from '@/tests/fixtures/backtest';

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

describe('BacktestResults', () => {
  it('should render loading state initially', () => {
    render(
      <BacktestResults backtestId="test-123" />,
      { wrapper: createWrapper() }
    );

    expect(screen.getByTestId('loading-skeleton')).toBeInTheDocument();
  });

  it('should display results after loading', async () => {
    render(
      <BacktestResults backtestId="test-123" />,
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(screen.getByText('Total Return:')).toBeInTheDocument();
      expect(screen.getByText('12.5%')).toBeInTheDocument();
    });
  });

  it('should handle tab switching', async () => {
    const user = userEvent.setup();

    render(
      <BacktestResults backtestId="test-123" />,
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(screen.getByRole('tab', { name: 'Overview' })).toBeInTheDocument();
    });

    await user.click(screen.getByRole('tab', { name: 'Trades' }));

    expect(screen.getByTestId('trades-table')).toBeInTheDocument();
  });

  it('should export results when export button is clicked', async () => {
    const user = userEvent.setup();
    const mockExport = jest.fn();

    render(
      <BacktestResults
        backtestId="test-123"
        onExport={mockExport}
      />,
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Export' })).toBeInTheDocument();
    });

    await user.click(screen.getByRole('button', { name: 'Export' }));

    expect(mockExport).toHaveBeenCalledWith({
      format: 'csv',
      data: expect.any(Object)
    });
  });

  it('should handle error states gracefully', async () => {
    // Mock API error
    server.use(
      rest.get('/api/backtests/:id', (req, res, ctx) => {
        return res(ctx.status(500), ctx.json({ error: 'Server error' }));
      })
    );

    render(
      <BacktestResults backtestId="test-123" />,
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(screen.getByText(/Something went wrong/)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Retry' })).toBeInTheDocument();
    });
  });
});
```

### Hook Testing
```typescript
// hooks/__tests__/useBacktestData.test.ts
import { renderHook, waitFor } from '@testing-library/react';
import { useBacktestData } from '../useBacktestData';
import { createWrapper } from '@/tests/utils';

describe('useBacktestData', () => {
  it('should fetch backtest data successfully', async () => {
    const { result } = renderHook(
      () => useBacktestData('test-123'),
      { wrapper: createWrapper() }
    );

    expect(result.current.isLoading).toBe(true);

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
      expect(result.current.data).toEqual({
        id: 'test-123',
        status: 'completed',
        results: expect.any(Object)
      });
    });
  });

  it('should handle pagination correctly', async () => {
    const { result } = renderHook(
      () => useBacktestData('test-123', { page: 2, pageSize: 20 }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.data?.trades).toHaveLength(20);
      expect(result.current.data?.pagination).toEqual({
        page: 2,
        pageSize: 20,
        total: 100
      });
    });
  });

  it('should refetch data when parameters change', async () => {
    const { result, rerender } = renderHook(
      ({ id }) => useBacktestData(id),
      {
        wrapper: createWrapper(),
        initialProps: { id: 'test-123' }
      }
    );

    await waitFor(() => {
      expect(result.current.data?.id).toBe('test-123');
    });

    rerender({ id: 'test-456' });

    await waitFor(() => {
      expect(result.current.data?.id).toBe('test-456');
    });
  });
});
```

### Integration Testing
```typescript
// api/__tests__/backtest.integration.test.ts
import request from 'supertest';
import { app } from '@/api/app';
import { prisma } from '@/api/db';
import { createTestUser, createTestStrategy } from '@/tests/factories';

describe('Backtest API Integration', () => {
  let user: User;
  let strategy: Strategy;
  let authToken: string;

  beforeEach(async () => {
    // Clean database
    await prisma.$transaction([
      prisma.backtest.deleteMany(),
      prisma.strategy.deleteMany(),
      prisma.user.deleteMany()
    ]);

    // Create test data
    user = await createTestUser();
    strategy = await createTestStrategy(user.id);
    authToken = generateAuthToken(user);
  });

  describe('POST /api/backtests', () => {
    it('should create a new backtest', async () => {
      const response = await request(app)
        .post('/api/backtests')
        .set('Authorization', `Bearer ${authToken}`)
        .send({
          strategyId: strategy.id,
          config: {
            startDate: '2023-01-01',
            endDate: '2023-12-31',
            initialCapital: 100000
          }
        });

      expect(response.status).toBe(201);
      expect(response.body).toMatchObject({
        id: expect.any(String),
        status: 'pending',
        strategyId: strategy.id
      });

      // Verify database
      const backtest = await prisma.backtest.findUnique({
        where: { id: response.body.id }
      });
      expect(backtest).toBeTruthy();
    });

    it('should validate input parameters', async () => {
      const response = await request(app)
        .post('/api/backtests')
        .set('Authorization', `Bearer ${authToken}`)
        .send({
          strategyId: strategy.id,
          config: {
            startDate: '2023-12-31',
            endDate: '2023-01-01', // Invalid: end before start
            initialCapital: -1000 // Invalid: negative capital
          }
        });

      expect(response.status).toBe(400);
      expect(response.body.errors).toContainEqual(
        expect.objectContaining({
          field: 'endDate',
          message: 'End date must be after start date'
        })
      );
    });
  });

  describe('WebSocket Integration', () => {
    it('should receive real-time updates during backtest', async () => {
      const ws = new WebSocket(`ws://localhost:8000/ws?token=${authToken}`);
      const messages: any[] = [];

      ws.on('message', (data) => {
        messages.push(JSON.parse(data.toString()));
      });

      await new Promise(resolve => ws.on('open', resolve));

      // Start backtest
      const response = await request(app)
        .post('/api/backtests')
        .set('Authorization', `Bearer ${authToken}`)
        .send({
          strategyId: strategy.id,
          config: { /* ... */ }
        });

      // Wait for updates
      await waitFor(() => {
        expect(messages).toContainEqual(
          expect.objectContaining({
            type: 'backtest.started',
            backtestId: response.body.id
          })
        );
      });

      ws.close();
    });
  });
});
```

### End-to-End Testing
```typescript
// e2e/backtest-flow.spec.ts
import { test, expect } from '@playwright/test';
import { loginAs, createStrategy } from './helpers';

test.describe('Backtest Flow', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'test@example.com');
  });

  test('should complete full backtest workflow', async ({ page }) => {
    // Navigate to strategies
    await page.goto('/strategies');

    // Create new strategy
    await page.click('button:has-text("New Strategy")');
    await page.fill('input[name="name"]', 'Test Strategy');
    await page.selectOption('select[name="type"]', 'scalping');
    await page.click('button:has-text("Create")');

    // Configure parameters
    await page.fill('input[name="stopLoss"]', '10');
    await page.fill('input[name="takeProfit"]', '20');
    await page.fill('input[name="positionSize"]', '1');

    // Start backtest
    await page.click('button:has-text("Run Backtest")');

    // Wait for backtest to complete
    await expect(page.locator('.backtest-status')).toHaveText('Completed', {
      timeout: 30000
    });

    // Verify results are displayed
    await expect(page.locator('.total-return')).toBeVisible();
    await expect(page.locator('.sharpe-ratio')).toBeVisible();

    // Navigate to trades tab
    await page.click('button[role="tab"]:has-text("Trades")');

    // Verify trades table is populated
    const tradeRows = page.locator('table.trades-table tbody tr');
    await expect(tradeRows).toHaveCount(expect.any(Number));

    // Export results
    await page.click('button:has-text("Export")');
    await page.click('button:has-text("CSV")');

    // Verify download started
    const download = await page.waitForEvent('download');
    expect(download.suggestedFilename()).toContain('backtest-results');
  });

  test('should handle errors gracefully', async ({ page }) => {
    // Simulate network error
    await page.route('**/api/backtests', route => route.abort());

    await page.goto('/backtests/new');
    await page.click('button:has-text("Run Backtest")');

    // Verify error message
    await expect(page.locator('.error-message')).toContainText(
      'Failed to start backtest'
    );

    // Verify retry button
    await expect(page.locator('button:has-text("Retry")')).toBeVisible();
  });
});
```

### Visual Regression Testing
```typescript
// visual-tests/charts.spec.ts
import { test, expect } from '@playwright/test';
import { setupMockData } from './helpers';

test.describe('Chart Visual Regression', () => {
  test('candlestick chart should render correctly', async ({ page }) => {
    await setupMockData(page);
    await page.goto('/backtests/test-123/charts');

    // Wait for chart to render
    await page.waitForSelector('.chart-container canvas');

    // Take screenshot
    await expect(page.locator('.chart-container')).toHaveScreenshot(
      'candlestick-chart.png',
      {
        maxDiffPixels: 100,
        threshold: 0.2
      }
    );
  });

  test('performance chart should match snapshot', async ({ page }) => {
    await setupMockData(page);
    await page.goto('/backtests/test-123/performance');

    await page.waitForSelector('.performance-chart');

    // Hide dynamic elements
    await page.addStyleTag({
      content: '.timestamp { visibility: hidden !important; }'
    });

    await expect(page.locator('.performance-chart')).toHaveScreenshot(
      'performance-chart.png'
    );
  });

  test('responsive layouts should render correctly', async ({ page }) => {
    const viewports = [
      { width: 375, height: 667, name: 'mobile' },
      { width: 768, height: 1024, name: 'tablet' },
      { width: 1920, height: 1080, name: 'desktop' }
    ];

    for (const viewport of viewports) {
      await page.setViewportSize(viewport);
      await page.goto('/dashboard');

      await expect(page).toHaveScreenshot(
        `dashboard-${viewport.name}.png`
      );
    }
  });
});
```

### Performance Testing
```typescript
// performance-tests/load-test.ts
import { check } from 'k6';
import http from 'k6/http';
import { Rate } from 'k6/metrics';

export const errorRate = new Rate('errors');

export const options = {
  stages: [
    { duration: '2m', target: 100 }, // Ramp up
    { duration: '5m', target: 100 }, // Stay at 100 users
    { duration: '2m', target: 200 }, // Ramp up more
    { duration: '5m', target: 200 }, // Stay at 200 users
    { duration: '2m', target: 0 },   // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'], // 95% of requests under 500ms
    errors: ['rate<0.1'],             // Error rate under 10%
  },
};

export default function () {
  // Test backtest creation
  const createBacktest = http.post(
    'http://localhost:3000/api/backtests',
    JSON.stringify({
      strategyId: 'test-strategy',
      config: {
        startDate: '2023-01-01',
        endDate: '2023-12-31',
        initialCapital: 100000
      }
    }),
    {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${__ENV.AUTH_TOKEN}`
      }
    }
  );

  check(createBacktest, {
    'backtest created': (r) => r.status === 201,
    'response time OK': (r) => r.timings.duration < 500,
  }) || errorRate.add(1);

  // Test results retrieval
  if (createBacktest.status === 201) {
    const backtestId = createBacktest.json('id');

    const getResults = http.get(
      `http://localhost:3000/api/backtests/${backtestId}/results`,
      {
        headers: {
          'Authorization': `Bearer ${__ENV.AUTH_TOKEN}`
        }
      }
    );

    check(getResults, {
      'results retrieved': (r) => r.status === 200,
      'has performance data': (r) => r.json('sharpeRatio') !== null,
    });
  }
}
```

### Accessibility Testing
```typescript
// a11y-tests/accessibility.spec.ts
import { test, expect } from '@playwright/test';
import { injectAxe, checkA11y } from 'axe-playwright';

test.describe('Accessibility', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await injectAxe(page);
  });

  test('dashboard should have no accessibility violations', async ({ page }) => {
    await page.goto('/dashboard');
    await checkA11y(page, null, {
      detailedReport: true,
      detailedReportOptions: {
        html: true
      }
    });
  });

  test('forms should be accessible', async ({ page }) => {
    await page.goto('/strategies/new');

    // Check form accessibility
    await checkA11y(page, '.strategy-form', {
      rules: {
        'label': { enabled: true },
        'aria-required-attr': { enabled: true },
        'form-field-multiple-labels': { enabled: true }
      }
    });

    // Test keyboard navigation
    await page.keyboard.press('Tab');
    const focusedElement = await page.evaluate(() => document.activeElement?.tagName);
    expect(focusedElement).toBeTruthy();

    // Test screen reader announcements
    await page.fill('input[name="name"]', '');
    await page.keyboard.press('Tab');

    const errorMessage = await page.getAttribute('input[name="name"]', 'aria-describedby');
    expect(errorMessage).toBeTruthy();
  });

  test('charts should have proper ARIA labels', async ({ page }) => {
    await page.goto('/backtests/test-123/charts');

    const chart = page.locator('.chart-container');
    await expect(chart).toHaveAttribute('role', 'img');
    await expect(chart).toHaveAttribute('aria-label', /chart/i);

    // Check for data table alternative
    const dataTable = page.locator('.chart-data-table');
    await expect(dataTable).toHaveAttribute('role', 'table');
  });
});
```

### Test Utilities and Helpers
```typescript
// tests/utils/test-helpers.ts
import { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { RouterContext } from 'next/dist/shared/lib/router-context';
import { NextRouter } from 'next/router';

// Custom render with providers
export function renderWithProviders(
  ui: ReactElement,
  {
    route = '/',
    ...renderOptions
  }: RenderOptions & { route?: string } = {}
) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false }
    }
  });

  const mockRouter: NextRouter = {
    basePath: '',
    pathname: route,
    route,
    asPath: route,
    query: {},
    push: jest.fn(),
    replace: jest.fn(),
    reload: jest.fn(),
    back: jest.fn(),
    prefetch: jest.fn(),
    beforePopState: jest.fn(),
    events: {
      on: jest.fn(),
      off: jest.fn(),
      emit: jest.fn(),
    },
    isFallback: false,
    isLocaleDomain: false,
    isReady: true,
    isPreview: false,
  };

  function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        <RouterContext.Provider value={mockRouter}>
          {children}
        </RouterContext.Provider>
      </QueryClientProvider>
    );
  }

  return render(ui, { wrapper: Wrapper, ...renderOptions });
}

// Test data factories
export const createMockBacktest = (overrides = {}) => ({
  id: 'test-123',
  status: 'completed',
  strategyId: 'strategy-456',
  config: {
    startDate: '2023-01-01',
    endDate: '2023-12-31',
    initialCapital: 100000
  },
  results: {
    totalReturn: 0.125,
    sharpeRatio: 1.8,
    maxDrawdown: 0.08,
    winRate: 0.65,
    totalTrades: 150
  },
  ...overrides
});

// API mocking utilities
export const mockApiResponse = (data: any, options = {}) => {
  return rest.get('*', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json(data),
      ...options
    );
  });
};
```

## UI/UX Considerations
- Fast test execution for quick feedback
- Clear test output and error messages
- Visual regression test reports
- Performance metrics dashboards
- Accessibility audit reports
- Test coverage visualization

## Testing Requirements
1. Unit test coverage > 80%
2. Integration test for all API endpoints
3. E2E tests for critical user journeys
4. Visual regression for all major components
5. Performance benchmarks met
6. Zero accessibility violations

## Dependencies
- UI_001: Next.js foundation
- UI_002: FastAPI backend
- All feature components
- CI/CD pipeline setup

## Story Points: 21

## Priority: High

## Implementation Notes
- Use GitHub Actions for CI
- Parallelize test execution
- Cache dependencies for speed
- Generate test reports
- Monitor flaky tests
- Use test containers for database
