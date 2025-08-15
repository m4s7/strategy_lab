export const mockBacktestData = {
  id: "test-123",
  status: "completed" as const,
  strategyId: "strategy-456",
  config: {
    startDate: "2023-01-01",
    endDate: "2023-12-31",
    initialCapital: 100000,
    dataLevel: "level1" as const,
    contracts: ["03-24", "06-24"],
  },
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
    calmarRatio: 1.56,
    sortinoRatio: 2.1,
    maxConsecutiveLosses: 4,
    maxConsecutiveWins: 8,
    averageTradeTime: 3600,
    profitableMonths: 8,
    losingMonths: 4,
  },
  equityCurve: Array.from({ length: 252 }, (_, i) => ({
    timestamp: new Date(2023, 0, 1 + i).toISOString(),
    value: 100000 * (1 + 0.125 * (i / 251) + Math.sin(i / 10) * 0.02),
  })),
  createdAt: "2023-12-31T10:00:00Z",
  completedAt: "2023-12-31T10:05:00Z",
  duration: 300,
};

export const mockStrategyData = {
  id: "strategy-456",
  name: "Test Scalping Strategy",
  type: "scalping",
  description: "A test scalping strategy for unit tests",
  parameters: {
    stopLoss: 10,
    takeProfit: 20,
    positionSize: 1,
    entryThreshold: 0.8,
    exitThreshold: 0.2,
    maxHoldTime: 300,
    useTrailingStop: false,
  },
  version: "1.0.0",
  createdAt: "2023-12-01T10:00:00Z",
  updatedAt: "2023-12-01T10:00:00Z",
};

export const mockSystemStatus = {
  cpuUsage: 45.2,
  memoryUsage: 62.8,
  diskUsage: 35.4,
  activeBacktests: 2,
  queuedBacktests: 5,
  completedToday: 12,
  averageExecutionTime: 180,
  systemHealth: "healthy" as const,
  services: {
    api: "running",
    database: "running",
    redis: "running",
    websocket: "running",
  },
};

export const mockTradeData = {
  id: "trade-001",
  backtestId: "test-123",
  entryTime: "2023-06-15T10:30:00Z",
  exitTime: "2023-06-15T10:45:00Z",
  entryPrice: 15250.5,
  exitPrice: 15275.75,
  quantity: 1,
  direction: "long" as const,
  pnl: 25.25,
  commission: 2.5,
  netPnl: 22.75,
  percentReturn: 0.15,
  mae: -5.0,
  mfe: 30.0,
  exitReason: "take_profit",
};

export const mockOptimizationResult = {
  id: "opt-001",
  type: "grid-search",
  status: "completed" as const,
  parameters: {
    stopLoss: { min: 5, max: 20, step: 5 },
    takeProfit: { min: 10, max: 40, step: 10 },
    positionSize: { min: 1, max: 3, step: 1 },
  },
  results: Array.from({ length: 48 }, (_, i) => ({
    iteration: i,
    parameters: {
      stopLoss: 5 + (i % 4) * 5,
      takeProfit: 10 + (Math.floor(i / 4) % 4) * 10,
      positionSize: 1 + Math.floor(i / 16),
    },
    metrics: {
      sharpeRatio: 0.5 + Math.random() * 2,
      totalReturn: -0.1 + Math.random() * 0.4,
      maxDrawdown: 0.05 + Math.random() * 0.15,
      winRate: 0.4 + Math.random() * 0.3,
    },
  })),
  bestResult: {
    parameters: { stopLoss: 15, takeProfit: 30, positionSize: 2 },
    metrics: {
      sharpeRatio: 2.1,
      totalReturn: 0.18,
      maxDrawdown: 0.08,
      winRate: 0.65,
    },
  },
  createdAt: "2023-12-31T08:00:00Z",
  completedAt: "2023-12-31T10:00:00Z",
};
