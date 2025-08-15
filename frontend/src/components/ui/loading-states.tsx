"use client";

import { cn } from "@/lib/utils";

interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "text" | "heading" | "button" | "card" | "chart" | "table-row";
  lines?: number;
}

export function Skeleton({
  className,
  variant = "text",
  lines = 1,
  ...props
}: SkeletonProps) {
  const baseClass = "skeleton animate-pulse";

  const variantClasses = {
    text: "h-4 w-full rounded-md",
    heading: "h-6 w-3/4 rounded-md",
    button: "h-10 w-24 rounded-lg",
    card: "h-32 w-full rounded-xl",
    chart: "h-64 w-full rounded-lg",
    "table-row": "h-12 w-full rounded-md",
  };

  if (lines > 1 && (variant === "text" || variant === "heading")) {
    return (
      <div className={cn("space-y-2", className)}>
        {Array.from({ length: lines }).map((_, i) => (
          <div
            key={i}
            className={cn(
              baseClass,
              variantClasses[variant],
              i === lines - 1 && "w-4/5"
            )}
            {...props}
          />
        ))}
      </div>
    );
  }

  return (
    <div
      className={cn(baseClass, variantClasses[variant], className)}
      {...props}
    />
  );
}

interface ProgressBarProps {
  value: number;
  max?: number;
  label?: string;
  showValue?: boolean;
  size?: "sm" | "md" | "lg";
  variant?: "default" | "success" | "warning" | "error";
  striped?: boolean;
  animated?: boolean;
}

export function ProgressBar({
  value,
  max = 100,
  label,
  showValue = false,
  size = "md",
  variant = "default",
  striped = false,
  animated = false,
}: ProgressBarProps) {
  const percentage = Math.round((value / max) * 100);

  const sizeClasses = {
    sm: "h-2",
    md: "h-3",
    lg: "h-4",
  };

  const variantClasses = {
    default: "bg-primary",
    success: "bg-success",
    warning: "bg-warning",
    error: "bg-error",
  };

  return (
    <div className="w-full">
      {(label || showValue) && (
        <div className="flex justify-between items-center mb-1">
          {label && (
            <span className="text-sm text-muted-foreground">{label}</span>
          )}
          {showValue && (
            <span className="text-sm font-medium">{percentage}%</span>
          )}
        </div>
      )}
      <div
        className={cn(
          "w-full bg-muted rounded-full overflow-hidden",
          sizeClasses[size]
        )}
      >
        <div
          className={cn(
            "h-full transition-all duration-300 ease-out",
            variantClasses[variant],
            striped && "progress-striped",
            animated &&
              striped &&
              "animate-[progress-striped_1s_linear_infinite]"
          )}
          style={{ width: `${percentage}%` }}
          role="progressbar"
          aria-valuenow={value}
          aria-valuemin={0}
          aria-valuemax={max}
        />
      </div>
    </div>
  );
}

interface SpinnerProps {
  size?: "sm" | "md" | "lg" | "xl";
  variant?: "default" | "primary" | "white";
  className?: string;
}

export function Spinner({
  size = "md",
  variant = "default",
  className,
}: SpinnerProps) {
  const sizeClasses = {
    sm: "w-4 h-4",
    md: "w-6 h-6",
    lg: "w-8 h-8",
    xl: "w-12 h-12",
  };

  const variantClasses = {
    default: "text-muted-foreground",
    primary: "text-primary",
    white: "text-white",
  };

  return (
    <svg
      className={cn(
        "animate-spin",
        sizeClasses[size],
        variantClasses[variant],
        className
      )}
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
    >
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
      />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
      />
    </svg>
  );
}

interface LoadingOverlayProps {
  visible: boolean;
  message?: string;
  blur?: boolean;
  children: React.ReactNode;
}

export function LoadingOverlay({
  visible,
  message = "Loading...",
  blur = true,
  children,
}: LoadingOverlayProps) {
  return (
    <div className="relative">
      {children}
      {visible && (
        <div
          className={cn(
            "absolute inset-0 z-10 flex items-center justify-center bg-background/50",
            blur && "backdrop-blur-sm"
          )}
        >
          <div className="flex flex-col items-center gap-3">
            <Spinner size="lg" variant="primary" />
            {message && (
              <p className="text-sm text-muted-foreground animate-pulse">
                {message}
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

interface PulsingDotProps {
  size?: "sm" | "md" | "lg";
  color?: "default" | "success" | "warning" | "error" | "info";
  label?: string;
}

export function PulsingDot({
  size = "md",
  color = "default",
  label,
}: PulsingDotProps) {
  const sizeClasses = {
    sm: "h-2 w-2",
    md: "h-3 w-3",
    lg: "h-4 w-4",
  };

  const colorClasses = {
    default: "bg-muted-foreground",
    success: "bg-success",
    warning: "bg-warning",
    error: "bg-error",
    info: "bg-info",
  };

  return (
    <span className="inline-flex items-center gap-2">
      <span className={cn("pulse-dot relative", sizeClasses[size])}>
        <span
          className={cn(
            "absolute inset-0 rounded-full opacity-75 animate-ping",
            colorClasses[color]
          )}
        />
        <span
          className={cn(
            "relative inline-flex h-full w-full rounded-full",
            colorClasses[color]
          )}
        />
      </span>
      {label && <span className="text-sm">{label}</span>}
    </span>
  );
}

interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
}

export function EmptyState({
  icon,
  title,
  description,
  action,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center p-8 text-center",
        className
      )}
    >
      {icon && <div className="mb-4 text-muted-foreground">{icon}</div>}
      <h3 className="text-lg font-medium mb-2">{title}</h3>
      {description && (
        <p className="text-sm text-muted-foreground mb-4 max-w-md">
          {description}
        </p>
      )}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

interface ErrorStateProps {
  error: Error | string;
  retry?: () => void;
  className?: string;
}

export function ErrorState({ error, retry, className }: ErrorStateProps) {
  const errorMessage = typeof error === "string" ? error : error.message;

  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center p-8 text-center",
        className
      )}
    >
      <div className="mb-4 text-error">
        <svg
          className="w-12 h-12"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
      </div>
      <h3 className="text-lg font-medium mb-2">Something went wrong</h3>
      <p className="text-sm text-muted-foreground mb-4 max-w-md">
        {errorMessage}
      </p>
      {retry && (
        <button
          onClick={retry}
          className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary-hover transition-colors-smooth"
        >
          Try again
        </button>
      )}
    </div>
  );
}
