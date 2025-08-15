"use client";

import { useState } from "react";
import {
  Calendar,
  Clock,
  Database,
  Settings,
  FileText,
  BarChart,
} from "lucide-react";
import { format } from "date-fns";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription } from "@/components/ui/alert";

interface RecoveryDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  backupId?: string;
  onRecover: (options: RecoveryOptions) => Promise<void>;
}

interface RecoveryOptions {
  recoveryPoint: "latest" | "specific" | "pointInTime";
  backupId?: string;
  timestamp?: Date;
  mode: "full" | "selective";
  components: {
    database: boolean;
    configurations: boolean;
    preferences: boolean;
    strategies: boolean;
    logs: boolean;
    optimizationResults: boolean;
  };
}

export function RecoveryDialog({
  open,
  onOpenChange,
  backupId,
  onRecover,
}: RecoveryDialogProps) {
  const [recovering, setRecovering] = useState(false);
  const [progress, setProgress] = useState(0);
  const [recoveryPoint, setRecoveryPoint] = useState<
    RecoveryOptions["recoveryPoint"]
  >(backupId ? "specific" : "latest");
  const [mode, setMode] = useState<RecoveryOptions["mode"]>("selective");
  const [components, setComponents] = useState<RecoveryOptions["components"]>({
    database: true,
    configurations: true,
    preferences: true,
    strategies: true,
    logs: false,
    optimizationResults: false,
  });
  const [previewData, setPreviewData] = useState<any>(null);

  const handleComponentToggle = (
    component: keyof RecoveryOptions["components"]
  ) => {
    setComponents((prev) => ({
      ...prev,
      [component]: !prev[component],
    }));
  };

  const handlePreview = async () => {
    // Simulate preview generation
    setPreviewData({
      database: { records: 15432, size: "45 MB" },
      configurations: { files: 23, size: "1.2 MB" },
      preferences: { users: 1, size: "24 KB" },
      strategies: { count: 8, size: "156 KB" },
    });
  };

  const handleRecover = async () => {
    setRecovering(true);
    setProgress(0);

    // Simulate recovery progress
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
      await onRecover({
        recoveryPoint,
        backupId,
        mode,
        components,
      });

      setTimeout(() => {
        setRecovering(false);
        onOpenChange(false);
      }, 5000);
    } catch (error) {
      clearInterval(interval);
      setRecovering(false);
      setProgress(0);
    }
  };

  const componentIcons = {
    database: Database,
    configurations: Settings,
    preferences: Settings,
    strategies: FileText,
    logs: FileText,
    optimizationResults: BarChart,
  };

  const componentLabels = {
    database: "Database",
    configurations: "Configurations",
    preferences: "User Preferences",
    strategies: "Strategy Definitions",
    logs: "Application Logs",
    optimizationResults: "Optimization Results",
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Data Recovery Tool</DialogTitle>
          <DialogDescription>
            Restore your data from a previous backup point
          </DialogDescription>
        </DialogHeader>

        {!recovering ? (
          <div className="space-y-6">
            {/* Recovery Point Selection */}
            <div className="space-y-3">
              <Label>Select Recovery Point</Label>
              <RadioGroup
                value={recoveryPoint}
                onValueChange={(value) => setRecoveryPoint(value as any)}
              >
                <div className="flex items-center space-x-2 p-3 rounded-lg border hover:bg-accent/50">
                  <RadioGroupItem value="latest" id="latest" />
                  <Label htmlFor="latest" className="flex-1 cursor-pointer">
                    <div className="flex items-center gap-2">
                      <Clock className="w-4 h-4" />
                      Latest backup (2 hours ago)
                    </div>
                  </Label>
                </div>
                <div className="flex items-center space-x-2 p-3 rounded-lg border hover:bg-accent/50">
                  <RadioGroupItem value="pointInTime" id="pointInTime" />
                  <Label
                    htmlFor="pointInTime"
                    className="flex-1 cursor-pointer"
                  >
                    <div className="flex items-center gap-2">
                      <Calendar className="w-4 h-4" />
                      Point in time
                    </div>
                  </Label>
                </div>
                <div className="flex items-center space-x-2 p-3 rounded-lg border hover:bg-accent/50">
                  <RadioGroupItem value="specific" id="specific" />
                  <Label htmlFor="specific" className="flex-1 cursor-pointer">
                    <div className="flex items-center gap-2">
                      <Database className="w-4 h-4" />
                      Specific backup
                    </div>
                  </Label>
                </div>
              </RadioGroup>
            </div>

            {/* Recovery Options */}
            <div className="space-y-3">
              <Label>Recovery Options</Label>
              <div className="grid grid-cols-2 gap-3">
                {Object.entries(components).map(([key, checked]) => {
                  const Icon =
                    componentIcons[key as keyof typeof componentIcons];
                  return (
                    <div
                      key={key}
                      className="flex items-center space-x-2 p-3 rounded-lg border hover:bg-accent/50"
                    >
                      <Checkbox
                        id={key}
                        checked={checked}
                        onCheckedChange={() =>
                          handleComponentToggle(key as any)
                        }
                      />
                      <Label htmlFor={key} className="flex-1 cursor-pointer">
                        <div className="flex items-center gap-2">
                          <Icon className="w-4 h-4" />
                          {componentLabels[key as keyof typeof componentLabels]}
                        </div>
                      </Label>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Recovery Mode */}
            <div className="space-y-3">
              <Label>Recovery Mode</Label>
              <RadioGroup
                value={mode}
                onValueChange={(value) => setMode(value as any)}
              >
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="full" id="full" />
                  <Label htmlFor="full">Full recovery (replace all data)</Label>
                </div>
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="selective" id="selective" />
                  <Label htmlFor="selective">
                    Selective recovery (merge with existing)
                  </Label>
                </div>
              </RadioGroup>
            </div>

            {/* Preview Data */}
            {previewData && (
              <Alert>
                <AlertDescription>
                  <div className="space-y-1">
                    <p className="font-medium">Preview:</p>
                    {Object.entries(previewData).map(
                      ([key, data]: [string, any]) => (
                        <p key={key} className="text-sm">
                          {componentLabels[key as keyof typeof componentLabels]}
                          : {data.records || data.count || data.files} items,{" "}
                          {data.size}
                        </p>
                      )
                    )}
                  </div>
                </AlertDescription>
              </Alert>
            )}
          </div>
        ) : (
          <div className="space-y-4 py-8">
            <div className="text-center space-y-2">
              <h3 className="text-lg font-medium">Recovery in Progress</h3>
              <p className="text-sm text-muted-foreground">
                Please do not close this window or navigate away
              </p>
            </div>
            <Progress value={progress} className="h-2" />
            <p className="text-center text-sm text-muted-foreground">
              {progress}% complete
            </p>
          </div>
        )}

        {!recovering && (
          <DialogFooter>
            <Button variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            {!previewData && (
              <Button variant="outline" onClick={handlePreview}>
                Preview Changes
              </Button>
            )}
            <Button
              onClick={handleRecover}
              disabled={!Object.values(components).some((v) => v)}
            >
              Start Recovery
            </Button>
          </DialogFooter>
        )}
      </DialogContent>
    </Dialog>
  );
}
