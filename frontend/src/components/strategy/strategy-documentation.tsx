"use client";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Strategy } from "@/hooks/useStrategies";
import { FileText, Tag, User, Calendar, Settings } from "lucide-react";

interface StrategyDocumentationProps {
  strategy: Strategy | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function StrategyDocumentation({
  strategy,
  open,
  onOpenChange,
}: StrategyDocumentationProps) {
  if (!strategy) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[80vh]">
        <DialogHeader>
          <DialogTitle className="flex items-center space-x-2">
            <FileText className="h-5 w-5" />
            <span>{strategy.name} Documentation</span>
          </DialogTitle>
          <DialogDescription>
            Detailed information about this trading strategy
          </DialogDescription>
        </DialogHeader>

        <ScrollArea className="h-[60vh] pr-4">
          <div className="space-y-6">
            {/* Strategy Overview */}
            <div>
              <h3 className="text-lg font-semibold mb-2">Overview</h3>
              <p className="text-muted-foreground">{strategy.description}</p>
            </div>

            {/* Metadata */}
            <div className="grid grid-cols-2 gap-4">
              <div className="flex items-center space-x-2">
                <User className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm">Author: {strategy.author}</span>
              </div>
              <div className="flex items-center space-x-2">
                <Tag className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm">Version: {strategy.version}</span>
              </div>
              <div className="flex items-center space-x-2">
                <Calendar className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm">Category: {strategy.category}</span>
              </div>
              <div className="flex items-center space-x-2">
                <Settings className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm">
                  Parameters: {strategy.parameters.length}
                </span>
              </div>
            </div>

            <Separator />

            {/* Documentation Content */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">Strategy Details</h3>

              {strategy.documentation ? (
                <div className="prose prose-sm dark:prose-invert max-w-none">
                  <div
                    dangerouslySetInnerHTML={{ __html: strategy.documentation }}
                  />
                </div>
              ) : (
                <div className="space-y-4">
                  {/* Default documentation structure */}
                  <div>
                    <h4 className="font-medium mb-2">Trading Logic</h4>
                    <p className="text-sm text-muted-foreground">
                      This strategy implements a{" "}
                      {strategy.category.toLowerCase()} approach to trading MNQ
                      futures. It analyzes market conditions and generates
                      trading signals based on the configured parameters.
                    </p>
                  </div>

                  <div>
                    <h4 className="font-medium mb-2">Key Features</h4>
                    <ul className="list-disc list-inside text-sm text-muted-foreground space-y-1">
                      <li>Real-time market data analysis</li>
                      <li>Risk management with stop-loss and take-profit</li>
                      <li>Position sizing based on account equity</li>
                      <li>Multiple timeframe analysis capability</li>
                    </ul>
                  </div>

                  <div>
                    <h4 className="font-medium mb-2">
                      Suitable Market Conditions
                    </h4>
                    <p className="text-sm text-muted-foreground">
                      This strategy performs best in{" "}
                      {strategy.category === "Scalping"
                        ? "high-liquidity, low-volatility"
                        : strategy.category === "Momentum"
                        ? "trending, high-volatility"
                        : "range-bound"}{" "}
                      market conditions.
                    </p>
                  </div>
                </div>
              )}
            </div>

            <Separator />

            {/* Parameters Documentation */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">Parameter Reference</h3>
              <div className="space-y-3">
                {strategy.parameters.map((param) => (
                  <div key={param.name} className="border rounded-lg p-3">
                    <div className="flex items-start justify-between">
                      <div className="space-y-1">
                        <div className="flex items-center space-x-2">
                          <span className="font-medium text-sm">
                            {param.name}
                          </span>
                          {param.required && (
                            <Badge variant="outline" className="text-xs">
                              Required
                            </Badge>
                          )}
                          <Badge variant="secondary" className="text-xs">
                            {param.type}
                          </Badge>
                        </div>
                        <p className="text-sm text-muted-foreground">
                          {param.description}
                        </p>
                      </div>
                      {param.default !== undefined && (
                        <div className="text-sm text-muted-foreground">
                          Default:{" "}
                          <span className="font-mono">
                            {String(param.default)}
                          </span>
                        </div>
                      )}
                    </div>
                    {param.validation && (
                      <div className="mt-2 text-xs text-muted-foreground">
                        {param.validation.min !== undefined && (
                          <span>Min: {param.validation.min} </span>
                        )}
                        {param.validation.max !== undefined && (
                          <span>Max: {param.validation.max} </span>
                        )}
                        {param.validation.step !== undefined && (
                          <span>Step: {param.validation.step}</span>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Performance Notes */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">
                Performance Considerations
              </h3>
              <div className="bg-muted/50 rounded-lg p-4">
                <ul className="text-sm space-y-2">
                  <li>
                    • This strategy processes tick-level data in real-time
                  </li>
                  <li>
                    • Recommended minimum tick data: 3 months for reliable
                    backtesting
                  </li>
                  <li>• Average execution time: 2-5 seconds per trading day</li>
                  <li>• Memory usage scales with data window size parameter</li>
                </ul>
              </div>
            </div>
          </div>
        </ScrollArea>
      </DialogContent>
    </Dialog>
  );
}
