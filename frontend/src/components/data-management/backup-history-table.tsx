"use client";

import { useState, useEffect } from "react";
import {
  CheckCircle,
  XCircle,
  AlertCircle,
  Download,
  RotateCcw,
} from "lucide-react";
import { formatDistanceToNow, format } from "date-fns";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/loading-states";

interface BackupRecord {
  id: string;
  timestamp: Date;
  type: "full" | "incremental" | "manual";
  size: number;
  duration: number;
  status: "success" | "failed" | "partial";
  filesBackedUp: number;
  errors?: string[];
}

interface BackupHistoryTableProps {
  limit?: number;
  onRestore?: (backupId: string) => void;
  onDownload?: (backupId: string) => void;
}

export function BackupHistoryTable({
  limit = 10,
  onRestore,
  onDownload,
}: BackupHistoryTableProps) {
  const [backups, setBackups] = useState<BackupRecord[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Simulate API call
    setTimeout(() => {
      const mockBackups: BackupRecord[] = [
        {
          id: "bkp-001",
          timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000),
          type: "incremental",
          size: 125 * 1024 * 1024,
          duration: 135,
          status: "success",
          filesBackedUp: 1543,
        },
        {
          id: "bkp-002",
          timestamp: new Date(Date.now() - 8 * 60 * 60 * 1000),
          type: "incremental",
          size: 89 * 1024 * 1024,
          duration: 114,
          status: "success",
          filesBackedUp: 1122,
        },
        {
          id: "bkp-003",
          timestamp: new Date(Date.now() - 24 * 60 * 60 * 1000),
          type: "full",
          size: 1.2 * 1024 * 1024 * 1024,
          duration: 522,
          status: "success",
          filesBackedUp: 8765,
        },
        {
          id: "bkp-004",
          timestamp: new Date(Date.now() - 32 * 60 * 60 * 1000),
          type: "incremental",
          size: 76 * 1024 * 1024,
          duration: 98,
          status: "partial",
          filesBackedUp: 987,
          errors: ["Failed to backup /logs/debug.log: File in use"],
        },
        {
          id: "bkp-005",
          timestamp: new Date(Date.now() - 48 * 60 * 60 * 1000),
          type: "manual",
          size: 1.1 * 1024 * 1024 * 1024,
          duration: 487,
          status: "success",
          filesBackedUp: 8432,
        },
      ];
      setBackups(mockBackups.slice(0, limit));
      setLoading(false);
    }, 1000);
  }, [limit]);

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

  const getStatusIcon = (status: BackupRecord["status"]) => {
    switch (status) {
      case "success":
        return <CheckCircle className="w-4 h-4 text-success" />;
      case "failed":
        return <XCircle className="w-4 h-4 text-error" />;
      case "partial":
        return <AlertCircle className="w-4 h-4 text-warning" />;
    }
  };

  const getTypeBadge = (type: BackupRecord["type"]) => {
    const variants = {
      full: "default" as const,
      incremental: "secondary" as const,
      manual: "outline" as const,
    };

    return (
      <Badge variant={variants[type]} className="capitalize">
        {type}
      </Badge>
    );
  };

  if (loading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} variant="table-row" />
        ))}
      </div>
    );
  }

  return (
    <div className="rounded-lg border overflow-hidden">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Time</TableHead>
            <TableHead>Type</TableHead>
            <TableHead>Size</TableHead>
            <TableHead>Duration</TableHead>
            <TableHead>Files</TableHead>
            <TableHead>Status</TableHead>
            <TableHead className="text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {backups.map((backup) => (
            <TableRow key={backup.id}>
              <TableCell>
                <div>
                  <p className="font-medium">
                    {format(backup.timestamp, "MMM dd, HH:mm")}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {formatDistanceToNow(backup.timestamp, { addSuffix: true })}
                  </p>
                </div>
              </TableCell>
              <TableCell>{getTypeBadge(backup.type)}</TableCell>
              <TableCell>{formatBytes(backup.size)}</TableCell>
              <TableCell>{formatDuration(backup.duration)}</TableCell>
              <TableCell>{backup.filesBackedUp.toLocaleString()}</TableCell>
              <TableCell>
                <div className="flex items-center gap-2">
                  {getStatusIcon(backup.status)}
                  <span className="capitalize">{backup.status}</span>
                </div>
                {backup.errors && backup.errors.length > 0 && (
                  <p className="text-xs text-muted-foreground mt-1">
                    {backup.errors.length} error(s)
                  </p>
                )}
              </TableCell>
              <TableCell className="text-right">
                <div className="flex items-center justify-end gap-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onDownload?.(backup.id)}
                    disabled={backup.status === "failed"}
                  >
                    <Download className="w-4 h-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onRestore?.(backup.id)}
                    disabled={backup.status === "failed"}
                  >
                    <RotateCcw className="w-4 h-4" />
                  </Button>
                </div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
