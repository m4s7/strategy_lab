"use client";

import { useState, useEffect } from "react";
import {
  Clock,
  CheckCircle,
  AlertCircle,
  Database,
  HardDrive,
} from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { HelpTooltip } from "@/components/ui/help-tooltip";

interface BackupStatus {
  lastBackup: {
    timestamp: Date;
    type: "full" | "incremental" | "manual";
    size: number;
    duration: number;
    status: "success" | "failed" | "partial";
  };
  nextBackup: {
    timestamp: Date;
    type: "full" | "incremental";
  };
  storage: {
    used: number;
    total: number;
    database: number;
    backups: number;
    logs: number;
  };
  health: "healthy" | "warning" | "critical";
}

export function BackupStatusCard() {
  const [status, setStatus] = useState<BackupStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Simulate API call
    setTimeout(() => {
      setStatus({
        lastBackup: {
          timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000), // 2 hours ago
          type: "incremental",
          size: 125 * 1024 * 1024, // 125 MB
          duration: 135, // 2m 15s
          status: "success",
        },
        nextBackup: {
          timestamp: new Date(Date.now() + 4 * 60 * 60 * 1000), // in 4 hours
          type: "incremental",
        },
        storage: {
          used: 65 * 1024 * 1024 * 1024, // 65 GB
          total: 100 * 1024 * 1024 * 1024, // 100 GB
          database: 45 * 1024 * 1024 * 1024, // 45 GB
          backups: 12 * 1024 * 1024 * 1024, // 12 GB
          logs: 8 * 1024 * 1024 * 1024, // 8 GB
        },
        health: "healthy",
      });
      setLoading(false);
    }, 1000);
  }, []);

  const formatBytes = (bytes: number): string => {
    const units = ["B", "KB", "MB", "GB", "TB"];
    let size = bytes;
    let unitIndex = 0;

    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex++;
    }

    return `${size.toFixed(1)} ${units[unitIndex]}`;
  };

  const formatDuration = (seconds: number): string => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  };

  const getHealthIcon = () => {
    if (!status) return null;

    switch (status.health) {
      case "healthy":
        return <CheckCircle className="w-5 h-5 text-success" />;
      case "warning":
        return <AlertCircle className="w-5 h-5 text-warning" />;
      case "critical":
        return <AlertCircle className="w-5 h-5 text-error" />;
    }
  };

  const getHealthBadge = () => {
    if (!status) return null;

    const variants = {
      healthy: "success" as const,
      warning: "warning" as const,
      critical: "destructive" as const,
    };

    return (
      <Badge variant={variants[status.health]}>
        {status.health.charAt(0).toUpperCase() + status.health.slice(1)}
      </Badge>
    );
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Backup Status</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="skeleton h-20 w-full rounded-lg" />
            <div className="skeleton h-32 w-full rounded-lg" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!status) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Backup Status</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">Unable to load backup status</p>
        </CardContent>
      </Card>
    );
  }

  const storagePercentage = (status.storage.used / status.storage.total) * 100;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Database className="w-5 h-5" />
            Backup Status
          </CardTitle>
          <div className="flex items-center gap-2">
            {getHealthBadge()}
            {getHealthIcon()}
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Last and Next Backup */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2 p-4 bg-surface rounded-lg">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Last Backup</span>
              <HelpTooltip
                content="The most recent backup of your data"
                size="sm"
              />
            </div>
            <div className="space-y-1">
              <p className="text-lg font-medium flex items-center gap-2">
                <Clock className="w-4 h-4" />
                {formatDistanceToNow(status.lastBackup.timestamp, {
                  addSuffix: true,
                })}
              </p>
              <p className="text-sm text-muted-foreground">
                {status.lastBackup.type === "full" ? "Full" : "Incremental"}{" "}
                backup
              </p>
              <p className="text-sm text-muted-foreground">
                Size: {formatBytes(status.lastBackup.size)} • Duration:{" "}
                {formatDuration(status.lastBackup.duration)}
              </p>
            </div>
          </div>

          <div className="space-y-2 p-4 bg-surface rounded-lg">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Next Backup</span>
              <HelpTooltip
                content="When the next automatic backup will run"
                size="sm"
              />
            </div>
            <div className="space-y-1">
              <p className="text-lg font-medium flex items-center gap-2">
                <Clock className="w-4 h-4" />
                {formatDistanceToNow(status.nextBackup.timestamp, {
                  addSuffix: true,
                })}
              </p>
              <p className="text-sm text-muted-foreground">
                {status.nextBackup.type === "full" ? "Full" : "Incremental"}{" "}
                backup scheduled
              </p>
            </div>
          </div>
        </div>

        {/* Storage Usage */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-medium flex items-center gap-2">
              <HardDrive className="w-4 h-4" />
              Storage Usage
            </h4>
            <span className="text-sm text-muted-foreground">
              {formatBytes(status.storage.used)} /{" "}
              {formatBytes(status.storage.total)}
            </span>
          </div>

          <Progress value={storagePercentage} className="h-2" />

          <div className="grid grid-cols-3 gap-2 text-sm">
            <div className="flex items-center justify-between p-2 bg-surface rounded">
              <span className="text-muted-foreground">Database</span>
              <span className="font-medium">
                {formatBytes(status.storage.database)}
              </span>
            </div>
            <div className="flex items-center justify-between p-2 bg-surface rounded">
              <span className="text-muted-foreground">Backups</span>
              <span className="font-medium">
                {formatBytes(status.storage.backups)}
              </span>
            </div>
            <div className="flex items-center justify-between p-2 bg-surface rounded">
              <span className="text-muted-foreground">Logs</span>
              <span className="font-medium">
                {formatBytes(status.storage.logs)}
              </span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
