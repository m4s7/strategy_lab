"use client";

import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  ResponsiveContainer,
  Cell,
} from "recharts";
import {
  Download,
  Filter,
  Sort,
  TrendingUp,
  Target,
  BarChart3,
} from "lucide-react";

interface OptimizationResult {
  id: string;
  parameters: Record<string, any>;
  metrics: {
    sharpeRatio: number;
    totalReturn: number;
    maxDrawdown: number;
    winRate: number;
    profitFactor: number;
    totalTrades: number;
  };
  rank: number;
  status: "completed" | "failed" | "running";
}

interface GridSearchResultsProps {
  optimizationId: string;
  results?: OptimizationResult[];
}

export function GridSearchResults({
  optimizationId,
  results: initialResults,
}: GridSearchResultsProps) {
  const [results, setResults] = useState<OptimizationResult[]>(
    initialResults || []
  );
  const [sortMetric, setSortMetric] = useState("sharpeRatio");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [xAxisMetric, setXAxisMetric] = useState("sharpeRatio");
  const [yAxisMetric, setYAxisMetric] = useState("totalReturn");
  const [colorMetric, setColorMetric] = useState("maxDrawdown");
  const [selectedParameters, setSelectedParameters] = useState<string[]>([]);

  useEffect(() => {
    if (!initialResults) {
      fetchResults();
    }
  }, [optimizationId]);

  const fetchResults = async () => {
    try {
      const response = await fetch(
        `/api/optimization/${optimizationId}/results`
      );
      if (response.ok) {
        const data = await response.json();
        setResults(data);
      }
    } catch (error) {
      console.error("Failed to fetch results:", error);
    }
  };

  const sortedResults = [...results].sort((a, b) => {
    const aValue = a.metrics[sortMetric as keyof typeof a.metrics];
    const bValue = b.metrics[sortMetric as keyof typeof b.metrics];
    return sortOrder === "desc" ? bValue - aValue : aValue - bValue;
  });

  const topResults = sortedResults.slice(0, 10);
  const allParameters =
    results.length > 0 ? Object.keys(results[0].parameters) : [];

  const getScatterData = () => {
    return results
      .filter((r) => r.status === "completed")
      .map((result) => ({
        x: result.metrics[xAxisMetric as keyof typeof result.metrics],
        y: result.metrics[yAxisMetric as keyof typeof result.metrics],
        color: result.metrics[colorMetric as keyof typeof result.metrics],
        ...result.parameters,
        id: result.id,
        rank: result.rank,
      }));
  };

  const getColorScale = (value: number, min: number, max: number) => {
    const normalized = (value - min) / (max - min);
    // Green for better values, red for worse
    const hue =
      colorMetric === "maxDrawdown" ? (1 - normalized) * 120 : normalized * 120;
    return `hsl(${hue}, 70%, 50%)`;
  };

  const scatterData = getScatterData();
  const colorValues = scatterData.map((d) => d.color);
  const minColor = Math.min(...colorValues);
  const maxColor = Math.max(...colorValues);

  const exportResults = () => {
    const csvData = [
      [
        "Rank",
        "Parameters",
        "Sharpe",
        "Return",
        "Drawdown",
        "Win Rate",
        "Profit Factor",
        "Trades",
      ].join(","),
      ...sortedResults.map((result) =>
        [
          result.rank,
          JSON.stringify(result.parameters),
          result.metrics.sharpeRatio.toFixed(3),
          result.metrics.totalReturn.toFixed(3),
          result.metrics.maxDrawdown.toFixed(3),
          result.metrics.winRate.toFixed(3),
          result.metrics.profitFactor.toFixed(3),
          result.metrics.totalTrades,
        ].join(",")
      ),
    ].join("\n");

    const blob = new Blob([csvData], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `grid-search-results-${optimizationId}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Grid Search Results</CardTitle>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={exportResults}>
                <Download className="h-4 w-4 mr-2" />
                Export CSV
              </Button>
              <Badge variant="outline">
                {results.filter((r) => r.status === "completed").length} /{" "}
                {results.length} completed
              </Badge>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-4 gap-4 mb-6">
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {results.length > 0
                  ? results[0]?.metrics.sharpeRatio.toFixed(2)
                  : "N/A"}
              </div>
              <div className="text-sm text-muted-foreground">Best Sharpe</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {results.length > 0
                  ? (results[0]?.metrics.totalReturn * 100).toFixed(1) + "%"
                  : "N/A"}
              </div>
              <div className="text-sm text-muted-foreground">Best Return</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">
                {results.length > 0
                  ? (results[0]?.metrics.maxDrawdown * 100).toFixed(1) + "%"
                  : "N/A"}
              </div>
              <div className="text-sm text-muted-foreground">Min Drawdown</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold">
                {results.filter((r) => r.status === "completed").length}
              </div>
              <div className="text-sm text-muted-foreground">Completed</div>
            </div>
          </div>

          <Tabs defaultValue="scatter" className="space-y-4">
            <TabsList>
              <TabsTrigger value="scatter">Parameter Scatter</TabsTrigger>
              <TabsTrigger value="table">Results Table</TabsTrigger>
              <TabsTrigger value="heatmap">Performance Heatmap</TabsTrigger>
            </TabsList>

            <TabsContent value="scatter" className="space-y-4">
              <div className="flex items-center gap-4 mb-4">
                <div className="flex items-center gap-2">
                  <span className="text-sm">X-Axis:</span>
                  <Select value={xAxisMetric} onValueChange={setXAxisMetric}>
                    <SelectTrigger className="w-40">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="sharpeRatio">Sharpe Ratio</SelectItem>
                      <SelectItem value="totalReturn">Total Return</SelectItem>
                      <SelectItem value="maxDrawdown">Max Drawdown</SelectItem>
                      <SelectItem value="winRate">Win Rate</SelectItem>
                      <SelectItem value="profitFactor">
                        Profit Factor
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-sm">Y-Axis:</span>
                  <Select value={yAxisMetric} onValueChange={setYAxisMetric}>
                    <SelectTrigger className="w-40">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="sharpeRatio">Sharpe Ratio</SelectItem>
                      <SelectItem value="totalReturn">Total Return</SelectItem>
                      <SelectItem value="maxDrawdown">Max Drawdown</SelectItem>
                      <SelectItem value="winRate">Win Rate</SelectItem>
                      <SelectItem value="profitFactor">
                        Profit Factor
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-sm">Color:</span>
                  <Select value={colorMetric} onValueChange={setColorMetric}>
                    <SelectTrigger className="w-40">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="sharpeRatio">Sharpe Ratio</SelectItem>
                      <SelectItem value="totalReturn">Total Return</SelectItem>
                      <SelectItem value="maxDrawdown">Max Drawdown</SelectItem>
                      <SelectItem value="winRate">Win Rate</SelectItem>
                      <SelectItem value="profitFactor">
                        Profit Factor
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <ResponsiveContainer width="100%" height={400}>
                <ScatterChart data={scatterData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" dataKey="x" name={xAxisMetric} />
                  <YAxis type="number" dataKey="y" name={yAxisMetric} />
                  <ChartTooltip
                    content={({ active, payload }) => {
                      if (active && payload && payload[0]) {
                        const data = payload[0].payload;
                        return (
                          <div className="bg-background border rounded p-3 shadow">
                            <p className="font-medium">Rank: {data.rank}</p>
                            <p>
                              {xAxisMetric}: {data.x?.toFixed(3)}
                            </p>
                            <p>
                              {yAxisMetric}: {data.y?.toFixed(3)}
                            </p>
                            <p>
                              {colorMetric}: {data.color?.toFixed(3)}
                            </p>
                            <div className="mt-2 text-xs">
                              {Object.entries(data).map(([key, value]) =>
                                allParameters.includes(key) ? (
                                  <p key={key}>
                                    {key}: {value}
                                  </p>
                                ) : null
                              )}
                            </div>
                          </div>
                        );
                      }
                      return null;
                    }}
                  />
                  <Scatter name="Results" data={scatterData}>
                    {scatterData.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={getColorScale(entry.color, minColor, maxColor)}
                      />
                    ))}
                  </Scatter>
                </ScatterChart>
              </ResponsiveContainer>
            </TabsContent>

            <TabsContent value="table" className="space-y-4">
              <div className="flex items-center gap-4 mb-4">
                <div className="flex items-center gap-2">
                  <Sort className="h-4 w-4" />
                  <span className="text-sm">Sort by:</span>
                  <Select value={sortMetric} onValueChange={setSortMetric}>
                    <SelectTrigger className="w-40">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="sharpeRatio">Sharpe Ratio</SelectItem>
                      <SelectItem value="totalReturn">Total Return</SelectItem>
                      <SelectItem value="maxDrawdown">Max Drawdown</SelectItem>
                      <SelectItem value="winRate">Win Rate</SelectItem>
                      <SelectItem value="profitFactor">
                        Profit Factor
                      </SelectItem>
                    </SelectContent>
                  </Select>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() =>
                      setSortOrder(sortOrder === "desc" ? "asc" : "desc")
                    }
                  >
                    {sortOrder === "desc" ? "↓" : "↑"}
                  </Button>
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full border-collapse border border-border">
                  <thead>
                    <tr className="bg-muted">
                      <th className="border border-border p-2 text-left">
                        Rank
                      </th>
                      {allParameters.map((param) => (
                        <th
                          key={param}
                          className="border border-border p-2 text-left"
                        >
                          {param}
                        </th>
                      ))}
                      <th className="border border-border p-2 text-left">
                        Sharpe
                      </th>
                      <th className="border border-border p-2 text-left">
                        Return
                      </th>
                      <th className="border border-border p-2 text-left">
                        Drawdown
                      </th>
                      <th className="border border-border p-2 text-left">
                        Win Rate
                      </th>
                      <th className="border border-border p-2 text-left">
                        Trades
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {topResults.map((result, index) => (
                      <tr
                        key={result.id}
                        className={index < 3 ? "bg-accent/20" : ""}
                      >
                        <td className="border border-border p-2">
                          <div className="flex items-center gap-2">
                            {result.rank}
                            {index < 3 && (
                              <TrendingUp className="h-4 w-4 text-green-600" />
                            )}
                          </div>
                        </td>
                        {allParameters.map((param) => (
                          <td key={param} className="border border-border p-2">
                            {result.parameters[param]}
                          </td>
                        ))}
                        <td className="border border-border p-2 font-mono">
                          {result.metrics.sharpeRatio.toFixed(3)}
                        </td>
                        <td className="border border-border p-2 font-mono">
                          {(result.metrics.totalReturn * 100).toFixed(1)}%
                        </td>
                        <td className="border border-border p-2 font-mono">
                          {(result.metrics.maxDrawdown * 100).toFixed(1)}%
                        </td>
                        <td className="border border-border p-2 font-mono">
                          {(result.metrics.winRate * 100).toFixed(1)}%
                        </td>
                        <td className="border border-border p-2 font-mono">
                          {result.metrics.totalTrades}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </TabsContent>

            <TabsContent value="heatmap" className="space-y-4">
              <div className="text-center text-muted-foreground py-8">
                Parameter correlation heatmap would be implemented here
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}
