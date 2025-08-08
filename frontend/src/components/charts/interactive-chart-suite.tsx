"use client";

import React, {
  useState,
  useEffect,
  useRef,
  createContext,
  useContext,
} from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Brush,
  ReferenceLine,
  ResponsiveContainer,
  ComposedChart,
} from "recharts";
import {
  Download,
  ZoomIn,
  ZoomOut,
  RefreshCw,
  Move,
  Settings,
} from "lucide-react";
import { format } from "date-fns";
import html2canvas from "html2canvas";

// Chart synchronization context
interface ChartSyncContextType {
  zoomDomain: [number, number] | null;
  setZoomDomain: (domain: [number, number] | null) => void;
  crosshairPosition: { x: number; y: number } | null;
  setCrosshairPosition: (pos: { x: number; y: number } | null) => void;
  brushDomain: [number, number] | null;
  setBrushDomain: (domain: [number, number] | null) => void;
}

const ChartSyncContext = createContext<ChartSyncContextType>({
  zoomDomain: null,
  setZoomDomain: () => {},
  crosshairPosition: null,
  setCrosshairPosition: () => {},
  brushDomain: null,
  setBrushDomain: () => {},
});

export const useChartSync = () => useContext(ChartSyncContext);

interface InteractiveChartSuiteProps {
  backtestId: string;
  data?: any;
}

export function InteractiveChartSuite({
  backtestId,
  data: initialData,
}: InteractiveChartSuiteProps) {
  const [data, setData] = useState(initialData);
  const [zoomDomain, setZoomDomain] = useState<[number, number] | null>(null);
  const [crosshairPosition, setCrosshairPosition] = useState<{
    x: number;
    y: number;
  } | null>(null);
  const [brushDomain, setBrushDomain] = useState<[number, number] | null>(null);
  const [timeframe, setTimeframe] = useState<string>("1D");
  const [syncEnabled, setSyncEnabled] = useState(true);

  useEffect(() => {
    if (!initialData && backtestId) {
      fetchChartData();
    }
  }, [backtestId]);

  const fetchChartData = async () => {
    try {
      const response = await fetch(`/api/backtests/${backtestId}/charts`);
      if (response.ok) {
        const chartData = await response.json();
        setData(chartData);
      }
    } catch (error) {
      console.error("Failed to fetch chart data:", error);
    }
  };

  const contextValue = {
    zoomDomain: syncEnabled ? zoomDomain : null,
    setZoomDomain: syncEnabled ? setZoomDomain : () => {},
    crosshairPosition: syncEnabled ? crosshairPosition : null,
    setCrosshairPosition: syncEnabled ? setCrosshairPosition : () => {},
    brushDomain: syncEnabled ? brushDomain : null,
    setBrushDomain: syncEnabled ? setBrushDomain : () => {},
  };

  return (
    <ChartSyncContext.Provider value={contextValue}>
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Interactive Chart Suite</CardTitle>
              <div className="flex items-center gap-2">
                <Select value={timeframe} onValueChange={setTimeframe}>
                  <SelectTrigger className="w-32">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="1T">1 Tick</SelectItem>
                    <SelectItem value="1M">1 Minute</SelectItem>
                    <SelectItem value="5M">5 Minutes</SelectItem>
                    <SelectItem value="1H">1 Hour</SelectItem>
                    <SelectItem value="1D">1 Day</SelectItem>
                  </SelectContent>
                </Select>
                <Button
                  variant={syncEnabled ? "default" : "outline"}
                  size="sm"
                  onClick={() => setSyncEnabled(!syncEnabled)}
                >
                  <Move className="h-4 w-4 mr-1" />
                  Sync
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setZoomDomain(null);
                    setBrushDomain(null);
                  }}
                >
                  <RefreshCw className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="equity" className="space-y-4">
              <TabsList className="grid w-full grid-cols-5">
                <TabsTrigger value="equity">Equity Curve</TabsTrigger>
                <TabsTrigger value="drawdown">Drawdown</TabsTrigger>
                <TabsTrigger value="returns">Returns</TabsTrigger>
                <TabsTrigger value="heatmap">Heatmap</TabsTrigger>
                <TabsTrigger value="composite">Composite</TabsTrigger>
              </TabsList>

              <TabsContent value="equity">
                <SynchronizedEquityCurve data={data?.equity} />
              </TabsContent>

              <TabsContent value="drawdown">
                <SynchronizedDrawdownChart data={data?.drawdown} />
              </TabsContent>

              <TabsContent value="returns">
                <SynchronizedReturnsChart data={data?.returns} />
              </TabsContent>

              <TabsContent value="heatmap">
                <InteractiveHeatmap data={data?.heatmap} />
              </TabsContent>

              <TabsContent value="composite">
                <CompositeChartView data={data} />
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      </div>
    </ChartSyncContext.Provider>
  );
}

