"use client";

import React, { useState } from "react";
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
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Calendar,
  TrendingUp,
  BarChart3,
  Info,
  Play,
  Clock,
} from "lucide-react";
import { format, addDays, differenceInDays } from "date-fns";

interface WalkForwardConfig {
  strategyId: string;
  windowType: "anchored" | "rolling";
  inSamplePeriod: number; // days
  outSamplePeriod: number; // days
  stepSize: number; // days
  startDate: string;
  endDate: string;
  minObservations: number;
  optimizationMetric: string;
}

interface WalkForwardSetupProps {
  onStart?: (config: WalkForwardConfig) => void;
}

export function WalkForwardSetup({ onStart }: WalkForwardSetupProps) {
  const [config, setConfig] = useState<WalkForwardConfig>({
    strategyId: "",
    windowType: "rolling",
    inSamplePeriod: 252, // 1 year
    outSamplePeriod: 63, // 3 months
    stepSize: 21, // 1 month
    startDate: format(addDays(new Date(), -2 * 365), "yyyy-MM-dd"), // 2 years ago
    endDate: format(new Date(), "yyyy-MM-dd"),
    minObservations: 100,
    optimizationMetric: "sharpeRatio",
  });

  const updateConfig = (field: keyof WalkForwardConfig, value: any) => {
    setConfig((prev) => ({ ...prev, [field]: value }));
  };

  const calculateWindows = () => {
    const start = new Date(config.startDate);
    const end = new Date(config.endDate);
    const totalDays = differenceInDays(end, start);

    if (totalDays < config.inSamplePeriod + config.outSamplePeriod) {
      return { windows: [], totalWindows: 0, estimatedDuration: 0 };
    }

    const windows = [];
    let currentDate = start;
    let windowNum = 1;

    while (true) {
      const inSampleStart =
        config.windowType === "anchored" ? start : currentDate;
      const inSampleEnd = addDays(currentDate, config.inSamplePeriod);
      const outSampleStart = inSampleEnd;
      const outSampleEnd = addDays(outSampleStart, config.outSamplePeriod);

      if (outSampleEnd > end) break;

      windows.push({
        id: windowNum++,
        inSample: {
          start: inSampleStart,
          end: inSampleEnd,
          days:
            config.windowType === "anchored"
              ? differenceInDays(inSampleEnd, start)
              : config.inSamplePeriod,
        },
        outSample: {
          start: outSampleStart,
          end: outSampleEnd,
          days: config.outSamplePeriod,
        },
      });

      currentDate = addDays(currentDate, config.stepSize);
    }

    return {
      windows,
      totalWindows: windows.length,
      estimatedDuration: windows.length * 5, // 5 minutes per window estimate
    };
  };

  const { windows, totalWindows, estimatedDuration } = calculateWindows();
  const isValid = config.strategyId && totalWindows > 0;

  const startWalkForward = () => {
    if (isValid && onStart) {
      onStart(config);
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            Walk-Forward Analysis Setup
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Strategy</Label>
              <Select
                value={config.strategyId}
                onValueChange={(value) => updateConfig("strategyId", value)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select strategy" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="scalper">Order Book Scalper</SelectItem>
                  <SelectItem value="momentum">Momentum Strategy</SelectItem>
                  <SelectItem value="mean_reversion">Mean Reversion</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Optimization Metric</Label>
              <Select
                value={config.optimizationMetric}
                onValueChange={(value) =>
                  updateConfig("optimizationMetric", value)
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="sharpeRatio">Sharpe Ratio</SelectItem>
                  <SelectItem value="totalReturn">Total Return</SelectItem>
                  <SelectItem value="calmarRatio">Calmar Ratio</SelectItem>
                  <SelectItem value="sortinoRatio">Sortino Ratio</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-4">
            <Label className="text-base font-medium">Window Type</Label>
            <RadioGroup
              value={config.windowType}
              onValueChange={(value) =>
                updateConfig("windowType", value as "anchored" | "rolling")
              }
            >
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="rolling" id="rolling" />
                <Label htmlFor="rolling" className="font-normal">
                  Rolling Windows - Fixed window size that moves forward
                </Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="anchored" id="anchored" />
                <Label htmlFor="anchored" className="font-normal">
                  Anchored Windows - Expanding in-sample period from start date
                </Label>
              </div>
            </RadioGroup>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>In-Sample Period (days)</Label>
              <Input
                type="number"
                value={config.inSamplePeriod}
                onChange={(e) =>
                  updateConfig("inSamplePeriod", Number(e.target.value))
                }
                min={30}
                max={1000}
              />
              <p className="text-xs text-muted-foreground">
                Training period for parameter optimization
              </p>
            </div>

            <div className="space-y-2">
              <Label>Out-of-Sample Period (days)</Label>
              <Input
                type="number"
                value={config.outSamplePeriod}
                onChange={(e) =>
                  updateConfig("outSamplePeriod", Number(e.target.value))
                }
                min={10}
                max={365}
              />
              <p className="text-xs text-muted-foreground">
                Testing period with optimized parameters
              </p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Step Size (days)</Label>
              <Input
                type="number"
                value={config.stepSize}
                onChange={(e) =>
                  updateConfig("stepSize", Number(e.target.value))
                }
                min={1}
                max={config.outSamplePeriod}
              />
              <p className="text-xs text-muted-foreground">
                How often to re-optimize parameters
              </p>
            </div>

            <div className="space-y-2">
              <Label>Min Observations</Label>
              <Input
                type="number"
                value={config.minObservations}
                onChange={(e) =>
                  updateConfig("minObservations", Number(e.target.value))
                }
                min={50}
                max={1000}
              />
              <p className="text-xs text-muted-foreground">
                Minimum trades required per window
              </p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Start Date</Label>
              <Input
                type="date"
                value={config.startDate}
                onChange={(e) => updateConfig("startDate", e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <Label>End Date</Label>
              <Input
                type="date"
                value={config.endDate}
                onChange={(e) => updateConfig("endDate", e.target.value)}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Info className="h-5 w-5" />
            Analysis Preview
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">Total Windows</p>
              <p className="text-2xl font-bold">{totalWindows}</p>
            </div>
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">Window Type</p>
              <Badge variant="outline" className="text-sm">
                {config.windowType === "rolling" ? "Rolling" : "Anchored"}
              </Badge>
            </div>
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">
                Estimated Duration
              </p>
              <p className="text-2xl font-bold">
                {Math.floor(estimatedDuration / 60)}h {estimatedDuration % 60}m
              </p>
            </div>
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">Step Size</p>
              <p className="text-2xl font-bold">{config.stepSize}d</p>
            </div>
          </div>

          {windows.length > 0 && (
            <div className="space-y-2">
              <h4 className="font-medium">Window Timeline</h4>
              <div className="max-h-40 overflow-y-auto space-y-1">
                {windows.slice(0, 5).map((window, index) => (
                  <div key={window.id} className="text-xs p-2 bg-muted rounded">
                    <div className="flex justify-between items-center">
                      <span className="font-medium">Window {window.id}</span>
                      <Badge variant="outline" className="text-xs">
                        {window.inSample.days + window.outSample.days} days
                      </Badge>
                    </div>
                    <div className="mt-1 grid grid-cols-2 gap-2">
                      <div>
                        <span className="text-blue-600">In-Sample:</span>
                        <div>
                          {format(window.inSample.start, "MM/dd/yy")} -{" "}
                          {format(window.inSample.end, "MM/dd/yy")}
                        </div>
                        <div className="text-muted-foreground">
                          ({window.inSample.days} days)
                        </div>
                      </div>
                      <div>
                        <span className="text-green-600">Out-Sample:</span>
                        <div>
                          {format(window.outSample.start, "MM/dd/yy")} -{" "}
                          {format(window.outSample.end, "MM/dd/yy")}
                        </div>
                        <div className="text-muted-foreground">
                          ({window.outSample.days} days)
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
                {windows.length > 5 && (
                  <div className="text-center text-muted-foreground text-xs py-2">
                    ... and {windows.length - 5} more windows
                  </div>
                )}
              </div>
            </div>
          )}

          {totalWindows === 0 && (
            <Alert>
              <AlertDescription>
                No valid windows can be created with current settings. Please
                adjust the date range or window parameters.
              </AlertDescription>
            </Alert>
          )}

          <div className="flex gap-2 mt-6">
            <Button
              onClick={startWalkForward}
              disabled={!isValid}
              className="flex-1"
            >
              <Play className="h-4 w-4 mr-2" />
              Start Walk-Forward Analysis
            </Button>
            <Button variant="outline">
              <Calendar className="h-4 w-4 mr-2" />
              Schedule for Later
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
