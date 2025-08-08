"use client";

import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Separator } from "@/components/ui/separator";
import {
  Plus,
  Minus,
  Play,
  Settings,
  Info,
  AlertTriangle,
  Calculator,
} from "lucide-react";

interface Parameter {
  name: string;
  type: "numeric" | "boolean" | "categorical";
  min?: number;
  max?: number;
  step?: number;
  values?: string[];
  current?: any;
}

interface ParameterRange {
  parameter: string;
  min: number;
  max: number;
  step: number;
  values?: string[];
}

interface GridSearchConfig {
  strategyId: string;
  parameters: ParameterRange[];
  parallelJobs: number;
  maxCombinations: number;
  dataConfig: any;
}

interface GridSearchSetupProps {
  strategyId?: string;
  onStart?: (config: GridSearchConfig) => void;
}

export function GridSearchSetup({
  strategyId: initialStrategyId,
  onStart,
}: GridSearchSetupProps) {
  const [strategyId, setStrategyId] = useState(initialStrategyId || "");
  const [strategies, setStrategies] = useState<any[]>([]);
  const [parameters, setParameters] = useState<Parameter[]>([]);
  const [parameterRanges, setParameterRanges] = useState<ParameterRange[]>([]);
  const [parallelJobs, setParallelJobs] = useState(4);
  const [maxCombinations, setMaxCombinations] = useState(1000);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    fetchStrategies();
  }, []);

  useEffect(() => {
    if (strategyId) {
      fetchStrategyParameters();
    }
  }, [strategyId]);

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
      const response = await fetch(`/api/strategies/${strategyId}/parameters`);
      if (response.ok) {
        const data = await response.json();
        setParameters(data);

        // Initialize parameter ranges
        const initialRanges = data
          .filter((p: Parameter) => p.type === "numeric")
          .map((p: Parameter) => ({
            parameter: p.name,
            min: p.min || 0,
            max: p.max || 100,
            step: p.step || 1,
          }));
        setParameterRanges(initialRanges);
      }
    } catch (error) {
      console.error("Failed to fetch parameters:", error);
    }
  };

  const updateParameterRange = (
    paramName: string,
    field: string,
    value: any
  ) => {
    setParameterRanges((prev) =>
      prev.map((range) =>
        range.parameter === paramName ? { ...range, [field]: value } : range
      )
    );
  };

  const addParameterRange = (paramName: string) => {
    const param = parameters.find((p) => p.name === paramName);
    if (param && !parameterRanges.find((r) => r.parameter === paramName)) {
      const newRange: ParameterRange = {
        parameter: paramName,
        min: param.min || 0,
        max: param.max || 100,
        step: param.step || 1,
      };

      if (param.type === "categorical" && param.values) {
        newRange.values = param.values;
      }

      setParameterRanges((prev) => [...prev, newRange]);
    }
  };

  const removeParameterRange = (paramName: string) => {
    setParameterRanges((prev) =>
      prev.filter((range) => range.parameter !== paramName)
    );
  };

  const calculateCombinations = () => {
    return parameterRanges.reduce((total, range) => {
      if (range.values) {
        return total * range.values.length;
      }
      const steps = Math.floor((range.max - range.min) / range.step) + 1;
      return total * steps;
    }, 1);
  };

  const startGridSearch = () => {
    const config: GridSearchConfig = {
      strategyId,
      parameters: parameterRanges,
      parallelJobs,
      maxCombinations,
      dataConfig: {}, // Would be populated from data configuration
    };

    onStart?.(config);
  };

  const totalCombinations = calculateCombinations();
  const estimatedTime = Math.ceil((totalCombinations / parallelJobs) * 30); // 30 seconds per backtest estimate
  const isValid =
    strategyId &&
    parameterRanges.length > 0 &&
    totalCombinations <= maxCombinations;

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calculator className="h-5 w-5" />
            Grid Search Configuration
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Strategy</Label>
              <Select value={strategyId} onValueChange={setStrategyId}>
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
              <Label>Parallel Jobs</Label>
              <Input
                type="number"
                value={parallelJobs}
                onChange={(e) => setParallelJobs(Number(e.target.value))}
                min={1}
                max={16}
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label>Max Combinations Limit</Label>
            <Input
              type="number"
              value={maxCombinations}
              onChange={(e) => setMaxCombinations(Number(e.target.value))}
              min={1}
              max={10000}
            />
          </div>
        </CardContent>
      </Card>

      {parameters.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Parameter Ranges</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Add Parameter</Label>
              <div className="flex gap-2">
                {parameters
                  .filter(
                    (p) => !parameterRanges.find((r) => r.parameter === p.name)
                  )
                  .map((param) => (
                    <Button
                      key={param.name}
                      variant="outline"
                      size="sm"
                      onClick={() => addParameterRange(param.name)}
                    >
                      <Plus className="h-4 w-4 mr-1" />
                      {param.name}
                    </Button>
                  ))}
              </div>
            </div>

            <Separator />

            <div className="space-y-4">
              {parameterRanges.map((range) => {
                const param = parameters.find(
                  (p) => p.name === range.parameter
                );
                return (
                  <Card key={range.parameter} className="p-4">
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="font-medium">{range.parameter}</h4>
                      <div className="flex items-center gap-2">
                        <Badge variant="outline">{param?.type}</Badge>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => removeParameterRange(range.parameter)}
                        >
                          <Minus className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>

                    {param?.type === "numeric" && (
                      <div className="grid grid-cols-3 gap-3">
                        <div className="space-y-1">
                          <Label className="text-xs">Min</Label>
                          <Input
                            type="number"
                            value={range.min}
                            onChange={(e) =>
                              updateParameterRange(
                                range.parameter,
                                "min",
                                Number(e.target.value)
                              )
                            }
                          />
                        </div>
                        <div className="space-y-1">
                          <Label className="text-xs">Max</Label>
                          <Input
                            type="number"
                            value={range.max}
                            onChange={(e) =>
                              updateParameterRange(
                                range.parameter,
                                "max",
                                Number(e.target.value)
                              )
                            }
                          />
                        </div>
                        <div className="space-y-1">
                          <Label className="text-xs">Step</Label>
                          <Input
                            type="number"
                            value={range.step}
                            onChange={(e) =>
                              updateParameterRange(
                                range.parameter,
                                "step",
                                Number(e.target.value)
                              )
                            }
                            step="0.01"
                          />
                        </div>
                      </div>
                    )}

                    {param?.type === "categorical" && param.values && (
                      <div className="space-y-2">
                        <Label className="text-xs">Values to Test</Label>
                        <div className="flex flex-wrap gap-2">
                          {param.values.map((value) => (
                            <Badge key={value} variant="secondary">
                              {value}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}

                    <div className="mt-2 text-xs text-muted-foreground">
                      {param?.type === "numeric" && (
                        <>
                          Combinations:{" "}
                          {Math.floor((range.max - range.min) / range.step) + 1}
                        </>
                      )}
                      {param?.type === "categorical" && param.values && (
                        <>Combinations: {param.values.length}</>
                      )}
                    </div>
                  </Card>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Info className="h-5 w-5" />
            Optimization Summary
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">
                Total Combinations
              </p>
              <p className="text-2xl font-bold">
                {totalCombinations.toLocaleString()}
              </p>
            </div>
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">Parallel Jobs</p>
              <p className="text-2xl font-bold">{parallelJobs}</p>
            </div>
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">Estimated Time</p>
              <p className="text-2xl font-bold">
                {Math.floor(estimatedTime / 3600)}h{" "}
                {Math.floor((estimatedTime % 3600) / 60)}m
              </p>
            </div>
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">Parameters</p>
              <p className="text-2xl font-bold">{parameterRanges.length}</p>
            </div>
          </div>

          {totalCombinations > maxCombinations && (
            <Alert className="mt-4">
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>
                Total combinations ({totalCombinations.toLocaleString()})
                exceeds the maximum limit ({maxCombinations.toLocaleString()}).
                Please reduce parameter ranges or increase the limit.
              </AlertDescription>
            </Alert>
          )}

          <div className="flex gap-2 mt-4">
            <Button
              onClick={startGridSearch}
              disabled={!isValid}
              className="flex-1"
            >
              <Play className="h-4 w-4 mr-2" />
              Start Grid Search
            </Button>
            <Button variant="outline">
              <Settings className="h-4 w-4 mr-2" />
              Advanced Settings
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
