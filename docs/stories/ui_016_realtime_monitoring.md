# UI_016: Real-time Monitoring System

## Story
As a trader, I want to monitor running backtests in real-time so that I can track progress and make decisions about whether to continue or abort long-running simulations.

## Acceptance Criteria
1. Display real-time progress for active backtests
2. Show current simulation time vs total time
3. Display processing speed (events/second)
4. Show partial results as they become available
5. Provide abort functionality with confirmation
6. Handle multiple concurrent backtests
7. Persist monitoring state across page refreshes
8. Show resource utilization (CPU, memory)

## Technical Requirements

### Frontend Components
```typescript
// components/monitoring/BacktestMonitor.tsx
interface BacktestMonitor {
  backtestId: string;
  status: 'running' | 'paused' | 'completed' | 'aborted';
  progress: {
    currentTime: number;
    totalTime: number;
    eventsProcessed: number;
    eventsPerSecond: number;
  };
  resources: {
    cpuUsage: number;
    memoryUsage: number;
  };
  partialResults?: {
    pnl: number;
    trades: number;
    sharpe?: number;
  };
}

// Real-time progress bar with ETA
<ProgressBar
  value={progress.currentTime}
  max={progress.totalTime}
  showETA={true}
/>

// Performance metrics display
<MetricsDisplay
  eventsPerSecond={progress.eventsPerSecond}
  cpuUsage={resources.cpuUsage}
  memoryUsage={resources.memoryUsage}
/>
```

### WebSocket Events
```typescript
// WebSocket message types
interface ProgressUpdate {
  type: 'progress';
  backtestId: string;
  timestamp: number;
  progress: number;
  eventsProcessed: number;
  currentPnL?: number;
}

interface ResourceUpdate {
  type: 'resources';
  cpu: number;
  memory: number;
  activeBacktests: number;
}

// Client-side handling
ws.on('progress', (data: ProgressUpdate) => {
  updateBacktestProgress(data);
  if (data.currentPnL !== undefined) {
    updatePartialResults(data.backtestId, { pnl: data.currentPnL });
  }
});
```

### Backend Implementation
```python
# api/monitoring/progress_tracker.py
class ProgressTracker:
    def __init__(self, websocket_manager: WebSocketManager):
        self.ws = websocket_manager
        self.active_backtests = {}

    async def track_backtest(self, backtest_id: str, total_events: int):
        """Initialize tracking for a backtest"""
        self.active_backtests[backtest_id] = {
            'start_time': time.time(),
            'total_events': total_events,
            'processed_events': 0,
            'last_update': time.time()
        }

    async def update_progress(self, backtest_id: str, events_processed: int,
                            partial_results: dict = None):
        """Send progress update via WebSocket"""
        tracker = self.active_backtests.get(backtest_id)
        if not tracker:
            return

        current_time = time.time()
        events_per_second = events_processed / (current_time - tracker['start_time'])

        await self.ws.broadcast({
            'type': 'progress',
            'backtestId': backtest_id,
            'timestamp': current_time,
            'progress': events_processed / tracker['total_events'],
            'eventsProcessed': events_processed,
            'eventsPerSecond': events_per_second,
            'partialResults': partial_results
        })

# Integration with backtest engine
async def run_backtest_with_monitoring(config: BacktestConfig, tracker: ProgressTracker):
    await tracker.track_backtest(config.id, total_events)

    async for chunk in process_data_chunks():
        results = await process_chunk(chunk)
        await tracker.update_progress(
            config.id,
            chunk.end_index,
            {'pnl': results.current_pnl, 'trades': results.trade_count}
        )
```

### Resource Monitoring
```python
# api/monitoring/resource_monitor.py
import psutil
import asyncio

class ResourceMonitor:
    def __init__(self, websocket_manager: WebSocketManager):
        self.ws = websocket_manager
        self.monitoring = False

    async def start_monitoring(self):
        """Monitor system resources every second"""
        self.monitoring = True
        while self.monitoring:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()

            await self.ws.broadcast({
                'type': 'resources',
                'cpu': cpu_percent,
                'memory': memory.percent,
                'activeBacktests': len(BacktestManager.active_backtests)
            })

            await asyncio.sleep(1)
```

### Abort Functionality
```python
# api/endpoints/backtest_control.py
@router.post("/backtests/{backtest_id}/abort")
async def abort_backtest(backtest_id: str):
    """Gracefully abort a running backtest"""
    manager = BacktestManager()

    if backtest_id not in manager.active_backtests:
        raise HTTPException(404, "Backtest not found")

    # Signal abort to backtest process
    await manager.signal_abort(backtest_id)

    # Wait for graceful shutdown (max 5 seconds)
    await manager.wait_for_completion(backtest_id, timeout=5)

    # Save partial results
    partial_results = await manager.get_partial_results(backtest_id)
    await save_aborted_backtest(backtest_id, partial_results)

    return {"status": "aborted", "partial_results": partial_results}
```

### State Persistence
```typescript
// hooks/useBacktestMonitor.ts
export function useBacktestMonitor() {
  const [monitors, setMonitors] = useState<BacktestMonitor[]>([]);

  // Restore monitoring state on mount
  useEffect(() => {
    const savedState = localStorage.getItem('backtest_monitors');
    if (savedState) {
      const parsed = JSON.parse(savedState);
      // Reconnect to active backtests
      parsed.forEach(monitor => {
        if (monitor.status === 'running') {
          subscribeToBacktest(monitor.backtestId);
        }
      });
      setMonitors(parsed);
    }
  }, []);

  // Save state on changes
  useEffect(() => {
    localStorage.setItem('backtest_monitors', JSON.stringify(monitors));
  }, [monitors]);

  return { monitors, updateMonitor, removeMonitor };
}
```

## UI/UX Considerations
- Use smooth animations for progress updates
- Color-code performance metrics (green/yellow/red)
- Provide clear visual feedback for abort actions
- Show estimated time remaining
- Use notifications for backtest completion
- Support minimized monitoring widgets

## Testing Requirements
1. Unit tests for progress calculations
2. WebSocket connection stability tests
3. Resource monitoring accuracy tests
4. Abort functionality edge cases
5. State persistence across refreshes
6. Performance under multiple concurrent backtests

## Dependencies
- UI_001: Next.js foundation
- UI_004: WebSocket infrastructure
- UI_011: System status dashboard
- UI_014: Backtest execution control

## Story Points: 13

## Priority: High

## Implementation Notes
- Consider using Web Workers for heavy calculations
- Implement exponential backoff for WebSocket reconnection
- Cache partial results in IndexedDB for large backtests
- Add option to export monitoring logs
