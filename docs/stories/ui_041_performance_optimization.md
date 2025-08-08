# UI_041: UI Performance Optimization

## Story Details
- **Story ID**: UI_041
- **Status**: Done

## Story
As a trader, I want the web interface to be fast and responsive even when working with large datasets and complex visualizations so that I can analyze results efficiently without delays.

## Acceptance Criteria
1. Implement data virtualization for large lists and tables
2. Optimize chart rendering for datasets with millions of points
3. Add progressive loading for heavy components
4. Implement efficient caching strategies
5. Minimize bundle size and optimize code splitting
6. Achieve sub-second page load times
7. Maintain 60 FPS during interactions
8. Support smooth scrolling with large datasets

## Technical Requirements

### Frontend Performance Optimizations
```typescript
// lib/performance/data-virtualization.tsx
import { VirtualList } from '@tanstack/react-virtual';
import { useInfiniteQuery } from '@tanstack/react-query';

interface VirtualizedDataTableProps<T> {
  fetchData: (params: FetchParams) => Promise<PagedResult<T>>;
  columns: ColumnDef<T>[];
  rowHeight?: number;
  overscan?: number;
}

export function VirtualizedDataTable<T>({
  fetchData,
  columns,
  rowHeight = 50,
  overscan = 10
}: VirtualizedDataTableProps<T>) {
  const parentRef = useRef<HTMLDivElement>(null);

  // Infinite query for data fetching
  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage
  } = useInfiniteQuery({
    queryKey: ['virtualizedData'],
    queryFn: ({ pageParam = 0 }) => fetchData({
      offset: pageParam,
      limit: 50
    }),
    getNextPageParam: (lastPage, pages) => {
      return lastPage.hasMore ? pages.length * 50 : undefined;
    }
  });

  const allRows = useMemo(() => {
    return data?.pages.flatMap(page => page.items) ?? [];
  }, [data]);

  // Virtual list instance
  const virtualizer = useVirtualizer({
    count: allRows.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => rowHeight,
    overscan,
    // Load more when reaching the end
    onChange: (instance) => {
      const lastItem = instance.getVirtualItems().at(-1);
      if (
        lastItem &&
        lastItem.index >= allRows.length - 1 &&
        hasNextPage &&
        !isFetchingNextPage
      ) {
        fetchNextPage();
      }
    }
  });

  return (
    <div ref={parentRef} className="h-full overflow-auto">
      <div
        style={{
          height: `${virtualizer.getTotalSize()}px`,
          width: '100%',
          position: 'relative'
        }}
      >
        {virtualizer.getVirtualItems().map((virtualItem) => {
          const row = allRows[virtualItem.index];
          return (
            <div
              key={virtualItem.key}
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                height: `${virtualItem.size}px`,
                transform: `translateY(${virtualItem.start}px)`
              }}
            >
              <TableRow data={row} columns={columns} />
            </div>
          );
        })}
      </div>
      {isFetchingNextPage && <LoadingIndicator />}
    </div>
  );
}
```

