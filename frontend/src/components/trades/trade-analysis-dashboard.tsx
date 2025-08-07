'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Trade } from '@/lib/trades/types';
import { generateMockTrades } from '@/lib/trades/mock-data';
import { TradeStatsSummary } from './trade-stats-summary';
import { TradeTable } from './trade-table';
import { TradeDetails } from './trade-details';
import { TradePatternAnalysis } from './trade-pattern-analysis';

interface TradeAnalysisDashboardProps {
  backtestId: string;
  className?: string;
}

export function TradeAnalysisDashboard({ backtestId, className }: TradeAnalysisDashboardProps) {
  const [trades, setTrades] = useState<Trade[]>([]);
  const [selectedTrade, setSelectedTrade] = useState<Trade | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load trades data
  useEffect(() => {
    const loadTrades = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // In a real application, this would fetch from an API
        // For now, we'll use mock data
        await new Promise(resolve => setTimeout(resolve, 1000)); // Simulate API delay
        
        const mockTrades = generateMockTrades(150); // Generate 150 mock trades
        setTrades(mockTrades);
      } catch (err) {
        setError('Failed to load trade data');
        console.error('Error loading trades:', err);
      } finally {
        setLoading(false);
      }
    };

    loadTrades();
  }, [backtestId]);

  if (loading) {
    return (
      <div className={`space-y-6 ${className}`}>
        <Skeleton className="h-48 w-full" />
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <Skeleton className="h-96 w-full" />
          </div>
          <div className="lg:col-span-1">
            <Skeleton className="h-96 w-full" />
          </div>
        </div>
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (error) {
    return (
      <Card className={className}>
        <CardContent className="p-6">
          <div className="text-center">
            <p className="text-red-600 mb-4">{error}</p>
            <button 
              onClick={() => window.location.reload()} 
              className="text-blue-600 hover:underline"
            >
              Try again
            </button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Trade Statistics Summary */}
      <TradeStatsSummary trades={trades} />

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Trade Table - Takes up 2/3 of the width on large screens */}
        <div className="lg:col-span-2">
          <TradeTable
            trades={trades}
            onTradeSelect={setSelectedTrade}
          />
        </div>

        {/* Trade Details or Placeholder - Takes up 1/3 of the width on large screens */}
        <div className="lg:col-span-1">
          {selectedTrade ? (
            <TradeDetails 
              trade={selectedTrade} 
              onClose={() => setSelectedTrade(null)} 
            />
          ) : (
            <Card className="h-full">
              <CardContent className="p-6 h-full flex items-center justify-center">
                <div className="text-center text-muted-foreground">
                  <p className="text-lg font-medium mb-2">Select a Trade</p>
                  <p className="text-sm">
                    Click the eye icon next to any trade to view detailed analysis
                  </p>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* Trade Pattern Analysis */}
      <TradePatternAnalysis trades={trades} />

      {/* Additional Insights */}
      {trades.length > 0 && (
        <Card>
          <CardContent className="p-6">
            <div className="text-center space-y-2">
              <h3 className="text-lg font-semibold">Trade Analysis Complete</h3>
              <p className="text-muted-foreground">
                Analyzed {trades.length} trades for backtest {backtestId}
              </p>
              <p className="text-sm text-muted-foreground">
                Use the filters and grouping options above to explore different patterns and insights
              </p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}