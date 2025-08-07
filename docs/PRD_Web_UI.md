# Product Requirements Document (PRD)
# Strategy Lab Web UI for Backtesting Control, Analysis & Optimization

## 1. Executive Summary

### Product Vision
Create a powerful, single-user web interface for Strategy Lab that provides complete control over backtesting operations, advanced analysis capabilities, and strategy optimization - all running on a private server (lab.m4s8.dev) behind VPN for personal trading research.

### Key Objectives
- Provide fast, efficient control over backtesting execution without unnecessary overhead
- Enable deep analysis of trading performance with professional-grade visualizations
- Support rapid strategy iteration and parameter optimization
- Maximize performance and responsiveness for single-user workload
- Create a personalized trading research environment optimized for productivity

## 2. Problem Statement

### Current Challenges
- Command-line interface limits accessibility and usability
- Difficulty visualizing complex trading metrics and patterns
- No real-time monitoring of backtest progress
- Limited ability to compare multiple strategy configurations
- Lack of interactive exploration of trade-by-trade performance

### User Pain Points
- Cannot easily monitor long-running backtests
- Difficult to identify patterns in trading performance
- Time-consuming to compare different strategy parameters
- No visual representation of order book dynamics
- Limited ability to drill down into specific trades

## 3. Target User

### Single User Profile
**Personal Trading Researcher**
- Sole user of the system running on private infrastructure
- Develops and tests MNQ futures scalping strategies
- Requires maximum performance without multi-user overhead
- Values speed, efficiency, and deep analytical capabilities
- Needs seamless integration with existing Python codebase

### Key Requirements
- **High Performance**: No authentication overhead or multi-user considerations
- **Full Control**: Direct access to all system capabilities
- **Rapid Iteration**: Quick strategy testing and modification cycles
- **Deep Analysis**: Professional-grade tools for trade-level inspection
- **Customization**: Ability to modify and extend without restrictions
- **Efficiency**: Optimized for single-user workflow patterns

## 4. Functional Requirements

### 4.1 Dashboard & Monitoring
- **Real-time System Status**
  - Active backtest count and status
  - System resource utilization (CPU, memory)
  - Data availability overview
  - Strategy registry status

- **Performance Overview**
  - Key metrics at a glance (Sharpe, returns, drawdown)
  - Recent backtest results summary
  - Equity curve visualization
  - Alert notifications for completed/failed tests

### 4.2 Backtest Configuration
- **Strategy Selection**
  - Dropdown of registered strategies
  - Strategy documentation display
  - Parameter input forms with validation
  - Template saving/loading

- **Data Configuration**
  - Date range picker with available data indicators
  - Contract month selection
  - Data level selection (L1/L2)
  - Data quality indicators

- **Execution Settings**
  - Thread count configuration
  - Memory allocation controls
  - Output format selection
  - Priority queuing

### 4.3 Execution Control
- **Backtest Management**
  - Start/pause/cancel controls
  - Batch execution support
  - Queue management
  - Progress tracking with ETA

- **Real-time Monitoring**
  - Live progress bars
  - Performance metrics updates
  - Resource usage graphs
  - Error/warning logs

### 4.4 Results Analysis
- **Performance Metrics**
  - Comprehensive statistics dashboard
  - Risk-adjusted returns (Sharpe, Sortino, Calmar)
  - Drawdown analysis
  - Trade statistics (win rate, profit factor)

- **Visualization Suite**
  - Interactive equity curves
  - Drawdown charts
  - Returns distribution histograms
  - P&L heatmaps by time/day
  - Order flow visualization

- **Comparative Analysis**
  - Side-by-side strategy comparison
  - Parameter sensitivity analysis
  - A/B testing interface
  - Benchmark overlays

### 4.5 Trade Explorer
- **Trade-Level Analysis**
  - Detailed trade journal
  - Entry/exit visualization on charts
  - MAE/MFE analysis
  - Trade duration analysis
  - Time-of-day patterns

- **Filtering & Search**
  - Multi-criteria trade filtering
  - Advanced search capabilities
  - Custom trade tagging
  - Export filtered results

### 4.6 Optimization Module
- **Parameter Optimization**
  - Grid search interface
  - Genetic algorithm controls
  - Walk-forward analysis setup
  - 3D parameter surface plots

- **Optimization Monitoring**
  - Real-time convergence graphs
  - Best parameter tracking
  - Resource allocation
  - Early stopping controls

