"use client";

import React, { useState, useEffect, useMemo } from "react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Dna,
  Users,
  Target,
  Play,
  Settings,
  Info,
  Zap,
  TrendingUp,
} from "lucide-react";

interface GeneticParameter {
  name: string;
  type: "continuous" | "discrete" | "binary";
  min?: number;
  max?: number;
  values?: any[];
  encoding: "real" | "binary" | "gray";
  precision?: number;
}

interface GeneticConfig {
  id: string;
  name: string;
  strategyId: string;
  populationSize: number;
  maxGenerations: number;
  eliteSize: number;
  mutationRate: number;
  crossoverRate: number;
  selectionMethod: "tournament" | "roulette" | "rank";
  fitnessFunction: string;
  parameters: GeneticParameter[];
  multiObjective?: boolean;
}

interface GeneticOptimizationSetupProps {
  strategyId?: string;
  onStart?: (config: GeneticConfig) => void;
}

export function GeneticOptimizationSetup({
  strategyId: initialStrategyId,
  onStart,
}: GeneticOptimizationSetupProps) {
  const [config, setConfig] = useState<GeneticConfig>({
    id: `genetic_${Date.now()}`,
    name: "Genetic Optimization",
    strategyId: initialStrategyId || "",
    populationSize: 100,
    maxGenerations: 50,
    eliteSize: 10,
    mutationRate: 0.1,
    crossoverRate: 0.8,
    selectionMethod: "tournament",
    fitnessFunction: "sharpeRatio",
    parameters: [],
    multiObjective: false,
  });

  const [strategies, setStrategies] = useState<any[]>([]);
  const [parameters, setParameters] = useState<GeneticParameter[]>([]);

  useEffect(() => {
    fetchStrategies();
  }, []);

  useEffect(() => {
    if (config.strategyId) {
      fetchStrategyParameters();
    }
  }, [config.strategyId]);

  const fetchStrategies = async () => {
    try {
      const response = await fetch("/api/strategies");
      if (response.ok) {
        const data = await response.json();
        setStrategies(data);
      }
    } catch (error) {
      console.error("Failed to fetch strategies:", error);
    }
  };

  const fetchStrategyParameters = async () => {
    try {
      const response = await fetch(
        `/api/strategies/${config.strategyId}/parameters`
      );
      if (response.ok) {
        const data = await response.json();
        const geneticParams = data.map((p: any) => ({
          name: p.name,
          type: p.type === "numeric" ? "continuous" : p.type,
          min: p.min || 0,
          max: p.max || 100,
          values: p.values,
          encoding: "real",
          precision: 0.001,
        }));
        setParameters(geneticParams);
        setConfig((prev) => ({ ...prev, parameters: geneticParams }));
      }
    } catch (error) {
      console.error("Failed to fetch parameters:", error);
    }
  };

  const preview = useMemo(() => {
    const totalEvaluations = config.populationSize * config.maxGenerations;
    const estimatedTime = totalEvaluations * 30; // 30 seconds per evaluation estimate
    const searchSpaceSize = config.parameters.reduce((acc, param) => {
      if (param.type === "continuous") {
        return acc * ((param.max! - param.min!) / (param.precision || 0.001));
      } else if (param.type === "discrete") {
        return acc * (param.values?.length || 1);
      }
      return acc * 2; // binary
    }, 1);
    const searchSpaceCoverage = Math.min(1, totalEvaluations / searchSpaceSize);

    return {
      totalEvaluations,
      estimatedTime,
      searchSpaceCoverage,
      searchSpaceSize,
    };
  }, [config]);

  const startGeneticOptimization = () => {
    if (config.strategyId && config.parameters.length > 0 && onStart) {
      onStart(config);
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Dna className="h-5 w-5" />
            Genetic Algorithm Configuration
          </CardTitle>
          <CardDescription>
            Configure evolutionary optimization parameters
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="algorithm">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="algorithm">Algorithm</TabsTrigger>
              <TabsTrigger value="parameters">Parameters</TabsTrigger>
              <TabsTrigger value="fitness">Fitness</TabsTrigger>
              <TabsTrigger value="advanced">Advanced</TabsTrigger>
            </TabsList>

            <TabsContent value="algorithm" className="space-y-6 mt-6">
              <div className="grid grid-cols-2 gap-6">
                <div className="space-y-2">
                  <Label>Strategy</Label>
                  <Select
                    value={config.strategyId}
                    onValueChange={(value) =>
                      setConfig((prev) => ({ ...prev, strategyId: value }))
                    }
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select strategy" />
                    </SelectTrigger>
                    <SelectContent>
                      {strategies.map((strategy) => (
                        <SelectItem key={strategy.id} value={strategy.id}>
                          {strategy.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label>Selection Method</Label>
                  <Select
                    value={config.selectionMethod}
                    onValueChange={(value) =>
                      setConfig((prev) => ({
                        ...prev,
                        selectionMethod: value as
                          | "tournament"
                          | "roulette"
                          | "rank",
                      }))
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="tournament">
                        Tournament Selection
                      </SelectItem>
                      <SelectItem value="roulette">Roulette Wheel</SelectItem>
                      <SelectItem value="rank">Rank Selection</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label>Population Size</Label>
                  <Input
                    type="number"
                    value={config.populationSize}
                    onChange={(e) =>
                      setConfig((prev) => ({
                        ...prev,
                        populationSize: parseInt(e.target.value) || 100,
                      }))
                    }
                    min={10}
                    max={1000}
                  />
                  <p className="text-xs text-muted-foreground">
                    Number of individuals per generation
                  </p>
                </div>

                <div className="space-y-2">
                  <Label>Max Generations</Label>
                  <Input
                    type="number"
                    value={config.maxGenerations}
                    onChange={(e) =>
                      setConfig((prev) => ({
                        ...prev,
                        maxGenerations: parseInt(e.target.value) || 50,
                      }))
                    }
                    min={10}
                    max={1000}
                  />
                  <p className="text-xs text-muted-foreground">
                    Maximum evolution iterations
                  </p>
                </div>
              </div>

              <div className="space-y-4">
                <div className="space-y-2">
                  <Label>Elite Size</Label>
                  <div className="flex items-center gap-2">
                    <Slider
                      value={[config.eliteSize]}
                      onValueChange={([value]) =>
                        setConfig((prev) => ({ ...prev, eliteSize: value }))
                      }
                      max={Math.floor(config.populationSize * 0.5)}
                      min={1}
                      className="flex-1"
                    />
                    <span className="w-12 text-right font-mono text-sm">
                      {config.eliteSize}
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Best individuals preserved each generation
                  </p>
                </div>

                <div className="space-y-2">
                  <Label>Mutation Rate</Label>
                  <div className="flex items-center gap-4">
                    <Slider
                      value={[config.mutationRate * 100]}
                      onValueChange={([value]) =>
                        setConfig((prev) => ({
                          ...prev,
                          mutationRate: value / 100,
                        }))
                      }
                      max={50}
                      min={0}
                      step={1}
                      className="flex-1"
                    />
                    <span className="w-12 text-right font-mono text-sm">
                      {(config.mutationRate * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>Crossover Rate</Label>
                  <div className="flex items-center gap-4">
                    <Slider
                      value={[config.crossoverRate * 100]}
                      onValueChange={([value]) =>
                        setConfig((prev) => ({
                          ...prev,
                          crossoverRate: value / 100,
                        }))
                      }
                      max={100}
                      min={50}
                      step={5}
                      className="flex-1"
                    />
                    <span className="w-12 text-right font-mono text-sm">
                      {(config.crossoverRate * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="parameters" className="space-y-4 mt-6">
              {parameters.length === 0 ? (
                <Alert>
                  <Info className="h-4 w-4" />
                  <AlertDescription>
                    Select a strategy to configure its parameters for
                    optimization
                  </AlertDescription>
                </Alert>
              ) : (
                <div className="space-y-4">
                  {parameters.map((param) => (
                    <Card key={param.name} className="p-4">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-medium">{param.name}</h4>
                        <Badge variant="outline">{param.type}</Badge>
                      </div>

                      {param.type === "continuous" && (
                        <div className="grid grid-cols-3 gap-3">
                          <div className="space-y-1">
                            <Label className="text-xs">Min</Label>
                            <Input
                              type="number"
                              value={param.min}
                              onChange={(e) => {
                                const newParams = parameters.map((p) =>
                                  p.name === param.name
                                    ? { ...p, min: parseFloat(e.target.value) }
                                    : p
                                );
                                setParameters(newParams);
                                setConfig((prev) => ({
                                  ...prev,
                                  parameters: newParams,
                                }));
                              }}
                              step="0.01"
                            />
                          </div>
                          <div className="space-y-1">
                            <Label className="text-xs">Max</Label>
                            <Input
                              type="number"
                              value={param.max}
                              onChange={(e) => {
                                const newParams = parameters.map((p) =>
                                  p.name === param.name
                                    ? { ...p, max: parseFloat(e.target.value) }
                                    : p
                                );
                                setParameters(newParams);
                                setConfig((prev) => ({
                                  ...prev,
                                  parameters: newParams,
                                }));
                              }}
                              step="0.01"
                            />
                          </div>
                          <div className="space-y-1">
                            <Label className="text-xs">Precision</Label>
                            <Input
                              type="number"
                              value={param.precision}
                              onChange={(e) => {
                                const newParams = parameters.map((p) =>
                                  p.name === param.name
                                    ? {
                                        ...p,
                                        precision: parseFloat(e.target.value),
                                      }
                                    : p
                                );
                                setParameters(newParams);
                                setConfig((prev) => ({
                                  ...prev,
                                  parameters: newParams,
                                }));
                              }}
                              step="0.001"
                            />
                          </div>
                        </div>
                      )}
                    </Card>
                  ))}
                </div>
              )}
            </TabsContent>

            <TabsContent value="fitness" className="space-y-4 mt-6">
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label>Fitness Function</Label>
                  <Select
                    value={config.fitnessFunction}
                    onValueChange={(value) =>
                      setConfig((prev) => ({ ...prev, fitnessFunction: value }))
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="sharpeRatio">Sharpe Ratio</SelectItem>
                      <SelectItem value="totalReturn">Total Return</SelectItem>
                      <SelectItem value="calmarRatio">Calmar Ratio</SelectItem>
                      <SelectItem value="sortinoRatio">
                        Sortino Ratio
                      </SelectItem>
                      <SelectItem value="multiObjective">
                        Multi-Objective
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {config.fitnessFunction === "multiObjective" && (
                  <Alert>
                    <Zap className="h-4 w-4" />
                    <AlertDescription>
                      Multi-objective optimization will optimize for multiple
                      metrics simultaneously using Pareto dominance
                    </AlertDescription>
                  </Alert>
                )}
              </div>
            </TabsContent>

            <TabsContent value="advanced" className="space-y-4 mt-6">
              <Alert>
                <Settings className="h-4 w-4" />
                <AlertDescription>
                  Advanced settings for fine-tuning the genetic algorithm
                  behavior
                </AlertDescription>
              </Alert>
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label>Tournament Size (for tournament selection)</Label>
                  <Input type="number" defaultValue={3} min={2} max={10} />
                </div>
                <div className="space-y-2">
                  <Label>Convergence Threshold</Label>
                  <Input type="number" defaultValue={0.001} step={0.001} />
                </div>
                <div className="space-y-2">
                  <Label>Random Seed (for reproducibility)</Label>
                  <Input type="number" placeholder="Leave empty for random" />
                </div>
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Info className="h-5 w-5" />
            Optimization Preview
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">Total Evaluations</p>
              <p className="text-2xl font-bold">
                {preview.totalEvaluations.toLocaleString()}
              </p>
            </div>
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">Estimated Time</p>
              <p className="text-2xl font-bold">
                {Math.floor(preview.estimatedTime / 3600)}h{" "}
                {Math.floor((preview.estimatedTime % 3600) / 60)}m
              </p>
            </div>
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">
                Search Space Coverage
              </p>
              <p className="text-2xl font-bold">
                {(preview.searchSpaceCoverage * 100).toFixed(1)}%
              </p>
            </div>
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">Parameters</p>
              <p className="text-2xl font-bold">{config.parameters.length}</p>
            </div>
          </div>

          <div className="flex gap-2 mt-6">
            <Button
              onClick={startGeneticOptimization}
              disabled={!config.strategyId || config.parameters.length === 0}
              className="flex-1"
            >
              <Play className="h-4 w-4 mr-2" />
              Start Evolution
            </Button>
            <Button variant="outline">
              <Settings className="h-4 w-4 mr-2" />
              Save Configuration
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
