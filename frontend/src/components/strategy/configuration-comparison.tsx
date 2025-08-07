"use client";

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { CheckCircle2, XCircle, Minus, ArrowRight } from "lucide-react";
import { ConfigurationTemplate, Strategy } from "@/hooks/useStrategies";

interface ConfigurationComparisonProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  currentConfig: Record<string, any>;
  templates: ConfigurationTemplate[];
  strategy: Strategy;
}

export function ConfigurationComparison({
  open,
  onOpenChange,
  currentConfig,
  templates,
  strategy,
}: ConfigurationComparisonProps) {
  const [selectedTemplateId, setSelectedTemplateId] = useState<string>("");

  const selectedTemplate = templates.find((t) => t.id === selectedTemplateId);

  const compareValues = (current: any, template: any) => {
    if (current === template) return "same";
    if (current === undefined || current === null) return "missing";
    if (template === undefined || template === null) return "added";
    return "different";
  };

  const formatValue = (value: any): string => {
    if (value === null || value === undefined) return "-";
    if (typeof value === "boolean") return value ? "Yes" : "No";
    if (typeof value === "number") return value.toString();
    return String(value);
  };

  const getComparisonIcon = (status: string) => {
    switch (status) {
      case "same":
        return <CheckCircle2 className="h-4 w-4 text-green-600" />;
      case "different":
        return <ArrowRight className="h-4 w-4 text-orange-600" />;
      case "missing":
        return <XCircle className="h-4 w-4 text-red-600" />;
      case "added":
        return <CheckCircle2 className="h-4 w-4 text-blue-600" />;
      default:
        return <Minus className="h-4 w-4 text-gray-400" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "same":
        return <Badge variant="secondary">Same</Badge>;
      case "different":
        return (
          <Badge variant="outline" className="text-orange-600">
            Changed
          </Badge>
        );
      case "missing":
        return (
          <Badge variant="outline" className="text-red-600">
            Not Set
          </Badge>
        );
      case "added":
        return (
          <Badge variant="outline" className="text-blue-600">
            New
          </Badge>
        );
      default:
        return null;
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[80vh]">
        <DialogHeader>
          <DialogTitle>Compare Configuration</DialogTitle>
          <DialogDescription>
            Compare your current configuration with a saved template
          </DialogDescription>
        </DialogHeader>

        {/* Template Selection */}
        <div className="space-y-4">
          <Select
            value={selectedTemplateId}
            onValueChange={setSelectedTemplateId}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select a template to compare" />
            </SelectTrigger>
            <SelectContent>
              {templates.map((template) => (
                <SelectItem key={template.id} value={template.id}>
                  <div className="flex items-center justify-between w-full">
                    <span>{template.name}</span>
                    <span className="text-xs text-muted-foreground ml-2">
                      {new Date(template.createdAt).toLocaleDateString()}
                    </span>
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          {/* Comparison Table */}
          {selectedTemplate && (
            <ScrollArea className="h-[50vh]">
              <div className="space-y-1">
                <div className="grid grid-cols-5 gap-2 p-2 font-medium text-sm border-b">
                  <div>Parameter</div>
                  <div>Current Value</div>
                  <div className="text-center">Status</div>
                  <div>Template Value</div>
                  <div className="text-center">Difference</div>
                </div>

                {strategy.parameters.map((param) => {
                  const currentValue = currentConfig[param.name];
                  const templateValue = selectedTemplate.parameters[param.name];
                  const status = compareValues(currentValue, templateValue);

                  return (
                    <div
                      key={param.name}
                      className="grid grid-cols-5 gap-2 p-2 hover:bg-muted/50 rounded-md text-sm"
                    >
                      <div className="font-medium">{param.name}</div>
                      <div className="font-mono">
                        {formatValue(currentValue)}
                      </div>
                      <div className="flex justify-center">
                        {getComparisonIcon(status)}
                      </div>
                      <div className="font-mono">
                        {formatValue(templateValue)}
                      </div>
                      <div className="flex justify-center">
                        {getStatusBadge(status)}
                      </div>
                    </div>
                  );
                })}
              </div>
            </ScrollArea>
          )}

          {/* Summary */}
          {selectedTemplate && (
            <div className="flex items-center justify-between p-4 bg-muted rounded-lg">
              <div className="space-y-1">
                <p className="text-sm font-medium">Comparison Summary</p>
                <p className="text-xs text-muted-foreground">
                  {
                    strategy.parameters.filter(
                      (p) =>
                        compareValues(
                          currentConfig[p.name],
                          selectedTemplate.parameters[p.name]
                        ) === "same"
                    ).length
                  }{" "}
                  parameters match,{" "}
                  {
                    strategy.parameters.filter(
                      (p) =>
                        compareValues(
                          currentConfig[p.name],
                          selectedTemplate.parameters[p.name]
                        ) === "different"
                    ).length
                  }{" "}
                  differ
                </p>
              </div>
              <Button onClick={() => onOpenChange(false)} variant="outline">
                Close
              </Button>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