## 5. Technical Requirements

### 5.1 Architecture
- **Frontend Framework**: Next.js 14+ with React 18+ for modern, performant UI
- **Backend**: FastAPI for REST API and WebSocket support
- **Database**: SQLite for simplicity or PostgreSQL for advanced queries
- **Cache**: In-memory caching (no Redis needed for single user)
- **Job Management**: Python threading/multiprocessing (no message queue needed)

### 5.2 Performance Requirements
- Page load time < 1 second (local network)
- Real-time updates every 100ms for running backtests
- Support unlimited concurrent backtests (limited only by server resources)
- Handle datasets with 100M+ ticks efficiently
- Chart rendering < 200ms for 1M data points (no network latency)

### 5.3 Data Integration
- Direct connection to Parquet data files
- Real-time streaming of backtest results
- Efficient data aggregation for large datasets
- Support for Level 1 and Level 2 market data

### 5.4 Security & Access
- Authentication system not needed because it's just me
- Server is running behind a VPN

### 5.5 Next.js Architecture
- **App Router**: Using Next.js 14+ App Router for better performance
- **API Routes**: Backend for Frontend (BFF) pattern for data aggregation
- **Server Components**: Default to server components, client components only when needed
- **Data Fetching**: Server-side data fetching with streaming support
- **Caching**: Aggressive caching with revalidation strategies
- **Static Generation**: Pre-render unchanging pages at build time

### 5.6 API Design
- **REST Endpoints**:
  - `GET /api/backtests` - List all backtests
  - `POST /api/backtests` - Create new backtest
  - `GET /api/backtests/:id` - Get backtest details
  - `DELETE /api/backtests/:id` - Cancel backtest
  - `GET /api/strategies` - List available strategies
  - `GET /api/data/contracts` - List available contracts
  - `GET /api/metrics/:id` - Get performance metrics
- **WebSocket Events**:
  - `backtest:progress` - Real-time progress updates
  - `backtest:complete` - Completion notifications
  - `metrics:update` - Live metric updates
  - `system:status` - System resource updates

## 6. User Interface Design

### 6.1 Design Principles
- **Performance First**: Server-side rendering with Next.js for instant loads
- **Real-time Updates**: WebSocket integration for live data streaming
- **Keyboard-Driven**: Extensive keyboard shortcuts for efficiency
- **Data Dense**: Maximum information density without clutter
- **Responsive**: Optimized for desktop with responsive scaling

### 6.2 Key UI Components
- **App Shell**: Persistent navigation with collapsible sidebar
- **Data Grids**: Virtual scrolling for large datasets (react-window)
- **Charts**: Interactive charts with zoom/pan (Recharts + D3.js)
- **Command Palette**: Quick actions via Cmd+K (cmdk)
- **Split Views**: Resizable panels for multi-tasking (react-resizable-panels)

### 6.3 Visual Design
- **Theme**: Dark mode optimized for long sessions
- **Typography**: Monospace for data, Inter for UI
- **Colors**: High contrast with semantic color coding
- **Animations**: Subtle transitions with Framer Motion
- **Layout**: CSS Grid for complex layouts, Flexbox for components

## 7. Success Metrics

### 7.1 Productivity Metrics
- Time from idea to backtest results
- Number of strategy iterations per day
- Speed of parameter optimization cycles
- Efficiency of trade analysis workflow

### 7.2 Performance Metrics
- Backtest execution speed vs CLI
- UI responsiveness under heavy load
- Memory efficiency with large datasets
- Parallel backtest throughput

### 7.3 Quality Metrics
- System stability (uptime)
- Result accuracy verification
- Data processing reliability
- Error recovery effectiveness

## 8. Implementation Phases

### Phase 1: Foundation (Week 1)
- Next.js project setup with TypeScript
- FastAPI backend with core endpoints
- Basic routing and layout components
- Authentication-free direct access
- Development environment configuration

### Phase 2: Core Features (Week 2)
- Dashboard with real-time metrics
- Backtest configuration interface
- Execution control panel
- WebSocket integration for live updates
- Basic results visualization

### Phase 3: Analysis Tools (Week 3)
- Advanced charting with D3.js/Recharts
- Trade explorer with filtering
- Performance metrics dashboard
- Comparative analysis views
- Export functionality

