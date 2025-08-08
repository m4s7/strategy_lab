"use client";

import React, { useState } from "react";
import { useSearchParams } from "next/navigation";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { GridSearchSetup } from "@/components/optimization/grid-search-setup";
import { GridSearchResults } from "@/components/optimization/grid-search-results";
import { OptimizationMonitor } from "@/components/optimization/optimization-monitor";
import {
  Calculator,
  TrendingUp,
  Activity,
  History,
  Settings,
  Play,
  BarChart3,
} from "lucide-react";

interface OptimizationRun {
  id: string;
  type: "grid_search" | "genetic" | "random";
  strategyName: string;
  status: string;
  startTime: string;
  completedAt?: string;
  totalCombinations: number;
  bestSharpe: number;
}

export default function OptimizationPage() {
  const searchParams = useSearchParams();
  const initialOptimizationId = searchParams.get("id");

  const [activeOptimizationId, setActiveOptimizationId] = useState<
    string | null
  >(initialOptimizationId);
  const [optimizationHistory, setOptimizationHistory] = useState<
    OptimizationRun[]
  >([]);
  const [activeTab, setActiveTab] = useState(
    initialOptimizationId ? "monitor" : "setup"
  );

  const handleOptimizationStart = (config: any) => {
    // This would start the optimization and get back an ID
    console.log("Starting optimization with config:", config);

    // Mock response - in real implementation this would come from API
    const mockId = `opt_${Date.now()}`;
    setActiveOptimizationId(mockId);
    setActiveTab("monitor");
  };

  const handleOptimizationComplete = (results: any) => {
    console.log("Optimization completed:", results);
    setActiveTab("results");
  };

  // Mock data for demonstration
  const mockHistory: OptimizationRun[] = [
    {
      id: "opt_001",
      type: "grid_search",
      strategyName: "OrderBookScalper",
      status: "completed",
      startTime: "2024-01-15T10:30:00Z",
      completedAt: "2024-01-15T14:45:00Z",
      totalCombinations: 256,
      bestSharpe: 2.34,
    },
    {
      id: "opt_002",
      type: "genetic",
      strategyName: "MeanReversion",
      status: "running",
      startTime: "2024-01-16T09:00:00Z",
      totalCombinations: 1000,
      bestSharpe: 1.87,
    },
  ];

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h1 className="text-3xl font-bold">Strategy Optimization</h1>
          <Badge variant="outline" className="px-3">
            <Activity className="h-4 w-4 mr-1" />
            Grid Search
          </Badge>
        </div>
        <div className="flex gap-2">
          <Button variant="outline">
            <Settings className="mr-2 h-4 w-4" />
            Settings
          </Button>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-4">
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Quick Stats</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Active Runs</span>
                  <span className="font-medium">2</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Completed</span>
                  <span className="font-medium">15</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Best Sharpe</span>
                  <span className="font-medium text-green-600">3.24</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Total Tests</span>
                  <span className="font-medium">12,456</span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="mt-4">
            <CardHeader>
              <CardTitle className="text-sm flex items-center gap-2">
                <History className="h-4 w-4" />
                Recent Runs
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {mockHistory.map((run) => (
                <div
                  key={run.id}
                  className="p-3 rounded border cursor-pointer hover:bg-accent/50"
                  onClick={() => {
                    setActiveOptimizationId(run.id);
                    setActiveTab("monitor");
                  }}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium truncate">
                      {run.strategyName}
                    </span>
                    <Badge
                      variant={
                        run.status === "completed" ? "secondary" : "default"
                      }
                      className="text-xs"
                    >
                      {run.status}
                    </Badge>
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {run.totalCombinations} combinations
                  </div>
                  <div className="text-xs font-mono">
                    Best: {run.bestSharpe.toFixed(2)}
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>

        <div className="lg:col-span-3">
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="setup" className="flex items-center gap-2">
                <Calculator className="h-4 w-4" />
                Setup
              </TabsTrigger>
              <TabsTrigger value="monitor" className="flex items-center gap-2">
                <Activity className="h-4 w-4" />
                Monitor
              </TabsTrigger>
              <TabsTrigger value="results" className="flex items-center gap-2">
                <BarChart3 className="h-4 w-4" />
                Results
              </TabsTrigger>
              <TabsTrigger value="history" className="flex items-center gap-2">
                <History className="h-4 w-4" />
                History
              </TabsTrigger>
            </TabsList>

            <TabsContent value="setup" className="mt-6">
              <GridSearchSetup onStart={handleOptimizationStart} />
            </TabsContent>

            <TabsContent value="monitor" className="mt-6">
              {activeOptimizationId ? (
                <OptimizationMonitor
                  optimizationId={activeOptimizationId}
                  onComplete={handleOptimizationComplete}
                />
              ) : (
                <Card>
                  <CardContent className="py-12">
                    <div className="text-center space-y-4">
                      <Activity className="mx-auto h-12 w-12 text-muted-foreground" />
                      <h3 className="text-lg font-semibold">
                        No Active Optimization
                      </h3>
                      <p className="text-sm text-muted-foreground">
                        Start a new optimization or select one from history
                      </p>
                      <Button onClick={() => setActiveTab("setup")}>
                        <Play className="mr-2 h-4 w-4" />
                        Start New Optimization
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              )}
            </TabsContent>

            <TabsContent value="results" className="mt-6">
              {activeOptimizationId ? (
                <GridSearchResults optimizationId={activeOptimizationId} />
              ) : (
                <Card>
                  <CardContent className="py-12">
                    <div className="text-center space-y-4">
                      <BarChart3 className="mx-auto h-12 w-12 text-muted-foreground" />
                      <h3 className="text-lg font-semibold">
                        No Results Available
                      </h3>
                      <p className="text-sm text-muted-foreground">
                        Complete an optimization to view results
                      </p>
                    </div>
                  </CardContent>
                </Card>
              )}
            </TabsContent>

            <TabsContent value="history" className="mt-6">
              <Card>
                <CardHeader>
                  <CardTitle>Optimization History</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {mockHistory.map((run) => (
                      <div
                        key={run.id}
                        className="flex items-center justify-between p-4 rounded border hover:bg-accent/50"
                      >
                        <div className="space-y-1">
                          <div className="flex items-center gap-3">
                            <span className="font-medium">
                              {run.strategyName}
                            </span>
                            <Badge
                              variant={
                                run.status === "completed"
                                  ? "secondary"
                                  : "default"
                              }
                            >
                              {run.status}
                            </Badge>
                            <Badge variant="outline">{run.type}</Badge>
                          </div>
                          <div className="text-sm text-muted-foreground">
                            Started: {new Date(run.startTime).toLocaleString()}
                            {run.completedAt && (
                              <>
                                {" "}
                                • Completed:{" "}
                                {new Date(run.completedAt).toLocaleString()}
                              </>
                            )}
                          </div>
                          <div className="text-sm">
                            {run.totalCombinations} combinations • Best Sharpe:{" "}
                            {run.bestSharpe.toFixed(2)}
                          </div>
                        </div>
                        <div className="flex gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => {
                              setActiveOptimizationId(run.id);
                              setActiveTab("results");
                            }}
                          >
                            View Results
                          </Button>
                          {run.status === "running" && (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => {
                                setActiveOptimizationId(run.id);
                                setActiveTab("monitor");
                              }}
                            >
                              Monitor
                            </Button>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
}