function SynchronizedEquityCurve({ data }: { data: any }) {
  const { zoomDomain, setZoomDomain, brushDomain, setBrushDomain } =
    useChartSync();
  const chartRef = useRef<HTMLDivElement>(null);

  const handleBrushChange = (domain: any) => {
    if (domain && domain.startIndex !== undefined) {
      setBrushDomain([domain.startIndex, domain.endIndex]);
    }
  };

  const exportChart = async () => {
    if (!chartRef.current) return;

    const canvas = await html2canvas(chartRef.current);
    const link = document.createElement("a");
    link.download = `equity-curve-${Date.now()}.png`;
    link.href = canvas.toDataURL();
    link.click();
  };

  if (!data) return <div>Loading equity curve...</div>;

  return (
    <div ref={chartRef} className="space-y-2">
      <div className="flex justify-between items-center mb-2">
        <h3 className="text-sm font-medium">Equity Curve</h3>
        <Button variant="ghost" size="sm" onClick={exportChart}>
          <Download className="h-4 w-4" />
        </Button>
      </div>
      <ResponsiveContainer width="100%" height={400}>
        <ComposedChart
          data={data}
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
          <XAxis
            dataKey="timestamp"
            tickFormatter={(value) => format(new Date(value), "MM/dd")}
            domain={zoomDomain || ["dataMin", "dataMax"]}
          />
          <YAxis />
          <ChartTooltip
            content={
              <ChartTooltipContent
                labelFormatter={(value) => format(new Date(value), "PPpp")}
              />
            }
          />
          <Area
            type="monotone"
            dataKey="drawdown"
            fill="hsl(var(--destructive))"
            fillOpacity={0.2}
            stroke="none"
          />
          <Line
            type="monotone"
            dataKey="equity"
            stroke="hsl(var(--chart-1))"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 6 }}
          />
          <Line
            type="monotone"
            dataKey="benchmark"
            stroke="hsl(var(--chart-2))"
            strokeWidth={1}
            strokeDasharray="5 5"
            dot={false}
          />
          <Brush
            dataKey="timestamp"
            height={30}
            stroke="hsl(var(--primary))"
            onChange={handleBrushChange}
            startIndex={brushDomain?.[0]}
            endIndex={brushDomain?.[1]}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}

