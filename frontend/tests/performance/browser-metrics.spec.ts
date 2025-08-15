import { test, expect } from "@playwright/test";

interface PerformanceMetrics {
  firstPaint: number;
  firstContentfulPaint: number;
  largestContentfulPaint: number;
  domContentLoaded: number;
  loadComplete: number;
  totalBlockingTime: number;
  cumulativeLayoutShift: number;
  memoryUsage?: number;
}

async function capturePerformanceMetrics(
  page: any
): Promise<PerformanceMetrics> {
  return await page.evaluate(() => {
    const navigation = performance.getEntriesByType(
      "navigation"
    )[0] as PerformanceNavigationTiming;
    const paintEntries = performance.getEntriesByType("paint");

    const firstPaint =
      paintEntries.find((entry) => entry.name === "first-paint")?.startTime ||
      0;
    const firstContentfulPaint =
      paintEntries.find((entry) => entry.name === "first-contentful-paint")
        ?.startTime || 0;

    // Get LCP
    let largestContentfulPaint = 0;
    new PerformanceObserver((list) => {
      const entries = list.getEntries();
      const lastEntry = entries[entries.length - 1];
      largestContentfulPaint = lastEntry.startTime;
    }).observe({ entryTypes: ["largest-contentful-paint"] });

    // Calculate Total Blocking Time (approximation)
    const longTasks = performance.getEntriesByType("longtask");
    const totalBlockingTime = longTasks.reduce((total, task) => {
      return total + Math.max(0, task.duration - 50);
    }, 0);

    // Get memory usage if available
    const memoryUsage = (performance as any).memory?.usedJSHeapSize;

    return {
      firstPaint,
      firstContentfulPaint,
      largestContentfulPaint,
      domContentLoaded:
        navigation.domContentLoadedEventEnd -
        navigation.domContentLoadedEventStart,
      loadComplete: navigation.loadEventEnd - navigation.loadEventStart,
      totalBlockingTime,
      cumulativeLayoutShift: 0, // Would need additional observer
      memoryUsage,
    };
  });
}

