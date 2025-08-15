import { test, expect, devices } from "@playwright/test";

const viewports = [
  { name: "mobile", viewport: { width: 375, height: 667 } },
  { name: "tablet", viewport: { width: 768, height: 1024 } },
  { name: "desktop", viewport: { width: 1920, height: 1080 } },
  { name: "desktop-4k", viewport: { width: 3840, height: 2160 } },
];

test.describe("Responsive Visual Regression", () => {
  for (const device of viewports) {
    test.describe(`${device.name} viewport`, () => {
      test.use({ viewport: device.viewport });

      test("dashboard should render correctly", async ({ page }) => {
        await page.goto("/");
        await page.waitForLoadState("networkidle");

        // Hide dynamic content
        await page.addStyleTag({
          content: `
            .timestamp, .real-time-value { visibility: hidden !important; }
            .loading-skeleton { display: none !important; }
          `,
        });

        await expect(page).toHaveScreenshot(`dashboard-${device.name}.png`, {
          fullPage: true,
          maxDiffPixels: 200,
          threshold: 0.2,
        });
      });

      test("strategy configuration should be responsive", async ({ page }) => {
        await page.goto("/strategies");
        await page.waitForLoadState("networkidle");

        await expect(page).toHaveScreenshot(`strategies-${device.name}.png`, {
          fullPage: true,
          maxDiffPixels: 200,
          threshold: 0.2,
        });
      });

      test("results page should adapt to viewport", async ({ page }) => {
        await page.goto("/results/test-123");
        await page.waitForLoadState("networkidle");

        // Hide timestamps
        await page.addStyleTag({
          content: ".timestamp { display: none !important; }",
        });

        await expect(page).toHaveScreenshot(`results-${device.name}.png`, {
          fullPage: true,
          maxDiffPixels: 200,
          threshold: 0.2,
        });
      });

      test("navigation menu should be responsive", async ({ page }) => {
        await page.goto("/");

        // For mobile/tablet, open the menu
        if (device.name === "mobile" || device.name === "tablet") {
          const menuButton = page.locator('[data-testid="mobile-menu-button"]');
          if (await menuButton.isVisible()) {
            await menuButton.click();
            await page.waitForTimeout(300); // Wait for animation
          }
        }

        await expect(
          page.locator('[data-testid="navigation"]')
        ).toHaveScreenshot(`navigation-${device.name}.png`, {
          maxDiffPixels: 100,
          threshold: 0.2,
        });
      });

      test("charts should scale properly", async ({ page }) => {
        await page.goto("/charts/interactive");
        await page.waitForSelector('[data-testid="chart-container"]');
        await page.waitForTimeout(500);

        await expect(
          page.locator('[data-testid="chart-container"]')
        ).toHaveScreenshot(`chart-container-${device.name}.png`, {
          maxDiffPixels: 150,
          threshold: 0.2,
        });
      });

      test("forms should be usable on all devices", async ({ page }) => {
        await page.goto("/backtests/new");
        await page.waitForLoadState("networkidle");

        await expect(
          page.locator('[data-testid="backtest-form"]')
        ).toHaveScreenshot(`backtest-form-${device.name}.png`, {
          maxDiffPixels: 150,
          threshold: 0.2,
        });
      });

      test("tables should be scrollable on mobile", async ({ page }) => {
        await page.goto("/results/test-123/trades");
        await page.waitForSelector('[data-testid="trades-table"]');

        await expect(
          page.locator('[data-testid="trades-table-container"]')
        ).toHaveScreenshot(`trades-table-${device.name}.png`, {
          maxDiffPixels: 150,
          threshold: 0.2,
        });
      });

      test("modals should fit viewport", async ({ page }) => {
        await page.goto("/strategies");
        await page.click('button:has-text("New Strategy")');
        await page.waitForSelector('[data-testid="strategy-modal"]');

        await expect(
          page.locator('[data-testid="strategy-modal"]')
        ).toHaveScreenshot(`strategy-modal-${device.name}.png`, {
          maxDiffPixels: 150,
          threshold: 0.2,
        });
      });
    });
  }

  test.describe("Dark mode visual regression", () => {
    test.beforeEach(async ({ page }) => {
      // Set dark mode
      await page.addInitScript(() => {
        localStorage.setItem("theme", "dark");
      });
    });

    test("dashboard dark mode", async ({ page }) => {
      await page.goto("/");
      await page.waitForLoadState("networkidle");

      await expect(page).toHaveScreenshot("dashboard-dark.png", {
        fullPage: true,
        maxDiffPixels: 200,
        threshold: 0.2,
      });
    });

    test("charts dark mode", async ({ page }) => {
      await page.goto("/charts/interactive");
      await page.waitForSelector('[data-testid="chart-container"]');

      await expect(page).toHaveScreenshot("charts-dark.png", {
        fullPage: true,
        maxDiffPixels: 200,
        threshold: 0.2,
      });
    });
  });

  test.describe("Print styles", () => {
    test("results should be printable", async ({ page }) => {
      await page.goto("/results/test-123");
      await page.waitForLoadState("networkidle");

      // Emulate print media
      await page.emulateMedia({ media: "print" });

      await expect(page).toHaveScreenshot("results-print.png", {
        fullPage: true,
        maxDiffPixels: 200,
        threshold: 0.2,
      });
    });
  });
});
