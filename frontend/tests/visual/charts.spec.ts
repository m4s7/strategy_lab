import { test, expect } from "@playwright/test";
import { setupMockData } from "../e2e/helpers";

test.describe("Chart Visual Regression", () => {
  test.beforeEach(async ({ page }) => {
    await setupMockData(page);
    await page.goto("/");
  });

  test("candlestick chart should render correctly", async ({ page }) => {
    await page.goto("/charts/interactive");

    // Wait for chart to render
    await page.waitForSelector('[data-testid="candlestick-chart"]');
    await page.waitForTimeout(1000); // Wait for animations

    // Take screenshot
    await expect(
      page.locator('[data-testid="candlestick-chart"]')
    ).toHaveScreenshot("candlestick-chart.png", {
      maxDiffPixels: 100,
      threshold: 0.2,
      animations: "disabled",
    });
  });

  test("equity curve chart should match snapshot", async ({ page }) => {
    await page.goto("/results/test-123");

    await page.waitForSelector('[data-testid="equity-curve-chart"]');
    await page.waitForTimeout(500);

    await expect(
      page.locator('[data-testid="equity-curve-chart"]')
    ).toHaveScreenshot("equity-curve-chart.png", {
      maxDiffPixels: 100,
      threshold: 0.2,
    });
  });

  test("performance heatmap should render consistently", async ({ page }) => {
    await page.goto("/results/test-123");
    await page.click('button[role="tab"]:has-text("Charts")');

    await page.waitForSelector('[data-testid="performance-heatmap"]');
    await page.waitForTimeout(500);

    await expect(
      page.locator('[data-testid="performance-heatmap"]')
    ).toHaveScreenshot("performance-heatmap.png", {
      maxDiffPixels: 150,
      threshold: 0.15,
    });
  });

  test("3D parameter surface should render", async ({ page }) => {
    await page.goto("/optimization/results/opt-123");
    await page.click('button:has-text("3D Parameter Surface")');

    await page.waitForSelector('[data-testid="3d-surface-chart"]');
    await page.waitForTimeout(1000); // 3D charts need more time

    // Hide dynamic elements
    await page.addStyleTag({
      content: ".tooltip { display: none !important; }",
    });

    await expect(
      page.locator('[data-testid="3d-surface-chart"]')
    ).toHaveScreenshot("3d-parameter-surface.png", {
      maxDiffPixels: 200,
      threshold: 0.2,
    });
  });

  test("trade distribution chart should be consistent", async ({ page }) => {
    await page.goto("/results/test-123/trades");

    await page.waitForSelector('[data-testid="trade-distribution-chart"]');
    await page.waitForTimeout(500);

    await expect(
      page.locator('[data-testid="trade-distribution-chart"]')
    ).toHaveScreenshot("trade-distribution-chart.png", {
      maxDiffPixels: 100,
      threshold: 0.2,
    });
  });

  test("drawdown chart should render correctly", async ({ page }) => {
    await page.goto("/results/test-123/risk");

    await page.waitForSelector('[data-testid="drawdown-chart"]');
    await page.waitForTimeout(500);

    await expect(
      page.locator('[data-testid="drawdown-chart"]')
    ).toHaveScreenshot("drawdown-chart.png", {
      maxDiffPixels: 100,
      threshold: 0.2,
    });
  });

  test("correlation heatmap should be pixel perfect", async ({ page }) => {
    await page.goto("/portfolio");

    await page.waitForSelector('[data-testid="correlation-heatmap"]');
    await page.waitForTimeout(500);

    await expect(
      page.locator('[data-testid="correlation-heatmap"]')
    ).toHaveScreenshot("correlation-heatmap.png", {
      maxDiffPixels: 50,
      threshold: 0.1,
    });
  });

  test("genetic evolution chart should render", async ({ page }) => {
    await page.goto("/optimization/genetic/gen-123");

    await page.waitForSelector('[data-testid="evolution-chart"]');
    await page.waitForTimeout(500);

    // Hide generation numbers that change
    await page.addStyleTag({
      content: ".generation-label { visibility: hidden !important; }",
    });

    await expect(
      page.locator('[data-testid="evolution-chart"]')
    ).toHaveScreenshot("genetic-evolution-chart.png", {
      maxDiffPixels: 150,
      threshold: 0.2,
    });
  });
});