### Chart Performance Optimization
```typescript
// lib/performance/optimized-charts.tsx
import { memo, useMemo, useCallback } from 'react';
import * as d3 from 'd3';
import { useWebGLRenderer } from '@/hooks/useWebGLRenderer';

interface OptimizedChartProps {
  data: DataPoint[];
  width: number;
  height: number;
  threshold?: number;
}

export const OptimizedChart = memo(({
  data,
  width,
  height,
  threshold = 10000
}: OptimizedChartProps) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const webglRef = useRef<HTMLCanvasElement>(null);

  // Decide rendering strategy based on data size
  const renderStrategy = useMemo(() => {
    if (data.length > threshold) return 'webgl';
    if (data.length > threshold / 2) return 'canvas';
    return 'svg';
  }, [data.length, threshold]);

  // Data decimation for large datasets
  const processedData = useMemo(() => {
    if (data.length <= threshold) return data;

    // Use LTTB (Largest Triangle Three Buckets) algorithm
    return downsampleLTTB(data, Math.min(threshold, data.length));
  }, [data, threshold]);

  // WebGL rendering for massive datasets
  const webglRenderer = useWebGLRenderer(webglRef.current);

  useEffect(() => {
    if (renderStrategy === 'webgl' && webglRenderer) {
      webglRenderer.render(processedData, { width, height });
    } else if (renderStrategy === 'canvas') {
      renderCanvas();
    }
  }, [processedData, renderStrategy, width, height]);

  const renderCanvas = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Clear canvas
    ctx.clearRect(0, 0, width, height);

    // Set up scales
    const xScale = d3.scaleTime()
      .domain(d3.extent(processedData, d => d.time))
      .range([0, width]);

    const yScale = d3.scaleLinear()
      .domain(d3.extent(processedData, d => d.value))
      .range([height, 0]);

    // Render with path batching
    ctx.beginPath();
    ctx.strokeStyle = '#8884d8';
    ctx.lineWidth = 1;

    processedData.forEach((d, i) => {
      const x = xScale(d.time);
      const y = yScale(d.value);

      if (i === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    });

    ctx.stroke();
  }, [processedData, width, height]);

  if (renderStrategy === 'svg') {
    return <SVGChart data={processedData} width={width} height={height} />;
  }

  if (renderStrategy === 'webgl') {
    return <canvas ref={webglRef} width={width} height={height} />;
  }

  return <canvas ref={canvasRef} width={width} height={height} />;
});

// LTTB downsampling algorithm
function downsampleLTTB(data: DataPoint[], threshold: number): DataPoint[] {
  if (data.length <= threshold) return data;

  const sampled: DataPoint[] = [];
  const bucketSize = (data.length - 2) / (threshold - 2);

  // Always include first point
  sampled.push(data[0]);

  let a = 0; // Previous selected point

  for (let i = 0; i < threshold - 2; i++) {
    const avgRangeStart = Math.floor((i + 1) * bucketSize) + 1;
    const avgRangeEnd = Math.floor((i + 2) * bucketSize) + 1;
    const avgRangeEnd2 = avgRangeEnd < data.length ? avgRangeEnd : data.length;

    // Calculate average for next bucket
    let avgX = 0;
    let avgY = 0;
    for (let j = avgRangeStart; j < avgRangeEnd2; j++) {
      avgX += data[j].time.getTime();
      avgY += data[j].value;
    }
    avgX /= avgRangeEnd2 - avgRangeStart;
    avgY /= avgRangeEnd2 - avgRangeStart;

    // Find point with largest triangle area
    const rangeStart = Math.floor(i * bucketSize) + 1;
    const rangeEnd = Math.floor((i + 1) * bucketSize) + 1;

    let maxArea = -1;
    let maxAreaIndex = rangeStart;

    for (let j = rangeStart; j < rangeEnd; j++) {
      const area = Math.abs(
        (data[a].time.getTime() - avgX) * (data[j].value - data[a].value) -
        (data[a].time.getTime() - data[j].time.getTime()) * (avgY - data[a].value)
      ) * 0.5;

      if (area > maxArea) {
        maxArea = area;
        maxAreaIndex = j;
      }
    }

    sampled.push(data[maxAreaIndex]);
    a = maxAreaIndex;
  }

  // Always include last point
  sampled.push(data[data.length - 1]);

  return sampled;
}
```

### Bundle Optimization
```typescript
// next.config.js
const withBundleAnalyzer = require('@next/bundle-analyzer')({
  enabled: process.env.ANALYZE === 'true',
});

module.exports = withBundleAnalyzer({
  reactStrictMode: true,

  // Enable SWC minification
  swcMinify: true,

  // Optimize images
  images: {
    domains: ['localhost'],
    formats: ['image/avif', 'image/webp'],
  },

  // Module federation for micro-frontends
  webpack: (config, { isServer }) => {
    // Code splitting strategy
    config.optimization = {
      ...config.optimization,
      splitChunks: {
        chunks: 'all',
        cacheGroups: {
          default: false,
          vendors: false,
          // Vendor chunk
          vendor: {
            name: 'vendor',
            chunks: 'all',
            test: /node_modules/,
            priority: 20,
          },
          // Common components chunk
          common: {
            name: 'common',
            minChunks: 2,
            chunks: 'all',
            priority: 10,
            reuseExistingChunk: true,
            enforce: true,
          },
          // Chart libraries chunk
          charts: {
            name: 'charts',
            test: /[\\/]node_modules[\\/](recharts|d3|plotly)[\\/]/,
            chunks: 'all',
            priority: 30,
          },
        },
      },
    };

    // Tree shaking for lodash
    config.resolve.alias = {
      ...config.resolve.alias,
      'lodash': 'lodash-es',
    };

    return config;
  },

  // Experimental features
  experimental: {
    optimizeCss: true,
    legacyBrowsers: false,
  },
});

// Dynamic imports for heavy components
export const DynamicHeavyComponent = dynamic(
  () => import('@/components/heavy/HeavyComponent').then(mod => mod.HeavyComponent),
  {
    loading: () => <ComponentSkeleton />,
    ssr: false,
  }
);
```

