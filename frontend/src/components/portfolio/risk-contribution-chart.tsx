'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ChartContainer, ChartTooltip, ChartTooltipContent, ChartLegend, ChartLegendContent } from "@/components/ui/chart";
import { 
  PieChart, 
  Pie, 
  Cell,
  BarChart,
  Bar,
  XAxis, 
  YAxis, 
  CartesianGrid,
  ResponsiveContainer,
  RadialBarChart,
  RadialBar
} from 'recharts';
import { useState, useMemo } from 'react';
import { 
  Download,
  Shield,
  TrendingUp,
  AlertCircle,
  BarChart3
} from 'lucide-react';
import { RiskContribution } from '@/lib/portfolio/types';

interface RiskContributionChartProps {
  data: RiskContribution[] | null;
  onExport?: () => void;
  className?: string;
}

const COLORS = [
  '#2563eb', // Blue
  '#dc2626', // Red
  '#059669', // Green
  '#7c3aed', // Purple
  '#ea580c', // Orange
  '#0891b2', // Cyan
  '#be185d', // Pink
  '#65a30d'  // Lime
];

export function RiskContributionChart({ data, onExport, className }: RiskContributionChartProps) {
  const [activeView, setActiveView] = useState<'pie' | 'bar' | 'radial' | 'table'>('pie');

  // Prepare chart data
  const chartData = useMemo(() => {
    if (!data) return [];
    
    return data.map((item, index) => ({
      name: item.strategy,
      shortName: item.strategy.length > 12 ? `${item.strategy.substring(0, 12)}...` : item.strategy,
      weight: item.weight,
      marginalRisk: item.marginalRisk,
      contribution: item.contributionToRisk,
      percentage: item.percentageOfRisk,
      standalone: item.standaloneRisk,
      diversification: item.diversificationBenefit,
      color: COLORS[index % COLORS.length]
    }));
  }, [data]);

  // Calculate key insights
  const riskInsights = useMemo(() => {
    if (!chartData.length) return null;

    const totalRisk = chartData.reduce((sum, item) => sum + item.contribution, 0);
    const weightedAvgRisk = chartData.reduce((sum, item) => sum + (item.weight / 100) * item.standalone, 0);
    
    const mostRiskyStrategy = chartData.reduce((max, current) => 
      current.percentage > max.percentage ? current : max
    );
    
    const leastRiskyStrategy = chartData.reduce((min, current) => 
      current.percentage < min.percentage ? current : min
    );
    
    const bestDiversifier = chartData.reduce((max, current) => 
      current.diversification > max.diversification ? current : max
    );

    const concentrationRisk = chartData.filter(item => item.percentage > 30).length;
    const diversificationBenefit = (weightedAvgRisk - totalRisk) / weightedAvgRisk * 100;

    return {
      totalRisk,
      weightedAvgRisk,
      mostRiskyStrategy,
      leastRiskyStrategy,
      bestDiversifier,
      concentrationRisk,
      diversificationBenefit: Math.max(0, diversificationBenefit)
    };
  }, [chartData]);

  // Custom pie chart label
  const renderCustomLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percentage }: any) => {
    if (percentage < 5) return null; // Don't show labels for small slices
    
    const RADIAN = Math.PI / 180;
    const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
    const x = cx + radius * Math.cos(-midAngle * RADIAN);
    const y = cy + radius * Math.sin(-midAngle * RADIAN);

    return (
      <text 
        x={x} 
        y={y} 
        fill="white" 
        textAnchor={x > cx ? 'start' : 'end'} 
        dominantBaseline="central"
        className="text-xs font-medium"
      >
        {`${percentage.toFixed(0)}%`}
      </text>
    );
  };

  // Custom tooltip
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload || !payload.length) return null;

    const data = payload[0].payload;
    return (
      <div className="bg-background/95 border border-border rounded-lg p-3 shadow-lg">
        <p className="font-medium mb-2">{data.name}</p>
        <div className="space-y-1 text-xs">
          <div className="flex justify-between">
            <span>Weight:</span>
            <span className="font-mono">{data.weight.toFixed(1)}%</span>
          </div>
          <div className="flex justify-between">
            <span>Risk Contribution:</span>
            <span className="font-mono">{data.percentage.toFixed(1)}%</span>
          </div>
          <div className="flex justify-between">
            <span>Marginal Risk:</span>
            <span className="font-mono">{data.marginalRisk.toFixed(2)}%</span>
          </div>
          <div className="flex justify-between">
            <span>Standalone Risk:</span>
            <span className="font-mono">{data.standalone.toFixed(2)}%</span>
          </div>
          <div className="flex justify-between">
            <span>Diversification Benefit:</span>
            <span className="font-mono text-green-600">-{data.diversification.toFixed(2)}%</span>
          </div>
        </div>
      </div>
    );
  };

  if (!data) {
    return (
      <Card className={className}>
        <CardContent className="p-6">
          <div className="text-center text-muted-foreground">Loading risk contribution data...</div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center space-x-2">
              <Shield className="h-5 w-5" />
              <span>Risk Contributions</span>
            </CardTitle>
            <CardDescription>
              How each strategy contributes to overall portfolio risk
            </CardDescription>
          </div>
          
          <div className="flex items-center space-x-2">
            <Badge variant="outline">
              {chartData.length} Strategies
            </Badge>
            {onExport && (
              <Button variant="outline" size="sm" onClick={onExport}>
                <Download className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent>
        {/* Key Insights */}
        {riskInsights && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Highest Risk</p>
                    <p className="font-medium">{riskInsights.mostRiskyStrategy.shortName}</p>
                    <p className="text-xs text-red-600">
                      {riskInsights.mostRiskyStrategy.percentage.toFixed(1)}% of risk
                    </p>
                  </div>
                  <AlertCircle className="h-8 w-8 text-red-600" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Best Diversifier</p>
                    <p className="font-medium">{riskInsights.bestDiversifier.shortName}</p>
                    <p className="text-xs text-green-600">
                      -{riskInsights.bestDiversifier.diversification.toFixed(1)}% risk reduction
                    </p>
                  </div>
                  <TrendingUp className="h-8 w-8 text-green-600" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Diversification Benefit</p>
                    <p className="font-medium text-green-600">
                      {riskInsights.diversificationBenefit.toFixed(1)}%
                    </p>
                    <p className="text-xs text-muted-foreground">Risk reduction</p>
                  </div>
                  <BarChart3 className="h-8 w-8 text-blue-600" />
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Chart Tabs */}
        <Tabs value={activeView} onValueChange={(value: any) => setActiveView(value)}>
          <TabsList className="grid w-full grid-cols-4 mb-6">
            <TabsTrigger value="pie">Pie Chart</TabsTrigger>
            <TabsTrigger value="bar">Bar Chart</TabsTrigger>
            <TabsTrigger value="radial">Radial</TabsTrigger>
            <TabsTrigger value="table">Table</TabsTrigger>
          </TabsList>

          <TabsContent value="pie">
            <div className="h-96">
              <ChartContainer config={{}} className="h-full w-full">
                <PieChart>
                  <Pie
                    data={chartData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={renderCustomLabel}
                    outerRadius={120}
                    fill="#8884d8"
                    dataKey="percentage"
                  >
                    {chartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <ChartTooltip content={<CustomTooltip />} />
                  <ChartLegend 
                    content={({ payload }) => (
                      <div className="flex flex-wrap justify-center gap-4 mt-4">
                        {payload?.map((entry: any, index: number) => (
                          <div key={index} className="flex items-center space-x-2">
                            <div 
                              className="w-3 h-3 rounded-full" 
                              style={{ backgroundColor: entry.color }}
                            />
                            <span className="text-sm">{entry.payload.shortName}</span>
                            <span className="text-sm text-muted-foreground">
                              ({entry.payload.percentage.toFixed(1)}%)
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                  />
                </PieChart>
              </ChartContainer>
            </div>
          </TabsContent>

          <TabsContent value="bar">
            <div className="h-96">
              <ChartContainer config={{}} className="h-full w-full">
                <BarChart data={chartData} layout="horizontal">
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" tickFormatter={(value) => `${value.toFixed(1)}%`} />
                  <YAxis 
                    dataKey="shortName" 
                    type="category" 
                    width={100}
                    tick={{ fontSize: 12 }}
                  />
                  <ChartTooltip content={<CustomTooltip />} />
                  <Bar dataKey="percentage" fill="#2563eb">
                    {chartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ChartContainer>
            </div>
          </TabsContent>

          <TabsContent value="radial">
            <div className="h-96">
              <ChartContainer config={{}} className="h-full w-full">
                <RadialBarChart 
                  cx="50%" 
                  cy="50%" 
                  innerRadius="20%" 
                  outerRadius="80%" 
                  data={chartData}
                >
                  <RadialBar
                    label={{ position: 'insideStart', fill: '#fff' }}
                    background
                    dataKey="percentage"
                  >
                    {chartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </RadialBar>
                  <ChartTooltip content={<CustomTooltip />} />
                </RadialBarChart>
              </ChartContainer>
            </div>
          </TabsContent>

          <TabsContent value="table">
            <div className="rounded-md border overflow-hidden">
              <table className="w-full">
                <thead className="bg-muted/50">
                  <tr>
                    <th className="text-left p-3 font-medium">Strategy</th>
                    <th className="text-right p-3 font-medium">Weight</th>
                    <th className="text-right p-3 font-medium">Risk Contrib.</th>
                    <th className="text-right p-3 font-medium">Marginal Risk</th>
                    <th className="text-right p-3 font-medium">Standalone Risk</th>
                    <th className="text-right p-3 font-medium">Diversification</th>
                  </tr>
                </thead>
                <tbody>
                  {chartData.map((item, index) => (
                    <tr key={index} className="border-t">
                      <td className="p-3">
                        <div className="flex items-center space-x-2">
                          <div 
                            className="w-3 h-3 rounded-full" 
                            style={{ backgroundColor: item.color }}
                          />
                          <span className="font-medium">{item.name}</span>
                        </div>
                      </td>
                      <td className="text-right p-3 font-mono">{item.weight.toFixed(1)}%</td>
                      <td className="text-right p-3 font-mono">{item.percentage.toFixed(1)}%</td>
                      <td className="text-right p-3 font-mono">{item.marginalRisk.toFixed(2)}%</td>
                      <td className="text-right p-3 font-mono">{item.standalone.toFixed(2)}%</td>
                      <td className="text-right p-3 font-mono text-green-600">
                        -{item.diversification.toFixed(2)}%
                      </td>
                    </tr>
                  ))}
                </tbody>
                <tfoot className="bg-muted/30 border-t">
                  <tr>
                    <td className="p-3 font-medium">Total</td>
                    <td className="text-right p-3 font-mono font-medium">
                      {chartData.reduce((sum, item) => sum + item.weight, 0).toFixed(1)}%
                    </td>
                    <td className="text-right p-3 font-mono font-medium">
                      {chartData.reduce((sum, item) => sum + item.percentage, 0).toFixed(1)}%
                    </td>
                    <td className="text-right p-3">-</td>
                    <td className="text-right p-3">-</td>
                    <td className="text-right p-3 font-mono font-medium text-green-600">
                      -{chartData.reduce((sum, item) => sum + item.diversification * (item.weight/100), 0).toFixed(2)}%
                    </td>
                  </tr>
                </tfoot>
              </table>
            </div>

            {/* Risk Analysis */}
            <div className="mt-6 p-4 bg-muted/20 rounded-lg">
              <h4 className="font-medium mb-3 flex items-center">
                <AlertCircle className="h-4 w-4 mr-2" />
                Risk Analysis
              </h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span>Concentration Risk:</span>
                  <span className={`font-medium ${
                    (riskInsights?.concentrationRisk || 0) > 0 ? 'text-red-600' : 'text-green-600'
                  }`}>
                    {(riskInsights?.concentrationRisk || 0) > 0 
                      ? `⚠️ ${riskInsights?.concentrationRisk} strategies > 30% risk`
                      : '✅ Well distributed'
                    }
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Portfolio Diversification:</span>
                  <span className="font-medium text-green-600">
                    {riskInsights?.diversificationBenefit.toFixed(1)}% risk reduction vs. weighted average
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Risk Efficiency:</span>
                  <span className="font-medium">
                    {((riskInsights?.diversificationBenefit || 0) > 15 ? '✅ Highly efficient' :
                      (riskInsights?.diversificationBenefit || 0) > 5 ? '📊 Moderately efficient' :
                      '⚠️ Room for improvement'
                    )}
                  </span>
                </div>
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}