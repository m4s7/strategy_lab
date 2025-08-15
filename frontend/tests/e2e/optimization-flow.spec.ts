import { test, expect } from "@playwright/test";

test.describe("Optimization Flow", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");
  });

  test("should run grid search optimization", async ({ page }) => {
    // Navigate to optimization page
    await page.click("text=Optimization");
    await expect(page).toHaveURL("/optimization");

    // Select optimization type
    await page.click('button:has-text("Grid Search")');

    // Select strategy
    await page.selectOption('select[name="strategy"]', {
      label: "Scalping Strategy",
    });

    // Configure parameter ranges
    await page.fill('input[name="stopLoss.min"]', "5");
    await page.fill('input[name="stopLoss.max"]', "20");
    await page.fill('input[name="stopLoss.step"]', "5");

    await page.fill('input[name="takeProfit.min"]', "10");
    await page.fill('input[name="takeProfit.max"]', "40");
    await page.fill('input[name="takeProfit.step"]', "10");

    // Configure optimization settings
    await page.fill('input[name="startDate"]', "2023-01-01");
    await page.fill('input[name="endDate"]', "2023-12-31");
    await page.selectOption('select[name="metric"]', "sharpeRatio");

    // Calculate combinations
    await page.click('button:has-text("Calculate Combinations")');
    await expect(page.locator("text=16 combinations")).toBeVisible();

    // Start optimization
    await page.click('button:has-text("Start Optimization")');

    // Wait for progress
    await expect(
      page.locator('[data-testid="optimization-progress"]')
    ).toBeVisible();
    await expect(page.locator("text=Running optimization")).toBeVisible();

    // Wait for completion (with reasonable timeout)
    await expect(page.locator("text=Optimization completed")).toBeVisible({
      timeout: 120000,
    });

    // Verify results
    await expect(page.locator('[data-testid="best-parameters"]')).toBeVisible();
    await expect(
      page.locator('[data-testid="parameter-heatmap"]')
    ).toBeVisible();

    // View detailed results
    await page.click('button:has-text("View Detailed Results")');
    await expect(
      page.locator('table[data-testid="results-table"]')
    ).toBeVisible();
  });

  test("should run genetic algorithm optimization", async ({ page }) => {
    // Navigate to optimization
    await page.goto("/optimization");

    // Select genetic algorithm
    await page.click('button:has-text("Genetic Algorithm")');

    // Configure GA settings
    await page.selectOption('select[name="strategy"]', { index: 1 });
    await page.fill('input[name="populationSize"]', "50");
    await page.fill('input[name="generations"]', "20");
    await page.fill('input[name="mutationRate"]', "0.1");
    await page.fill('input[name="crossoverRate"]', "0.8");

    // Set fitness function
    await page.selectOption('select[name="fitnessMetric"]', "sharpeRatio");
    await page.fill('input[name="minSharpe"]', "1.0");

    // Start optimization
    await page.click('button:has-text("Start Evolution")');

    // Monitor evolution progress
    await expect(
      page.locator('[data-testid="generation-chart"]')
    ).toBeVisible();
    await expect(page.locator("text=Generation 1")).toBeVisible();

    // Wait for some generations to complete
    await expect(page.locator("text=Generation 5")).toBeVisible({
      timeout: 30000,
    });

    // Check evolution visualization
    await expect(
      page.locator('[data-testid="fitness-evolution"]')
    ).toBeVisible();
    await expect(
      page.locator('[data-testid="population-diversity"]')
    ).toBeVisible();

    // Stop early if needed
    await page.click('button:has-text("Stop Evolution")');
    await expect(page.locator("text=Evolution stopped")).toBeVisible();
  });

  test("should run walk-forward optimization", async ({ page }) => {
    await page.goto("/optimization");

    // Select walk-forward
    await page.click('button:has-text("Walk-Forward Analysis")');

    // Configure walk-forward settings
    await page.selectOption('select[name="strategy"]', { index: 1 });
    await page.fill('input[name="totalPeriod"]', "365");
    await page.fill('input[name="inSampleRatio"]', "0.7");
    await page.fill('input[name="stepSize"]', "30");

    // Configure parameter ranges (simplified)
    await page.fill('input[name="stopLoss.min"]', "10");
    await page.fill('input[name="stopLoss.max"]', "20");

    // Preview windows
    await page.click('button:has-text("Preview Windows")');
    await expect(
      page.locator('[data-testid="window-visualization"]')
    ).toBeVisible();

    // Start walk-forward
    await page.click('button:has-text("Start Walk-Forward")');

    // Monitor progress
    await expect(page.locator("text=Window 1 of")).toBeVisible();

    // Wait for first window
    await expect(page.locator("text=Window 1 completed")).toBeVisible({
      timeout: 60000,
    });

    // View intermediate results
    await page.click('button:has-text("View Window Results")');
    await expect(
      page.locator('[data-testid="window-performance"]')
    ).toBeVisible();
  });

  test("should visualize 3D parameter surface", async ({ page }) => {
    // Navigate to completed optimization
    await page.goto("/optimization/results/opt-123");

    // Click 3D visualization
    await page.click('button:has-text("3D Parameter Surface")');

    // Wait for 3D chart to load
    await expect(
      page.locator('[data-testid="3d-surface-chart"]')
    ).toBeVisible();

    // Interact with 3D chart
    await page.mouse.move(640, 360);
    await page.mouse.down();
    await page.mouse.move(740, 360);
    await page.mouse.up();

    // Change Z-axis metric
    await page.selectOption('select[name="zAxisMetric"]', "totalReturn");
    await expect(page.locator("text=Z-Axis: Total Return")).toBeVisible();

    // Toggle contour lines
    await page.click('input[name="showContours"]');

    // Export visualization
    await page.click('button:has-text("Export Chart")');
    await page.click("text=Export as PNG");

    const downloadPromise = page.waitForEvent("download");
    await page.click('button:has-text("Download")');
    const download = await downloadPromise;

    expect(download.suggestedFilename()).toContain("parameter-surface");
  });

  test("should compare optimization results", async ({ page }) => {
    await page.goto("/optimization");

    // Navigate to comparison
    await page.click('a:has-text("Compare Results")');

    // Select optimizations to compare
    await page.check('input[value="opt-123"]');
    await page.check('input[value="opt-456"]');
    await page.check('input[value="opt-789"]');

    await page.click('button:has-text("Compare Selected")');

    // View comparison
    await expect(
      page.locator('[data-testid="comparison-chart"]')
    ).toBeVisible();
    await expect(page.locator('[data-testid="metrics-table"]')).toBeVisible();

    // Change comparison metric
    await page.selectOption('select[name="comparisonMetric"]', "maxDrawdown");

    // View parameter differences
    await page.click('tab:has-text("Parameter Analysis")');
    await expect(
      page.locator('[data-testid="parameter-comparison"]')
    ).toBeVisible();
  });

  test("should save and load optimization templates", async ({ page }) => {
    await page.goto("/optimization");

    // Configure an optimization
    await page.click('button:has-text("Grid Search")');
    await page.selectOption('select[name="strategy"]', { index: 1 });

    // Set up parameters
    await page.fill('input[name="stopLoss.min"]', "5");
    await page.fill('input[name="stopLoss.max"]', "25");

    // Save as template
    await page.click('button:has-text("Save as Template")');
    await page.fill('input[name="templateName"]', "E2E Test Template");
    await page.fill(
      'textarea[name="templateDescription"]',
      "Template for E2E testing"
    );
    await page.click('button:has-text("Save Template")');

    await expect(page.locator("text=Template saved")).toBeVisible();

    // Load template
    await page.reload();
    await page.click('button:has-text("Load Template")');
    await page.click("text=E2E Test Template");

    // Verify loaded values
    await expect(page.locator('input[name="stopLoss.min"]')).toHaveValue("5");
    await expect(page.locator('input[name="stopLoss.max"]')).toHaveValue("25");
  });
});
