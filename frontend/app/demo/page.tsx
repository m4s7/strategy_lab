'use client'

import { useState } from 'react'
import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { StrategyLibrary } from '@/components/strategy/StrategyLibrary'
import { BacktestPanel } from '@/components/backtest/BacktestPanel'
import { OptimizationPanel } from '@/components/optimization/OptimizationPanel'
import { ResultsPanel } from '@/components/results/ResultsPanel'
import { SystemMonitor } from '@/components/monitoring/SystemMonitor'
import { GuidedWorkflow } from '@/components/workflow/GuidedWorkflow'
import { ProgressiveDisclosure } from '@/components/cognitive/ProgressiveDisclosure'
import { SmartDefaults } from '@/components/cognitive/SmartDefaults'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Rocket, BookOpen, Settings, BarChart3 } from 'lucide-react'

export default function DemoPage() {
  const [activeTab, setActiveTab] = useState('workflow')
  
  // Example sections for progressive disclosure
  const disclosureSections = [
    {
      id: 'basic_metrics',
      title: 'Basic Performance Metrics',
      complexity: 'basic' as const,
      description: 'Essential metrics for strategy evaluation',
      content: (
        <div className="grid grid-cols-3 gap-4">
          <div>
            <p className="text-sm text-gray-500">Total Return</p>
            <p className="text-xl font-bold">24.5%</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Sharpe Ratio</p>
            <p className="text-xl font-bold">1.82</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Win Rate</p>
            <p className="text-xl font-bold">62%</p>
          </div>
        </div>
      ),
      helpText: 'These are the most important metrics to evaluate strategy performance',
    },
    {
      id: 'risk_metrics',
      title: 'Risk Analysis',
      complexity: 'intermediate' as const,
      description: 'Detailed risk and drawdown analysis',
      content: (
        <div className="space-y-2">
          <p>Max Drawdown: -8.3%</p>
          <p>Value at Risk (95%): $2,450</p>
          <p>Recovery Factor: 3.2</p>
        </div>
      ),
      helpText: 'Risk metrics help you understand potential losses',
    },
    {
      id: 'advanced_stats',
      title: 'Advanced Statistics',
      complexity: 'advanced' as const,
      description: 'Complex statistical analysis and correlations',
      content: (
        <div className="space-y-2">
          <p>Sortino Ratio: 2.15</p>
          <p>Calmar Ratio: 2.95</p>
          <p>Tail Ratio: 1.2</p>
          <p>Kelly Criterion: 18.5%</p>
        </div>
      ),
      helpText: 'Advanced metrics for sophisticated analysis',
    },
  ]
  
  // Example parameters for smart defaults
  const strategyParameters = [
    {
      key: 'position_size',
      label: 'Position Size',
      type: 'number' as const,
      min: 1,
      max: 10,
      step: 1,
      helpText: 'Number of contracts per trade',
    },
    {
      key: 'stop_loss',
      label: 'Stop Loss',
      type: 'number' as const,
      min: 0.001,
      max: 0.02,
      step: 0.001,
      helpText: 'Maximum loss per trade',
    },
    {
      key: 'lookback_period',
      label: 'Lookback Period',
      type: 'number' as const,
      min: 10,
      max: 200,
      step: 10,
      helpText: 'Historical data period for analysis',
      advanced: true,
    },
  ]
  
  return (
    <DashboardLayout>
      <div className="p-6">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold mb-2">Strategy Lab Demo</h1>
          <p className="text-gray-600">
            Comprehensive demonstration of all implemented features
          </p>
        </div>
        
        {/* Alert */}
        <Alert className="mb-6">
          <Rocket className="h-4 w-4" />
          <AlertDescription>
            This demo showcases all 10 user stories implemented in Strategy Lab.
            Navigate through the tabs to explore different features.
          </AlertDescription>
        </Alert>
        
        {/* Main Content */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-6">
            <TabsTrigger value="workflow">Workflow</TabsTrigger>
            <TabsTrigger value="strategies">Strategies</TabsTrigger>
            <TabsTrigger value="backtest">Backtest</TabsTrigger>
            <TabsTrigger value="optimize">Optimize</TabsTrigger>
            <TabsTrigger value="results">Results</TabsTrigger>
            <TabsTrigger value="cognitive">Cognitive</TabsTrigger>
          </TabsList>
          
          <TabsContent value="workflow" className="mt-6">
            <GuidedWorkflow
              title="Create Your First Strategy"
              description="Follow this guided workflow to create, test, and optimize a trading strategy"
              onComplete={(data) => console.log('Workflow completed:', data)}
            />
          </TabsContent>
          
          <TabsContent value="strategies" className="mt-6">
            <StrategyLibrary />
          </TabsContent>
          
          <TabsContent value="backtest" className="mt-6">
            <BacktestPanel />
          </TabsContent>
          
          <TabsContent value="optimize" className="mt-6">
            <OptimizationPanel />
          </TabsContent>
          
          <TabsContent value="results" className="mt-6">
            <ResultsPanel />
          </TabsContent>
          
          <TabsContent value="cognitive" className="mt-6 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Cognitive Load Management</CardTitle>
                <CardDescription>
                  Progressive disclosure and smart defaults to reduce complexity
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Tabs defaultValue="progressive">
                  <TabsList>
                    <TabsTrigger value="progressive">Progressive Disclosure</TabsTrigger>
                    <TabsTrigger value="defaults">Smart Defaults</TabsTrigger>
                  </TabsList>
                  
                  <TabsContent value="progressive" className="mt-4">
                    <ProgressiveDisclosure
                      sections={disclosureSections}
                      defaultExpandedLevel="basic"
                    />
                  </TabsContent>
                  
                  <TabsContent value="defaults" className="mt-4">
                    <SmartDefaults
                      parameters={strategyParameters}
                      onApply={(values) => console.log('Applied values:', values)}
                      userHistory={[
                        { date: '2024-01-10', values: { position_size: 2 }, performance: 1.8 },
                        { date: '2024-01-05', values: { position_size: 1 }, performance: 1.5 },
                      ]}
                    />
                  </TabsContent>
                </Tabs>
              </CardContent>
            </Card>
            
            <SystemMonitor />
          </TabsContent>
        </Tabs>
      </div>
    </DashboardLayout>
  )
}