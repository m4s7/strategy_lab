"use client";

import { useRef, useEffect, useState } from "react";
import { cn } from "@/lib/utils";

interface ChartDataPoint {
  x: number | string;
  y: number;
  label?: string;
}

interface AccessibleChartProps {
  data: ChartDataPoint[];
  title: string;
  description?: string;
  xLabel?: string;
  yLabel?: string;
  width?: number;
  height?: number;
  className?: string;
  onDataPointFocus?: (point: ChartDataPoint, index: number) => void;
}

export function AccessibleChart({
  data,
  title,
  description,
  xLabel = "X Axis",
  yLabel = "Y Axis",
  width = 600,
  height = 400,
  className,
  onDataPointFocus,
}: AccessibleChartProps) {
  const chartRef = useRef<HTMLDivElement>(null);
  const [focusedIndex, setFocusedIndex] = useState<number>(-1);
  const [announceMessage, setAnnounceMessage] = useState("");

  // Calculate chart dimensions and scales
  const padding = 40;
  const chartWidth = width - 2 * padding;
  const chartHeight = height - 2 * padding;

  const yValues = data.map((d) => d.y);
  const yMin = Math.min(...yValues);
  const yMax = Math.max(...yValues);
  const yScale = chartHeight / (yMax - yMin || 1);

  const xScale = chartWidth / (data.length - 1 || 1);

  // Handle keyboard navigation
  const handleKeyDown = (event: React.KeyboardEvent) => {
    let newIndex = focusedIndex;
    let handled = false;

    switch (event.key) {
      case "ArrowRight":
        newIndex = Math.min(focusedIndex + 1, data.length - 1);
        handled = true;
        break;
      case "ArrowLeft":
        newIndex = Math.max(focusedIndex - 1, 0);
        handled = true;
        break;
      case "Home":
        newIndex = 0;
        handled = true;
        break;
      case "End":
        newIndex = data.length - 1;
        handled = true;
        break;
    }

    if (handled) {
      event.preventDefault();
      setFocusedIndex(newIndex);
      const point = data[newIndex];
      setAnnounceMessage(
        `Data point ${newIndex + 1} of ${data.length}: ${xLabel} ${
          point.x
        }, ${yLabel} ${point.y}${point.label ? `, ${point.label}` : ""}`
      );
      onDataPointFocus?.(point, newIndex);
    }
  };

  // Generate data table for screen readers
  const renderDataTable = () => (
    <table className="sr-only" aria-label={`Data table for ${title}`}>
      <caption>{description}</caption>
      <thead>
        <tr>
          <th>{xLabel}</th>
          <th>{yLabel}</th>
          {data.some((d) => d.label) && <th>Label</th>}
        </tr>
      </thead>
      <tbody>
        {data.map((point, index) => (
          <tr key={index}>
            <td>{point.x}</td>
            <td>{point.y}</td>
            {point.label && <td>{point.label}</td>}
          </tr>
        ))}
      </tbody>
    </table>
  );

  // Generate SVG path for the chart line
  const generatePath = () => {
    return data
      .map((point, index) => {
        const x = padding + index * xScale;
        const y = padding + chartHeight - (point.y - yMin) * yScale;
        return `${index === 0 ? "M" : "L"} ${x} ${y}`;
      })
      .join(" ");
  };

  return (
    <div
      ref={chartRef}
      className={cn("relative focus:outline-none", className)}
      tabIndex={0}
      role="application"
      aria-label={`Interactive chart: ${title}`}
      aria-describedby={description ? `${title}-description` : undefined}
      onKeyDown={handleKeyDown}
    >
      {/* Screen reader announcements */}
      <div
        role="status"
        aria-live="polite"
        aria-atomic="true"
        className="sr-only"
      >
        {announceMessage}
      </div>

      {/* Chart description */}
      {description && (
        <p id={`${title}-description`} className="sr-only">
          {description}
        </p>
      )}

      {/* Data table for screen readers */}
      {renderDataTable()}

      {/* Visual chart */}
      <svg
        width={width}
        height={height}
        aria-hidden="true"
        className="bg-surface border border-border rounded-lg"
      >
        {/* Y-axis labels */}
        <text
          x={padding / 2}
          y={height / 2}
          transform={`rotate(-90 ${padding / 2} ${height / 2})`}
          className="fill-text-secondary text-sm"
          textAnchor="middle"
        >
          {yLabel}
        </text>

        {/* X-axis labels */}
        <text
          x={width / 2}
          y={height - 10}
          className="fill-text-secondary text-sm"
          textAnchor="middle"
        >
          {xLabel}
        </text>

        {/* Grid lines */}
        <g className="stroke-border opacity-20">
          {Array.from({ length: 5 }, (_, i) => {
            const y = padding + (chartHeight / 4) * i;
            return (
              <line
                key={`grid-y-${i}`}
                x1={padding}
                y1={y}
                x2={width - padding}
                y2={y}
                strokeDasharray="2 2"
              />
            );
          })}
        </g>

        {/* Chart line */}
        <path
          d={generatePath()}
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          className="stroke-primary"
        />

        {/* Data points */}
        {data.map((point, index) => {
          const x = padding + index * xScale;
          const y = padding + chartHeight - (point.y - yMin) * yScale;
          const isFocused = index === focusedIndex;

          return (
            <g key={index}>
              <circle
                cx={x}
                cy={y}
                r={isFocused ? 6 : 4}
                className={cn(
                  "transition-all duration-200",
                  isFocused
                    ? "fill-primary stroke-primary-foreground stroke-2"
                    : "fill-primary hover:r-6"
                )}
              />
              {isFocused && (
                <>
                  <rect
                    x={x - 40}
                    y={y - 30}
                    width="80"
                    height="24"
                    rx="4"
                    className="fill-popover stroke-border"
                  />
                  <text
                    x={x}
                    y={y - 14}
                    className="fill-popover-foreground text-xs font-medium"
                    textAnchor="middle"
                  >
                    {point.y}
                  </text>
                </>
              )}
            </g>
          );
        })}
      </svg>

      {/* Keyboard instructions */}
      <div className="mt-2 text-xs text-muted-foreground text-center">
        Use arrow keys to navigate data points
      </div>
    </div>
  );
}

// High contrast mode support
export function useHighContrast() {
  const [isHighContrast, setIsHighContrast] = useState(false);

  useEffect(() => {
    const mediaQuery = window.matchMedia("(prefers-contrast: high)");
    setIsHighContrast(mediaQuery.matches);

    const handler = (e: MediaQueryListEvent) => setIsHighContrast(e.matches);
    mediaQuery.addEventListener("change", handler);
    return () => mediaQuery.removeEventListener("change", handler);
  }, []);

  return isHighContrast;
}

// Reduced motion support
export function useReducedMotion() {
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);

  useEffect(() => {
    const mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
    setPrefersReducedMotion(mediaQuery.matches);

    const handler = (e: MediaQueryListEvent) =>
      setPrefersReducedMotion(e.matches);
    mediaQuery.addEventListener("change", handler);
    return () => mediaQuery.removeEventListener("change", handler);
  }, []);

  return prefersReducedMotion;
}