### Caching Strategy
```typescript
// lib/performance/cache-manager.ts
import { LRUCache } from 'lru-cache';
import { compress, decompress } from 'lz-string';

interface CacheOptions {
  maxSize?: number;
  ttl?: number;
  compress?: boolean;
}

class CacheManager {
  private memoryCache: LRUCache<string, any>;
  private storageCache: Storage | null;

  constructor(options: CacheOptions = {}) {
    this.memoryCache = new LRUCache({
      max: options.maxSize || 100,
      ttl: options.ttl || 1000 * 60 * 5, // 5 minutes
    });

    this.storageCache = typeof window !== 'undefined' ? localStorage : null;
  }

  async get<T>(key: string): Promise<T | null> {
    // Check memory cache first
    const memCached = this.memoryCache.get(key);
    if (memCached) return memCached;

    // Check storage cache
    if (this.storageCache) {
      const stored = this.storageCache.getItem(key);
      if (stored) {
        try {
          const decompressed = decompress(stored);
          const parsed = JSON.parse(decompressed);

          // Validate TTL
          if (parsed.expires > Date.now()) {
            // Restore to memory cache
            this.memoryCache.set(key, parsed.data);
            return parsed.data;
          } else {
            // Expired, remove
            this.storageCache.removeItem(key);
          }
        } catch (e) {
          console.error('Cache parse error:', e);
        }
      }
    }

    return null;
  }

  async set<T>(key: string, value: T, ttl?: number): Promise<void> {
    // Set in memory cache
    this.memoryCache.set(key, value);

    // Set in storage cache
    if (this.storageCache) {
      const expires = Date.now() + (ttl || this.memoryCache.ttl);
      const data = { data: value, expires };

      try {
        const compressed = compress(JSON.stringify(data));
        this.storageCache.setItem(key, compressed);
      } catch (e) {
        // Storage quota exceeded, clear old entries
        this.clearOldEntries();
      }
    }
  }

  private clearOldEntries(): void {
    if (!this.storageCache) return;

    const keys: string[] = [];
    for (let i = 0; i < this.storageCache.length; i++) {
      const key = this.storageCache.key(i);
      if (key && key.startsWith('cache:')) {
        keys.push(key);
      }
    }

    // Sort by age and remove oldest 25%
    keys.sort().slice(0, Math.floor(keys.length * 0.25))
      .forEach(key => this.storageCache!.removeItem(key));
  }
}

// React Query integration
export function useCachedQuery<T>(
  key: string[],
  fetcher: () => Promise<T>,
  options?: UseQueryOptions<T>
) {
  const cache = useMemo(() => new CacheManager(), []);

  return useQuery({
    queryKey: key,
    queryFn: async () => {
      const cacheKey = key.join(':');
      const cached = await cache.get<T>(cacheKey);

      if (cached) return cached;

      const data = await fetcher();
      await cache.set(cacheKey, data);

      return data;
    },
    staleTime: 1000 * 60 * 5, // 5 minutes
    ...options,
  });
}
```

