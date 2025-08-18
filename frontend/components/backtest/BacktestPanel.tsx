'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Slider } from '@/components/ui/slider'
import { Switch } from '@/components/ui/switch'
import { Calendar, Play, Pause, RotateCcw, Settings, TrendingUp, AlertCircle } from 'lucide-react'
import { Progress } from '@/components/ui/progress'

interface BacktestConfig {
  strategy: string
  startDate: string
  endDate: string
  initialCapital: number
  positionSize: number
  maxPositions: number
  commissionRate: number
  slippageModel: 'fixed' | 'linear' | 'square_root'
  slippageValue: number
}

export function BacktestPanel() {
  const [isRunning, setIsRunning] = useState(false)
  const [progress, setProgress] = useState(0)
  const [config, setConfig] = useState<BacktestConfig>({
    strategy: 'order_book_imbalance',
    startDate: '2024-01-01',
    endDate: '2024-01-31',
    initialCapital: 100000,
    positionSize: 1,
    maxPositions: 3,
    commissionRate: 0.0002,
    slippageModel: 'linear',
    slippageValue: 0.0001,
  })

  const handleRunBacktest = () => {
    setIsRunning(true)
    setProgress(0)
    
    // Simulate progress
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval)
          setIsRunning(false)
          return 100
        }
        return prev + 2
      })
    }, 100)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">Backtesting Engine</h2>
          <p className="text-gray-500">Test strategies against historical data</p>
        </div>
        <div className="flex gap-2">
          <Button
            onClick={handleRunBacktest}
            disabled={isRunning}
            className="flex items-center gap-2"
          >
            {isRunning ? (
              <><Pause className="h-4 w-4" /> Pause</>
            ) : (
              <><Play className="h-4 w-4" /> Run Backtest</>
            )}
          </Button>
          <Button variant="outline" disabled={isRunning}>
            <RotateCcw className="h-4 w-4 mr-2" />
            Reset
          </Button>
        </div>
      </div>

      {/* Progress Bar */}
      {isRunning && (
        <Card>
          <CardContent className="pt-6">
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Processing tick data...</span>
                <span>{progress}%</span>
              </div>
              <Progress value={progress} className="h-2" />
              <p className="text-xs text-gray-500">
                Estimated time remaining: {Math.ceil((100 - progress) / 10)}s
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Configuration Tabs */}
      <Tabs defaultValue="basic" className="space-y-4">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="basic">Basic Settings</TabsTrigger>
          <TabsTrigger value="risk">Risk Management</TabsTrigger>
          <TabsTrigger value="costs">Transaction Costs</TabsTrigger>
          <TabsTrigger value="advanced">Advanced</TabsTrigger>
        </TabsList>

        <TabsContent value="basic" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Basic Configuration</CardTitle>
              <CardDescription>
                Set up the fundamental parameters for your backtest
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="strategy">Strategy</Label>
                  <select
                    id="strategy"
                    className="w-full px-3 py-2 border rounded-md"
                    value={config.strategy}
                    onChange={(e) => setConfig({...config, strategy: e.target.value})}
                  >
                    <option value="order_book_imbalance">Order Book Imbalance</option>
                    <option value="bid_ask_bounce">Bid-Ask Bounce</option>
                    <option value="momentum_breakout">Momentum Breakout</option>
                  </select>
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="capital">Initial Capital ($)</Label>
                  <Input
                    id="capital"
                    type="number"
                    value={config.initialCapital}
                    onChange={(e) => setConfig({...config, initialCapital: Number(e.target.value)})}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="start-date">Start Date</Label>
                  <Input
                    id="start-date"
                    type="date"
                    value={config.startDate}
                    onChange={(e) => setConfig({...config, startDate: e.target.value})}
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="end-date">End Date</Label>
                  <Input
                    id="end-date"
                    type="date"
                    value={config.endDate}
                    onChange={(e) => setConfig({...config, endDate: e.target.value})}
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="risk" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Risk Management</CardTitle>
              <CardDescription>
                Configure position sizing and risk limits
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="position-size">Position Size (contracts)</Label>
                  <Input
                    id="position-size"
                    type="number"
                    value={config.positionSize}
                    onChange={(e) => setConfig({...config, positionSize: Number(e.target.value)})}
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="max-positions">Max Concurrent Positions</Label>
                  <Input
                    id="max-positions"
                    type="number"
                    value={config.maxPositions}
                    onChange={(e) => setConfig({...config, maxPositions: Number(e.target.value)})}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label>Max Drawdown Limit (%)</Label>
                <div className="flex items-center space-x-4">
                  <Slider
                    defaultValue={[20]}
                    max={50}
                    step={5}
                    className="flex-1"
                  />
                  <span className="w-12 text-right">20%</span>
                </div>
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <Label htmlFor="stop-on-drawdown">Stop on Drawdown Breach</Label>
                  <p className="text-sm text-gray-500">Halt backtest if drawdown limit is exceeded</p>
                </div>
                <Switch id="stop-on-drawdown" />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="costs" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Transaction Costs</CardTitle>
              <CardDescription>
                Model realistic trading costs and market impact
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="commission">Commission Rate</Label>
                  <Input
                    id="commission"
                    type="number"
                    step="0.0001"
                    value={config.commissionRate}
                    onChange={(e) => setConfig({...config, commissionRate: Number(e.target.value)})}
                  />
                  <p className="text-xs text-gray-500">Per contract per side</p>
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="slippage-model">Slippage Model</Label>
                  <select
                    id="slippage-model"
                    className="w-full px-3 py-2 border rounded-md"
                    value={config.slippageModel}
                    onChange={(e) => setConfig({...config, slippageModel: e.target.value as any})}
                  >
                    <option value="fixed">Fixed</option>
                    <option value="linear">Linear</option>
                    <option value="square_root">Square Root</option>
                  </select>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="slippage-value">Slippage Value</Label>
                <Input
                  id="slippage-value"
                  type="number"
                  step="0.0001"
                  value={config.slippageValue}
                  onChange={(e) => setConfig({...config, slippageValue: Number(e.target.value)})}
                />
                <p className="text-xs text-gray-500">
                  {config.slippageModel === 'fixed' ? 'Fixed amount per trade' :
                   config.slippageModel === 'linear' ? 'Linear factor based on position size' :
                   'Square root factor based on position size'}
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="advanced" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Advanced Settings</CardTitle>
              <CardDescription>
                Fine-tune execution and data handling
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <Label htmlFor="use-bid-ask">Use Bid-Ask Prices</Label>
                  <p className="text-sm text-gray-500">Execute at bid/ask instead of mid price</p>
                </div>
                <Switch id="use-bid-ask" defaultChecked />
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <Label htmlFor="partial-fills">Allow Partial Fills</Label>
                  <p className="text-sm text-gray-500">Simulate partial order execution</p>
                </div>
                <Switch id="partial-fills" />
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <Label htmlFor="latency-sim">Simulate Latency</Label>
                  <p className="text-sm text-gray-500">Add realistic order processing delays</p>
                </div>
                <Switch id="latency-sim" defaultChecked />
              </div>

              <div className="space-y-2">
                <Label>Data Validation Level</Label>
                <select className="w-full px-3 py-2 border rounded-md">
                  <option value="none">None</option>
                  <option value="basic">Basic</option>
                  <option value="standard" selected>Standard</option>
                  <option value="strict">Strict</option>
                </select>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Quick Stats */}
      <div className="grid grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Data Points</p>
                <p className="text-2xl font-bold">7.2M</p>
              </div>
              <TrendingUp className="h-8 w-8 text-gray-400" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Time Period</p>
                <p className="text-2xl font-bold">31d</p>
              </div>
              <Calendar className="h-8 w-8 text-gray-400" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Est. Runtime</p>
                <p className="text-2xl font-bold">45s</p>
              </div>
              <Settings className="h-8 w-8 text-gray-400" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Warnings</p>
                <p className="text-2xl font-bold">0</p>
              </div>
              <AlertCircle className="h-8 w-8 text-gray-400" />
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}