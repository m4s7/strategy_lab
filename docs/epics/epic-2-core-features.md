# Epic 2: Core Backtesting Features

## Epic Goal
Implement the essential backtesting workflow including dashboard overview, backtest configuration, execution control, and basic results visualization to enable users to run and monitor backtests through the web interface.

## Epic Description

**Business Value:**
Enable users to configure and execute backtests through an intuitive web interface, replacing command-line workflows with visual controls and real-time monitoring capabilities.

**Technical Scope:**
- Dashboard with system status and backtest overview
- Backtest configuration interface with strategy selection
- Execution control panel with real-time progress tracking
- Basic results visualization and metrics display
- Integration with existing Strategy Lab Python backend

## User Stories

### Story 2.1: System Dashboard
**As a** trading researcher
**I want** a dashboard showing system status and backtest overview
**So that** I can quickly understand system health and recent activity

**Acceptance Criteria:**
- [ ] Dashboard displays active backtest count and status
- [ ] System resource utilization shown (CPU, memory)
- [ ] Recent backtest results summary displayed
- [ ] Data availability overview (available contract months, data quality)
- [ ] Quick action buttons for common tasks
- [ ] Real-time updates via WebSocket
- [ ] Responsive layout for different screen sizes

**Technical Requirements:**
- Create dashboard page as Next.js app route
- Implement metrics API endpoints in FastAPI
- Connect to existing Python strategy engine for system stats
- Use charts library (Recharts) for resource visualizations
- WebSocket subscription for live system updates

### Story 2.2: Strategy Selection & Configuration
**As a** trading researcher
**I want** to select and configure strategies through a web form
**So that** I can set up backtests without writing configuration files

**Acceptance Criteria:**
- [ ] Dropdown showing available registered strategies
- [ ] Strategy documentation displayed when selected
- [ ] Dynamic parameter input forms based on strategy requirements
- [ ] Parameter validation with helpful error messages
- [ ] Template saving and loading functionality
- [ ] Configuration preview before execution
- [ ] Form remembers last used configuration

**Technical Requirements:**
- Connect to Strategy Lab's strategy registry
- Dynamic form generation based on strategy parameter schemas
- Implement configuration templates storage
- Add form validation using React Hook Form + Zod
- Create API endpoints for strategy management

### Story 2.3: Data Configuration Interface
**As a** trading researcher
**I want** to configure data parameters for backtests
**So that** I can specify date ranges, contracts, and data levels visually

**Acceptance Criteria:**
- [ ] Date range picker with calendar interface
- [ ] Available data indicators showing data quality/coverage
- [ ] Contract month selection with multi-select capability
- [ ] Data level selection (L1/L2) with descriptions
- [ ] Data quality warnings for selected ranges
- [ ] Estimated backtest duration display
- [ ] Configuration validation before proceeding

**Technical Requirements:**
- Integrate with MNQ Parquet file index
- Create date picker component with data availability overlay
- Implement data quality checking API endpoints
- Add duration estimation based on data volume

### Story 2.4: Backtest Execution Control
**As a** trading researcher
**I want** to start, monitor, and control backtest execution
**So that** I can track progress and manage running tests

**Acceptance Criteria:**
- [ ] Start backtest button with confirmation dialog
- [ ] Real-time progress bars with meaningful stages
- [ ] ETA calculation and display
- [ ] Pause/resume functionality (if supported by engine)
- [ ] Cancel backtest with confirmation
- [ ] Queue management for multiple backtests
- [ ] Status updates via WebSocket
- [ ] Error handling and display

**Technical Requirements:**
- Integrate with existing BacktestEngine
- Implement job queue management
- WebSocket events for progress streaming
- Create progress tracking components
- Handle backtest lifecycle management

### Story 2.5: Basic Results Visualization
**As a** trading researcher
**I want** to see backtest results with key metrics and charts
**So that** I can quickly evaluate strategy performance

**Acceptance Criteria:**
- [ ] Key metrics display (Sharpe ratio, returns, drawdown, win rate)
- [ ] Equity curve visualization
- [ ] Basic performance statistics table
- [ ] Results loading states and error handling
- [ ] Export functionality for results data
- [ ] Link to detailed analysis views
- [ ] Comparison with previous backtest results

**Technical Requirements:**
- Connect to backtest results storage
- Implement chart components using Recharts
- Create results API endpoints
- Add export functionality (CSV, JSON)
- Performance optimization for large datasets

### Story 2.6: Real-time Monitoring System
**As a** trading researcher
**I want** real-time updates during backtest execution
**So that** I can monitor progress without page refreshing

**Acceptance Criteria:**
- [ ] Live progress updates every 100ms
- [ ] Real-time metrics streaming during execution
- [ ] System resource monitoring
- [ ] Error and warning notifications
- [ ] Connection status indicator
- [ ] Automatic reconnection on disconnect
- [ ] Performance metrics (processing speed, ETA updates)

**Technical Requirements:**
- Implement WebSocket message protocol
- Create real-time update components
- Handle connection state management
- Optimize update frequency to prevent UI blocking
- Add connection recovery mechanisms

## Definition of Done

**Epic Completion Criteria:**
- [ ] All user stories completed with acceptance criteria met
- [ ] Complete backtest workflow functional (configure → execute → view results)
- [ ] Real-time updates working reliably
- [ ] Integration with existing Python backend successful
- [ ] Performance meets requirements (< 2min workflow completion)
- [ ] Error handling covers common failure scenarios

**User Acceptance:**
- [ ] User can complete full backtest workflow in under 2 minutes
- [ ] System handles concurrent backtests without issues
- [ ] Real-time updates provide meaningful feedback
- [ ] Results display is accurate and useful
- [ ] UI is intuitive and requires minimal training

## Dependencies
- Epic 1 (Foundation) completed
- Access to existing Strategy Lab Python components
- MNQ Parquet data files available and indexed
- Strategy registry populated with test strategies

## Integration Points
- Strategy Lab BacktestEngine
- Strategy registry system
- MNQ data index (parquet files)
- Existing performance analytics modules

## Risks & Mitigation
- **Risk**: Performance issues with large datasets
- **Mitigation**: Implement data pagination, streaming, and progressive loading

- **Risk**: WebSocket connection stability
- **Mitigation**: Add robust reconnection logic and fallback to polling

- **Risk**: Integration complexity with existing Python codebase
- **Mitigation**: Create clear API boundaries and test integration points thoroughly

## Estimated Effort
- **Total Effort**: 2-3 weeks
- **Story Points**: 34 (2.1: 5pts, 2.2: 8pts, 2.3: 5pts, 2.4: 8pts, 2.5: 5pts, 2.6: 3pts)
- **Team Size**: 2-3 developers

## Success Metrics
- Backtest workflow completion time < 2 minutes
- Real-time update latency < 200ms
- System uptime > 99% during backtests
- User task completion rate > 95%
