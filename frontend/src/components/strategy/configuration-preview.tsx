"use client";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Strategy } from "@/hooks/useStrategies";
import { CheckCircle, AlertCircle, Copy, FileJson, Cpu, MemoryStick, Clock, HardDrive } from "lucide-react";
import { useState } from "react";

interface ConfigurationPreviewProps {
  strategy: Strategy;
  configuration: Record<string, any>;
  isValid: boolean;
  onStartBacktest?: () => void;
}

// Helper function to estimate resource usage based on strategy and configuration
function estimateResourceUsage(strategy: Strategy, configuration: Record<string, any>) {
  // Base estimates
  let cpu = 20; // Base CPU usage %
  let memory = 512; // Base memory MB
  let time = "5-10 min"; // Base time estimate
  let disk = 50; // Base disk space MB

  // Adjust based on strategy type
  switch (strategy.id) {
    case "order_book_scalper":
      cpu += 30; // High-frequency trading requires more CPU
      memory += 256;
      if (configuration.lookback_hours) {
        const hours = parseFloat(configuration.lookback_hours);
        memory += hours * 50; // ~50MB per hour of data
        disk += hours * 20;
        if (hours > 24) {
          time = "15-30 min";
        } else if (hours > 8) {
          time = "10-20 min";
        }
      }
      break;

    case "momentum_breakout":
      cpu += 20;
      memory += 128;
      if (configuration.lookback_period) {
        const period = parseInt(configuration.lookback_period);
        memory += period * 2;
        if (period > 100) {
          time = "10-15 min";
        }
      }
      break;

    case "mean_reversion":
      cpu += 25;
      memory += 192;
      if (configuration.bollinger_period) {
        const period = parseInt(configuration.bollinger_period);
        memory += period * 3;
        if (period > 50) {
          time = "8-12 min";
        }
      }
      break;

    default:
      // Generic strategy
      cpu += 15;
      memory += 128;
  }

  // Adjust based on common parameters
  if (configuration.position_size && parseFloat(configuration.position_size) > 5) {
    cpu += 5; // More positions = more calculations
    memory += 64;
  }

  if (configuration.enable_ml_features) {
    cpu += 20; // ML features are compute-intensive
    memory += 512;
    disk += 100; // ML models take disk space
    // Increase time estimate
    if (time === "5-10 min") time = "15-25 min";
    else if (time === "10-20 min") time = "25-40 min";
    else time = "30-60 min";
  }

  if (configuration.optimization_enabled) {
    cpu += 15;
    memory += 256;
    // Double the time for optimization
    const [min, max] = time.split("-").map(t => parseInt(t));
    time = `${min * 2}-${max * 2} min`;
  }

  // Cap values at reasonable maximums
  cpu = Math.min(cpu, 90);
  memory = Math.min(memory, 4096);
  disk = Math.min(disk, 1024);

  return {
    cpu: `${cpu}`,
    memory: `${memory}`,
    time,
    disk: `${disk}`,
  };
}

