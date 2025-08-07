import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface MetricCardProps {
  title: string;
  value: string | number;
  description?: string;
  icon?: LucideIcon;
  trend?: {
    value: number;
    label: string;
    isPositive?: boolean;
  };
  status?: 'healthy' | 'warning' | 'error' | 'neutral';
  className?: string;
}

export function MetricCard({
  title,
  value,
  description,
  icon: Icon,
  trend,
  status = 'neutral',
  className
}: MetricCardProps) {
  const statusColors = {
    healthy: 'border-green-500/20 bg-green-50/50 text-green-900',
    warning: 'border-yellow-500/20 bg-yellow-50/50 text-yellow-900', 
    error: 'border-red-500/20 bg-red-50/50 text-red-900',
    neutral: 'border-border bg-card text-card-foreground'
  };

  const statusIconColors = {
    healthy: 'text-green-600',
    warning: 'text-yellow-600',
    error: 'text-red-600', 
    neutral: 'text-muted-foreground'
  };

  return (
    <Card className={cn(statusColors[status], className)}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">
          {title}
        </CardTitle>
        {Icon && (
          <Icon className={cn("h-4 w-4", statusIconColors[status])} />
        )}
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {description && (
          <p className="text-xs text-muted-foreground">
            {description}
          </p>
        )}
        {trend && (
          <div className="flex items-center space-x-2 text-xs">
            <span className={cn(
              trend.isPositive ? 'text-green-600' : 'text-red-600'
            )}>
              {trend.isPositive ? '↗' : '↘'} {Math.abs(trend.value)}%
            </span>
            <span className="text-muted-foreground">
              {trend.label}
            </span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}