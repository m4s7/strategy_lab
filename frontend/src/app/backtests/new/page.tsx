"use client";

import { useState, useEffect } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ExecutionMonitor } from "@/components/execution/execution-monitor";
import { useBacktestExecution } from "@/hooks/useBacktestExecution";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import {
  Play,
  Settings,
  Database,
  CheckCircle,
  AlertCircle,
  ArrowLeft,
} from "lucide-react";

export default function BacktestExecutionPage() {
  const router = useRouter();
  const {
    executions,
    loading,
    startExecution,
    controlExecution,
    deleteExecution,
  } = useBacktestExecution();

  const [strategyConfig, setStrategyConfig] = useState<any>(null);
  const [dataConfig, setDataConfig] = useState<any>(null);
  const [startingExecution, setStartingExecution] = useState(false);

  useEffect(() => {
    // Load configurations from session storage
    const storedStrategyConfig = sessionStorage.getItem("backtestConfig");
    const storedDataConfig = sessionStorage.getItem("dataConfig");

    if (storedStrategyConfig) {
      setStrategyConfig(JSON.parse(storedStrategyConfig));
    }

    if (storedDataConfig) {
      setDataConfig(JSON.parse(storedDataConfig));
    }
  }, []);

  const handleStartBacktest = async () => {
    if (!strategyConfig || !dataConfig) {
      toast.error("Strategy and data configuration required");
      return;
    }

    setStartingExecution(true);
    try {
      const result = await startExecution({
        strategy_id: strategyConfig.strategy_id,
        strategy_parameters: strategyConfig.parameters,
        data_configuration: dataConfig,
        priority: 5,
      });

      toast.success(
        `Backtest started! Execution ID: ${result.execution_id.slice(0, 8)}...`
      );

      // Clear session storage after successful start
      sessionStorage.removeItem("backtestConfig");
      sessionStorage.removeItem("dataConfig");
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "Failed to start backtest"
      );
    } finally {
      setStartingExecution(false);
    }
  };

  const handleControlExecution = async (
    executionId: string,
    action: string
  ) => {
    try {
      await controlExecution(executionId, action);
      toast.success(`Execution ${action}ed successfully`);
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : `Failed to ${action} execution`
      );
    }
  };

  const handleDeleteExecution = async (executionId: string) => {
    try {
      await deleteExecution(executionId);
      toast.success("Execution deleted successfully");
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "Failed to delete execution"
      );
    }
  };

  const activeExecutions = executions.filter(
    (e) => !["completed", "failed", "cancelled"].includes(e.status)
  );

  const completedExecutions = executions.filter((e) =>
    ["completed", "failed", "cancelled"].includes(e.status)
  );

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Backtest Execution</h1>
          <p className="text-muted-foreground mt-2">
            Start and monitor backtest executions
          </p>
        </div>
        <Button variant="outline" onClick={() => router.back()}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </Button>
      </div>

      {/* Configuration Review */}
      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Settings className="h-5 w-5" />
              <span>Strategy Configuration</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {strategyConfig ? (
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">
                    Strategy
                  </span>
                  <span className="font-medium">
                    {strategyConfig.strategy_name}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">
                    Parameters
                  </span>
                  <Badge variant="outline">
                    {Object.keys(strategyConfig.parameters).length} configured
                  </Badge>
                </div>
                <div className="pt-2 border-t">
                  <details className="text-sm">
                    <summary className="cursor-pointer text-muted-foreground">
                      View Parameters
                    </summary>
                    <div className="mt-2 space-y-1">
                      {Object.entries(strategyConfig.parameters).map(
                        ([key, value]) => (
                          <div key={key} className="flex justify-between">
                            <span>{key}:</span>
                            <span className="font-mono">{String(value)}</span>
                          </div>
                        )
                      )}
                    </div>
                  </details>
                </div>
              </div>
            ) : (
              <div className="text-center py-6 text-muted-foreground">
                <Settings className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p>No strategy configuration found</p>
                <Button
                  variant="outline"
                  size="sm"
                  className="mt-2"
                  onClick={() => router.push("/strategies")}
                >
                  Configure Strategy
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Database className="h-5 w-5" />
              <span>Data Configuration</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {dataConfig ? (
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">
                    Date Range
                  </span>
                  <span className="font-medium">
                    {dataConfig.date_range.start} to {dataConfig.date_range.end}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">
                    Contracts
                  </span>
                  <Badge variant="outline">
                    {dataConfig.contracts.length} selected
                  </Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">
                    Data Level
                  </span>
                  <Badge variant="secondary">{dataConfig.data_level}</Badge>
                </div>
              </div>
            ) : (
              <div className="text-center py-6 text-muted-foreground">
                <Database className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p>No data configuration found</p>
                <Button
                  variant="outline"
                  size="sm"
                  className="mt-2"
                  onClick={() => router.push("/data")}
                >
                  Configure Data
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Start Execution */}
      {strategyConfig && dataConfig && (
        <Card>
          <CardHeader>
            <CardTitle>Ready to Execute</CardTitle>
            <CardDescription>
              Your backtest configuration is ready. Click start to begin
              execution.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center space-x-4">
              <Button
                onClick={handleStartBacktest}
                disabled={startingExecution}
                size="lg"
              >
                <Play className="h-4 w-4 mr-2" />
                {startingExecution ? "Starting..." : "Start Backtest"}
              </Button>
              <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                <CheckCircle className="h-4 w-4 text-green-600" />
                <span>Configuration validated</span>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Active Executions */}
      {activeExecutions.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-2xl font-bold">Active Executions</h2>
          <div className="grid gap-4">
            {activeExecutions.map((execution) => (
              <ExecutionMonitor
                key={execution.id}
                execution={execution}
                onControl={(action) =>
                  handleControlExecution(execution.id, action)
                }
                onDelete={() => handleDeleteExecution(execution.id)}
              />
            ))}
          </div>
        </div>
      )}

      {/* Completed Executions */}
      {completedExecutions.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-2xl font-bold">Recent Executions</h2>
          <ScrollArea className="h-[400px]">
            <div className="grid gap-4">
              {completedExecutions.slice(0, 10).map((execution) => (
                <ExecutionMonitor
                  key={execution.id}
                  execution={execution}
                  onControl={(action) =>
                    handleControlExecution(execution.id, action)
                  }
                  onDelete={() => handleDeleteExecution(execution.id)}
                />
              ))}
            </div>
          </ScrollArea>
        </div>
      )}

      {/* No Executions State */}
      {executions.length === 0 && !loading && (
        <Card>
          <CardContent className="text-center py-12">
            <Play className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <h3 className="text-lg font-medium mb-2">No Executions Yet</h3>
            <p className="text-muted-foreground mb-4">
              Start your first backtest to see execution monitoring here
            </p>
            {!strategyConfig && !dataConfig && (
              <div className="space-x-2">
                <Button
                  variant="outline"
                  onClick={() => router.push("/strategies")}
                >
                  Configure Strategy
                </Button>
                <Button variant="outline" onClick={() => router.push("/data")}>
                  Configure Data
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
