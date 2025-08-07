import { Trade, GroupingCriteria, GroupedData } from './types';

export function groupTrades(
  trades: Trade[],
  groupBy: GroupingCriteria,
  metric: string
): GroupedData[] {
  const groups = new Map<string, Trade[]>();

  trades.forEach(trade => {
    const key = getGroupKey(trade, groupBy);
    if (!groups.has(key)) {
      groups.set(key, []);
    }
    groups.get(key)!.push(trade);
  });

  return Array.from(groups.entries())
    .map(([group, trades]) => ({
      group,
      value: calculateMetricValue(trades, metric),
      trades: trades.length,
      details: getGroupDetails(trades)
    }))
    .sort((a, b) => {
      // Sort by group name for time-based groupings
      if (['hourOfDay', 'dayOfWeek', 'month'].includes(groupBy)) {
        return getGroupSortOrder(a.group, groupBy) - getGroupSortOrder(b.group, groupBy);
      }
      // Sort by value for other groupings
      return b.value - a.value;
    });
}

export function getGroupKey(trade: Trade, groupBy: GroupingCriteria): string {
  const entryDate = new Date(trade.entryTime);
  
  switch (groupBy) {
    case 'hourOfDay':
      return entryDate.getHours().toString().padStart(2, '0') + ':00';
    
    case 'dayOfWeek':
      return ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'][
        entryDate.getDay()
      ];
    
    case 'month':
      return entryDate.toLocaleString('default', { month: 'long' });
    
    case 'entryReason':
      return trade.entryReason || 'Unknown';
    
    case 'exitReason':
      return trade.exitReason || 'Unknown';
    
    case 'duration':
      return getDurationBucket(trade.duration);
    
    case 'side':
      return trade.side === 'long' ? 'Long' : 'Short';
    
    default:
      return 'Unknown';
  }
}

export function getDurationBucket(duration: number): string {
  const minutes = duration / (1000 * 60);
  const hours = duration / (1000 * 60 * 60);
  
  if (minutes < 5) return '< 5min';
  if (minutes < 15) return '5-15min';
  if (minutes < 30) return '15-30min';
  if (minutes < 60) return '30-60min';
  if (hours < 2) return '1-2hr';
  if (hours < 4) return '2-4hr';
  if (hours < 8) return '4-8hr';
  return '> 8hr';
}

export function calculateMetricValue(trades: Trade[], metric: string): number {
  if (trades.length === 0) return 0;

  switch (metric) {
    case 'count':
      return trades.length;
    
    case 'pnl':
      return trades.reduce((sum, t) => sum + t.pnl, 0);
    
    case 'winRate':
      const winners = trades.filter(t => t.pnl > 0).length;
      return winners / trades.length;
    
    case 'avgReturn':
      const totalReturn = trades.reduce((sum, t) => sum + t.returnPct, 0);
      return totalReturn / trades.length;
    
    default:
      return 0;
  }
}

export function getGroupDetails(trades: Trade[]) {
  if (trades.length === 0) {
    return { winRate: 0, avgPnl: 0, totalPnl: 0 };
  }

  const winners = trades.filter(t => t.pnl > 0).length;
  const totalPnl = trades.reduce((sum, t) => sum + t.pnl, 0);
  
  return {
    winRate: winners / trades.length,
    avgPnl: totalPnl / trades.length,
    totalPnl
  };
}

function getGroupSortOrder(group: string, groupBy: GroupingCriteria): number {
  switch (groupBy) {
    case 'hourOfDay':
      return parseInt(group.split(':')[0]);
    
    case 'dayOfWeek':
      const dayOrder = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
      return dayOrder.indexOf(group);
    
    case 'month':
      const monthOrder = [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
      ];
      return monthOrder.indexOf(group);
    
    default:
      return 0;
  }
}