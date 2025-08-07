# 2. System Architecture Overview

## 2.1 High-Level Architecture

```mermaid
graph TB
    subgraph "Client Browser"
        UI[Next.js Frontend<br/>React 18 + TypeScript]
        WS[WebSocket Client]
    end

    subgraph "Application Server - lab.m4s8.dev"
        subgraph "Frontend Server :3000"
            NEXT[Next.js Server]
            RSC[React Server Components]
            API_ROUTES[API Routes/BFF]
        end

        subgraph "Backend Server :8000"
            FASTAPI[FastAPI Server]
            WS_SERVER[WebSocket Server]
            EXECUTOR[Backtest Executor]
            OPTIMIZER[Optimization Engine]
        end

        subgraph "Data Layer"
            SQLITE[(SQLite DB)]
            PARQUET[Parquet Files<br/>MNQ Data]
            CACHE[In-Memory Cache]
        end

        subgraph "Python Core"
            ENGINE[Backtest Engine]
            STRATEGIES[Strategy Registry]
            ANALYTICS[Analysis Module]
        end
    end

    UI <--> NEXT
    UI <--> WS
    WS <--> WS_SERVER
    NEXT <--> API_ROUTES
    RSC <--> API_ROUTES
    API_ROUTES <--> FASTAPI
    FASTAPI <--> ENGINE
    FASTAPI <--> SQLITE
    FASTAPI <--> CACHE
    ENGINE <--> PARQUET
    ENGINE <--> STRATEGIES
    ENGINE <--> ANALYTICS
    EXECUTOR <--> ENGINE
    OPTIMIZER <--> ENGINE
    WS_SERVER <--> EXECUTOR
```

## 2.2 Component Responsibilities

| Component | Responsibility | Technology |
|-----------|---------------|------------|
| **Frontend** | UI rendering, user interactions | Next.js, React, TypeScript |
| **API Gateway** | Request routing, data aggregation | Next.js API Routes |
| **Backend API** | Business logic, data processing | FastAPI |
| **WebSocket Server** | Real-time updates, streaming | FastAPI WebSockets |
| **Backtest Engine** | Strategy execution, metrics | Python, hftbacktest |
| **Data Layer** | Persistence, caching | SQLite, Parquet, Memory |

---
