'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { Slider } from '@/components/ui/slider'
import { Switch } from '@/components/ui/switch'
import { Zap, Grid3x3, Dna, Brain, Play, Settings, TrendingUp } from 'lucide-react'
import { Progress } from '@/components/ui/progress'

interface OptimizationParameter {
  name: string
  min: number
  max: number
  step: number
  current: number
}

export function OptimizationPanel() {
  const [optimizationType, setOptimizationType] = useState<'grid' | 'genetic' | 'bayesian'>('grid')
  const [isRunning, setIsRunning] = useState(false)
  const [progress, setProgress] = useState(0)
  const [currentGeneration, setCurrentGeneration] = useState(0)
  
  const [parameters, setParameters] = useState<OptimizationParameter[]>([
    { name: 'lookback_period', min: 10, max: 100, step: 10, current: 50 },
    { name: 'threshold', min: 0.5, max: 2.0, step: 0.1, current: 1.0 },
    { name: 'stop_loss', min: 0.001, max: 0.01, step: 0.001, current: 0.005 },
    { name: 'take_profit', min: 0.002, max: 0.02, step: 0.002, current: 0.01 },
  ])

  const handleStartOptimization = () => {
    setIsRunning(true)
    setProgress(0)
    setCurrentGeneration(0)
    
    // Simulate optimization progress
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval)
          setIsRunning(false)
          return 100
        }
        return prev + 1
      })
      
      if (optimizationType === 'genetic') {
        setCurrentGeneration((prev) => Math.min(prev + 1, 50))
      }
    }, 200)
  }

  const calculateTotalCombinations = () => {
    return parameters.reduce((total, param) => {
      const steps = Math.floor((param.max - param.min) / param.step) + 1
      return total * steps
    }, 1)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">Optimization Engine</h2>
          <p className="text-gray-500">Find optimal strategy parameters</p>
        </div>
        <div className="flex gap-2">
          <Button
            onClick={handleStartOptimization}
            disabled={isRunning}
            className="flex items-center gap-2"
          >
            {isRunning ? (
              <>Running...</>
            ) : (
              <><Play className="h-4 w-4" /> Start Optimization</>
            )}
          </Button>
        </div>
      </div>

      {/* Optimization Type Selection */}
      <Card>
        <CardHeader>
          <CardTitle>Optimization Method</CardTitle>
          <CardDescription>
            Choose the optimization algorithm for parameter search
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4">
            <button
              onClick={() => setOptimizationType('grid')}
              className={`p-4 border rounded-lg transition-colors ${
                optimizationType === 'grid' ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
              }`}
            >
              <Grid3x3 className="h-8 w-8 mb-2 mx-auto" />
              <h3 className="font-semibold">Grid Search</h3>
              <p className="text-sm text-gray-500 mt-1">
                Exhaustive search across parameter space
              </p>
            </button>
            
            <button
              onClick={() => setOptimizationType('genetic')}
              className={`p-4 border rounded-lg transition-colors ${
                optimizationType === 'genetic' ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
              }`}
            >
              <Dna className="h-8 w-8 mb-2 mx-auto" />
              <h3 className="font-semibold">Genetic Algorithm</h3>
              <p className="text-sm text-gray-500 mt-1">
                Evolutionary optimization approach
              </p>
            </button>
            
            <button
              onClick={() => setOptimizationType('bayesian')}
              className={`p-4 border rounded-lg transition-colors ${
                optimizationType === 'bayesian' ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
              }`}
            >
              <Brain className="h-8 w-8 mb-2 mx-auto" />
              <h3 className="font-semibold">Bayesian</h3>
              <p className="text-sm text-gray-500 mt-1">
                Smart probabilistic search
              </p>
            </button>
          </div>
        </CardContent>
      </Card>

      {/* Progress Tracking */}
      {isRunning && (
        <Card>
          <CardContent className="pt-6">
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium">Optimization Progress</span>
                <span className="text-sm text-gray-500">{progress}%</span>
              </div>
              <Progress value={progress} className="h-2" />
              
              {optimizationType === 'grid' && (
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <p className="text-gray-500">Combinations Tested</p>
                    <p className="font-semibold">{Math.floor(calculateTotalCombinations() * progress / 100)}</p>
                  </div>
                  <div>
                    <p className="text-gray-500">Total Combinations</p>
                    <p className="font-semibold">{calculateTotalCombinations()}</p>
                  </div>
                  <div>
                    <p className="text-gray-500">Est. Time Remaining</p>
                    <p className="font-semibold">{Math.ceil((100 - progress) * 0.5)}s</p>
                  </div>
                </div>
              )}
              
              {optimizationType === 'genetic' && (
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <p className="text-gray-500">Generation</p>
                    <p className="font-semibold">{currentGeneration} / 50</p>
                  </div>
                  <div>
                    <p className="text-gray-500">Population Size</p>
                    <p className="font-semibold">100</p>
                  </div>
                  <div>
                    <p className="text-gray-500">Best Fitness</p>
                    <p className="font-semibold">0.823</p>
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Parameter Configuration */}
      <Card>
        <CardHeader>
          <CardTitle>Parameter Configuration</CardTitle>
          <CardDescription>
            Define the search space for each parameter
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {parameters.map((param, index) => (
            <div key={param.name} className="space-y-3 pb-4 border-b last:border-0">
              <div className="flex justify-between items-center">
                <Label className="text-base font-medium">{param.name}</Label>
                <Badge variant="outline">
                  Current: {param.current}
                </Badge>
              </div>
              
              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-1">
                  <Label className="text-sm text-gray-500">Min</Label>
                  <Input
                    type="number"
                    value={param.min}
                    onChange={(e) => {
                      const newParams = [...parameters]
                      newParams[index].min = Number(e.target.value)
                      setParameters(newParams)
                    }}
                    step={param.step}
                  />
                </div>
                
                <div className="space-y-1">
                  <Label className="text-sm text-gray-500">Max</Label>
                  <Input
                    type="number"
                    value={param.max}
                    onChange={(e) => {
                      const newParams = [...parameters]
                      newParams[index].max = Number(e.target.value)
                      setParameters(newParams)
                    }}
                    step={param.step}
                  />
                </div>
                
                <div className="space-y-1">
                  <Label className="text-sm text-gray-500">Step</Label>
                  <Input
                    type="number"
                    value={param.step}
                    onChange={(e) => {
                      const newParams = [...parameters]
                      newParams[index].step = Number(e.target.value)
                      setParameters(newParams)
                    }}
                    step={param.step}
                  />
                </div>
              </div>
              
              <div className="flex items-center gap-4">
                <Slider
                  value={[param.current]}
                  min={param.min}
                  max={param.max}
                  step={param.step}
                  onValueChange={(value) => {
                    const newParams = [...parameters]
                    newParams[index].current = value[0]
                    setParameters(newParams)
                  }}
                  className="flex-1"
                />
                <span className="w-16 text-right text-sm">{param.current}</span>
              </div>
            </div>
          ))}
          
          <Button variant="outline" className="w-full">
            + Add Parameter
          </Button>
        </CardContent>
      </Card>

      {/* Optimization Settings */}
      <Card>
        <CardHeader>
          <CardTitle>Optimization Settings</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Objective Function</Label>
              <select className="w-full px-3 py-2 border rounded-md">
                <option>Sharpe Ratio</option>
                <option>Total Return</option>
                <option>Sortino Ratio</option>
                <option>Calmar Ratio</option>
                <option>Profit Factor</option>
              </select>
            </div>
            
            <div className="space-y-2">
              <Label>Walk-Forward Period</Label>
              <select className="w-full px-3 py-2 border rounded-md">
                <option>None</option>
                <option>1 Month</option>
                <option>3 Months</option>
                <option>6 Months</option>
              </select>
            </div>
          </div>
          
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <Label htmlFor="parallel">Parallel Processing</Label>
              <p className="text-sm text-gray-500">Use multiple CPU cores</p>
            </div>
            <Switch id="parallel" defaultChecked />
          </div>
          
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <Label htmlFor="early-stop">Early Stopping</Label>
              <p className="text-sm text-gray-500">Stop if no improvement after 10 iterations</p>
            </div>
            <Switch id="early-stop" />
          </div>
        </CardContent>
      </Card>
    </div>
  )
}