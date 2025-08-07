# 12. Appendices

## A. Technical Stack Details
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

## B. Mockup References
- TradingView for charting inspiration
- QuantConnect for backtest interface patterns
- ThinkOrSwim for professional trading UI
- Jupyter Lab for notebook-style interaction

## C. Deployment Configuration
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

## D. Personalization Features
- Customizable keyboard shortcuts
- Saved workspace layouts
- Personal trading notes/annotations
- Custom metric definitions
- Quick access bookmarks for frequent operations

## E. Next.js Project Structure
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