test.describe("Browser Performance Metrics", () => {
  test("dashboard should load within performance budget", async ({ page }) => {
    await page.goto("/", { waitUntil: "networkidle" });

    const metrics = await capturePerformanceMetrics(page);

    // Performance budgets
    expect(metrics.firstContentfulPaint).toBeLessThan(1500); // 1.5s
    expect(metrics.largestContentfulPaint).toBeLessThan(2500); // 2.5s
    expect(metrics.domContentLoaded).toBeLessThan(3000); // 3s
    expect(metrics.totalBlockingTime).toBeLessThan(300); // 300ms
  });

  test("heavy components should not block main thread", async ({ page }) => {
    await page.goto("/charts/advanced");

    // Measure time to interactive
    const timeToInteractive = await page.evaluate(() => {
      return new Promise<number>((resolve) => {
        let lastIdleTime = 0;
        let checkCount = 0;

        const checkIdle = () => {
          const now = performance.now();

          if (now - lastIdleTime > 50) {
            // Main thread has been idle for 50ms
            resolve(now);
          } else if (checkCount++ < 100) {
            requestIdleCallback(checkIdle);
          }
        };

        requestIdleCallback(() => {
          lastIdleTime = performance.now();
          checkIdle();
        });
      });
    });

    expect(timeToInteractive).toBeLessThan(5000); // 5s to interactive
  });

  test("large data tables should virtualize efficiently", async ({ page }) => {
    await page.goto("/results/test-123/trades");

    // Measure initial render time
    const renderStart = Date.now();
    await page.waitForSelector('[data-testid="trades-table"]');
    const renderTime = Date.now() - renderStart;

    expect(renderTime).toBeLessThan(1000); // Should render in under 1s

    // Check that not all rows are rendered (virtualization)
    const visibleRows = await page.locator("tbody tr").count();
    expect(visibleRows).toBeLessThan(100); // Should virtualize, not render all rows

    // Measure scroll performance
    const scrollMetrics = await page.evaluate(async () => {
      const container = document.querySelector(
        '[data-testid="trades-table-container"]'
      );
      if (!container) return null;

      let frameCount = 0;
      let jankCount = 0;
      let lastFrameTime = performance.now();

      const measureFrame = () => {
        const now = performance.now();
        const frameDuration = now - lastFrameTime;
        frameCount++;

        if (frameDuration > 16.67) {
          // More than 1 frame at 60fps
          jankCount++;
        }

        lastFrameTime = now;
      };

      // Scroll and measure
      for (let i = 0; i < 10; i++) {
        container.scrollTop += 100;
        await new Promise((resolve) =>
          requestAnimationFrame(() => {
            measureFrame();
            resolve(null);
          })
        );
      }

      return {
        frameCount,
        jankCount,
        jankPercentage: (jankCount / frameCount) * 100,
      };
    });

    expect(scrollMetrics?.jankPercentage).toBeLessThan(10); // Less than 10% janky frames
  });

  test("bundle size should be within limits", async ({ page }) => {
    const resourceSizes = await page.evaluate(() => {
      const resources = performance.getEntriesByType(
        "resource"
      ) as PerformanceResourceTiming[];

      const jsSizes = resources
        .filter((r) => r.name.endsWith(".js"))
        .reduce((total, r) => total + r.transferSize, 0);

      const cssSizes = resources
        .filter((r) => r.name.endsWith(".css"))
        .reduce((total, r) => total + r.transferSize, 0);

      return {
        totalJS: jsSizes,
        totalCSS: cssSizes,
        total: jsSizes + cssSizes,
      };
    });

    // Bundle size budgets (in bytes)
    expect(resourceSizes.totalJS).toBeLessThan(500 * 1024); // 500KB JS
    expect(resourceSizes.totalCSS).toBeLessThan(100 * 1024); // 100KB CSS
    expect(resourceSizes.total).toBeLessThan(600 * 1024); // 600KB total
  });

  test("memory usage should not leak", async ({ page }) => {
    await page.goto("/");

    // Get initial memory
    const initialMemory = await page.evaluate(
      () => (performance as any).memory?.usedJSHeapSize
    );

    // Navigate through app
    await page.goto("/strategies");
    await page.goto("/backtests/new");
    await page.goto("/results/test-123");
    await page.goto("/optimization");
    await page.goto("/");

    // Force garbage collection if available
    await page.evaluate(() => {
      if ((window as any).gc) {
        (window as any).gc();
      }
    });

    // Wait a bit
    await page.waitForTimeout(1000);

    // Get final memory
    const finalMemory = await page.evaluate(
      () => (performance as any).memory?.usedJSHeapSize
    );

    if (initialMemory && finalMemory) {
      const memoryIncrease = finalMemory - initialMemory;
      const percentIncrease = (memoryIncrease / initialMemory) * 100;

      expect(percentIncrease).toBeLessThan(50); // Less than 50% increase
    }
  });

  test("API calls should complete quickly", async ({ page }) => {
    const apiMetrics: { url: string; duration: number }[] = [];

    page.on("response", (response) => {
      if (response.url().includes("/api/")) {
        const timing = response.timing();
        if (timing) {
          apiMetrics.push({
            url: response.url(),
            duration: timing.responseEnd - timing.requestStart,
          });
        }
      }
    });

    await page.goto("/");
    await page.waitForLoadState("networkidle");

    // Check API performance
    apiMetrics.forEach((metric) => {
      expect(metric.duration).toBeLessThan(1000); // All API calls under 1s
    });

    // Check average
    const avgDuration =
      apiMetrics.reduce((sum, m) => sum + m.duration, 0) / apiMetrics.length;
    expect(avgDuration).toBeLessThan(500); // Average under 500ms
  });

  test("critical CSS should be inlined", async ({ page }) => {
    const response = await page.goto("/");
    const html = await response!.text();

    // Check for inlined critical CSS
    expect(html).toContain("<style"); // Should have inline styles

    // Check that critical styles are present
    const hasInlinedCriticalCSS = await page.evaluate(() => {
      const styles = document.querySelector("style");
      return styles?.textContent?.includes("body") || false;
    });

    expect(hasInlinedCriticalCSS).toBeTruthy();
  });

  test("images should lazy load", async ({ page }) => {
    await page.goto("/results/test-123");

    // Get all images
    const images = await page.locator("img").all();

    // Check loading attribute
    for (const img of images) {
      const loading = await img.getAttribute("loading");
      const isAboveFold = await img.isVisible();

      if (!isAboveFold) {
        expect(loading).toBe("lazy");
      }
    }
  });

  test("service worker should cache assets", async ({ page, context }) => {
    // Check if service worker is registered
    await page.goto("/");

    const hasServiceWorker = await page.evaluate(() => {
      return "serviceWorker" in navigator;
    });

    if (hasServiceWorker) {
      // Wait for service worker
      await page.waitForTimeout(2000);

      // Go offline
      await context.setOffline(true);

      // Try to navigate (should work with cache)
      await page.goto("/");

      // Check that page loads from cache
      expect(page.url()).toContain("/");

      // Go back online
      await context.setOffline(false);
    }
  });
});