export function ConfigurationPreview({
  strategy,
  configuration,
  isValid,
  onStartBacktest,
}: ConfigurationPreviewProps) {
  const [copied, setCopied] = useState(false);

  const copyToClipboard = () => {
    const configJson = JSON.stringify(configuration, null, 2);
    navigator.clipboard.writeText(configJson);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const exportAsJson = () => {
    const dataStr = JSON.stringify(
      {
        strategy_id: strategy.id,
        strategy_name: strategy.name,
        parameters: configuration,
        timestamp: new Date().toISOString(),
      },
      null,
      2
    );

    const dataUri =
      "data:application/json;charset=utf-8," + encodeURIComponent(dataStr);
    const exportFileDefaultName = `${strategy.id}-config-${Date.now()}.json`;

    const linkElement = document.createElement("a");
    linkElement.setAttribute("href", dataUri);
    linkElement.setAttribute("download", exportFileDefaultName);
    linkElement.click();
  };

  // Calculate configuration completeness
  const requiredParams = strategy.parameters.filter((p) => p.required);
  const configuredRequired = requiredParams.filter(
    (p) =>
      configuration[p.name] !== undefined &&
      configuration[p.name] !== null &&
      configuration[p.name] !== ""
  );
  const completeness = Math.round(
    (configuredRequired.length / requiredParams.length) * 100
  );

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Configuration Summary</CardTitle>
            <CardDescription>
              Review your strategy configuration before running
            </CardDescription>
          </div>
          <div className="flex items-center space-x-2">
            <Button variant="outline" size="sm" onClick={copyToClipboard}>
              <Copy className="h-4 w-4 mr-2" />
              {copied ? "Copied!" : "Copy"}
            </Button>
            <Button variant="outline" size="sm" onClick={exportAsJson}>
              <FileJson className="h-4 w-4 mr-2" />
              Export
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Status Overview */}
        <div className="flex items-center justify-between p-3 bg-muted rounded-lg">
          <div className="flex items-center space-x-2">
            {isValid ? (
              <>
                <CheckCircle className="h-5 w-5 text-green-600" />
                <span className="font-medium">Configuration Valid</span>
              </>
            ) : (
              <>
                <AlertCircle className="h-5 w-5 text-yellow-600" />
                <span className="font-medium">Configuration Incomplete</span>
              </>
            )}
          </div>
          <Badge variant={isValid ? "default" : "secondary"}>
            {completeness}% Complete
          </Badge>
        </div>

        {/* Strategy Info */}
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-muted-foreground">
            Strategy
          </h4>
          <div className="p-3 border rounded-lg">
            <div className="font-medium">{strategy.name}</div>
            <div className="text-sm text-muted-foreground">
              {strategy.category} • v{strategy.version}
            </div>
          </div>
        </div>

        {/* Resource Estimation */}
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-muted-foreground">
            Estimated Resource Requirements
          </h4>
          <div className="grid grid-cols-2 gap-2">
            <div className="flex items-center space-x-2 p-2 bg-muted/50 rounded">
              <Cpu className="h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-xs text-muted-foreground">CPU Usage</p>
                <p className="text-sm font-medium">
                  {estimateResourceUsage(strategy, configuration).cpu}%
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-2 p-2 bg-muted/50 rounded">
              <MemoryStick className="h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-xs text-muted-foreground">Memory</p>
                <p className="text-sm font-medium">
                  {estimateResourceUsage(strategy, configuration).memory} MB
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-2 p-2 bg-muted/50 rounded">
              <Clock className="h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-xs text-muted-foreground">Est. Time</p>
                <p className="text-sm font-medium">
                  {estimateResourceUsage(strategy, configuration).time}
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-2 p-2 bg-muted/50 rounded">
              <HardDrive className="h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-xs text-muted-foreground">Disk Space</p>
                <p className="text-sm font-medium">
                  {estimateResourceUsage(strategy, configuration).disk} MB
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Parameters Summary */}
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-muted-foreground">
            Configured Parameters ({Object.keys(configuration).length}/
            {strategy.parameters.length})
          </h4>
          <ScrollArea className="h-[200px] pr-4">
            <div className="space-y-2">
              {strategy.parameters.map((param) => {
                const value = configuration[param.name];
                const isConfigured =
                  value !== undefined && value !== null && value !== "";

                return (
                  <div
                    key={param.name}
                    className="flex items-center justify-between p-2 rounded-lg bg-muted/50"
                  >
                    <div className="flex items-center space-x-2">
                      <div
                        className={`w-2 h-2 rounded-full ${
                          isConfigured ? "bg-green-500" : "bg-gray-400"
                        }`}
                      />
                      <span className="text-sm font-medium">{param.name}</span>
                      {param.required && (
                        <Badge variant="outline" className="text-xs">
                          Required
                        </Badge>
                      )}
                    </div>
                    <div className="text-sm">
                      {isConfigured ? (
                        <span className="font-mono">
                          {typeof value === "boolean"
                            ? value.toString()
                            : value}
                        </span>
                      ) : (
                        <span className="text-muted-foreground">Not set</span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </ScrollArea>
        </div>

        {/* Action Buttons */}
        <div className="pt-4 border-t">
          <Button
            className="w-full"
            disabled={!isValid}
            onClick={onStartBacktest}
          >
            {isValid ? "Start Backtest" : "Complete Configuration First"}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
