'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import { Settings, Sparkles, History, TrendingUp, AlertCircle, Check } from 'lucide-react'

interface DefaultPreset {
  id: string
  name: string
  description: string
  icon: React.ReactNode
  values: Record<string, any>
  recommended?: boolean
  riskLevel: 'conservative' | 'moderate' | 'aggressive'
}

interface SmartDefaultsProps {
  parameters: Array<{
    key: string
    label: string
    type: 'number' | 'string' | 'boolean' | 'select'
    min?: number
    max?: number
    step?: number
    options?: Array<{ value: string; label: string }>
    helpText?: string
    advanced?: boolean
  }>
  onApply: (values: Record<string, any>) => void
  userHistory?: Array<{ date: string; values: Record<string, any>; performance: number }>
}

export function SmartDefaults({ parameters, onApply, userHistory }: SmartDefaultsProps) {
  const [selectedPreset, setSelectedPreset] = useState<string>('recommended')
  const [customValues, setCustomValues] = useState<Record<string, any>>({});
  const [showAdvanced, setShowAdvanced] = useState(false)
  
  // Smart preset definitions
  const presets: DefaultPreset[] = [
    {
      id: 'conservative',
      name: 'Conservative',
      description: 'Lower risk, steady returns',
      icon: <Settings className="h-4 w-4" />,
      riskLevel: 'conservative',
      values: {
        position_size: 1,
        stop_loss: 0.005,
        take_profit: 0.01,
        max_positions: 1,
        lookback_period: 100,
        threshold: 1.5,
      },
    },
    {
      id: 'recommended',
      name: 'Recommended',
      description: 'Balanced risk and reward',
      icon: <Sparkles className="h-4 w-4" />,
      riskLevel: 'moderate',
      recommended: true,
      values: {
        position_size: 2,
        stop_loss: 0.007,
        take_profit: 0.015,
        max_positions: 3,
        lookback_period: 50,
        threshold: 1.0,
      },
    },
    {
      id: 'aggressive',
      name: 'Aggressive',
      description: 'Higher risk, higher potential',
      icon: <TrendingUp className="h-4 w-4" />,
      riskLevel: 'aggressive',
      values: {
        position_size: 3,
        stop_loss: 0.01,
        take_profit: 0.02,
        max_positions: 5,
        lookback_period: 20,
        threshold: 0.8,
      },
    },
  ]
  
  // Add best performing preset from history
  useEffect(() => {
    if (userHistory && userHistory.length > 0) {
      const bestPerforming = userHistory.reduce((best, current) => 
        current.performance > best.performance ? current : best
      )
      
      if (bestPerforming.performance > 1.5) {
        const historicalPreset: DefaultPreset = {
          id: 'historical_best',
          name: 'Your Best',
          description: `Based on your best results (${bestPerforming.performance.toFixed(2)} Sharpe)`,
          icon: <History className="h-4 w-4" />,
          riskLevel: 'moderate',
          values: bestPerforming.values,
        }
        // Add to presets if not already there
        if (!presets.find(p => p.id === 'historical_best')) {
          presets.push(historicalPreset)
        }
      }
    }
  }, [userHistory])
  
  // Initialize custom values with selected preset
  useEffect(() => {
    const preset = presets.find(p => p.id === selectedPreset)
    if (preset) {
      setCustomValues(preset.values)
    }
  }, [selectedPreset])
  
  const handleParameterChange = (key: string, value: any) => {
    setCustomValues(prev => ({ ...prev, [key]: value }))
    setSelectedPreset('custom')
  }
  
  const handleApply = () => {
    onApply(customValues)
  }
  
  const getRiskColor = (level: string) => {
    switch (level) {
      case 'conservative': return 'text-green-600 bg-green-50'
      case 'moderate': return 'text-yellow-600 bg-yellow-50'
      case 'aggressive': return 'text-red-600 bg-red-50'
      default: return 'text-gray-600 bg-gray-50'
    }
  }
  
  return (
    <TooltipProvider>
      <div className="space-y-6">
        {/* Preset Selection */}
        <Card>
          <CardHeader>
            <CardTitle>Quick Start Presets</CardTitle>
            <CardDescription>
              Select a preset configuration or customize your own
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {presets.map((preset) => (
                <button
                  key={preset.id}
                  onClick={() => setSelectedPreset(preset.id)}
                  className={cn(
                    "p-4 border rounded-lg text-left transition-all hover:shadow-md",
                    selectedPreset === preset.id ? 
                      "border-blue-500 bg-blue-50" : 
                      "border-gray-200 hover:border-gray-300"
                  )}
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center gap-2">
                      {preset.icon}
                      <span className="font-semibold">{preset.name}</span>
                    </div>
                    {preset.recommended && (
                      <Badge variant="default" className="text-xs">
                        Recommended
                      </Badge>
                    )}
                  </div>
                  <p className="text-sm text-gray-600 mb-2">{preset.description}</p>
                  <Badge 
                    variant="outline" 
                    className={cn("text-xs", getRiskColor(preset.riskLevel))}
                  >
                    {preset.riskLevel}
                  </Badge>
                </button>
              ))}
            </div>
            
            {selectedPreset === 'custom' && (
              <Alert className="mt-4">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  Custom configuration selected. Parameters have been modified from presets.
                </AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>
        
        {/* Parameter Configuration */}
        <Card>
          <CardHeader>
            <div className="flex justify-between items-center">
              <div>
                <CardTitle>Parameters</CardTitle>
                <CardDescription>
                  Fine-tune your strategy parameters
                </CardDescription>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowAdvanced(!showAdvanced)}
              >
                {showAdvanced ? 'Hide' : 'Show'} Advanced
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {parameters
                .filter(param => showAdvanced || !param.advanced)
                .map((param) => (
                <div key={param.key} className="space-y-2">
                  <div className="flex items-center gap-2">
                    <Label htmlFor={param.key}>{param.label}</Label>
                    {param.helpText && (
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <AlertCircle className="h-3 w-3 text-gray-400" />
                        </TooltipTrigger>
                        <TooltipContent>
                          <p className="max-w-xs">{param.helpText}</p>
                        </TooltipContent>
                      </Tooltip>
                    )}
                  </div>
                  
                  {param.type === 'number' && (
                    <Input
                      id={param.key}
                      type="number"
                      min={param.min}
                      max={param.max}
                      step={param.step}
                      value={customValues[param.key] || 0}
                      onChange={(e) => handleParameterChange(param.key, Number(e.target.value))}
                    />
                  )}
                  
                  {param.type === 'string' && (
                    <Input
                      id={param.key}
                      type="text"
                      value={customValues[param.key] || ''}
                      onChange={(e) => handleParameterChange(param.key, e.target.value)}
                    />
                  )}
                  
                  {param.type === 'select' && (
                    <select
                      id={param.key}
                      className="w-full px-3 py-2 border rounded-md"
                      value={customValues[param.key] || ''}
                      onChange={(e) => handleParameterChange(param.key, e.target.value)}
                    >
                      {param.options?.map(option => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
        
        {/* Apply Button */}
        <div className="flex justify-end gap-2">
          <Button
            variant="outline"
            onClick={() => setSelectedPreset('recommended')}
          >
            Reset to Recommended
          </Button>
          <Button onClick={handleApply} className="flex items-center gap-2">
            <Check className="h-4 w-4" />
            Apply Configuration
          </Button>
        </div>
      </div>
    </TooltipProvider>
  )
}

function cn(...classes: string[]) {
  return classes.filter(Boolean).join(' ')
}