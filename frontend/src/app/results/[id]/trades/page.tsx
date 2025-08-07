import { TradeAnalysisDashboard } from '@/components/trades/trade-analysis-dashboard';

interface TradesPageProps {
  params: Promise<{
    id: string;
  }>;
}

export default async function TradesPage({ params }: TradesPageProps) {
  const { id } = await params;
  return (
    <div className="container mx-auto py-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Trade Analysis</h1>
        <p className="text-muted-foreground">
          Detailed analysis of individual trades for backtest {id}
        </p>
      </div>
      
      <TradeAnalysisDashboard backtestId={id} />
    </div>
  );
}