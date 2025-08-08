# UI_024: Trade-by-Trade Analysis

## Story Details
- **Story ID**: UI_024
- **Status**: Done

## Story
As a trader, I want to analyze individual trades in detail including entry/exit timing, slippage, market conditions, and profitability patterns so that I can identify areas for strategy improvement.

## Acceptance Criteria
1. Display detailed trade list with filtering and sorting
2. Show trade lifecycle visualization (signal → entry → management → exit)
3. Calculate trade statistics (win rate, profit factor, average win/loss)
4. Analyze entry/exit quality and slippage
5. Group trades by various criteria (time, symbol, strategy rule)
6. Show market context for each trade
7. Export trade data for external analysis
8. Identify best/worst trades with explanations

## Technical Requirements

### Frontend Components
```typescript
// components/trades/TradeAnalysisDashboard.tsx
interface TradeAnalysisDashboard {
  trades: Trade[];
  filters: TradeFilters;
  groupBy: GroupingCriteria;
  selectedTrade: Trade | null;
}

export function TradeAnalysisDashboard({ backtestId }: { backtestId: string }) {
  const [trades, setTrades] = useState<Trade[]>([]);
  const [filters, setFilters] = useState<TradeFilters>({
    dateRange: { start: null, end: null },
    profitability: 'all',
    minDuration: null,
    maxDuration: null,
    tags: []
  });
  const [selectedTrade, setSelectedTrade] = useState<Trade | null>(null);

  return (
    <div className="trade-analysis">
      <TradeStatsSummary trades={filteredTrades} />

      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-2">
          <TradeTable
            trades={filteredTrades}
            onTradeSelect={setSelectedTrade}
            filters={filters}
            onFilterChange={setFilters}
          />
        </div>

        <div className="col-span-1">
          {selectedTrade ? (
            <TradeDetails trade={selectedTrade} />
          ) : (
            <TradeDistributions trades={filteredTrades} />
          )}
        </div>
      </div>

      <TradePatternAnalysis trades={filteredTrades} />
    </div>
  );
}
```

### Trade Table Component (shadcn/ui)
```typescript
// components/trades/TradeTable.tsx
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

export function TradeTable({
  trades,
  onTradeSelect,
  filters,
  onFilterChange
}: TradeTableProps) {
  const [sortConfig, setSortConfig] = useState<SortConfig>({
    key: 'entryTime',
    direction: 'desc'
  });

  const columns: ColumnDef<Trade>[] = [
    {
      accessorKey: 'id',
      header: 'ID',
      cell: ({ row }) => (
        <Badge variant="outline">{row.original.id.slice(0, 8)}</Badge>
      )
    },
    {
      accessorKey: 'entryTime',
      header: 'Entry Time',
      cell: ({ row }) => formatDateTime(row.original.entryTime)
    },
    {
      accessorKey: 'exitTime',
      header: 'Exit Time',
      cell: ({ row }) => formatDateTime(row.original.exitTime)
    },
    {
      accessorKey: 'side',
      header: 'Side',
      cell: ({ row }) => (
        <Badge variant={row.original.side === 'long' ? 'default' : 'secondary'}>
          {row.original.side.toUpperCase()}
        </Badge>
      )
    },
    {
      accessorKey: 'entryPrice',
      header: 'Entry',
      cell: ({ row }) => formatPrice(row.original.entryPrice)
    },
    {
      accessorKey: 'exitPrice',
      header: 'Exit',
      cell: ({ row }) => formatPrice(row.original.exitPrice)
    },
    {
      accessorKey: 'quantity',
      header: 'Size'
    },
    {
      accessorKey: 'pnl',
      header: 'P&L',
      cell: ({ row }) => (
        <span className={row.original.pnl >= 0 ? 'text-green-600' : 'text-red-600'}>
          {formatCurrency(row.original.pnl)}
        </span>
      )
    },
    {
      accessorKey: 'returnPct',
      header: 'Return %',
      cell: ({ row }) => (
        <span className={row.original.returnPct >= 0 ? 'text-green-600' : 'text-red-600'}>
          {(row.original.returnPct * 100).toFixed(2)}%
        </span>
      )
    },
    {
      accessorKey: 'duration',
      header: 'Duration',
      cell: ({ row }) => formatDuration(row.original.duration)
    },
    {
      id: 'actions',
      cell: ({ row }) => (
        <Button
          variant="ghost"
          size="sm"
          onClick={() => onTradeSelect(row.original)}
        >
          <Eye className="h-4 w-4" />
        </Button>
      )
    }
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Trade History</CardTitle>
        <TradeFilters filters={filters} onChange={onFilterChange} />
      </CardHeader>
      <CardContent>
        <DataTable
          columns={columns}
          data={trades}
          onSort={setSortConfig}
          sortConfig={sortConfig}
        />
      </CardContent>
    </Card>
  );
}
```

