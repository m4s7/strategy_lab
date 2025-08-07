export interface Trade {
  id: string;
  backtestId: string;

  // Timing
  signalTime: string;
  entryTime: string;
  exitTime: string;
  duration: number; // milliseconds

  // Trade details
  side: 'long' | 'short';
  quantity: number;

  // Pricing
  signalPrice: number;
  entryPrice: number;
  exitPrice: number;

  // Performance
  pnl: number;
  returnPct: number;
  maxProfit: number;
  maxLoss: number;

  // Slippage
  entrySlippage: number;
  exitSlippage: number;

  // Reasons
  entryReason: string;
  exitReason: string;
  signalType: string;

  // Risk management
  stopLoss?: number;
  takeProfit?: number;
  stopLossUpdates?: StopLossUpdate[];

  // Context
  marketContext?: MarketSnapshot;
}

export interface StopLossUpdate {
  time: string;
  oldValue: number;
  newValue: number;
  reason: string;
}

export interface MarketSnapshot {
  volatility: number;
  volumeRank: number;
  trendStrength: number;
  regime: 'trending' | 'ranging';
  priceContext?: OHLC[];
  conditions: string[];
}

export interface OHLC {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface TradeStats {
  totalTrades: number;
  winRate: number;
  profitFactor: number;
  avgWin: number;
  avgLoss: number;
  expectancy: number;
  maxConsecutiveWins: number;
  maxConsecutiveLosses: number;
  largestWin: number;
  largestLoss: number;
}

export interface TradeFilters {
  dateRange: {
    start: string | null;
    end: string | null;
  };
  profitability: 'all' | 'winners' | 'losers';
  minDuration: number | null;
  maxDuration: number | null;
  tags: string[];
  side?: 'all' | 'long' | 'short';
  minPnl?: number;
  maxPnl?: number;
}

export type GroupingCriteria =
  | 'hourOfDay'
  | 'dayOfWeek'
  | 'month'
  | 'entryReason'
  | 'exitReason'
  | 'duration'
  | 'side';

export interface GroupedData {
  group: string;
  value: number;
  trades: number;
  details: {
    winRate: number;
    avgPnl: number;
    totalPnl: number;
  };
}

export interface SortConfig {
  key: keyof Trade;
  direction: 'asc' | 'desc';
}

export interface TimelineEvent {
  type: 'signal' | 'entry' | 'management' | 'exit';
  time: string;
  price?: number;
  description: string;
  slippage?: number;
  details?: any;
}
