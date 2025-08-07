import { cn } from "@/lib/utils";

interface StatusIndicatorProps {
  status: 'connected' | 'disconnected' | 'healthy' | 'warning' | 'error';
  label?: string;
  className?: string;
}

export function StatusIndicator({ status, label, className }: StatusIndicatorProps) {
  const statusConfig = {
    connected: {
      color: 'bg-green-500',
      label: label || 'Connected',
      textColor: 'text-green-700'
    },
    disconnected: {
      color: 'bg-red-500',
      label: label || 'Disconnected', 
      textColor: 'text-red-700'
    },
    healthy: {
      color: 'bg-green-500',
      label: label || 'Healthy',
      textColor: 'text-green-700'
    },
    warning: {
      color: 'bg-yellow-500',
      label: label || 'Warning',
      textColor: 'text-yellow-700'
    },
    error: {
      color: 'bg-red-500', 
      label: label || 'Error',
      textColor: 'text-red-700'
    }
  };

  const config = statusConfig[status];

  return (
    <div className={cn("flex items-center space-x-2", className)}>
      <div className={cn("w-2 h-2 rounded-full", config.color)} />
      <span className={cn("text-sm font-medium", config.textColor)}>
        {config.label}
      </span>
    </div>
  );
}