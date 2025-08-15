"use client";

import { useState } from "react";
import {
  Download,
  FileJson,
  FileText,
  FileArchive,
  Database,
} from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Progress } from "@/components/ui/progress";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

interface ExportDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onExport: (options: ExportOptions) => Promise<void>;
}

interface ExportOptions {
  format: "json" | "csv" | "excel" | "sqlite" | "archive";
  scope: "all" | "selected" | "dateRange";
  dataTypes: {
    backtestResults: boolean;
    strategies: boolean;
    configurations: boolean;
    optimizationResults: boolean;
    marketData: boolean;
    logs: boolean;
  };
  dateRange?: {
    start: Date;
    end: Date;
  };
  compression: boolean;
  encryption: boolean;
}

export function DataExportDialog({
  open,
  onOpenChange,
  onExport,
}: ExportDialogProps) {
  const [exporting, setExporting] = useState(false);
  const [progress, setProgress] = useState(0);
  const [format, setFormat] = useState<ExportOptions["format"]>("json");
  const [scope, setScope] = useState<ExportOptions["scope"]>("all");
  const [dataTypes, setDataTypes] = useState<ExportOptions["dataTypes"]>({
    backtestResults: true,
    strategies: true,
    configurations: true,
    optimizationResults: true,
    marketData: false,
    logs: false,
  });
  const [compression, setCompression] = useState(true);
  const [encryption, setEncryption] = useState(false);
  const [estimatedSize, setEstimatedSize] = useState<number | null>(null);

  const handleDataTypeToggle = (type: keyof ExportOptions["dataTypes"]) => {
    setDataTypes((prev) => ({
      ...prev,
      [type]: !prev[type],
    }));
  };

  const estimateSize = () => {
    // Simulate size estimation
    let size = 0;
    if (dataTypes.backtestResults) size += 245;
    if (dataTypes.strategies) size += 12;
    if (dataTypes.configurations) size += 3;
    if (dataTypes.optimizationResults) size += 156;
    if (dataTypes.marketData) size += 1024;
    if (dataTypes.logs) size += 89;

    if (compression) size *= 0.3;
    setEstimatedSize(size);
  };

  const handleExport = async () => {
    setExporting(true);
    setProgress(0);

    // Simulate export progress
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          return 100;
        }
        return prev + 10;
      });
    }, 500);

    try {
      await onExport({
        format,
        scope,
        dataTypes,
        compression,
        encryption,
      });

      setTimeout(() => {
        setExporting(false);
        onOpenChange(false);
      }, 5000);
    } catch (error) {
      clearInterval(interval);
      setExporting(false);
      setProgress(0);
    }
  };

  const formatIcons = {
    json: FileJson,
    csv: FileText,
    excel: FileText,
    sqlite: Database,
    archive: FileArchive,
  };

  const formatDescriptions = {
    json: "Universal format, human-readable",
    csv: "Spreadsheet compatible, simple structure",
    excel: "Full Excel workbook with multiple sheets",
    sqlite: "Complete database snapshot",
    archive: "Compressed archive with all data",
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Export Data</DialogTitle>
          <DialogDescription>
            Export your trading data in various formats
          </DialogDescription>
        </DialogHeader>

        {!exporting ? (
          <Tabs defaultValue="format" className="space-y-4">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="format">Format</TabsTrigger>
              <TabsTrigger value="data">Data Selection</TabsTrigger>
              <TabsTrigger value="options">Options</TabsTrigger>
            </TabsList>

            <TabsContent value="format" className="space-y-4">
              <div className="space-y-3">
                <Label>Export Format</Label>
                <RadioGroup
                  value={format}
                  onValueChange={(value) => setFormat(value as any)}
                >
                  {Object.entries(formatIcons).map(([key, Icon]) => (
                    <div
                      key={key}
                      className="flex items-center space-x-2 p-3 rounded-lg border hover:bg-accent/50"
                    >
                      <RadioGroupItem value={key} id={key} />
                      <Label htmlFor={key} className="flex-1 cursor-pointer">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <Icon className="w-4 h-4" />
                            <span className="uppercase">{key}</span>
                          </div>
                          <span className="text-sm text-muted-foreground">
                            {
                              formatDescriptions[
                                key as keyof typeof formatDescriptions
                              ]
                            }
                          </span>
                        </div>
                      </Label>
                    </div>
                  ))}
                </RadioGroup>
              </div>
            </TabsContent>

            <TabsContent value="data" className="space-y-4">
              <div className="space-y-3">
                <Label>Data Scope</Label>
                <Select
                  value={scope}
                  onValueChange={(value) => setScope(value as any)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Data</SelectItem>
                    <SelectItem value="selected">
                      Selected Items Only
                    </SelectItem>
                    <SelectItem value="dateRange">Date Range</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-3">
                <Label>Data Types</Label>
                <div className="grid grid-cols-2 gap-3">
                  <div className="flex items-center space-x-2 p-3 rounded-lg border">
                    <Checkbox
                      id="backtestResults"
                      checked={dataTypes.backtestResults}
                      onCheckedChange={() =>
                        handleDataTypeToggle("backtestResults")
                      }
                    />
                    <Label htmlFor="backtestResults" className="cursor-pointer">
                      Backtest Results
                    </Label>
                  </div>
                  <div className="flex items-center space-x-2 p-3 rounded-lg border">
                    <Checkbox
                      id="strategies"
                      checked={dataTypes.strategies}
                      onCheckedChange={() => handleDataTypeToggle("strategies")}
                    />
                    <Label htmlFor="strategies" className="cursor-pointer">
                      Strategies
                    </Label>
                  </div>
                  <div className="flex items-center space-x-2 p-3 rounded-lg border">
                    <Checkbox
                      id="configurations"
                      checked={dataTypes.configurations}
                      onCheckedChange={() =>
                        handleDataTypeToggle("configurations")
                      }
                    />
                    <Label htmlFor="configurations" className="cursor-pointer">
                      Configurations
                    </Label>
                  </div>
                  <div className="flex items-center space-x-2 p-3 rounded-lg border">
                    <Checkbox
                      id="optimizationResults"
                      checked={dataTypes.optimizationResults}
                      onCheckedChange={() =>
                        handleDataTypeToggle("optimizationResults")
                      }
                    />
                    <Label
                      htmlFor="optimizationResults"
                      className="cursor-pointer"
                    >
                      Optimization Results
                    </Label>
                  </div>
                  <div className="flex items-center space-x-2 p-3 rounded-lg border">
                    <Checkbox
                      id="marketData"
                      checked={dataTypes.marketData}
                      onCheckedChange={() => handleDataTypeToggle("marketData")}
                    />
                    <Label htmlFor="marketData" className="cursor-pointer">
                      Market Data
                    </Label>
                  </div>
                  <div className="flex items-center space-x-2 p-3 rounded-lg border">
                    <Checkbox
                      id="logs"
                      checked={dataTypes.logs}
                      onCheckedChange={() => handleDataTypeToggle("logs")}
                    />
                    <Label htmlFor="logs" className="cursor-pointer">
                      Application Logs
                    </Label>
                  </div>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="options" className="space-y-4">
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 rounded-lg border">
                  <div>
                    <Label htmlFor="compression">Compression</Label>
                    <p className="text-sm text-muted-foreground">
                      Reduce file size with ZIP compression
                    </p>
                  </div>
                  <Checkbox
                    id="compression"
                    checked={compression}
                    onCheckedChange={setCompression}
                  />
                </div>

                <div className="flex items-center justify-between p-4 rounded-lg border">
                  <div>
                    <Label htmlFor="encryption">Encryption</Label>
                    <p className="text-sm text-muted-foreground">
                      Protect exported data with AES-256 encryption
                    </p>
                  </div>
                  <Checkbox
                    id="encryption"
                    checked={encryption}
                    onCheckedChange={setEncryption}
                  />
                </div>

                {estimatedSize !== null && (
                  <Alert>
                    <AlertDescription>
                      Estimated export size:{" "}
                      {estimatedSize > 1000
                        ? `${(estimatedSize / 1024).toFixed(1)} GB`
                        : `${estimatedSize} MB`}
                    </AlertDescription>
                  </Alert>
                )}

                <Button
                  variant="outline"
                  className="w-full"
                  onClick={estimateSize}
                >
                  Estimate Size
                </Button>
              </div>
            </TabsContent>
          </Tabs>
        ) : (
          <div className="space-y-4 py-8">
            <div className="text-center space-y-2">
              <Download className="w-12 h-12 mx-auto text-primary animate-pulse" />
              <h3 className="text-lg font-medium">Exporting Data</h3>
              <p className="text-sm text-muted-foreground">
                Preparing your export file...
              </p>
            </div>
            <Progress value={progress} className="h-2" />
            <p className="text-center text-sm text-muted-foreground">
              {progress}% complete
            </p>
          </div>
        )}

        {!exporting && (
          <DialogFooter>
            <Button variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleExport}
              disabled={!Object.values(dataTypes).some((v) => v)}
            >
              <Download className="w-4 h-4 mr-2" />
              Export Data
            </Button>
          </DialogFooter>
        )}
      </DialogContent>
    </Dialog>
  );
}
