'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  LineChart, Line, AreaChart, Area, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, ScatterChart, Scatter
} from 'recharts'
import { Download, Share2, Filter, TrendingUp, TrendingDown, Activity, DollarSign } from 'lucide-react'

// Mock data for charts
const equityCurveData = Array.from({ length: 100 }, (_, i) => ({
  date: `Day ${i + 1}`,
  equity: 100000 + Math.random() * 20000 - 5000 + i * 100,
  drawdown: -Math.random() * 5000,
}))

const tradesData = Array.from({ length: 50 }, (_, i) => ({
  id: i + 1,
  entry: Math.random() * 100 + 4000,
  exit: Math.random() * 100 + 4000,
  pnl: Math.random() * 1000 - 400,
  duration: Math.floor(Math.random() * 60),
}))

const monthlyReturns = [
  { month: 'Jan', return: 5.2, trades: 120 },
  { month: 'Feb', return: 3.8, trades: 98 },
  { month: 'Mar', return: -1.2, trades: 145 },
  { month: 'Apr', return: 7.5, trades: 132 },
  { month: 'May', return: 2.1, trades: 110 },
  { month: 'Jun', return: 4.6, trades: 128 },
]

export function ResultsPanel() {
  const [selectedPeriod, setSelectedPeriod] = useState('all')
  const [selectedMetric, setSelectedMetric] = useState('equity')

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">Results Analysis</h2>
          <p className="text-gray-500">Performance metrics and detailed analytics</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm">
            <Filter className="h-4 w-4 mr-2" />
            Filter
          </Button>
          <Button variant="outline" size="sm">
            <Share2 className="h-4 w-4 mr-2" />
            Share
          </Button>
          <Button size="sm">
            <Download className="h-4 w-4 mr-2" />
            Export Report
          </Button>
        </div>
      </div>

      {/* Key Metrics Cards */}
      <div className="grid grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Total Return</p>
                <p className="text-2xl font-bold text-green-600">+24.5%</p>
                <p className="text-xs text-gray-400">$24,500</p>
              </div>
              <TrendingUp className="h-8 w-8 text-green-600" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Sharpe Ratio</p>
                <p className="text-2xl font-bold">1.82</p>
                <p className="text-xs text-gray-400">Excellent</p>
              </div>
              <Activity className="h-8 w-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Max Drawdown</p>
                <p className="text-2xl font-bold text-red-600">-8.3%</p>
                <p className="text-xs text-gray-400">$8,300</p>
              </div>
              <TrendingDown className="h-8 w-8 text-red-600" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Win Rate</p>
                <p className="text-2xl font-bold">62%</p>
                <p className="text-xs text-gray-400">310/500 trades</p>
              </div>
              <DollarSign className="h-8 w-8 text-green-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <Tabs defaultValue="equity" className="space-y-4">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="equity">Equity Curve</TabsTrigger>
          <TabsTrigger value="returns">Returns Distribution</TabsTrigger>
          <TabsTrigger value="trades">Trade Analysis</TabsTrigger>
          <TabsTrigger value="metrics">Risk Metrics</TabsTrigger>
        </TabsList>

        <TabsContent value="equity">
          <Card>
            <CardHeader>
              <CardTitle>Equity Curve & Drawdown</CardTitle>
              <CardDescription>
                Portfolio value over time with drawdown visualization
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={equityCurveData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis yAxisId="left" />
                  <YAxis yAxisId="right" orientation="right" />
                  <Tooltip />
                  <Legend />
                  <Line
                    yAxisId="left"
                    type="monotone"
                    dataKey="equity"
                    stroke="#3b82f6"
                    strokeWidth={2}
                    dot={false}
                    name="Equity"
                  />
                  <Area
                    yAxisId="right"
                    type="monotone"
                    dataKey="drawdown"
                    stroke="#ef4444"
                    fill="#ef4444"
                    fillOpacity={0.2}
                    name="Drawdown"
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="returns">
          <Card>
            <CardHeader>
              <CardTitle>Monthly Returns</CardTitle>
              <CardDescription>
                Performance breakdown by month
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={monthlyReturns}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar
                    dataKey="return"
                    fill={(entry) => entry.return >= 0 ? '#10b981' : '#ef4444'}
                    name="Return %"
                  />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="trades">
          <Card>
            <CardHeader>
              <CardTitle>Trade Distribution</CardTitle>
              <CardDescription>
                Profit/Loss distribution across all trades
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <ScatterChart>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="duration" name="Duration (min)" />
                  <YAxis dataKey="pnl" name="P&L ($)" />
                  <Tooltip cursor={{ strokeDasharray: '3 3' }} />
                  <Scatter
                    name="Trades"
                    data={tradesData}
                    fill="#3b82f6"
                  />
                </ScatterChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="metrics">
          <div className="grid grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Performance Metrics</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-500">Sortino Ratio</span>
                    <span className="font-semibold">2.15</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-500">Calmar Ratio</span>
                    <span className="font-semibold">2.95</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-500">Profit Factor</span>
                    <span className="font-semibold">1.68</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-500">Expectancy</span>
                    <span className="font-semibold">$45.20</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-500">Kelly Criterion</span>
                    <span className="font-semibold">18.5%</span>
                  </div>
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader>
                <CardTitle>Risk Metrics</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-500">Value at Risk (95%)</span>
                    <span className="font-semibold">$2,450</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-500">CVaR (95%)</span>
                    <span className="font-semibold">$3,120</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-500">Max Consecutive Losses</span>
                    <span className="font-semibold">5</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-500">Recovery Factor</span>
                    <span className="font-semibold">3.2</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-500">Ulcer Index</span>
                    <span className="font-semibold">4.8</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>

      {/* Trade Statistics */}
      <Card>
        <CardHeader>
          <CardTitle>Trade Statistics</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-4 gap-6">
            <div>
              <p className="text-sm text-gray-500">Total Trades</p>
              <p className="text-xl font-semibold">500</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Avg Win</p>
              <p className="text-xl font-semibold text-green-600">$125.40</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Avg Loss</p>
              <p className="text-xl font-semibold text-red-600">-$74.60</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Avg Duration</p>
              <p className="text-xl font-semibold">23 min</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Best Trade</p>
              <p className="text-xl font-semibold text-green-600">$890.50</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Worst Trade</p>
              <p className="text-xl font-semibold text-red-600">-$420.30</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Commission Paid</p>
              <p className="text-xl font-semibold">$1,250</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Slippage Cost</p>
              <p className="text-xl font-semibold">$780</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}