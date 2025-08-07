"use client";

import { useState, useEffect, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  ComposedChart,
  Line,
  LineChart,
  ScatterChart,
  Scatter,
} from "recharts";
import { Activity, AlertCircle, CheckCircle, Download } from "lucide-react";
import { VaRResults } from "@/lib/risk/types";
import { generateMockVaRResults } from "@/lib/risk/mock-data";
import { 
  calculateHistoricalVaR, 
  calculateParametricVaR, 
  calculateMonteCarloVaR, 
  calculateCVaR,
  backtestVaR
} from "@/lib/risk/calculations";

interface ValueAtRiskAnalysisProps {
  backtestId: string;
}

interface VaRCard {
  confidence: number;
  var: number;
  cvar: number;
}

export function ValueAtRiskAnalysis({ backtestId }: ValueAtRiskAnalysisProps) {
  const [method, setMethod] = useState<"historical" | "parametric" | "montecarlo">("historical");
  const [confidenceLevels] = useState([90, 95, 99]);
  const [varResults, setVarResults] = useState<VaRResults>();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const calculateVaR = async () => {
      setLoading(true);
      try {
        // Simulate API delay
        await new Promise(resolve => setTimeout(resolve, 800));
        
        // Generate mock results
        const mockResults = generateMockVaRResults(method);
        setVarResults(mockResults);
      } catch (error) {
        console.error("Failed to calculate VaR:", error);
      } finally {
        setLoading(false);
      }
    };

    calculateVaR();
  }, [backtestId, method]);

  // Distribution histogram data
  const distributionData = useMemo(() => {
    if (!varResults?.returns) return [];

    const returns = varResults.returns;
    const min = Math.min(...returns);
    const max = Math.max(...returns);
    const binCount = 50;
    const binWidth = (max - min) / binCount;

    const bins = Array(binCount).fill(0).map((_, i) => ({
      x: min + (i + 0.5) * binWidth,
      y: 0,
      range: [min + i * binWidth, min + (i + 1) * binWidth]
    }));

    returns.forEach(return_ => {
      const binIndex = Math.min(Math.floor((return_ - min) / binWidth), binCount - 1);
      if (binIndex >= 0 && binIndex < binCount) {
        bins[binIndex].y++;
      }
    });

    return bins;
  }, [varResults?.returns]);

  // VaR backtest data
  const backtestData = useMemo(() => {
    if (!varResults?.returns) return null;

    const backtest = backtestVaR(varResults.returns, varResults.var[95], 95, 30);
    return backtest;
  }, [varResults]);

  // VaR violations over time
  const violationsData = useMemo(() => {
    if (!varResults?.returns) return [];

    const data = [];
    const window = 30;
    
    for (let i = window; i < varResults.returns.length; i++) {
      const windowReturns = varResults.returns.slice(i - window, i);
      const rollingVar = calculateHistoricalVaR(windowReturns, [95])[95];
      const actualReturn = varResults.returns[i];
      const isViolation = actualReturn < rollingVar;
      
      data.push({
        index: i,
        date: `Day ${i}`,
        return: actualReturn * 100,
        var: rollingVar * 100,
        violation: isViolation ? actualReturn * 100 : null
      });
    }
    
    return data;
  }, [varResults?.returns]);

  if (loading) {
    return (
      <div className="space-y-6">
        <Card>
          <CardContent className="p-6">
            <div className="animate-pulse space-y-4">
              <div className="h-4 bg-muted rounded w-1/4"></div>
              <div className="grid grid-cols-3 gap-4">
                {[...Array(3)].map((_, i) => (
                  <div key={i} className="h-24 bg-muted rounded"></div>
                ))}
              </div>
              <div className="h-64 bg-muted rounded"></div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  const handleExport = () => {
    if (!varResults) return;

    const csvData = [
      ["Confidence Level", "VaR", "CVaR"],
      ...confidenceLevels.map(level => [
        `${level}%`,
        (varResults.var[level] * 100).toFixed(4),
        (varResults.cvar[level] * 100).toFixed(4)
      ])
    ].map(row => row.join(",")).join("\\n");

    const blob = new Blob([csvData], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `var-analysis-${method}-${backtestId}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center space-x-2">
              <Activity className="h-5 w-5" />
              <span>Value at Risk Analysis</span>
            </CardTitle>
            
            <div className="flex items-center space-x-4">
              <Select value={method} onValueChange={(value: any) => setMethod(value)}>
                <SelectTrigger className="w-40">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="historical">Historical VaR</SelectItem>
                  <SelectItem value="parametric">Parametric VaR</SelectItem>
                  <SelectItem value="montecarlo">Monte Carlo VaR</SelectItem>
                </SelectContent>
              </Select>
              
              <Button variant="outline" size="sm" onClick={handleExport}>
                <Download className="h-4 w-4 mr-2" />
                Export
              </Button>
            </div>
          </div>
        </CardHeader>
        
        <CardContent>
          {/* VaR/CVaR Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            {confidenceLevels.map(level => (
              <VaRCard
                key={level}
                confidence={level}
                var={varResults?.var[level] || 0}
                cvar={varResults?.cvar[level] || 0}
              />
            ))}
          </div>

          {/* Return Distribution with VaR Lines */}
          <Card className="mb-6">
            <CardHeader>
              <CardTitle className="text-base">Return Distribution ({method.toUpperCase()})</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <ComposedChart data={distributionData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="x" 
                    tick={{ fontSize: 12 }}
                    tickFormatter={(value) => `${(value * 100).toFixed(1)}%`}
                  />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip 
                    formatter={(value, name) => [value, "Frequency"]}
                    labelFormatter={(value) => `Return: ${(Number(value) * 100).toFixed(2)}%`}
                  />
                  
                  <Bar dataKey="y" fill="#3b82f6" opacity={0.7} />
                  
                  {/* VaR reference lines */}
                  {varResults && Object.entries(varResults.var).map(([level, value]) => (
                    <ReferenceLine
                      key={level}
                      x={value}
                      stroke={level === "95" ? "#ef4444" : level === "99" ? "#dc2626" : "#f59e0b"}
                      strokeDasharray="5 5"
                      strokeWidth={2}
                      label={{ value: `VaR ${level}%`, position: "topRight" }}
                    />
                  ))}
                </ComposedChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* VaR Backtest Results */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2 text-base">
                  {backtestData?.isAccurate ? (
                    <CheckCircle className="h-4 w-4 text-green-600" />
                  ) : (
                    <AlertCircle className="h-4 w-4 text-red-600" />
                  )}
                  <span>VaR Backtest Results</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">Expected Violations (5%)</span>
                    <span className="text-sm font-medium">
                      {((varResults?.returns.length || 0) * 0.05).toFixed(0)}
                    </span>
                  </div>
                  
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">Actual Violations</span>
                    <span className="text-sm font-medium">
                      {backtestData?.violations || 0}
                    </span>
                  </div>
                  
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">Violation Rate</span>
                    <Badge variant={backtestData?.isAccurate ? "default" : "destructive"}>
                      {((backtestData?.violationRate || 0) * 100).toFixed(2)}%
                    </Badge>
                  </div>
                  
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">Model Accuracy</span>
                    <Badge variant={backtestData?.isAccurate ? "default" : "destructive"}>
                      {backtestData?.isAccurate ? "PASS" : "FAIL"}
                    </Badge>
                  </div>
                </div>
                
                <div className="mt-4 text-xs text-muted-foreground">
                  VaR model is considered accurate if violation rate is within 5% tolerance of expected rate.
                </div>
              </CardContent>
            </Card>

            {/* VaR Violations Timeline */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">VaR Violations Timeline</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={200}>
                  <ComposedChart data={violationsData.slice(-60)}> {/* Last 60 data points */}
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="index" 
                      tick={{ fontSize: 10 }}
                    />
                    <YAxis tick={{ fontSize: 10 }} />
                    <Tooltip 
                      formatter={(value, name) => [
                        `${Number(value).toFixed(2)}%`, 
                        name === "return" ? "Actual Return" : name === "var" ? "VaR 95%" : "Violation"
                      ]}
                    />
                    
                    <Line 
                      type="monotone" 
                      dataKey="return" 
                      stroke="#3b82f6" 
                      strokeWidth={1}
                      dot={false}
                      name="return"
                    />
                    
                    <Line 
                      type="monotone" 
                      dataKey="var" 
                      stroke="#ef4444" 
                      strokeWidth={2}
                      strokeDasharray="5 5"
                      dot={false}
                      name="var"
                    />
                    
                    <Scatter 
                      dataKey="violation" 
                      fill="#dc2626" 
                      name="violation"
                    />
                  </ComposedChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function VaRCard({ confidence, var: varValue, cvar }: VaRCard) {
  const severity = Math.abs(varValue) > 0.05 ? "high" : Math.abs(varValue) > 0.03 ? "medium" : "low";
  const colors = {
    low: "text-green-600 bg-green-50 border-green-200",
    medium: "text-yellow-600 bg-yellow-50 border-yellow-200",
    high: "text-red-600 bg-red-50 border-red-200"
  };

  return (
    <Card className={`${colors[severity]} border-2`}>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium">
          VaR/CVaR ({confidence}%)
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <div>
            <div className="text-xl font-bold">
              {(varValue * 100).toFixed(2)}%
            </div>
            <div className="text-xs text-muted-foreground">Value at Risk</div>
          </div>
          
          <div>
            <div className="text-lg font-semibold">
              {(cvar * 100).toFixed(2)}%
            </div>
            <div className="text-xs text-muted-foreground">Expected Shortfall</div>
          </div>
          
          <Badge variant="outline" className="text-xs">
            {severity.toUpperCase()} RISK
          </Badge>
        </div>
      </CardContent>
    </Card>
  );
}