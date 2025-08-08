"use client";

import React, { useState } from "react";
import { useSearchParams } from "next/navigation";
import { InteractiveChartSuite } from "@/components/charts/interactive-chart-suite";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Settings, Maximize2 } from "lucide-react";
import Link from "next/link";

// Sample data for demonstration
const sampleChartData = {
  equity: Array.from({ length: 100 }, (_, i) => ({
    timestamp: Date.now() - (100 - i) * 86400000,
    equity: 10000 + Math.random() * 5000 + i * 50,
    benchmark: 10000 + i * 30,
    drawdown: Math.min(0, -Math.random() * 0.1),
  })),
  drawdown: Array.from({ length: 100 }, (_, i) => ({
    timestamp: Date.now() - (100 - i) * 86400000,
    drawdown: -Math.random() * 0.2,
  })),
  returns: Array.from({ length: 20 }, (_, i) => ({
    bin: -0.1 + i * 0.01,
    count: Math.floor(Math.random() * 50),
  })),
  heatmap: {
    min: -100,
    max: 100,
    cells: Array.from({ length: 7 }, (_, i) =>
      Array.from({ length: 24 }, (_, j) => ({
        value: Math.random() * 200 - 100,
        label: `Day ${i + 1}, Hour ${j}`,
      }))
    ),
  },
};

export default function InteractiveChartsPage() {
  const searchParams = useSearchParams();
  const backtestId = searchParams.get("backtestId");
  const [fullscreen, setFullscreen] = useState(false);

  return (
    <div
      className={`${
        fullscreen ? "fixed inset-0 z-50 bg-background" : "container mx-auto"
      } py-6 space-y-6`}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          {backtestId && (
            <Link href={`/results/${backtestId}`}>
              <Button variant="ghost" size="sm">
                <ArrowLeft className="mr-2 h-4 w-4" />
                Back to Results
              </Button>
            </Link>
          )}
          <h1 className="text-3xl font-bold">Interactive Charts</h1>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setFullscreen(!fullscreen)}
          >
            <Maximize2 className="h-4 w-4" />
          </Button>
          <Link href="/charts/advanced">
            <Button variant="outline">
              <Settings className="mr-2 h-4 w-4" />
              Advanced Charts
            </Button>
          </Link>
        </div>
      </div>

      <InteractiveChartSuite
        backtestId={backtestId || "demo"}
        data={backtestId ? undefined : sampleChartData}
      />

      <Card>
        <CardHeader>
          <CardTitle>Chart Features</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <h4 className="font-medium mb-1">Zoom & Pan</h4>
              <p className="text-muted-foreground">
                Click and drag to zoom, use brush for navigation
              </p>
            </div>
            <div>
              <h4 className="font-medium mb-1">Synchronization</h4>
              <p className="text-muted-foreground">
                Charts stay synchronized when sync is enabled
              </p>
            </div>
            <div>
              <h4 className="font-medium mb-1">Export</h4>
              <p className="text-muted-foreground">
                Download charts as PNG images
              </p>
            </div>
            <div>
              <h4 className="font-medium mb-1">Timeframes</h4>
              <p className="text-muted-foreground">
                Switch between tick, minute, hour, and day views
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
