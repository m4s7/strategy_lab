# 5. Technical Requirements

## 5.1 Architecture
- **Frontend Framework**: Next.js 14+ with React 18+ for modern, performant UI
- **Backend**: FastAPI for REST API and WebSocket support
- **Database**: SQLite for simplicity or PostgreSQL for advanced queries
- **Cache**: In-memory caching (no Redis needed for single user)
- **Job Management**: Python threading/multiprocessing (no message queue needed)

## 5.2 Performance Requirements
- Page load time < 1 second (local network)
- Real-time updates every 100ms for running backtests
- Support unlimited concurrent backtests (limited only by server resources)
- Handle datasets with 100M+ ticks efficiently
- Chart rendering < 200ms for 1M data points (no network latency)

## 5.3 Data Integration
- Direct connection to Parquet data files
- Real-time streaming of backtest results
- Efficient data aggregation for large datasets
- Support for Level 1 and Level 2 market data

## 5.4 Security & Access
- Authentication system not needed because it's just me
- Server is running behind a VPN

## 5.5 Next.js Architecture
- **App Router**: Using Next.js 14+ App Router for better performance
- **API Routes**: Backend for Frontend (BFF) pattern for data aggregation
- **Server Components**: Default to server components, client components only when needed
- **Data Fetching**: Server-side data fetching with streaming support
- **Caching**: Aggressive caching with revalidation strategies
- **Static Generation**: Pre-render unchanging pages at build time

## 5.6 API Design
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
