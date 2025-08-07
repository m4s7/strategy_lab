# 3. Frontend Architecture

## 3.1 Next.js Application Structure

```typescript
// File Structure
strategy-lab-ui/
├── app/                         // App Router
│   ├── layout.tsx              // Root layout with providers
│   ├── page.tsx                // Dashboard home
│   ├── (dashboard)/            // Dashboard route group
│   │   ├── layout.tsx          // Dashboard shell
│   │   ├── backtests/
│   │   │   ├── page.tsx        // Backtest list
│   │   │   ├── [id]/
│   │   │   │   └── page.tsx    // Backtest details
│   │   │   └── new/
│   │   │       └── page.tsx    // New backtest config
│   │   ├── strategies/
│   │   │   ├── page.tsx        // Strategy management
│   │   │   └── [id]/
│   │   │       └── page.tsx    // Strategy details
│   │   ├── results/
│   │   │   ├── page.tsx        // Results browser
│   │   │   └── [id]/
│   │   │       └── page.tsx    // Result analysis
│   │   ├── trades/
│   │   │   └── page.tsx        // Trade explorer
│   │   └── optimization/
│   │       └── page.tsx        // Optimization control
│   └── api/                    // API Routes (BFF)
│       ├── backtests/
│       ├── strategies/
│       └── metrics/
```

## 3.2 Component Architecture

```typescript
// Core Component Hierarchy
interface ComponentArchitecture {
  // Layout Components
  AppShell: {
    CommandBar: CommandPalette,
    Navigation: SideNav | TopNav,
    Content: MainContent,
    StatusBar: SystemStatus
  },

  // Feature Components
  Dashboard: {
    MetricsGrid: MetricCard[],
    ActivityFeed: ActivityItem[],
    QuickActions: ActionButton[],
    SystemHealth: ResourceMonitor
  },

  // Data Components
  DataGrid: {
    VirtualScroller: ReactWindow,
    ColumnConfig: ColumnDef[],
    RowActions: ActionMenu,
    Export: ExportHandler
  },

  // Visualization Components
  Charts: {
    EquityCurve: LineChart,
    DrawdownChart: AreaChart,
    TradeScatter: ScatterPlot,
    Heatmap: HeatmapGrid,
    OrderBook: DepthChart
  }
}
```

## 3.3 State Management Architecture

```typescript
// Zustand Store Structure
interface StoreArchitecture {
  // Application State
  appStore: {
    theme: 'dark',
    commandPaletteOpen: boolean,
    notifications: Notification[],
    shortcuts: KeyboardShortcut[]
  },

  // Backtest State
  backtestStore: {
    activeBacktests: Map<string, Backtest>,
    queue: BacktestJob[],
    results: Map<string, BacktestResult>,
    subscribe: (id: string) => void,
    unsubscribe: (id: string) => void
  },

  // WebSocket State
  wsStore: {
    connection: WebSocket | null,
    status: 'connected' | 'disconnected' | 'error',
    subscriptions: Set<string>,
    messages: MessageQueue
  },

  // UI State
  uiStore: {
    selectedBacktest: string | null,
    compareMode: boolean,
    compareItems: string[],
    filters: FilterState,
    layout: LayoutConfig
  }
}
```

## 3.4 Data Fetching Strategy

```typescript
// TanStack Query Configuration
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 1000,           // 5 seconds
      cacheTime: 10 * 60 * 1000,      // 10 minutes
      refetchOnWindowFocus: false,    // Single user, no need
      retry: 2,
    },
  },
});

// Server Components (Default)
async function DashboardPage() {
  const metrics = await fetchMetrics(); // Server-side fetch
  return <MetricsGrid metrics={metrics} />;
}

// Client Components (Interactive)
'use client';
function BacktestMonitor({ id }: { id: string }) {
  const { data, isLoading } = useBacktest(id);
  const ws = useWebSocket(`backtest:${id}`);
  // Real-time updates via WebSocket
}
```

## 3.5 Performance Optimizations

```typescript
// Optimization Strategies
const optimizations = {
  // 1. Code Splitting
  dynamic: () => import('./HeavyComponent'),

  // 2. Image Optimization
  images: {
    formats: ['webp', 'avif'],
    sizes: [640, 750, 1080, 1200],
    lazy: true
  },

  // 3. Bundle Optimization
  bundler: {
    splitChunks: true,
    treeShaking: true,
    minification: true
  },

  // 4. Rendering Optimization
  rendering: {
    serverComponents: 'default',
    streaming: true,
    suspense: true,
    virtualScrolling: true  // For large datasets
  },

  // 5. Caching Strategy
  caching: {
    staticAssets: '1 year',
    apiResponses: 'stale-while-revalidate',
    localStorage: 'user-preferences',
    sessionStorage: 'temporary-state'
  }
};
```

---
