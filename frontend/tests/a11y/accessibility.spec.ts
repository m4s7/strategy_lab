import { test, expect } from "@playwright/test";
import { injectAxe, checkA11y, getViolations } from "axe-playwright";

test.describe("Accessibility Tests", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
    await injectAxe(page);
  });

  test("dashboard should have no accessibility violations", async ({
    page,
  }) => {
    await checkA11y(page, null, {
      detailedReport: true,
      detailedReportOptions: {
        html: true,
      },
    });
  });

  test("forms should be accessible", async ({ page }) => {
    await page.goto("/strategies/new");
    await injectAxe(page);

    await checkA11y(page, '[data-testid="strategy-form"]', {
      rules: {
        label: { enabled: true },
        "aria-required-attr": { enabled: true },
        "form-field-multiple-labels": { enabled: true },
        "autocomplete-valid": { enabled: true },
      },
    });
  });

  test("navigation should be keyboard accessible", async ({ page }) => {
    // Test tab navigation
    await page.keyboard.press("Tab");
    const firstFocused = await page.evaluate(
      () => document.activeElement?.tagName
    );
    expect(firstFocused).toBeTruthy();

    // Tab through navigation
    for (let i = 0; i < 5; i++) {
      await page.keyboard.press("Tab");
    }

    // Test enter key on link
    await page.keyboard.press("Enter");

    // Verify navigation occurred
    expect(page.url()).not.toBe("/");
  });

  test("charts should have proper ARIA labels", async ({ page }) => {
    await page.goto("/charts/interactive");
    await injectAxe(page);

    // Check chart accessibility
    await checkA11y(page, '[data-testid="chart-container"]', {
      rules: {
        "aria-label": { enabled: true },
        "role-img-alt": { enabled: true },
      },
    });

    // Verify alternative text representation
    const chartAltText = await page.locator('[data-testid="chart-data-table"]');
    await expect(chartAltText).toHaveAttribute("role", "table");
  });

  test("modals should trap focus", async ({ page }) => {
    await page.goto("/strategies");
    await page.click('button:has-text("New Strategy")');

    // Wait for modal
    await page.waitForSelector('[role="dialog"]');

    // Check modal accessibility
    await injectAxe(page);
    await checkA11y(page, '[role="dialog"]');

    // Test focus trap
    const modalElements = await page
      .locator(
        '[role="dialog"] *:is(button, input, select, textarea, a[href], [tabindex])'
      )
      .all();

    // Tab through all focusable elements
    for (let i = 0; i < modalElements.length + 1; i++) {
      await page.keyboard.press("Tab");
    }

    // Focus should wrap back to first element
    const focusedElement = await page.evaluate(
      () => document.activeElement?.getAttribute("data-testid")
    );
    expect(focusedElement).toBeTruthy();
  });

  test("color contrast should meet WCAG standards", async ({ page }) => {
    await checkA11y(page, null, {
      rules: {
        "color-contrast": { enabled: true },
      },
    });
  });

  test("images should have alt text", async ({ page }) => {
    const violations = await getViolations(page, null, {
      rules: {
        "image-alt": { enabled: true },
      },
    });

    expect(violations).toHaveLength(0);
  });

  test("form errors should be announced", async ({ page }) => {
    await page.goto("/backtests/new");
    await injectAxe(page);

    // Submit empty form
    await page.click('button[type="submit"]');

    // Wait for errors
    await page.waitForSelector('[role="alert"]');

    // Check error accessibility
    await checkA11y(page, "form", {
      rules: {
        "aria-valid-attr-value": { enabled: true },
        "aria-describedby": { enabled: true },
      },
    });

    // Verify screen reader announcements
    const errorMessages = await page.locator('[role="alert"]').all();
    for (const error of errorMessages) {
      await expect(error).toHaveAttribute("aria-live", "polite");
    }
  });

  test("tables should have proper headers", async ({ page }) => {
    await page.goto("/results/test-123/trades");
    await injectAxe(page);

    await checkA11y(page, "table", {
      rules: {
        "table-duplicate-name": { enabled: true },
        "td-headers-attr": { enabled: true },
        "th-has-data-cells": { enabled: true },
      },
    });
  });

  test("skip links should be present", async ({ page }) => {
    const skipLink = page.locator('a[href="#main-content"]');

    // Focus skip link
    await page.keyboard.press("Tab");

    // Verify skip link is visible when focused
    await expect(skipLink).toBeVisible();
    await expect(skipLink).toHaveText(/skip to main content/i);
  });

  test("page should have proper heading hierarchy", async ({ page }) => {
    const violations = await getViolations(page, null, {
      rules: {
        "heading-order": { enabled: true },
        "page-has-heading-one": { enabled: true },
      },
    });

    expect(violations).toHaveLength(0);
  });

  test("interactive elements should have focus indicators", async ({
    page,
  }) => {
    await page.goto("/");

    // Tab to first interactive element
    await page.keyboard.press("Tab");

    // Check focus visibility
    const focusedElement = await page.evaluate(() => {
      const element = document.activeElement;
      if (!element) return null;

      const styles = window.getComputedStyle(element);
      return {
        outline: styles.outline,
        boxShadow: styles.boxShadow,
        border: styles.border,
      };
    });

    // Should have visible focus indicator
    expect(
      focusedElement?.outline !== "none" ||
        focusedElement?.boxShadow !== "none" ||
        focusedElement?.border !== "none"
    ).toBeTruthy();
  });

  test("loading states should be announced", async ({ page }) => {
    await page.goto("/backtests/new");

    // Start a backtest
    await page.selectOption('select[name="strategy"]', { index: 1 });
    await page.fill('input[name="startDate"]', "2023-01-01");
    await page.fill('input[name="endDate"]', "2023-01-31");
    await page.click('button[type="submit"]');

    // Check loading announcement
    const loadingElement = await page.locator('[aria-live="polite"]');
    await expect(loadingElement).toContainText(/loading|processing/i);
  });

  test("tooltips should be accessible", async ({ page }) => {
    await page.goto("/strategies");

    const tooltip = page.locator('[data-testid="parameter-tooltip"]').first();

    // Hover to show tooltip
    await tooltip.hover();

    // Check tooltip accessibility
    await expect(tooltip).toHaveAttribute("aria-describedby");

    const tooltipContent = await page.locator(
      `#${await tooltip.getAttribute("aria-describedby")}`
    );
    await expect(tooltipContent).toBeVisible();
  });

  test("error recovery should be accessible", async ({ page }) => {
    // Simulate error
    await page.route("**/api/system/status", (route) => {
      route.fulfill({ status: 500 });
    });

    await page.goto("/");
    await injectAxe(page);

    // Wait for error message
    await page.waitForSelector('[data-testid="error-message"]');

    // Check error message accessibility
    await checkA11y(page, '[data-testid="error-message"]');

    // Verify retry button is accessible
    const retryButton = page.locator('button:has-text("Retry")');
    await expect(retryButton).toHaveAttribute("aria-label");
  });
});
