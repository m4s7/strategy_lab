"use client";

import React, { useState } from "react";
import { useSearchParams } from "next/navigation";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { BacktestExecutionControl } from "@/components/execution/backtest-execution-control";
import { BacktestQueue } from "@/components/execution/backtest-queue";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Settings, Play } from "lucide-react";
import Link from "next/link";

export default function BacktestExecutionPage() {
  const searchParams = useSearchParams();
  const configurationId = searchParams.get("configId");
  const [selectedExecutionId, setSelectedExecutionId] = useState<
    string | undefined
  >();
  const [executionResults, setExecutionResults] = useState<any>(null);

  const handleExecutionComplete = (results: any) => {
    setExecutionResults(results);
  };

  const handleSelectBacktest = (executionId: string) => {
    setSelectedExecutionId(executionId);
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/backtests/new">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Configuration
            </Button>
          </Link>
          <h1 className="text-3xl font-bold">Backtest Execution</h1>
        </div>
        <div className="flex gap-2">
          <Link href="/backtests/new">
            <Button variant="outline">
              <Settings className="mr-2 h-4 w-4" />
              New Configuration
            </Button>
          </Link>
        </div>
      </div>

      {!configurationId && !selectedExecutionId && (
        <Alert>
          <AlertDescription>
            No configuration selected. Please{" "}
            <Link href="/backtests/new" className="underline">
              create a new configuration
            </Link>{" "}
            or select a backtest from the queue below.
          </AlertDescription>
        </Alert>
      )}

      <Tabs defaultValue="execution" className="space-y-4">
        <TabsList>
          <TabsTrigger value="execution">Current Execution</TabsTrigger>
          <TabsTrigger value="queue">Queue Management</TabsTrigger>
          <TabsTrigger value="history">Execution History</TabsTrigger>
        </TabsList>

        <TabsContent value="execution">
          {configurationId || selectedExecutionId ? (
            <div className="grid gap-6 lg:grid-cols-2">
              <div className="lg:col-span-2">
                <BacktestExecutionControl
                  executionId={selectedExecutionId}
                  configurationId={configurationId || ""}
                  onComplete={handleExecutionComplete}
                />
              </div>

              {executionResults && (
                <Card className="lg:col-span-2">
                  <CardHeader>
                    <CardTitle>Execution Results</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-4 gap-4">
                      <div className="space-y-1">
                        <p className="text-2xl font-bold">
                          ${executionResults.totalPnl?.toLocaleString() || "0"}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          Total P&L
                        </p>
                      </div>
                      <div className="space-y-1">
                        <p className="text-2xl font-bold">
                          {executionResults.sharpeRatio?.toFixed(2) || "0.00"}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          Sharpe Ratio
                        </p>
                      </div>
                      <div className="space-y-1">
                        <p className="text-2xl font-bold">
                          {executionResults.winRate?.toFixed(1) || "0"}%
                        </p>
                        <p className="text-xs text-muted-foreground">
                          Win Rate
                        </p>
                      </div>
                      <div className="space-y-1">
                        <p className="text-2xl font-bold">
                          {executionResults.totalTrades || "0"}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          Total Trades
                        </p>
                      </div>
                    </div>
                    <div className="mt-4 flex gap-2">
                      <Link href={`/results/${executionResults.id}`}>
                        <Button>View Full Results</Button>
                      </Link>
                      <Button variant="outline">Export Results</Button>
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          ) : (
            <Card>
              <CardContent className="py-12">
                <div className="text-center space-y-4">
                  <Play className="mx-auto h-12 w-12 text-muted-foreground" />
                  <h3 className="text-lg font-semibold">No Active Execution</h3>
                  <p className="text-sm text-muted-foreground">
                    Configure and start a new backtest or select one from the
                    queue
                  </p>
                  <Link href="/backtests/new">
                    <Button>
                      <Settings className="mr-2 h-4 w-4" />
                      Configure New Backtest
                    </Button>
                  </Link>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="queue">
          <BacktestQueue onSelectBacktest={handleSelectBacktest} />
        </TabsContent>

        <TabsContent value="history">
          <ExecutionHistory />
        </TabsContent>
      </Tabs>
    </div>
  );
}

function ExecutionHistory() {
  const [history, setHistory] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  React.useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      const response = await fetch("/api/backtests/history");
      if (response.ok) {
        const data = await response.json();
        setHistory(data);
      }
    } catch (error) {
      console.error("Failed to fetch history:", error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Execution History</CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        ) : history.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            No execution history available
          </div>
        ) : (
          <div className="space-y-2">
            {history.map((item) => (
              <div
                key={item.id}
                className="flex items-center justify-between p-3 rounded-lg border"
              >
                <div>
                  <p className="font-medium">{item.strategyName}</p>
                  <p className="text-sm text-muted-foreground">
                    {new Date(item.completedAt).toLocaleString()}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <span
                    className={`text-sm font-medium ${
                      item.status === "completed"
                        ? "text-green-600"
                        : "text-red-600"
                    }`}
                  >
                    {item.status}
                  </span>
                  <Link href={`/results/${item.resultId}`}>
                    <Button variant="outline" size="sm">
                      View Results
                    </Button>
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
