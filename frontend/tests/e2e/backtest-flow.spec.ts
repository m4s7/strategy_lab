import { test, expect } from "@playwright/test";

test.describe("Backtest Flow", () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the application
    await page.goto("/");

    // Wait for the page to load
    await page.waitForLoadState("networkidle");
  });

  test("should complete full backtest workflow", async ({ page }) => {
    // Navigate to strategies page
    await page.click("text=Strategies");
    await expect(page).toHaveURL("/strategies");

    // Click new strategy button
    await page.click('button:has-text("New Strategy")');

    // Fill in strategy details
    await page.fill('input[name="name"]', "E2E Test Strategy");
    await page.selectOption('select[name="type"]', "scalping");
    await page.fill(
      'textarea[name="description"]',
      "Strategy created by E2E test"
    );

    // Configure parameters
    await page.fill('input[name="stopLoss"]', "15");
    await page.fill('input[name="takeProfit"]', "30");
    await page.fill('input[name="positionSize"]', "2");

    // Save strategy
    await page.click('button:has-text("Create Strategy")');

    // Wait for success message
    await expect(
      page.locator("text=Strategy created successfully")
    ).toBeVisible();

    // Navigate to backtest execution
    await page.click('button:has-text("Run Backtest")');
    await expect(page).toHaveURL(/\/backtests\/new/);

    // Configure backtest
    await page.fill('input[name="startDate"]', "2023-01-01");
    await page.fill('input[name="endDate"]', "2023-12-31");
    await page.fill('input[name="initialCapital"]', "100000");

    // Select data contracts
    await page.click("text=Select Contracts");
    await page.check('input[value="03-24"]');
    await page.check('input[value="06-24"]');
    await page.click('button:has-text("Confirm Selection")');

    // Start backtest
    await page.click('button:has-text("Start Backtest")');

    // Wait for backtest to start
    await expect(page.locator("text=Backtest started")).toBeVisible();

    // Wait for progress indicator
    await expect(page.locator('[data-testid="progress-bar"]')).toBeVisible();

    // Wait for backtest to complete (with timeout)
    await expect(page.locator("text=Completed")).toBeVisible({
      timeout: 60000,
    });

    // Verify results are displayed
    await expect(page.locator('[data-testid="total-return"]')).toBeVisible();
    await expect(page.locator('[data-testid="sharpe-ratio"]')).toBeVisible();
    await expect(page.locator('[data-testid="max-drawdown"]')).toBeVisible();

    // Navigate to trades tab
    await page.click('button[role="tab"]:has-text("Trades")');

    // Verify trades table is populated
    const tradeRows = page.locator(
      'table[data-testid="trades-table"] tbody tr'
    );
    await expect(tradeRows).toHaveCount(20); // First page of trades

    // Export results
    await page.click('button:has-text("Export")');
    await page.click("text=Export as CSV");

    // Verify download started
    const downloadPromise = page.waitForEvent("download");
    await page.click('button:has-text("Download CSV")');
    const download = await downloadPromise;

    expect(download.suggestedFilename()).toContain("backtest-results");
    expect(download.suggestedFilename()).toContain(".csv");
  });

  test("should handle errors gracefully", async ({ page }) => {
    // Navigate to backtest page
    await page.goto("/backtests/new");

    // Try to start backtest without required fields
    await page.click('button:has-text("Start Backtest")');

    // Verify validation errors
    await expect(page.locator("text=Strategy is required")).toBeVisible();
    await expect(page.locator("text=Start date is required")).toBeVisible();
    await expect(page.locator("text=End date is required")).toBeVisible();
  });

  test("should stop running backtest", async ({ page }) => {
    // Start a backtest (abbreviated setup)
    await page.goto("/backtests/new");

    // Quick fill required fields
    await page.selectOption('select[name="strategy"]', { index: 1 });
    await page.fill('input[name="startDate"]', "2023-01-01");
    await page.fill('input[name="endDate"]', "2023-01-31");

    // Start backtest
    await page.click('button:has-text("Start Backtest")');

    // Wait for it to start
    await expect(page.locator("text=Running")).toBeVisible();

    // Stop the backtest
    await page.click('button:has-text("Stop Backtest")');

    // Confirm stop
    await page.click('button:has-text("Yes, stop it")');

    // Verify it stopped
    await expect(page.locator("text=Stopped")).toBeVisible();
  });

  test("should navigate between different result views", async ({ page }) => {
    // Go directly to a completed backtest
    await page.goto("/results/test-123");

    // Verify overview tab is active
    await expect(
      page.locator('button[role="tab"][aria-selected="true"]')
    ).toHaveText("Overview");

    // Navigate to Trades
    await page.click('button[role="tab"]:has-text("Trades")');
    await expect(page.locator('[data-testid="trades-table"]')).toBeVisible();

    // Navigate to Risk Analysis
    await page.click('button[role="tab"]:has-text("Risk Analysis")');
    await expect(page.locator('[data-testid="risk-metrics"]')).toBeVisible();

    // Navigate to Charts
    await page.click('button[role="tab"]:has-text("Charts")');
    await expect(
      page.locator('[data-testid="equity-curve-chart"]')
    ).toBeVisible();
  });

  test("should filter and sort trades", async ({ page }) => {
    // Navigate to trades view
    await page.goto("/results/test-123/trades");

    // Apply filters
    await page.selectOption('select[name="direction"]', "long");
    await page.fill('input[name="minPnl"]', "0");
    await page.click('button:has-text("Apply Filters")');

    // Verify filtered results
    const directionCells = page.locator('td[data-testid="trade-direction"]');
    const count = await directionCells.count();

    for (let i = 0; i < count; i++) {
      await expect(directionCells.nth(i)).toHaveText("Long");
    }

    // Sort by PnL
    await page.click('th:has-text("P&L")');

    // Verify sorting (should be ascending first click)
    const pnlCells = page.locator('td[data-testid="trade-pnl"]');
    const firstPnl = await pnlCells.first().textContent();
    const lastPnl = await pnlCells.last().textContent();

    expect(parseFloat(firstPnl!.replace("$", ""))).toBeLessThan(
      parseFloat(lastPnl!.replace("$", ""))
    );
  });

  test("should share backtest results", async ({ page }) => {
    // Navigate to results
    await page.goto("/results/test-123");

    // Click share button
    await page.click('button:has-text("Share")');

    // Select share options
    await page.check('input[name="includeCharts"]');
    await page.check('input[name="includeTrades"]');

    // Generate shareable link
    await page.click('button:has-text("Generate Link")');

    // Verify link is generated
    await expect(page.locator('input[data-testid="share-link"]')).toHaveValue(
      /^https?:\/\/.+/
    );

    // Copy link
    await page.click('button:has-text("Copy Link")');

    // Verify copied confirmation
    await expect(page.locator("text=Link copied!")).toBeVisible();
  });
});
