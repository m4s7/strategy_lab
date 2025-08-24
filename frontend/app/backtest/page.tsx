'use client'

import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { BacktestPanel } from '@/components/backtest/BacktestPanel'

export default function BacktestPage() {
  return (
    <DashboardLayout>
      <div className="p-6">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Backtesting Engine</h1>
          <p className="text-gray-600 mt-2">Test your strategies against historical data</p>
        </div>
        
        <BacktestPanel />
      </div>
    </DashboardLayout>
  )
}