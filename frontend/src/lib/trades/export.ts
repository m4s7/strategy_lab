import { Trade } from './types';
import { calculateEntryEfficiency, calculateExitEfficiency, calculateRiskReward, calculateTradeDrawdown } from './calculations';

export class TradeExporter {
  static async exportToCSV(trades: Trade[], filename: string = 'trades.csv') {
    const headers = [
      'ID', 'Entry Time', 'Exit Time', 'Side', 'Entry Price',
      'Exit Price', 'Quantity', 'P&L', 'Return %', 'Duration',
      'Entry Reason', 'Exit Reason', 'Max Profit', 'Max Loss',
      'Entry Slippage', 'Exit Slippage', 'Signal Price', 'Signal Time'
    ];

    const rows = trades.map(trade => [
      trade.id,
      trade.entryTime,
      trade.exitTime,
      trade.side,
      trade.entryPrice,
      trade.exitPrice,
      trade.quantity,
      trade.pnl,
      trade.returnPct,
      trade.duration,
      trade.entryReason,
      trade.exitReason,
      trade.maxProfit,
      trade.maxLoss,
      trade.entrySlippage,
      trade.exitSlippage,
      trade.signalPrice,
      trade.signalTime
    ]);

    const csv = [
      headers.join(','),
      ...rows.map(row => row.map(cell =>
        typeof cell === 'string' && cell.includes(',') ? `"${cell}"` : cell
      ).join(','))
    ].join('\n');

    downloadFile(csv, filename, 'text/csv');
  }

  static async exportToJSON(trades: Trade[], filename: string = 'trades.json') {
    const data = {
      exportDate: new Date().toISOString(),
      tradeCount: trades.length,
      trades: trades.map(trade => ({
        ...trade,
        analysis: {
          entryEfficiency: calculateEntryEfficiency(trade),
          exitEfficiency: calculateExitEfficiency(trade),
          riskRewardRatio: calculateRiskReward(trade),
          drawdown: calculateTradeDrawdown(trade)
        }
      }))
    };

    downloadFile(JSON.stringify(data, null, 2), filename, 'application/json');
  }

  static async exportToExcel(trades: Trade[], filename: string = 'trades.xlsx') {
    // For Excel export, we'll create a comprehensive CSV that can be opened in Excel
    const headers = [
      'Trade ID', 'Backtest ID', 'Signal Time', 'Entry Time', 'Exit Time',
      'Duration (min)', 'Side', 'Quantity', 'Signal Price', 'Entry Price',
      'Exit Price', 'P&L', 'Return %', 'Max Profit', 'Max Loss',
      'Entry Slippage', 'Exit Slippage', 'Entry Reason', 'Exit Reason',
      'Signal Type', 'Entry Efficiency', 'Exit Efficiency', 'Risk/Reward',
      'Drawdown %'
    ];

    const rows = trades.map(trade => [
      trade.id,
      trade.backtestId,
      new Date(trade.signalTime).toLocaleString(),
      new Date(trade.entryTime).toLocaleString(),
      new Date(trade.exitTime).toLocaleString(),
      Math.round(trade.duration / 60000), // Convert to minutes
      trade.side.toUpperCase(),
      trade.quantity,
      trade.signalPrice,
      trade.entryPrice,
      trade.exitPrice,
      trade.pnl.toFixed(2),
      (trade.returnPct * 100).toFixed(2),
      trade.maxProfit.toFixed(2),
      trade.maxLoss.toFixed(2),
      trade.entrySlippage.toFixed(4),
      trade.exitSlippage.toFixed(4),
      trade.entryReason,
      trade.exitReason,
      trade.signalType,
      (calculateEntryEfficiency(trade) * 100).toFixed(1),
      (calculateExitEfficiency(trade) * 100).toFixed(1),
      calculateRiskReward(trade).toFixed(2),
      (calculateTradeDrawdown(trade) * 100).toFixed(2)
    ]);

    const csv = [
      headers.join(','),
      ...rows.map(row => row.map(cell =>
        typeof cell === 'string' && (cell.includes(',') || cell.includes('\n') || cell.includes('"'))
          ? `"${cell.replace(/"/g, '""')}"`
          : cell
      ).join(','))
    ].join('\n');

    downloadFile(csv, filename.replace('.xlsx', '.csv'), 'text/csv');
  }

  static async exportSummaryReport(trades: Trade[], filename: string = 'trade-summary.txt') {
    const winners = trades.filter(t => t.pnl > 0);
    const losers = trades.filter(t => t.pnl < 0);
    const totalPnl = trades.reduce((sum, t) => sum + t.pnl, 0);
    const avgHoldingTime = trades.reduce((sum, t) => sum + t.duration, 0) / trades.length;

    const report = `
TRADE ANALYSIS SUMMARY
Generated: ${new Date().toLocaleString()}
========================

OVERVIEW
--------
Total Trades: ${trades.length}
Winners: ${winners.length} (${(winners.length / trades.length * 100).toFixed(1)}%)
Losers: ${losers.length} (${(losers.length / trades.length * 100).toFixed(1)}%)

PERFORMANCE
-----------
Total P&L: $${totalPnl.toFixed(2)}
Average P&L: $${(totalPnl / trades.length).toFixed(2)}
Win Rate: ${(winners.length / trades.length * 100).toFixed(1)}%
Profit Factor: ${losers.length > 0 ? (winners.reduce((sum, t) => sum + t.pnl, 0) / Math.abs(losers.reduce((sum, t) => sum + t.pnl, 0))).toFixed(2) : 'N/A'}

WINNERS
-------
Count: ${winners.length}
Total: $${winners.reduce((sum, t) => sum + t.pnl, 0).toFixed(2)}
Average: $${winners.length > 0 ? (winners.reduce((sum, t) => sum + t.pnl, 0) / winners.length).toFixed(2) : '0.00'}
Largest: $${winners.length > 0 ? Math.max(...winners.map(t => t.pnl)).toFixed(2) : '0.00'}

LOSERS
------
Count: ${losers.length}
Total: $${losers.reduce((sum, t) => sum + t.pnl, 0).toFixed(2)}
Average: $${losers.length > 0 ? (losers.reduce((sum, t) => sum + t.pnl, 0) / losers.length).toFixed(2) : '0.00'}
Largest: $${losers.length > 0 ? Math.min(...losers.map(t => t.pnl)).toFixed(2) : '0.00'}

TIMING
------
Average Holding Time: ${Math.round(avgHoldingTime / 60000)} minutes
Shortest Trade: ${Math.min(...trades.map(t => t.duration)) / 60000} minutes
Longest Trade: ${Math.max(...trades.map(t => t.duration)) / 60000} minutes

TOP 5 WINNERS
-------------
${winners.sort((a, b) => b.pnl - a.pnl).slice(0, 5).map((t, i) =>
  `${i + 1}. ${t.id.slice(0, 8)} - $${t.pnl.toFixed(2)} (${(t.returnPct * 100).toFixed(2)}%)`
).join('\n')}

TOP 5 LOSERS
------------
${losers.sort((a, b) => a.pnl - b.pnl).slice(0, 5).map((t, i) =>
  `${i + 1}. ${t.id.slice(0, 8)} - $${t.pnl.toFixed(2)} (${(t.returnPct * 100).toFixed(2)}%)`
).join('\n')}
`;

    downloadFile(report, filename, 'text/plain');
  }
}

function downloadFile(content: string, filename: string, mimeType: string) {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
