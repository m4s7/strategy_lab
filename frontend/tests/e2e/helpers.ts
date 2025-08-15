import { Page, expect } from "@playwright/test";

export async function login(page: Page, username: string, password: string) {
  await page.goto("/login");
  await page.fill('input[name="username"]', username);
  await page.fill('input[name="password"]', password);
  await page.click('button[type="submit"]');

  // Wait for redirect to dashboard
  await expect(page).toHaveURL("/");
  await expect(page.locator("text=Dashboard")).toBeVisible();
}

export async function createStrategy(
  page: Page,
  strategy: {
    name: string;
    type: string;
    parameters?: Record<string, any>;
  }
) {
  await page.goto("/strategies");
  await page.click('button:has-text("New Strategy")');

  await page.fill('input[name="name"]', strategy.name);
  await page.selectOption('select[name="type"]', strategy.type);

  if (strategy.parameters) {
    for (const [key, value] of Object.entries(strategy.parameters)) {
      const input = page.locator(`input[name="${key}"]`);
      if (await input.isVisible()) {
        await input.fill(String(value));
      }
    }
  }

  await page.click('button:has-text("Create Strategy")');
  await expect(
    page.locator("text=Strategy created successfully")
  ).toBeVisible();
}

export async function runBacktest(
  page: Page,
  config: {
    strategyId?: string;
    startDate: string;
    endDate: string;
    initialCapital?: number;
    contracts?: string[];
  }
) {
  await page.goto("/backtests/new");

  if (config.strategyId) {
    await page.selectOption('select[name="strategy"]', config.strategyId);
  }

  await page.fill('input[name="startDate"]', config.startDate);
  await page.fill('input[name="endDate"]', config.endDate);

  if (config.initialCapital) {
    await page.fill(
      'input[name="initialCapital"]',
      String(config.initialCapital)
    );
  }

  if (config.contracts && config.contracts.length > 0) {
    await page.click("text=Select Contracts");
    for (const contract of config.contracts) {
      await page.check(`input[value="${contract}"]`);
    }
    await page.click('button:has-text("Confirm")');
  }

  await page.click('button:has-text("Start Backtest")');
  await expect(page.locator("text=Backtest started")).toBeVisible();

  return page.url().match(/\/backtests\/([^\/]+)/)?.[1];
}

export async function waitForBacktestCompletion(
  page: Page,
  backtestId: string,
  timeout = 120000
) {
  await page.goto(`/results/${backtestId}`);

  await expect(page.locator("text=Completed")).toBeVisible({ timeout });
}

export async function setupMockData(page: Page) {
  // Inject mock data for faster E2E tests
  await page.addInitScript(() => {
    (window as any).__E2E_MODE__ = true;
    (window as any).__MOCK_DELAY__ = 100; // Fast responses
  });
}

export async function clearLocalStorage(page: Page) {
  await page.evaluate(() => {
    localStorage.clear();
    sessionStorage.clear();
  });
}

export async function mockAPIResponse(page: Page, url: string, response: any) {
  await page.route(url, (route) => {
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(response),
    });
  });
}

export async function waitForWebSocket(page: Page) {
  await page.waitForFunction(
    () => {
      return (window as any).wsClient?.readyState === 1;
    },
    { timeout: 5000 }
  );
}

export async function captureMetrics(page: Page) {
  return await page.evaluate(() => {
    const navigation = performance.getEntriesByType(
      "navigation"
    )[0] as PerformanceNavigationTiming;
    return {
      domContentLoaded:
        navigation.domContentLoadedEventEnd -
        navigation.domContentLoadedEventStart,
      loadComplete: navigation.loadEventEnd - navigation.loadEventStart,
      firstPaint:
        performance.getEntriesByName("first-paint")[0]?.startTime || 0,
      firstContentfulPaint:
        performance.getEntriesByName("first-contentful-paint")[0]?.startTime ||
        0,
    };
  });
}

export async function checkAccessibility(page: Page) {
  // Basic accessibility checks
  const issues: string[] = [];

  // Check for missing alt text
  const imagesWithoutAlt = await page.locator("img:not([alt])").count();
  if (imagesWithoutAlt > 0) {
    issues.push(`${imagesWithoutAlt} images without alt text`);
  }

  // Check for missing form labels
  const inputsWithoutLabels = await page
    .locator("input:not([aria-label]):not([id])")
    .count();
  if (inputsWithoutLabels > 0) {
    issues.push(`${inputsWithoutLabels} inputs without labels`);
  }

  // Check for proper heading hierarchy
  const h1Count = await page.locator("h1").count();
  if (h1Count !== 1) {
    issues.push(`Page has ${h1Count} h1 elements (should have exactly 1)`);
  }

  return issues;
}

export async function takeScreenshot(page: Page, name: string) {
  await page.screenshot({
    path: `tests/e2e/screenshots/${name}.png`,
    fullPage: true,
  });
}

export async function compareSnapshots(page: Page, name: string) {
  await expect(page).toHaveScreenshot(`${name}.png`, {
    maxDiffPixels: 100,
    threshold: 0.2,
  });
}
