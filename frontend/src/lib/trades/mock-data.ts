import { Trade, MarketSnapshot } from './types';

// Generate mock trade data for development
export function generateMockTrades(count: number = 100): Trade[] {
  const trades: Trade[] = [];
  const baseDate = new Date('2024-01-01');

  const entryReasons = [
    'Momentum breakout', 'Mean reversion', 'Support bounce', 'Resistance break',
    'Volume spike', 'Technical pattern', 'Trend continuation', 'Gap fill'
  ];

  const exitReasons = [
    'Take profit', 'Stop loss', 'Time exit', 'Signal reversal',
    'Risk management', 'Target reached', 'Trailing stop', 'Market close'
  ];

  const signalTypes = [
    'RSI oversold', 'MACD crossover', 'Bollinger squeeze', 'Volume breakout',
    'Moving average cross', 'Pattern completion', 'Support test', 'Resistance test'
  ];

  for (let i = 0; i < count; i++) {
    const signalTime = new Date(baseDate.getTime() + i * 86400000 + Math.random() * 86400000);
    const entryDelay = Math.random() * 300000; // 0-5 minutes
    const entryTime = new Date(signalTime.getTime() + entryDelay);
    const duration = Math.random() * 7200000 + 300000; // 5 minutes to 2 hours
    const exitTime = new Date(entryTime.getTime() + duration);

    const side = Math.random() > 0.5 ? 'long' : 'short';
    const signalPrice = 15000 + Math.random() * 2000; // MNQ price range
    const entrySlippage = (Math.random() - 0.5) * 2; // -1 to +1 point slippage
    const entryPrice = signalPrice + entrySlippage;

    // Generate realistic P&L distribution (more losers, occasional big winners)
    const isWinner = Math.random() > 0.4; // 60% win rate
    let pnlPoints: number;

    if (isWinner) {
      // Winners: mostly small, occasional big wins
      pnlPoints = Math.random() > 0.1 ?
        Math.random() * 20 + 5 : // Small wins: 5-25 points
        Math.random() * 100 + 50; // Big wins: 50-150 points
    } else {
      // Losers: controlled risk
      pnlPoints = -(Math.random() * 30 + 5); // Losses: 5-35 points
    }

    const exitPrice = side === 'long' ? entryPrice + pnlPoints : entryPrice - pnlPoints;
    const exitSlippage = (Math.random() - 0.5) * 1; // Exit slippage
    const quantity = Math.floor(Math.random() * 5) + 1; // 1-5 contracts

    const pnl = (side === 'long' ?
      (exitPrice - entryPrice) :
      (entryPrice - exitPrice)) * quantity * 2; // $2 per point for MNQ

    const returnPct = pnl / (entryPrice * quantity * 2);

    // Generate max profit/loss during trade
    const maxFavorableMove = Math.abs(pnlPoints) + Math.random() * 20;
    const maxAdverseMove = Math.random() * 15 + 5;

    const maxProfit = isWinner ?
      Math.max(pnl, pnl + Math.random() * 20) :
      Math.random() * 10 + 2;

    const maxLoss = isWinner ?
      -(Math.random() * 10 + 2) :
      Math.min(pnl, pnl - Math.random() * 10);

    const trade: Trade = {
      id: `trade_${i.toString().padStart(6, '0')}`,
      backtestId: 'backtest_001',

      signalTime: signalTime.toISOString(),
      entryTime: entryTime.toISOString(),
      exitTime: exitTime.toISOString(),
      duration: duration,

      side,
      quantity,

      signalPrice,
      entryPrice,
      exitPrice,

      pnl,
      returnPct,
      maxProfit,
      maxLoss,

      entrySlippage,
      exitSlippage,

      entryReason: entryReasons[Math.floor(Math.random() * entryReasons.length)],
      exitReason: exitReasons[Math.floor(Math.random() * exitReasons.length)],
      signalType: signalTypes[Math.floor(Math.random() * signalTypes.length)],

      stopLoss: entryPrice + (side === 'long' ? -25 : 25),
      takeProfit: entryPrice + (side === 'long' ? 50 : -50),

      marketContext: generateMockMarketContext()
    };

    trades.push(trade);
  }

  // Sort by entry time
  return trades.sort((a, b) => new Date(a.entryTime).getTime() - new Date(b.entryTime).getTime());
}

function generateMockMarketContext(): MarketSnapshot {
  return {
    volatility: Math.random() * 0.03 + 0.005, // 0.5% to 3.5% volatility
    volumeRank: Math.random(), // Percentile rank
    trendStrength: Math.random() * 100, // ADX value
    regime: Math.random() > 0.5 ? 'trending' : 'ranging',
    conditions: [
      Math.random() > 0.7 ? 'High volume' : 'Normal volume',
      Math.random() > 0.8 ? 'News event' : null,
      Math.random() > 0.9 ? 'Market open' : null,
      Math.random() > 0.85 ? 'Earnings season' : null
    ].filter(Boolean) as string[]
  };
}

// Get sample trade for testing
export function getSampleTrade(): Trade {
  return generateMockTrades(1)[0];
}
