"use client";

import React, { useState, useEffect, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  Legend,
  Cell,
} from "recharts";
import {
  Play,
  Pause,
  Square,
  RefreshCw,
  Dna,
  Users,
  Target,
  TrendingUp,
  Activity,
  Clock,
} from "lucide-react";
import { useWebSocket } from "@/hooks/use-websocket";

interface Individual {
  id: string;
  genome: number[];
  parameters: Record<string, any>;
  fitness: number;
  age: number;
  parents?: [string, string];
}

interface Generation {
  id: number;
  population: Individual[];
  bestFitness: number;
  avgFitness: number;
  worstFitness: number;
  diversity: number;
  convergence: number;
  computeTime?: number;
}

interface GeneticExecution {
  id: string;
  configId: string;
  status: "running" | "paused" | "completed" | "failed";
  currentGeneration: number;
  maxGenerations: number;
  startTime: string;
  endTime?: string;
  bestIndividual?: Individual;
}

interface GeneticEvolutionMonitorProps {
  executionId: string;
  onComplete?: (bestIndividual: Individual) => void;
}

export function GeneticEvolutionMonitor({
  executionId,
  onComplete,
}: GeneticEvolutionMonitorProps) {
  const [execution, setExecution] = useState<GeneticExecution | null>(null);
  const [currentGeneration, setCurrentGeneration] = useState<Generation | null>(
    null
  );
  const [history, setHistory] = useState<Generation[]>([]);
  const [viewMode, setViewMode] = useState<
    "evolution" | "population" | "analysis"
  >("evolution");
  const { subscribe, unsubscribe, sendMessage } = useWebSocket();

  useEffect(() => {
    fetchExecution();

    // Subscribe to real-time updates
    const handleGenerationComplete = (data: any) => {
      const generation: Generation = data.generation;
      setCurrentGeneration(generation);
      setHistory((prev) => [...prev, generation]);
      setExecution((prev) =>
        prev
          ? {
              ...prev,
              currentGeneration: generation.id,
              bestIndividual: generation.population.reduce((best, ind) =>
                ind.fitness > best.fitness ? ind : best
              ),
            }
          : null
      );
    };

    const handleEvolutionComplete = (data: any) => {
      setExecution((prev) =>
        prev
          ? { ...prev, status: "completed", endTime: new Date().toISOString() }
          : null
      );
      if (onComplete && data.bestIndividual) {
        onComplete(data.bestIndividual);
      }
    };

    subscribe(`genetic:${executionId}:generation`, handleGenerationComplete);
    subscribe(`genetic:${executionId}:complete`, handleEvolutionComplete);

    return () => {
      unsubscribe(`genetic:${executionId}:generation`);
      unsubscribe(`genetic:${executionId}:complete`);
    };
  }, [executionId]);

  const fetchExecution = async () => {
    try {
      const response = await fetch(`/api/optimization/genetic/${executionId}`);
      if (response.ok) {
        const data = await response.json();
        setExecution(data.execution);
        setHistory(data.history || []);
        if (data.history?.length > 0) {
          setCurrentGeneration(data.history[data.history.length - 1]);
        }
      }
    } catch (error) {
      console.error("Failed to fetch genetic execution:", error);
    }
  };

  const handleControl = (action: "pause" | "resume" | "stop") => {
    sendMessage("genetic:control", {
      executionId,
      action,
    });
  };

  const evolutionData = useMemo(() => {
    return history.map((gen) => ({
      generation: gen.id,
      bestFitness: gen.bestFitness,
      avgFitness: gen.avgFitness,
      worstFitness: gen.worstFitness,
      diversity: gen.diversity * 100,
      convergence: gen.convergence * 100,
    }));
  }, [history]);

  const fitnessDistribution = useMemo(() => {
    if (!currentGeneration) return [];

    const fitnesses = currentGeneration.population.map((ind) => ind.fitness);
    const min = Math.min(...fitnesses);
    const max = Math.max(...fitnesses);
    const binCount = 20;
    const binSize = (max - min) / binCount;

    const bins: { range: string; count: number; min: number; max: number }[] =
      [];
    for (let i = 0; i < binCount; i++) {
      const binMin = min + i * binSize;
      const binMax = binMin + binSize;
      const count = fitnesses.filter((f) => f >= binMin && f < binMax).length;
      bins.push({
        range: `${binMin.toFixed(2)}-${binMax.toFixed(2)}`,
        count,
        min: binMin,
        max: binMax,
      });
    }

    return bins;
  }, [currentGeneration]);

  const getImprovementTrend = () => {
    if (history.length < 2) return 0;
    const recent = history.slice(-5);
    const improvements = [];
    for (let i = 1; i < recent.length; i++) {
      improvements.push(recent[i].bestFitness - recent[i - 1].bestFitness);
    }
    return improvements.reduce((a, b) => a + b, 0) / improvements.length;
  };

  if (!execution) {
    return (
      <Card>
        <CardContent className="py-8">
          <div className="flex items-center justify-center">
            <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Dna className="h-5 w-5" />
              Genetic Evolution Monitor
            </CardTitle>
            <div className="flex items-center gap-2">
              <Badge
                variant={
                  execution.status === "running" ? "default" : "secondary"
                }
              >
                {execution.status}
              </Badge>
              <span className="text-sm text-muted-foreground">
                Generation {execution.currentGeneration} /{" "}
                {execution.maxGenerations}
              </span>
              <div className="flex gap-1">
                {execution.status === "running" && (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleControl("pause")}
                  >
                    <Pause className="h-4 w-4" />
                  </Button>
                )}
                {execution.status === "paused" && (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleControl("resume")}
                  >
                    <Play className="h-4 w-4" />
                  </Button>
                )}
                {execution.status !== "completed" && (
                  <Button
                    size="sm"
                    variant="destructive"
                    onClick={() => handleControl("stop")}
                  >
                    <Square className="h-4 w-4" />
                  </Button>
                )}
              </div>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <Progress
              value={
                (execution.currentGeneration / execution.maxGenerations) * 100
              }
              className="h-2"
            />

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <Target className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm font-medium">Best Fitness</span>
                </div>
                <div className="text-2xl font-bold">
                  {currentGeneration?.bestFitness.toFixed(3) || "N/A"}
                </div>
                <div className="text-xs text-muted-foreground">
                  Improvement: {getImprovementTrend() > 0 ? "+" : ""}
                  {getImprovementTrend().toFixed(4)}
                </div>
              </div>

              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <Users className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm font-medium">
                    Population Diversity
                  </span>
                </div>
                <div className="text-2xl font-bold">
                  {currentGeneration
                    ? `${(currentGeneration.diversity * 100).toFixed(1)}%`
                    : "N/A"}
                </div>
              </div>

              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <Activity className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm font-medium">Convergence</span>
                </div>
                <div className="text-2xl font-bold">
                  {currentGeneration
                    ? `${(currentGeneration.convergence * 100).toFixed(1)}%`
                    : "N/A"}
                </div>
              </div>

              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <Clock className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm font-medium">Runtime</span>
                </div>
                <div className="text-2xl font-bold">
                  {formatRuntime(execution.startTime)}
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Tabs value={viewMode} onValueChange={setViewMode}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="evolution">Evolution Progress</TabsTrigger>
          <TabsTrigger value="population">Population Analysis</TabsTrigger>
          <TabsTrigger value="analysis">Parameter Analysis</TabsTrigger>
        </TabsList>

        <TabsContent value="evolution" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Evolution Progress</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={evolutionData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="generation" />
                  <YAxis yAxisId="fitness" />
                  <YAxis
                    yAxisId="percent"
                    orientation="right"
                    domain={[0, 100]}
                  />
                  <Tooltip />
                  <Legend />

                  <Line
                    yAxisId="fitness"
                    type="monotone"
                    dataKey="bestFitness"
                    stroke="hsl(var(--chart-1))"
                    strokeWidth={2}
                    name="Best Fitness"
                    dot={false}
                  />
                  <Line
                    yAxisId="fitness"
                    type="monotone"
                    dataKey="avgFitness"
                    stroke="hsl(var(--chart-2))"
                    strokeWidth={2}
                    name="Average Fitness"
                    dot={false}
                  />
                  <Line
                    yAxisId="percent"
                    type="monotone"
                    dataKey="diversity"
                    stroke="hsl(var(--chart-3))"
                    strokeWidth={2}
                    name="Diversity %"
                    strokeDasharray="5 5"
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Fitness Distribution</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={fitnessDistribution}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="range"
                    angle={-45}
                    textAnchor="end"
                    height={80}
                  />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="count" fill="hsl(var(--chart-1))" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="population" className="space-y-4">
          <PopulationVisualization
            generation={currentGeneration}
            history={history}
          />
        </TabsContent>

        <TabsContent value="analysis" className="space-y-4">
          <ParameterAnalysis generation={currentGeneration} history={history} />
        </TabsContent>
      </Tabs>
    </div>
  );
}

