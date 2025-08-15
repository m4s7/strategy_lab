import { http, HttpResponse } from "msw";
import {
  mockBacktestData,
  mockStrategyData,
  mockSystemStatus,
} from "../fixtures/backtest";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const handlers = [
  // System status
  http.get(`${API_URL}/api/health`, () => {
    return HttpResponse.json({
      status: "healthy",
      version: "1.0.0",
      timestamp: new Date().toISOString(),
    });
  }),

  http.get(`${API_URL}/api/system/status`, () => {
    return HttpResponse.json(mockSystemStatus);
  }),

  // Strategies
  http.get(`${API_URL}/api/strategies`, () => {
    return HttpResponse.json({
      strategies: [mockStrategyData],
    });
  }),

  http.get(`${API_URL}/api/strategies/:id`, ({ params }) => {
    return HttpResponse.json({
      ...mockStrategyData,
      id: params.id as string,
    });
  }),

  http.post(`${API_URL}/api/strategies`, async ({ request }) => {
    const body = await request.json();
    return HttpResponse.json(
      {
        ...mockStrategyData,
        ...body,
        id: "new-strategy-" + Date.now(),
      },
      { status: 201 }
    );
  }),

  // Backtests
  http.get(`${API_URL}/api/backtests`, () => {
    return HttpResponse.json({
      backtests: [mockBacktestData],
      total: 1,
      page: 1,
      pageSize: 20,
    });
  }),

  http.get(`${API_URL}/api/backtests/:id`, ({ params }) => {
    return HttpResponse.json({
      ...mockBacktestData,
      id: params.id as string,
    });
  }),

  http.post(`${API_URL}/api/backtests`, async ({ request }) => {
    const body = await request.json();
    return HttpResponse.json(
      {
        id: "backtest-" + Date.now(),
        status: "pending",
        ...body,
      },
      { status: 201 }
    );
  }),

  http.get(`${API_URL}/api/backtests/:id/results`, ({ params }) => {
    return HttpResponse.json({
      id: params.id as string,
      results: {
        totalReturn: 0.125,
        sharpeRatio: 1.8,
        maxDrawdown: 0.08,
        winRate: 0.65,
        totalTrades: 150,
        profitFactor: 1.8,
        averageWin: 25.5,
        averageLoss: -12.3,
        expectancy: 8.2,
      },
    });
  }),

  http.get(`${API_URL}/api/backtests/:id/trades`, ({ params }) => {
    return HttpResponse.json({
      trades: Array.from({ length: 20 }, (_, i) => ({
        id: `trade-${i}`,
        backtestId: params.id as string,
        entryTime: new Date(Date.now() - (20 - i) * 86400000).toISOString(),
        exitTime: new Date(
          Date.now() - (20 - i) * 86400000 + 3600000
        ).toISOString(),
        entryPrice: 15000 + Math.random() * 1000,
        exitPrice: 15000 + Math.random() * 1000,
        quantity: 1,
        direction: i % 2 === 0 ? "long" : "short",
        pnl: (Math.random() - 0.4) * 100,
        commission: 2.5,
      })),
      total: 150,
      page: 1,
      pageSize: 20,
    });
  }),

  // Data configuration
  http.get(`${API_URL}/api/data/contracts`, () => {
    return HttpResponse.json({
      contracts: [
        {
          month: "03-24",
          startDate: "2024-03-01",
          endDate: "2024-03-31",
          tickCount: 1500000,
        },
        {
          month: "06-24",
          startDate: "2024-06-01",
          endDate: "2024-06-30",
          tickCount: 1800000,
        },
      ],
    });
  }),

  http.post(`${API_URL}/api/data/validate`, async ({ request }) => {
    const body = await request.json();
    return HttpResponse.json({
      valid: true,
      contracts: body.contracts,
      totalTicks: 3300000,
      estimatedDuration: 45,
    });
  }),

  // Optimization
  http.post(`${API_URL}/api/optimization/grid-search`, async ({ request }) => {
    const body = await request.json();
    return HttpResponse.json(
      {
        id: "opt-" + Date.now(),
        type: "grid-search",
        status: "pending",
        ...body,
      },
      { status: 201 }
    );
  }),

  http.get(`${API_URL}/api/optimization/:id/status`, ({ params }) => {
    return HttpResponse.json({
      id: params.id as string,
      status: "completed",
      progress: 100,
      currentIteration: 100,
      totalIterations: 100,
      bestResult: {
        parameters: { stopLoss: 15, takeProfit: 30 },
        sharpeRatio: 2.1,
        totalReturn: 0.18,
      },
    });
  }),

  // WebSocket mock endpoint
  http.get(`${API_URL}/ws`, () => {
    return new HttpResponse(null, {
      status: 101,
      headers: {
        Upgrade: "websocket",
        Connection: "Upgrade",
      },
    });
  }),
];