### Phase 4: Optimization (Week 4)
- Parameter optimization interface
- Grid search visualization
- Genetic algorithm controls
- Walk-forward analysis setup
- 3D optimization surfaces

### Phase 5: Polish & Performance (Week 5)
- UI/UX refinements
- Performance optimization
- Caching strategies
- Error handling
- Production deployment

## 9. Dependencies & Risks

### 9.1 Dependencies
- hftbacktest library stability
- Parquet file data availability
- Python package compatibility
- Server infrastructure readiness

### 9.2 Risks & Mitigation
| Risk | Impact | Probability | Mitigation |
|------|---------|------------|------------|
| Performance degradation with large datasets | High | Medium | Implement efficient data sampling and aggregation |
| Memory overflow with multiple backtests | High | Low | Resource monitoring and automatic cleanup |
| Data corruption during concurrent access | High | Low | File locking and transaction management |
| UI blocking during heavy computation | Medium | Medium | Background processing with progress indicators |

## 10. Future Enhancements

### Near-term (3-6 months)
- Automated strategy discovery using ML
- Custom backtesting metrics builder
- Advanced position sizing algorithms
- Integration with broker APIs for live trading
- Automated report generation with insights

### Long-term (6-12 months)
- AI-powered strategy optimization
- Real-time market data integration
- Paper trading simulation mode
- Advanced risk management tools
- Strategy performance prediction models

## 11. Success Criteria

The Web UI will be considered successful when:
1. Full backtest workflow completion in < 2 minutes
2. 99% of backtests complete without errors
3. Instant performance analysis (< 500ms load time on local network)
4. 10x improvement in strategy iteration speed vs CLI
5. Zero downtime during normal operations
6. Ability to run 50+ backtests per day efficiently

## 12. Appendices

### A. Technical Stack Details
- **Frontend**:
  - Next.js 14+ with App Router
  - React 18+ with TypeScript
  - Tailwind CSS for styling
  - shadcn/ui for components
  - Recharts/D3.js for visualizations
  - TanStack Query for data fetching
  - Zustand for state management
- **Backend**:
  - FastAPI 0.100+ for REST API
  - WebSockets for real-time updates
  - Pydantic for data validation
- **Database**: SQLite (default), PostgreSQL (optional)
- **Deployment**: PM2 for Next.js, systemd for FastAPI on Ubuntu Server

### B. Mockup References
- TradingView for charting inspiration
- QuantConnect for backtest interface patterns
- ThinkOrSwim for professional trading UI
- Jupyter Lab for notebook-style interaction

### C. Deployment Configuration
- **Server**: lab.m4s8.dev (Ubuntu Server)
- **Access**: VPN-only (no public internet exposure)
- **Ports**:
  - 3000 (Next.js frontend)
  - 8000 (FastAPI backend)
- **Process Manager**:
  - PM2 for Next.js
  - systemd for FastAPI
- **Build**: Next.js production build with optimization
- **Monitoring**: Local resource monitoring only

### D. Personalization Features
- Customizable keyboard shortcuts
- Saved workspace layouts
- Personal trading notes/annotations
- Custom metric definitions
- Quick access bookmarks for frequent operations

### E. Next.js Project Structure
```
strategy-lab-ui/
├── app/                      # Next.js App Router
│   ├── (dashboard)/         # Dashboard layout group
│   │   ├── page.tsx         # Main dashboard
│   │   ├── backtests/       # Backtest management
│   │   ├── strategies/      # Strategy configuration
│   │   ├── results/         # Results analysis
│   │   └── trades/          # Trade explorer
│   ├── api/                 # API routes
│   │   ├── backtests/       # Backtest endpoints
│   │   ├── strategies/      # Strategy endpoints
│   │   └── ws/              # WebSocket handler
│   └── layout.tsx           # Root layout
├── components/              # React components
│   ├── ui/                  # shadcn/ui components
│   ├── charts/              # Chart components
│   ├── tables/              # Data grid components
│   └── forms/               # Form components
├── lib/                     # Utilities
│   ├── api.ts               # API client
│   ├── ws.ts                # WebSocket client
│   └── utils.ts             # Helper functions
├── hooks/                   # Custom React hooks
├── stores/                  # Zustand stores
└── types/                   # TypeScript types
```

---

**Document Version**: 1.1
**Last Updated**: 2025-08-06
**Status**: Final Draft
**Owner**: Personal Trading Research
**Deployment**: Private server (lab.m4s8.dev) behind VPN