function SynchronizedDrawdownChart({ data }: { data: any }) {
  const { zoomDomain, brushDomain } = useChartSync();
  const chartRef = useRef<HTMLDivElement>(null);

  if (!data) return <div>Loading drawdown chart...</div>;

  return (
    <div ref={chartRef} className="space-y-2">
      <div className="flex justify-between items-center mb-2">
        <h3 className="text-sm font-medium">Underwater Equity (Drawdown)</h3>
        <Button variant="ghost" size="sm">
          <Download className="h-4 w-4" />
        </Button>
      </div>
      <ResponsiveContainer width="100%" height={300}>
        <AreaChart
          data={data}
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
          <XAxis
            dataKey="timestamp"
            tickFormatter={(value) => format(new Date(value), "MM/dd")}
            domain={zoomDomain || ["dataMin", "dataMax"]}
          />
          <YAxis tickFormatter={(value) => `${(value * 100).toFixed(1)}%`} />
          <ChartTooltip
            content={
              <ChartTooltipContent
                labelFormatter={(value) => format(new Date(value), "PPpp")}
                formatter={(value: any) => `${(value * 100).toFixed(2)}%`}
              />
            }
          />
          <Area
            type="monotone"
            dataKey="drawdown"
            stroke="hsl(var(--destructive))"
            fill="hsl(var(--destructive))"
            fillOpacity={0.3}
          />
          <ReferenceLine y={0} stroke="hsl(var(--border))" />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

function SynchronizedReturnsChart({ data }: { data: any }) {
  const { brushDomain } = useChartSync();
  const chartRef = useRef<HTMLDivElement>(null);

  if (!data) return <div>Loading returns distribution...</div>;

  const stats = {
    mean: data.reduce((sum: number, d: any) => sum + d.return, 0) / data.length,
    stdDev: Math.sqrt(
      data.reduce(
        (sum: number, d: any) => sum + Math.pow(d.return - mean, 2),
        0
      ) / data.length
    ),
  };

  return (
    <div ref={chartRef} className="space-y-2">
      <div className="flex justify-between items-center mb-2">
        <h3 className="text-sm font-medium">Returns Distribution</h3>
        <div className="flex gap-2 text-xs text-muted-foreground">
          <span>μ: {stats.mean.toFixed(4)}</span>
          <span>σ: {stats.stdDev.toFixed(4)}</span>
        </div>
      </div>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart
          data={data}
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
          <XAxis dataKey="bin" tickFormatter={(value) => value.toFixed(2)} />
          <YAxis />
          <ChartTooltip content={<ChartTooltipContent />} />
          <Bar dataKey="count" fill="hsl(var(--chart-1))" />
          <ReferenceLine
            x={stats.mean}
            stroke="hsl(var(--chart-2))"
            strokeWidth={2}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

function InteractiveHeatmap({ data }: { data: any }) {
  const [selectedCell, setSelectedCell] = useState<any>(null);

  if (!data) return <div>Loading heatmap...</div>;

  const colorScale = (value: number) => {
    const normalized = (value - data.min) / (data.max - data.min);
    if (normalized < 0.5) {
      return `hsl(0, ${70 + normalized * 60}%, ${50 + normalized * 20}%)`;
    } else {
      return `hsl(120, ${70 + (1 - normalized) * 60}%, ${
        50 + (1 - normalized) * 20
      }%)`;
    }
  };

  return (
    <div className="space-y-2">
      <div className="flex justify-between items-center mb-2">
        <h3 className="text-sm font-medium">Performance Heatmap</h3>
        <Select defaultValue="pnl">
          <SelectTrigger className="w-32">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="pnl">P&L</SelectItem>
            <SelectItem value="trades">Trade Count</SelectItem>
            <SelectItem value="winrate">Win Rate</SelectItem>
          </SelectContent>
        </Select>
      </div>
      <div className="relative">
        <div className="grid grid-cols-24 gap-0.5">
          {data.cells.map((row: any, i: number) => (
            <div key={i} className="contents">
              {row.map((cell: any, j: number) => (
                <div
                  key={`${i}-${j}`}
                  className="aspect-square cursor-pointer hover:ring-2 hover:ring-primary transition-all"
                  style={{ backgroundColor: colorScale(cell.value) }}
                  onMouseEnter={() => setSelectedCell(cell)}
                  onMouseLeave={() => setSelectedCell(null)}
                />
              ))}
            </div>
          ))}
        </div>
        {selectedCell && (
          <div className="absolute top-0 left-0 bg-background border rounded p-2 shadow-lg z-10">
            <p className="text-sm font-medium">{selectedCell.label}</p>
            <p className="text-xs">Value: {selectedCell.value.toFixed(2)}</p>
          </div>
        )}
      </div>
    </div>
  );
}

function CompositeChartView({ data }: { data: any }) {
  if (!data) return <div>Loading composite view...</div>;

  return (
    <div className="grid grid-cols-2 gap-4">
      <div className="col-span-2">
        <SynchronizedEquityCurve data={data?.equity} />
      </div>
      <SynchronizedDrawdownChart data={data?.drawdown} />
      <SynchronizedReturnsChart data={data?.returns} />
    </div>
  );
}
