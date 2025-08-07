# Story UI_011: System Dashboard

## Story Details
- **Story ID**: UI_011
- **Epic**: Epic 2 - Core Backtesting Features
- **Story Points**: 5
- **Priority**: High
- **Type**: User Interface

## User Story
**As a** trading researcher
**I want** a dashboard showing system status and backtest overview
**So that** I can quickly understand system health, recent activity, and navigate to key functions efficiently

## Acceptance Criteria

### 1. System Status Overview
- [ ] Active backtest count displayed with status indicators
- [ ] System resource utilization shown (CPU percentage, memory usage)
- [ ] Database connection status and health
- [ ] WebSocket connection status indicator
- [ ] Data availability overview (MNQ contracts and date ranges)

### 2. Backtest Activity Summary
- [ ] Recent backtest results (last 10) with key metrics
- [ ] Currently running backtests with progress indicators
- [ ] Failed backtests with error summaries
- [ ] Quick access buttons to view detailed results
- [ ] Backtest queue status and estimated completion times

### 3. Performance Metrics Cards
- [ ] Today's statistics (backtests run, success rate, average duration)
- [ ] System performance indicators (average response time, uptime)
- [ ] Data processing statistics (records processed, processing speed)
- [ ] Alert indicators for system issues or warnings

### 4. Quick Actions
- [ ] "New Backtest" button leading to configuration
- [ ] "View All Results" button leading to results browser
- [ ] "System Health" button leading to detailed monitoring
- [ ] Quick strategy selection dropdown for fast backtest setup

### 5. Real-time Updates
- [ ] Dashboard updates automatically via WebSocket
- [ ] Live progress bars for running backtests
- [ ] Real-time system resource monitoring
- [ ] Automatic refresh of status indicators
- [ ] Connection status indicators update in real-time

### 6. Responsive Layout
- [ ] Mobile-responsive design for different screen sizes
- [ ] Card-based layout that adapts to viewport
- [ ] Collapsible sections for smaller screens
- [ ] Touch-friendly controls for mobile devices

## Technical Requirements

### Dashboard Layout Structure
```typescript
interface DashboardLayout {
  header: {
    title: "Strategy Lab Dashboard";
    quickActions: QuickActionButton[];
    systemStatus: SystemStatusIndicator;
  };
  main: {
    systemOverview: SystemMetricsGrid;
    recentActivity: RecentBacktestsList;
    quickStats: PerformanceStatsCards;
    activeBacktests: ActiveBacktestsMonitor;
  };
}
```

### Component Architecture
```typescript
// Main Dashboard Component
export default function Dashboard() {
  const { systemStatus } = useSystemStatus();
  const { recentBacktests } = useRecentBacktests();
  const { activeBacktests } = useActiveBacktests();

  return (
    <DashboardLayout>
      <SystemMetricsGrid metrics={systemStatus} />
      <RecentActivityPanel backtests={recentBacktests} />
      <ActiveBacktestsMonitor backtests={activeBacktests} />
      <QuickActionPanel />
    </DashboardLayout>
  );
}

// System Metrics Grid
interface SystemMetrics {
  cpu: number;
  memory: number;
  diskUsage: number;
  dbStatus: 'connected' | 'disconnected' | 'error';
  wsStatus: 'connected' | 'disconnected' | 'error';
  backtestCount: {
    active: number;
    queued: number;
    completed: number;
    failed: number;
  };
}
```

### API Endpoints Required
```typescript
// System Status API
GET /api/system/status
Response: {
  cpu: number;
  memory: number;
  disk: number;
  database: 'healthy' | 'warning' | 'error';
  websocket: 'connected' | 'disconnected';
  uptime: number;
}

// Recent Backtests API
GET /api/backtests/recent?limit=10
Response: BacktestSummary[]

// Active Backtests API
GET /api/backtests/active
Response: ActiveBacktest[]

// System Statistics API
GET /api/system/stats
Response: {
  today: {
    backtestsRun: number;
    successRate: number;
    averageDuration: number;
  };
  performance: {
    averageResponseTime: number;
    uptime: number;
  };
}
```

### Real-time Data Integration
```typescript
// WebSocket subscriptions for real-time updates
const useRealtimeDashboard = () => {
  const { subscribe, unsubscribe } = useWebSocket();

  useEffect(() => {
    subscribe('system:status', handleSystemUpdate);
    subscribe('backtest:all', handleBacktestUpdate);
    subscribe('system:performance', handlePerformanceUpdate);

    return () => {
      unsubscribe('system:status');
      unsubscribe('backtest:all');
      unsubscribe('system:performance');
    };
  }, []);
};
```

## Definition of Done
- [ ] Dashboard loads in < 2 seconds
- [ ] All system status indicators display correctly
- [ ] Real-time updates work via WebSocket
- [ ] Quick actions navigate to correct pages
- [ ] Responsive design works on mobile and desktop
- [ ] Error states handled gracefully
- [ ] Loading states provide user feedback
- [ ] Data refreshes automatically every 30 seconds

## Testing Checklist
- [ ] Dashboard displays without JavaScript errors
- [ ] System metrics update when backend changes
- [ ] WebSocket connection status indicator works
- [ ] Quick action buttons navigate correctly
- [ ] Responsive layout works on different screen sizes
- [ ] Error handling displays appropriate messages
- [ ] Performance metrics are accurate
- [ ] Auto-refresh doesn't cause memory leaks

## Integration Points
- **System Health**: Integration with UI_002 (FastAPI backend health)
- **Database Status**: Integration with UI_003 (database health check)
- **WebSocket Status**: Integration with UI_004 (WebSocket connection)
- **Backtest Data**: Integration with backtest execution system
- **Navigation**: Links to other parts of the application

## Performance Requirements
- Dashboard load time < 2 seconds
- Real-time updates with < 200ms latency
- Memory usage < 100MB for dashboard page
- Smooth animations and transitions
- No visual jank during updates

## Accessibility Requirements
- Keyboard navigation for all interactive elements
- Screen reader support with proper ARIA labels
- High contrast mode support
- Focus indicators visible
- Text alternatives for visual indicators

## Security Considerations
- No sensitive data exposed in frontend state
- Proper error handling without information leakage
- Rate limiting for API calls
- Input validation for any user inputs

## Implementation Notes
- Use React Server Components where possible for better performance
- Implement proper error boundaries
- Add loading skeletons for better perceived performance
- Use semantic HTML for better accessibility
- Include proper meta tags for SEO (if applicable)

## Follow-up Stories
- UI_012: Strategy Configuration (linked from quick actions)
- UI_016: Real-time Monitoring (enhanced version of dashboard monitoring)
- UI_041: Performance Optimization (dashboard performance improvements)