### Performance Monitoring
```typescript
// lib/performance/monitoring.ts
import { getCLS, getFID, getLCP, getTTFB, getFCP } from 'web-vitals';

interface PerformanceMetrics {
  cls: number;
  fid: number;
  lcp: number;
  ttfb: number;
  fcp: number;
  customMetrics: Record<string, number>;
}

class PerformanceMonitor {
  private metrics: Partial<PerformanceMetrics> = {};
  private observers: Map<string, PerformanceObserver> = new Map();

  constructor() {
    this.initWebVitals();
    this.initCustomObservers();
  }

  private initWebVitals(): void {
    getCLS((metric) => { this.metrics.cls = metric.value; });
    getFID((metric) => { this.metrics.fid = metric.value; });
    getLCP((metric) => { this.metrics.lcp = metric.value; });
    getTTFB((metric) => { this.metrics.ttfb = metric.value; });
    getFCP((metric) => { this.metrics.fcp = metric.value; });
  }

  private initCustomObservers(): void {
    // Long task observer
    if ('PerformanceObserver' in window) {
      const longTaskObserver = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          console.warn('Long task detected:', {
            duration: entry.duration,
            startTime: entry.startTime,
            name: entry.name,
          });

          // Report to analytics
          this.reportMetric('longTask', {
            duration: entry.duration,
            timestamp: entry.startTime,
          });
        }
      });

      longTaskObserver.observe({ entryTypes: ['longtask'] });
      this.observers.set('longtask', longTaskObserver);
    }
  }

  measureComponent(name: string, fn: () => void): void {
    const startMark = `${name}-start`;
    const endMark = `${name}-end`;
    const measureName = `${name}-duration`;

    performance.mark(startMark);
    fn();
    performance.mark(endMark);

    performance.measure(measureName, startMark, endMark);
    const measure = performance.getEntriesByName(measureName)[0];

    if (measure) {
      this.reportMetric('componentRender', {
        component: name,
        duration: measure.duration,
      });
    }
  }

  private reportMetric(name: string, data: any): void {
    // Send to analytics endpoint
    if (process.env.NODE_ENV === 'production') {
      fetch('/api/analytics/performance', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ metric: name, ...data }),
      }).catch(console.error);
    }
  }
}

// React hook for performance monitoring
export function usePerformanceMonitor(componentName: string) {
  const monitor = useMemo(() => new PerformanceMonitor(), []);

  useEffect(() => {
    monitor.measureComponent(componentName, () => {
      // Component mount logic
    });

    return () => {
      // Cleanup
    };
  }, [componentName, monitor]);

  return monitor;
}
```

### Memory Management
```typescript
// lib/performance/memory-management.ts
class MemoryManager {
  private disposables: Set<() => void> = new Set();
  private workers: Map<string, Worker> = new Map();
  private objectURLs: Set<string> = new Set();

  registerDisposable(dispose: () => void): void {
    this.disposables.add(dispose);
  }

  createWorker(name: string, scriptURL: string): Worker {
    // Terminate existing worker if any
    this.terminateWorker(name);

    const worker = new Worker(scriptURL);
    this.workers.set(name, worker);

    return worker;
  }

  terminateWorker(name: string): void {
    const worker = this.workers.get(name);
    if (worker) {
      worker.terminate();
      this.workers.delete(name);
    }
  }

  createObjectURL(blob: Blob): string {
    const url = URL.createObjectURL(blob);
    this.objectURLs.add(url);
    return url;
  }

  revokeObjectURL(url: string): void {
    URL.revokeObjectURL(url);
    this.objectURLs.delete(url);
  }

  cleanup(): void {
    // Dispose all registered disposables
    this.disposables.forEach(dispose => dispose());
    this.disposables.clear();

    // Terminate all workers
    this.workers.forEach(worker => worker.terminate());
    this.workers.clear();

    // Revoke all object URLs
    this.objectURLs.forEach(url => URL.revokeObjectURL(url));
    this.objectURLs.clear();
  }

  getMemoryUsage(): MemoryInfo | null {
    if ('memory' in performance) {
      return (performance as any).memory;
    }
    return null;
  }
}

// React hook for memory management
export function useMemoryManagement() {
  const manager = useMemo(() => new MemoryManager(), []);

  useEffect(() => {
    return () => {
      manager.cleanup();
    };
  }, [manager]);

  return manager;
}
```

## UI/UX Considerations
- Show loading states during optimization
- Provide feedback for performance improvements
- Graceful degradation for slower devices
- Progressive enhancement approach
- Maintain visual consistency during optimizations
- User-configurable performance settings

## Testing Requirements
1. Performance benchmarks for key operations
2. Memory leak detection tests
3. Bundle size monitoring
4. Load time measurements
5. FPS monitoring during interactions
6. Cross-browser performance testing

## Dependencies
- UI_001: Next.js foundation
- UI_021: Interactive charts
- UI_023: Portfolio analysis
- UI_024: Trade analysis

## Story Points: 13

## Priority: High

## Implementation Notes
- Use Chrome DevTools for profiling
- Implement performance budgets
- Monitor Core Web Vitals
- Consider using Partytown for third-party scripts
- Add service worker for offline caching