function PopulationVisualization({
  generation,
  history,
}: {
  generation: Generation | null;
  history: Generation[];
}) {
  const [xParam, setXParam] = useState<string>("");
  const [yParam, setYParam] = useState<string>("");

  const parameters = generation?.population[0]?.parameters
    ? Object.keys(generation.population[0].parameters)
    : [];

  const scatterData = useMemo(() => {
    if (!generation || !xParam || !yParam) return [];

    return generation.population.map((ind) => ({
      id: ind.id,
      x: ind.parameters[xParam],
      y: ind.parameters[yParam],
      fitness: ind.fitness,
      age: ind.age,
    }));
  }, [generation, xParam, yParam]);

  const getColorByFitness = (fitness: number) => {
    if (!generation) return "hsl(var(--chart-1))";
    const min = generation.worstFitness;
    const max = generation.bestFitness;
    const normalized = (fitness - min) / (max - min);
    const hue = normalized * 120; // 0 (red) to 120 (green)
    return `hsl(${hue}, 70%, 50%)`;
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Population Distribution</CardTitle>
        <div className="flex gap-4">
          <select
            value={xParam}
            onChange={(e) => setXParam(e.target.value)}
            className="text-sm border rounded px-2 py-1"
          >
            <option value="">Select X Parameter</option>
            {parameters.map((param) => (
              <option key={param} value={param}>
                {param}
              </option>
            ))}
          </select>
          <select
            value={yParam}
            onChange={(e) => setYParam(e.target.value)}
            className="text-sm border rounded px-2 py-1"
          >
            <option value="">Select Y Parameter</option>
            {parameters.map((param) => (
              <option key={param} value={param}>
                {param}
              </option>
            ))}
          </select>
        </div>
      </CardHeader>
      <CardContent>
        {scatterData.length > 0 ? (
          <ResponsiveContainer width="100%" height={400}>
            <ScatterChart>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="x" name={xParam} />
              <YAxis dataKey="y" name={yParam} />
              <Tooltip cursor={{ strokeDasharray: "3 3" }} />
              <Scatter name="Population" data={scatterData}>
                {scatterData.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={getColorByFitness(entry.fitness)}
                  />
                ))}
              </Scatter>
            </ScatterChart>
          </ResponsiveContainer>
        ) : (
          <div className="text-center py-8 text-muted-foreground">
            Select parameters to visualize population distribution
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function ParameterAnalysis({
  generation,
  history,
}: {
  generation: Generation | null;
  history: Generation[];
}) {
  const parameterEvolution = useMemo(() => {
    if (!history || history.length === 0) return [];

    const parameters = generation?.population[0]?.parameters
      ? Object.keys(generation.population[0].parameters)
      : [];

    return parameters.map((param) => {
      const evolution = history.map((gen) => {
        const values = gen.population.map((ind) => ind.parameters[param]);
        return {
          generation: gen.id,
          mean: values.reduce((a, b) => a + b, 0) / values.length,
          std: Math.sqrt(
            values.reduce((sum, val) => {
              const diff =
                val - values.reduce((a, b) => a + b, 0) / values.length;
              return sum + diff * diff;
            }, 0) / values.length
          ),
          min: Math.min(...values),
          max: Math.max(...values),
        };
      });
      return { parameter: param, evolution };
    });
  }, [generation, history]);

  return (
    <div className="space-y-4">
      {parameterEvolution.map(({ parameter, evolution }) => (
        <Card key={parameter}>
          <CardHeader>
            <CardTitle className="text-sm">{parameter} Evolution</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={evolution}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="generation" />
                <YAxis />
                <Tooltip />
                <Area
                  type="monotone"
                  dataKey="max"
                  stackId="1"
                  stroke="none"
                  fill="hsl(var(--chart-1))"
                  fillOpacity={0.2}
                />
                <Area
                  type="monotone"
                  dataKey="min"
                  stackId="2"
                  stroke="none"
                  fill="white"
                />
                <Line
                  type="monotone"
                  dataKey="mean"
                  stroke="hsl(var(--chart-1))"
                  strokeWidth={2}
                  dot={false}
                />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function formatRuntime(startTime: string): string {
  const start = new Date(startTime).getTime();
  const now = Date.now();
  const seconds = Math.floor((now - start) / 1000);

  if (seconds < 60) return `${seconds}s`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ${seconds % 60}s`;
  const hours = Math.floor(minutes / 60);
  return `${hours}h ${minutes % 60}m`;
}
