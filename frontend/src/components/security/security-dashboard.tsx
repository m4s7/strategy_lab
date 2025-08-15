"use client";

import React, { useState, useEffect } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Progress } from "@/components/ui/progress";
import {
  Shield,
  Lock,
  Key,
  AlertTriangle,
  CheckCircle,
  Activity,
  UserCheck,
  ShieldCheck,
  ShieldAlert,
  RefreshCw,
  Download,
  Search,
} from "lucide-react";
import { getAuditLogger, SecurityEvents } from "@/lib/security/audit-logger";
import { useAuth } from "@/lib/auth/auth-provider";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface SecurityMetrics {
  totalEvents: number;
  successfulLogins: number;
  failedLogins: number;
  suspiciousActivities: number;
  permissionDenials: number;
  activeUsers: number;
  securityScore: number;
  lastScan: Date;
}

interface SecurityEvent {
  id: string;
  timestamp: Date;
  action: string;
  resource: string;
  userId?: string;
  status: "success" | "failure";
  risk: "low" | "medium" | "high" | "critical";
  details?: any;
}

export function SecurityDashboard() {
  const { user, hasPermission } = useAuth();
  const [metrics, setMetrics] = useState<SecurityMetrics>({
    totalEvents: 0,
    successfulLogins: 0,
    failedLogins: 0,
    suspiciousActivities: 0,
    permissionDenials: 0,
    activeUsers: 0,
    securityScore: 85,
    lastScan: new Date(),
  });
  const [events, setEvents] = useState<SecurityEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    risk: "all",
    dateRange: "24h",
    action: "all",
  });

  // Check permissions
  const canViewLogs = hasPermission("security.view_logs");
  const canManageSecurity = hasPermission("security.manage");

  useEffect(() => {
    if (canViewLogs) {
      fetchSecurityData();
    }
  }, [canViewLogs, filters]);

  const fetchSecurityData = async () => {
    setLoading(true);
    try {
      // Fetch security metrics
      const metricsResponse = await fetch("/api/security/metrics", {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("authToken")}`,
        },
      });

      if (metricsResponse.ok) {
        const metricsData = await metricsResponse.json();
        setMetrics(metricsData);
      }

      // Fetch recent events
      const logger = getAuditLogger();
      const dateFrom = getDateFromFilter(filters.dateRange);

      const auditLogs = await logger.query({
        dateFrom,
        risk: filters.risk === "all" ? undefined : (filters.risk as any),
        action: filters.action === "all" ? undefined : filters.action,
        limit: 100,
      });

      setEvents(auditLogs as SecurityEvent[]);
    } catch (error) {
      console.error("Failed to fetch security data:", error);
    } finally {
      setLoading(false);
    }
  };

  const getDateFromFilter = (range: string): Date => {
    const now = new Date();
    switch (range) {
      case "1h":
        return new Date(now.getTime() - 60 * 60 * 1000);
      case "24h":
        return new Date(now.getTime() - 24 * 60 * 60 * 1000);
      case "7d":
        return new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
      case "30d":
        return new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
      default:
        return new Date(now.getTime() - 24 * 60 * 60 * 1000);
    }
  };

  const runSecurityScan = async () => {
    if (!canManageSecurity) return;

    try {
      const response = await fetch("/api/security/scan", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${localStorage.getItem("authToken")}`,
        },
      });

      if (response.ok) {
        const result = await response.json();
        setMetrics((prev) => ({
          ...prev,
          securityScore: result.score,
          lastScan: new Date(),
        }));
      }
    } catch (error) {
      console.error("Security scan failed:", error);
    }
  };

  const exportAuditLogs = () => {
    const csv = [
      "Timestamp,Action,Resource,User,Status,Risk,Details",
      ...events.map(
        (event) =>
          `${event.timestamp},${event.action},${event.resource},${
            event.userId || "System"
          },${event.status},${event.risk},"${JSON.stringify(
            event.details || {}
          )}"`
      ),
    ].join("\n");

    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `security-audit-${new Date().toISOString()}.csv`;
    a.click();
  };

  if (!canViewLogs) {
    return (
      <Alert>
        <ShieldAlert className="h-4 w-4" />
        <AlertDescription>
          You don't have permission to view security information.
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Security Dashboard</h1>
          <p className="text-muted-foreground">
            Monitor and manage system security
          </p>
        </div>
        <div className="flex items-center gap-2">
          {canManageSecurity && (
            <Button onClick={runSecurityScan} variant="outline">
              <RefreshCw className="h-4 w-4 mr-2" />
              Run Security Scan
            </Button>
          )}
          <Button onClick={exportAuditLogs} variant="outline">
            <Download className="h-4 w-4 mr-2" />
            Export Logs
          </Button>
        </div>
      </div>

      {/* Security Score */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            Security Score
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-4xl font-bold">
                {metrics.securityScore}%
              </span>
              <Badge
                variant={
                  metrics.securityScore >= 80
                    ? "default"
                    : metrics.securityScore >= 60
                    ? "secondary"
                    : "destructive"
                }
              >
                {metrics.securityScore >= 80
                  ? "Good"
                  : metrics.securityScore >= 60
                  ? "Fair"
                  : "Poor"}
              </Badge>
            </div>
            <Progress value={metrics.securityScore} className="h-3" />
            <p className="text-sm text-muted-foreground">
              Last scan: {new Date(metrics.lastScan).toLocaleString()}
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Total Events"
          value={metrics.totalEvents}
          icon={Activity}
          trend="+12%"
        />
        <MetricCard
          title="Failed Logins"
          value={metrics.failedLogins}
          icon={ShieldAlert}
          trend="-5%"
          variant="destructive"
        />
        <MetricCard
          title="Active Users"
          value={metrics.activeUsers}
          icon={UserCheck}
          trend="+8%"
        />
        <MetricCard
          title="Suspicious Activities"
          value={metrics.suspiciousActivities}
          icon={AlertTriangle}
          trend="-15%"
          variant="warning"
        />
      </div>

      {/* Audit Logs */}
      <Card>
        <CardHeader>
          <CardTitle>Security Audit Logs</CardTitle>
          <CardDescription>
            Recent security events and activities
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Filters */}
            <div className="flex gap-4">
              <div className="flex-1">
                <Label>Risk Level</Label>
                <Select
                  value={filters.risk}
                  onValueChange={(value) =>
                    setFilters({ ...filters, risk: value })
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Levels</SelectItem>
                    <SelectItem value="low">Low</SelectItem>
                    <SelectItem value="medium">Medium</SelectItem>
                    <SelectItem value="high">High</SelectItem>
                    <SelectItem value="critical">Critical</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="flex-1">
                <Label>Time Range</Label>
                <Select
                  value={filters.dateRange}
                  onValueChange={(value) =>
                    setFilters({ ...filters, dateRange: value })
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="1h">Last Hour</SelectItem>
                    <SelectItem value="24h">Last 24 Hours</SelectItem>
                    <SelectItem value="7d">Last 7 Days</SelectItem>
                    <SelectItem value="30d">Last 30 Days</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="flex-1">
                <Label>Action Type</Label>
                <Select
                  value={filters.action}
                  onValueChange={(value) =>
                    setFilters({ ...filters, action: value })
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Actions</SelectItem>
                    <SelectItem value={SecurityEvents.LOGIN_SUCCESS}>
                      Login Success
                    </SelectItem>
                    <SelectItem value={SecurityEvents.LOGIN_FAILURE}>
                      Login Failure
                    </SelectItem>
                    <SelectItem value={SecurityEvents.PERMISSION_DENIED}>
                      Permission Denied
                    </SelectItem>
                    <SelectItem value={SecurityEvents.SUSPICIOUS_ACTIVITY}>
                      Suspicious Activity
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Events Table */}
            <div className="border rounded-lg overflow-hidden">
              <table className="w-full">
                <thead className="bg-muted">
                  <tr>
                    <th className="px-4 py-2 text-left text-sm font-medium">
                      Time
                    </th>
                    <th className="px-4 py-2 text-left text-sm font-medium">
                      Action
                    </th>
                    <th className="px-4 py-2 text-left text-sm font-medium">
                      User
                    </th>
                    <th className="px-4 py-2 text-left text-sm font-medium">
                      Resource
                    </th>
                    <th className="px-4 py-2 text-left text-sm font-medium">
                      Status
                    </th>
                    <th className="px-4 py-2 text-left text-sm font-medium">
                      Risk
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {loading ? (
                    <tr>
                      <td
                        colSpan={6}
                        className="px-4 py-8 text-center text-muted-foreground"
                      >
                        Loading security events...
                      </td>
                    </tr>
                  ) : events.length === 0 ? (
                    <tr>
                      <td
                        colSpan={6}
                        className="px-4 py-8 text-center text-muted-foreground"
                      >
                        No events found for the selected filters
                      </td>
                    </tr>
                  ) : (
                    events.map((event) => (
                      <EventRow key={event.id} event={event} />
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function MetricCard({
  title,
  value,
  icon: Icon,
  trend,
  variant = "default",
}: {
  title: string;
  value: number;
  icon: React.ElementType;
  trend?: string;
  variant?: "default" | "destructive" | "warning";
}) {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-muted-foreground">{title}</p>
            <p className="text-2xl font-bold">{value.toLocaleString()}</p>
            {trend && (
              <p
                className={`text-xs ${
                  trend.startsWith("+") ? "text-green-600" : "text-red-600"
                }`}
              >
                {trend} from last period
              </p>
            )}
          </div>
          <Icon
            className={`h-8 w-8 ${
              variant === "destructive"
                ? "text-destructive"
                : variant === "warning"
                ? "text-yellow-600"
                : "text-muted-foreground"
            }`}
          />
        </div>
      </CardContent>
    </Card>
  );
}

function EventRow({ event }: { event: SecurityEvent }) {
  const getRiskBadgeVariant = (risk: string) => {
    switch (risk) {
      case "critical":
        return "destructive";
      case "high":
        return "destructive";
      case "medium":
        return "secondary";
      default:
        return "outline";
    }
  };

  return (
    <tr className="border-t hover:bg-muted/50">
      <td className="px-4 py-2 text-sm">
        {new Date(event.timestamp).toLocaleString()}
      </td>
      <td className="px-4 py-2 text-sm">{event.action}</td>
      <td className="px-4 py-2 text-sm">{event.userId || "System"}</td>
      <td className="px-4 py-2 text-sm font-mono text-xs">{event.resource}</td>
      <td className="px-4 py-2">
        <Badge variant={event.status === "success" ? "default" : "destructive"}>
          {event.status}
        </Badge>
      </td>
      <td className="px-4 py-2">
        <Badge variant={getRiskBadgeVariant(event.risk)}>{event.risk}</Badge>
      </td>
    </tr>
  );
}
