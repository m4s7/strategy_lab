'use client'

import { useState } from 'react'
import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { StrategyLibrary } from '@/components/strategy/StrategyLibrary'
import { BacktestPanel } from '@/components/backtest/BacktestPanel'
import { OptimizationPanel } from '@/components/optimization/OptimizationPanel'
import { ResultsPanel } from '@/components/results/ResultsPanel'
import { SystemMonitor } from '@/components/monitoring/SystemMonitor'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

export default function DashboardPage() {
  const [activeTab, setActiveTab] = useState('strategies')

  return (
    <DashboardLayout>
      <div className="flex flex-col h-full">
        {/* Header */}
        <div className="border-b bg-white px-6 py-4">
          <h1 className="text-2xl font-bold text-gray-900">Strategy Lab</h1>
          <p className="text-sm text-gray-500 mt-1">
            High-performance backtesting for MNQ futures scalping strategies
          </p>
        </div>

        {/* Main Content */}
        <div className="flex-1 overflow-hidden">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="h-full">
            <div className="border-b bg-white px-6">
              <TabsList className="h-12">
                <TabsTrigger value="strategies">Strategy Library</TabsTrigger>
                <TabsTrigger value="backtest">Backtesting</TabsTrigger>
                <TabsTrigger value="optimization">Optimization</TabsTrigger>
                <TabsTrigger value="results">Results</TabsTrigger>
                <TabsTrigger value="monitor">System Monitor</TabsTrigger>
              </TabsList>
            </div>

            <div className="flex-1 overflow-auto bg-gray-50">
              <TabsContent value="strategies" className="h-full p-6">
                <StrategyLibrary />
              </TabsContent>

              <TabsContent value="backtest" className="h-full p-6">
                <BacktestPanel />
              </TabsContent>

              <TabsContent value="optimization" className="h-full p-6">
                <OptimizationPanel />
              </TabsContent>

              <TabsContent value="results" className="h-full p-6">
                <ResultsPanel />
              </TabsContent>

              <TabsContent value="monitor" className="h-full p-6">
                <SystemMonitor />
              </TabsContent>
            </div>
          </Tabs>
        </div>
      </div>
    </DashboardLayout>
  )
}