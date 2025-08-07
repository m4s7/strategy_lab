import { Trade, TradeStats } from './types';

export function calculateTradeStats(trades: Trade[]): TradeStats {
  if (trades.length === 0) {
    return {
      totalTrades: 0,
      winRate: 0,
      profitFactor: 0,
      avgWin: 0,
      avgLoss: 0,
      expectancy: 0,
      maxConsecutiveWins: 0,
      maxConsecutiveLosses: 0,
      largestWin: 0,
      largestLoss: 0
    };
  }

  const winners = trades.filter(t => t.pnl > 0);
  const losers = trades.filter(t => t.pnl < 0);

  const totalWins = winners.reduce((sum, t) => sum + t.pnl, 0);
  const totalLosses = Math.abs(losers.reduce((sum, t) => sum + t.pnl, 0));

  return {
    totalTrades: trades.length,
    winRate: winners.length / trades.length,
    profitFactor: totalLosses > 0 ? totalWins / totalLosses : totalWins,
    avgWin: winners.length > 0 ? totalWins / winners.length : 0,
    avgLoss: losers.length > 0 ? totalLosses / losers.length : 0,
    expectancy: trades.reduce((sum, t) => sum + t.pnl, 0) / trades.length,
    maxConsecutiveWins: calculateMaxConsecutive(trades, true),
    maxConsecutiveLosses: calculateMaxConsecutive(trades, false),
    largestWin: trades.length > 0 ? Math.max(...trades.map(t => t.pnl)) : 0,
    largestLoss: trades.length > 0 ? Math.min(...trades.map(t => t.pnl)) : 0
  };
}

export function calculateMaxConsecutive(trades: Trade[], winners: boolean): number {
  let maxConsecutive = 0;
  let currentConsecutive = 0;

  trades.forEach(trade => {
    const isWinner = trade.pnl > 0;
    if (isWinner === winners) {
      currentConsecutive++;
      maxConsecutive = Math.max(maxConsecutive, currentConsecutive);
    } else {
      currentConsecutive = 0;
    }
  });

  return maxConsecutive;
}

export function calculateEntryEfficiency(trade: Trade): number {
  if (!trade.signalPrice || trade.signalPrice === 0) return 0;
  
  const slippage = Math.abs(trade.entryPrice - trade.signalPrice);
  const maxSlippage = trade.signalPrice * 0.01; // 1% as max reasonable slippage
  
  return Math.max(0, 1 - (slippage / maxSlippage));
}

export function calculateExitEfficiency(trade: Trade): number {
  // Calculate based on how much of the favorable move was captured
  if (trade.side === 'long') {
    const favorableMove = Math.max(0, trade.maxProfit - trade.pnl);
    const totalFavorableMove = trade.maxProfit;
    return totalFavorableMove > 0 ? 1 - (favorableMove / totalFavorableMove) : 1;
  } else {
    // For short trades
    const favorableMove = Math.max(0, trade.maxProfit - trade.pnl);
    const totalFavorableMove = trade.maxProfit;
    return totalFavorableMove > 0 ? 1 - (favorableMove / totalFavorableMove) : 1;
  }
}

export function calculateRiskReward(trade: Trade): number {
  const risk = Math.abs(trade.maxLoss);
  const reward = Math.abs(trade.maxProfit);
  return risk > 0 ? reward / risk : 0;
}

export function calculateTradeDrawdown(trade: Trade): number {
  // Return the maximum adverse excursion as a percentage of entry price
  return Math.abs(trade.maxLoss) / trade.entryPrice;
}

export function filterTrades(trades: Trade[], filters: any): Trade[] {
  return trades.filter(trade => {
    // Date range filter
    if (filters.dateRange.start && new Date(trade.entryTime) < new Date(filters.dateRange.start)) {
      return false;
    }
    if (filters.dateRange.end && new Date(trade.entryTime) > new Date(filters.dateRange.end)) {
      return false;
    }

    // Profitability filter
    if (filters.profitability === 'winners' && trade.pnl <= 0) return false;
    if (filters.profitability === 'losers' && trade.pnl >= 0) return false;

    // Duration filter
    if (filters.minDuration && trade.duration < filters.minDuration) return false;
    if (filters.maxDuration && trade.duration > filters.maxDuration) return false;

    // Side filter
    if (filters.side && filters.side !== 'all' && trade.side !== filters.side) return false;

    // P&L range filter
    if (filters.minPnl && trade.pnl < filters.minPnl) return false;
    if (filters.maxPnl && trade.pnl > filters.maxPnl) return false;

    return true;
  });
}

export function sortTrades(trades: Trade[], sortConfig: any): Trade[] {
  return [...trades].sort((a, b) => {
    const aValue = a[sortConfig.key as keyof Trade];
    const bValue = b[sortConfig.key as keyof Trade];

    if (aValue === bValue) return 0;

    const comparison = aValue > bValue ? 1 : -1;
    return sortConfig.direction === 'asc' ? comparison : -comparison;
  });
}