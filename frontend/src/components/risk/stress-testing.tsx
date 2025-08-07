"use client";

import { useState, useEffect, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
} from "recharts";
import { 
  Zap, 
  AlertTriangle, 
  Play, 
  Download,
  Target,
  TrendingDown,
  Calendar,
  Activity
} from "lucide-react";
import { StressScenario, StressTestResults, EventResult } from "@/lib/risk/types";
import { 
  generateMockStressTestResults, 
  generateMockHistoricalEvents 
} from "@/lib/risk/mock-data";

interface StressTestingProps {
  backtestId: string;
}

export function StressTesting({ backtestId }: StressTestingProps) {
  const [scenarios, setScenarios] = useState<StressScenario[]>([
    { name: 'Market Crash', marketDrop: -20, volatilityMultiplier: 3 },
    { name: 'Flash Crash', marketDrop: -10, volatilityMultiplier: 5, duration: 1 },
    { name: 'Prolonged Bear', marketDrop: -30, volatilityMultiplier: 2, duration: 90 },
    { name: 'Volatile Sideways', marketDrop: 0, volatilityMultiplier: 4, duration: 30 },
    { name: 'Custom', marketDrop: 0, volatilityMultiplier: 1, duration: 1 }
  ]);

  const [results, setResults] = useState<StressTestResults[]>([]);
  const [selectedScenario, setSelectedScenario] = useState(scenarios[0]);
  const [customScenario, setCustomScenario] = useState<StressScenario>({
    name: 'Custom',
    marketDrop: -15,
    volatilityMultiplier: 2.5,
    duration: 7
  });
  const [running, setRunning] = useState(false);
  const [historicalEvents, setHistoricalEvents] = useState<Map<string, EventResult>>();

  useEffect(() => {
    // Load historical stress event results
    const loadHistoricalEvents = async () => {
      await new Promise(resolve => setTimeout(resolve, 500));
      const mockEvents = generateMockHistoricalEvents();
      setHistoricalEvents(mockEvents);
    };

    loadHistoricalEvents();
  }, [backtestId]);

  const runStressTest = async () => {
    setRunning(true);
    try {
      // Simulate stress test execution
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      const mockResults = generateMockStressTestResults();
      
      // Add custom scenario result if it's the selected one
      if (selectedScenario.name === 'Custom') {
        const customResult: StressTestResults = {
          scenario: customScenario,
          strategyReturn: -Math.abs(customScenario.marketDrop) * 0.6 / 100, // 60% correlation
          marketReturn: customScenario.marketDrop / 100,
          maxDrawdown: Math.abs(customScenario.marketDrop) * 0.8 / 100,
          volatility: 0.02 * customScenario.volatilityMultiplier,
          sharpeRatio: -1.2
        };
        mockResults.push(customResult);
      }
      
      setResults(mockResults);
    } catch (error) {
      console.error("Stress test failed:", error);
    } finally {
      setRunning(false);
    }
  };

  // Stress test comparison data
  const comparisonData = useMemo(() => {
    return results.map(result => ({
      scenario: result.scenario.name.length > 10 ? 
        result.scenario.name.substring(0, 10) + '...' : 
        result.scenario.name,
      fullName: result.scenario.name,
      strategyReturn: result.strategyReturn * 100,
      marketReturn: result.marketReturn * 100,
      outperformance: (result.strategyReturn - result.marketReturn) * 100,
      maxDrawdown: result.maxDrawdown * 100,
      volatility: result.volatility * 100,
      sharpeRatio: result.sharpeRatio
    }));
  }, [results]);

  // Radar chart data for risk profile
  const riskProfileData = useMemo(() => {
    if (!results.length) return [];
    
    const avgResult = results.reduce((acc, result) => ({
      maxDrawdown: acc.maxDrawdown + Math.abs(result.maxDrawdown),
      volatility: acc.volatility + result.volatility,
      correlation: acc.correlation + Math.abs(result.strategyReturn / result.marketReturn),
      recovery: acc.recovery + (result.sharpeRatio > -2 ? 0.8 : 0.3)
    }), { maxDrawdown: 0, volatility: 0, correlation: 0, recovery: 0 });

    const count = results.length;
    
    return [
      {
        metric: 'Max Drawdown',
        value: (avgResult.maxDrawdown / count) * 100,
        fullMark: 30
      },
      {
        metric: 'Volatility',
        value: (avgResult.volatility / count) * 100,
        fullMark: 10
      },
      {
        metric: 'Market Correlation',
        value: (avgResult.correlation / count) * 100,
        fullMark: 100
      },
      {
        metric: 'Recovery Ability',
        value: (avgResult.recovery / count) * 100,
        fullMark: 100
      }
    ];
  }, [results]);

  const handleExport = () => {
    if (!results.length) return;

    const csvData = [
      ["Scenario", "Strategy Return (%)", "Market Return (%)", "Outperformance (%)", 
       "Max Drawdown (%)", "Volatility (%)", "Sharpe Ratio"],
      ...results.map(result => [
        result.scenario.name,
        (result.strategyReturn * 100).toFixed(2),
        (result.marketReturn * 100).toFixed(2),
        ((result.strategyReturn - result.marketReturn) * 100).toFixed(2),
        (result.maxDrawdown * 100).toFixed(2),
        (result.volatility * 100).toFixed(2),
        result.sharpeRatio.toFixed(2)
      ])
    ].map(row => row.join(",")).join("\\n");

    const blob = new Blob([csvData], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `stress-test-results-${backtestId}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      {/* Stress Test Setup */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Zap className="h-5 w-5" />
            <span>Stress Test Scenarios</span>
          </CardTitle>
        </CardHeader>
        
        <CardContent>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Scenario Selection */}
            <div className="space-y-4">
              <div>
                <Label>Select Scenario</Label>
                <Select 
                  value={selectedScenario.name} 
                  onValueChange={(value) => {
                    const scenario = scenarios.find(s => s.name === value);
                    if (scenario) setSelectedScenario(scenario);
                  }}
                >
                  <SelectTrigger className="mt-1">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {scenarios.map(scenario => (
                      <SelectItem key={scenario.name} value={scenario.name}>
                        {scenario.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Custom Scenario Form */}
              {selectedScenario.name === 'Custom' && (
                <div className="space-y-4 p-4 bg-muted/20 rounded-lg">
                  <h4 className="font-medium">Custom Scenario Parameters</h4>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label>Market Drop (%)</Label>
                      <Input
                        type="number"
                        value={customScenario.marketDrop}
                        onChange={(e) => setCustomScenario(prev => ({
                          ...prev,
                          marketDrop: parseFloat(e.target.value)
                        }))}
                        className="mt-1"
                        step="0.1"
                        max="0"
                      />
                    </div>
                    
                    <div>
                      <Label>Volatility Multiplier</Label>
                      <Input
                        type="number"
                        value={customScenario.volatilityMultiplier}
                        onChange={(e) => setCustomScenario(prev => ({
                          ...prev,
                          volatilityMultiplier: parseFloat(e.target.value)
                        }))}
                        className="mt-1"
                        step="0.1"
                        min="0.1"
                      />
                    </div>
                  </div>
                  
                  <div>
                    <Label>Duration (days)</Label>
                    <Input
                      type="number"
                      value={customScenario.duration || 1}
                      onChange={(e) => setCustomScenario(prev => ({
                        ...prev,
                        duration: parseInt(e.target.value)
                      }))}
                      className="mt-1"
                      min="1"
                    />
                  </div>
                </div>
              )}

              <Button 
                onClick={runStressTest} 
                disabled={running}
                className="w-full"
              >
                {running ? (
                  <Activity className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Play className="h-4 w-4 mr-2" />
                )}
                {running ? "Running Stress Test..." : "Run Stress Test"}
              </Button>
            </div>

            {/* Current Scenario Details */}
            <div className="space-y-4">
              <h4 className="font-medium">Selected Scenario</h4>
              
              <Card className="bg-muted/20">
                <CardContent className="p-4">
                  <div className="space-y-3">
                    <div className="flex items-center space-x-2">
                      <Target className="h-4 w-4 text-muted-foreground" />
                      <span className="font-medium">
                        {selectedScenario.name === 'Custom' ? customScenario.name : selectedScenario.name}
                      </span>
                    </div>
                    
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Market Drop:</span>
                        <span className="font-medium text-red-600">
                          {selectedScenario.name === 'Custom' ? 
                            customScenario.marketDrop : 
                            selectedScenario.marketDrop}%
                        </span>
                      </div>
                      
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Volatility:</span>
                        <span className="font-medium">
                          {selectedScenario.name === 'Custom' ? 
                            customScenario.volatilityMultiplier : 
                            selectedScenario.volatilityMultiplier}x
                        </span>
                      </div>
                      
                      {((selectedScenario.name === 'Custom' && customScenario.duration) || 
                        selectedScenario.duration) && (
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Duration:</span>
                          <span className="font-medium">
                            {selectedScenario.name === 'Custom' ? 
                              customScenario.duration : 
                              selectedScenario.duration} days
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Quick Scenario Buttons */}
              <div className="flex flex-wrap gap-2">
                {scenarios.filter(s => s.name !== 'Custom').map(scenario => (
                  <Button
                    key={scenario.name}
                    variant={selectedScenario.name === scenario.name ? "default" : "outline"}
                    size="sm"
                    onClick={() => setSelectedScenario(scenario)}
                  >
                    {scenario.name}
                  </Button>
                ))}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Stress Test Results */}
      {results.length > 0 && (
        <>
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center space-x-2">
                  <TrendingDown className="h-5 w-5" />
                  <span>Stress Test Results</span>
                </CardTitle>
                
                <Button variant="outline" size="sm" onClick={handleExport}>
                  <Download className="h-4 w-4 mr-2" />
                  Export
                </Button>
              </div>
            </CardHeader>
            
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={comparisonData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="scenario" tick={{ fontSize: 12 }} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip 
                    formatter={(value, name) => [
                      `${Number(value).toFixed(2)}%`, 
                      name === 'strategyReturn' ? 'Strategy Return' :
                      name === 'marketReturn' ? 'Market Return' : 'Outperformance'
                    ]}
                    labelFormatter={(label) => {
                      const item = comparisonData.find(d => d.scenario === label);
                      return item?.fullName || label;
                    }}
                  />
                  <Bar dataKey="strategyReturn" fill="#3b82f6" name="strategyReturn" />
                  <Bar dataKey="marketReturn" fill="#ef4444" name="marketReturn" />
                  <Bar dataKey="outperformance" fill="#10b981" name="outperformance" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Risk Profile Radar */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Risk Profile Assessment</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={250}>
                  <RadarChart data={riskProfileData}>
                    <PolarGrid />
                    <PolarAngleAxis dataKey="metric" tick={{ fontSize: 11 }} />
                    <PolarRadiusAxis angle={90} domain={[0, 100]} />
                    <Radar
                      name="Risk Score"
                      dataKey="value"
                      stroke="#3b82f6"
                      fill="#3b82f6"
                      fillOpacity={0.3}
                    />
                  </RadarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Results Summary Table */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Summary Table</CardTitle>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Scenario</TableHead>
                      <TableHead>Return</TableHead>
                      <TableHead>Max DD</TableHead>
                      <TableHead>Sharpe</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {results.map((result, index) => (
                      <TableRow key={index}>
                        <TableCell className="font-medium">
                          {result.scenario.name}
                        </TableCell>
                        <TableCell>
                          <span className={
                            result.strategyReturn >= 0 ? "text-green-600" : "text-red-600"
                          }>
                            {(result.strategyReturn * 100).toFixed(1)}%
                          </span>
                        </TableCell>
                        <TableCell>
                          <span className="text-red-600">
                            -{(result.maxDrawdown * 100).toFixed(1)}%
                          </span>
                        </TableCell>
                        <TableCell>
                          <Badge variant={result.sharpeRatio > -1 ? "default" : "destructive"}>
                            {result.sharpeRatio.toFixed(2)}
                          </Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </div>
        </>
      )}

      {/* Historical Stress Events */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Calendar className="h-5 w-5" />
            <span>Historical Stress Events</span>
          </CardTitle>
        </CardHeader>
        
        <CardContent>
          {historicalEvents ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Event</TableHead>
                  <TableHead>Period</TableHead>
                  <TableHead>Market Return</TableHead>
                  <TableHead>Strategy Return</TableHead>
                  <TableHead>Outperformance</TableHead>
                  <TableHead>Max Drawdown</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {Array.from(historicalEvents.entries()).map(([eventName, result]) => (
                  <TableRow key={eventName}>
                    <TableCell className="font-medium">{eventName}</TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {eventName.includes('2008') ? 'Sep 2008 - Mar 2009' :
                       eventName.includes('COVID') ? 'Feb 2020 - Mar 2020' :
                       eventName.includes('Volmageddon') ? 'Feb 2018' :
                       'Aug 2015'}
                    </TableCell>
                    <TableCell>
                      <span className="text-red-600 font-medium">
                        {(result.marketReturn * 100).toFixed(1)}%
                      </span>
                    </TableCell>
                    <TableCell>
                      <span className={
                        result.strategyReturn >= 0 ? "text-green-600" : "text-red-600"
                      }>
                        {(result.strategyReturn * 100).toFixed(1)}%
                      </span>
                    </TableCell>
                    <TableCell>
                      <span className={
                        result.strategyReturn > result.marketReturn ? "text-green-600" : "text-red-600"
                      }>
                        {((result.strategyReturn - result.marketReturn) * 100).toFixed(1)}%
                      </span>
                    </TableCell>
                    <TableCell>
                      <span className="text-red-600">
                        -{(result.maxDrawdown * 100).toFixed(1)}%
                      </span>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <div className="flex items-center justify-center h-32">
              <div className="animate-pulse text-muted-foreground">
                Loading historical events...
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}