### Trade Details View
```typescript
// components/trades/TradeDetails.tsx
export function TradeDetails({ trade }: { trade: Trade }) {
  const [activeTab, setActiveTab] = useState('overview');

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Trade Details</CardTitle>
        <Badge variant={trade.pnl >= 0 ? 'success' : 'destructive'}>
          {formatCurrency(trade.pnl)}
        </Badge>
      </CardHeader>
      <CardContent>
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="lifecycle">Lifecycle</TabsTrigger>
            <TabsTrigger value="market">Market</TabsTrigger>
            <TabsTrigger value="analysis">Analysis</TabsTrigger>
          </TabsList>

          <TabsContent value="overview">
            <TradeOverview trade={trade} />
          </TabsContent>

          <TabsContent value="lifecycle">
            <TradeLifecycle trade={trade} />
          </TabsContent>

          <TabsContent value="market">
            <MarketContext trade={trade} />
          </TabsContent>

          <TabsContent value="analysis">
            <TradeAnalysis trade={trade} />
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}

// Trade lifecycle visualization
function TradeLifecycle({ trade }: { trade: Trade }) {
  const events = [
    {
      type: 'signal',
      time: trade.signalTime,
      price: trade.signalPrice,
      description: `${trade.signalType} signal generated`
    },
    {
      type: 'entry',
      time: trade.entryTime,
      price: trade.entryPrice,
      description: `Entered ${trade.side} position`,
      slippage: trade.entryPrice - trade.signalPrice
    },
    {
      type: 'management',
      time: trade.stopLossUpdates?.[0]?.time,
      description: 'Stop loss adjusted',
      details: trade.stopLossUpdates
    },
    {
      type: 'exit',
      time: trade.exitTime,
      price: trade.exitPrice,
      description: `Exited: ${trade.exitReason}`,
      slippage: trade.exitSlippage
    }
  ];

  return (
    <div className="space-y-4">
      <Timeline events={events} />

      <div className="grid grid-cols-2 gap-4">
        <MetricCard
          title="Entry Efficiency"
          value={calculateEntryEfficiency(trade)}
          format="percentage"
          description="How close to signal price"
        />
        <MetricCard
          title="Exit Efficiency"
          value={calculateExitEfficiency(trade)}
          format="percentage"
          description="Capture of available move"
        />
      </div>
    </div>
  );
}
```

### Trade Statistics
```typescript
// components/trades/TradeStatsSummary.tsx
export function TradeStatsSummary({ trades }: { trades: Trade[] }) {
  const stats = useMemo(() => calculateTradeStats(trades), [trades]);

  return (
    <div className="grid grid-cols-6 gap-4 mb-6">
      <StatCard
        title="Total Trades"
        value={stats.totalTrades}
        icon={Activity}
      />
      <StatCard
        title="Win Rate"
        value={`${(stats.winRate * 100).toFixed(1)}%`}
        icon={TrendingUp}
        trend={stats.winRate > 0.5 ? 'up' : 'down'}
      />
      <StatCard
        title="Profit Factor"
        value={stats.profitFactor.toFixed(2)}
        icon={DollarSign}
        trend={stats.profitFactor > 1 ? 'up' : 'down'}
      />
      <StatCard
        title="Avg Win"
        value={formatCurrency(stats.avgWin)}
        icon={Plus}
        className="text-green-600"
      />
      <StatCard
        title="Avg Loss"
        value={formatCurrency(stats.avgLoss)}
        icon={Minus}
        className="text-red-600"
      />
      <StatCard
        title="Expectancy"
        value={formatCurrency(stats.expectancy)}
        icon={Calculator}
        trend={stats.expectancy > 0 ? 'up' : 'down'}
      />
    </div>
  );
}

// Trade statistics calculation
function calculateTradeStats(trades: Trade[]): TradeStats {
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
    largestWin: Math.max(...trades.map(t => t.pnl)),
    largestLoss: Math.min(...trades.map(t => t.pnl))
  };
}
```

### Trade Pattern Analysis
```typescript
// components/trades/TradePatternAnalysis.tsx
export function TradePatternAnalysis({ trades }: { trades: Trade[] }) {
  const [groupBy, setGroupBy] = useState<GroupingCriteria>('hourOfDay');
  const [metric, setMetric] = useState<'count' | 'pnl' | 'winRate'>('pnl');

  const groupedData = useMemo(() => {
    return groupTrades(trades, groupBy, metric);
  }, [trades, groupBy, metric]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Trade Patterns</CardTitle>
        <div className="flex gap-4">
          <Select value={groupBy} onValueChange={setGroupBy}>
            <SelectItem value="hourOfDay">Hour of Day</SelectItem>
            <SelectItem value="dayOfWeek">Day of Week</SelectItem>
            <SelectItem value="month">Month</SelectItem>
            <SelectItem value="entryReason">Entry Reason</SelectItem>
            <SelectItem value="exitReason">Exit Reason</SelectItem>
            <SelectItem value="duration">Duration Bucket</SelectItem>
          </Select>

          <Select value={metric} onValueChange={setMetric}>
            <SelectItem value="count">Trade Count</SelectItem>
            <SelectItem value="pnl">Total P&L</SelectItem>
            <SelectItem value="winRate">Win Rate</SelectItem>
            <SelectItem value="avgReturn">Avg Return</SelectItem>
          </Select>
        </div>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={groupedData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="group" />
            <YAxis />
            <Tooltip />
            <Bar
              dataKey="value"
              fill="#8884d8"
              label={<CustomLabel metric={metric} />}
            />
          </BarChart>
        </ResponsiveContainer>

        <PatternInsights data={groupedData} groupBy={groupBy} metric={metric} />
      </CardContent>
    </Card>
  );
}

// Pattern grouping logic
function groupTrades(
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

  return Array.from(groups.entries()).map(([group, trades]) => ({
    group,
    value: calculateMetricValue(trades, metric),
    trades: trades.length,
    details: getGroupDetails(trades)
  }));
}

function getGroupKey(trade: Trade, groupBy: GroupingCriteria): string {
  switch (groupBy) {
    case 'hourOfDay':
      return new Date(trade.entryTime).getHours().toString();
    case 'dayOfWeek':
      return ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'][
        new Date(trade.entryTime).getDay()
      ];
    case 'month':
      return new Date(trade.entryTime).toLocaleString('default', { month: 'short' });
    case 'entryReason':
      return trade.entryReason || 'Unknown';
    case 'exitReason':
      return trade.exitReason || 'Unknown';
    case 'duration':
      return getDurationBucket(trade.duration);
    default:
      return 'Unknown';
  }
}
```

### Market Context Analysis
```typescript
// components/trades/MarketContext.tsx
export function MarketContext({ trade }: { trade: Trade }) {
  const [marketData, setMarketData] = useState<MarketSnapshot>();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadMarketContext(trade).then(setMarketData).finally(() => setLoading(false));
  }, [trade]);

  if (loading) return <Skeleton />;

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <MetricCard
          title="Market Volatility"
          value={marketData?.volatility}
          format="percentage"
          description="ATR at entry"
        />
        <MetricCard
          title="Volume Profile"
          value={marketData?.volumeRank}
          format="percentile"
          description="vs 20-day average"
        />
        <MetricCard
          title="Trend Strength"
          value={marketData?.trendStrength}
          format="score"
          description="ADX value"
        />
        <MetricCard
          title="Market Regime"
          value={marketData?.regime}
          format="text"
          description="Trending/Ranging"
        />
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Price Action Context</CardTitle>
        </CardHeader>
        <CardContent>
          <MiniChart
            data={marketData?.priceContext}
            trade={trade}
            width={400}
            height={200}
          />
        </CardContent>
      </Card>

      <MarketConditions conditions={marketData?.conditions} />
    </div>
  );
}
```

### Trade Export
```typescript
// lib/trades/export.ts
export class TradeExporter {
  static async exportToCSV(trades: Trade[], filename: string = 'trades.csv') {
    const headers = [
      'ID', 'Entry Time', 'Exit Time', 'Side', 'Entry Price',
      'Exit Price', 'Quantity', 'P&L', 'Return %', 'Duration',
      'Entry Reason', 'Exit Reason', 'Max Profit', 'Max Loss',
      'Entry Slippage', 'Exit Slippage'
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
      trade.exitSlippage
    ]);

    const csv = [
      headers.join(','),
      ...rows.map(row => row.join(','))
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
}
```

## UI/UX Considerations
- Fast filtering and sorting for large trade lists
- Visual indicators for profitable/losing trades
- Interactive timeline for trade lifecycle
- Contextual tooltips for metrics
- Responsive design for mobile access
- Keyboard shortcuts for navigation

## Testing Requirements
1. Trade calculation accuracy tests
2. Filtering and sorting functionality
3. Export format verification
4. Performance with large datasets
5. Market context data accuracy
6. Pattern recognition algorithms

## Dependencies
- UI_001: Next.js foundation
- UI_003: Database setup
- UI_015: Basic results visualization
- UI_022: Advanced time series charts

## Story Points: 13

## Priority: High

## Implementation Notes
- Implement virtual scrolling for large trade lists
- Cache market context data for performance
- Use Web Workers for pattern analysis
- Consider pagination for very large datasets
