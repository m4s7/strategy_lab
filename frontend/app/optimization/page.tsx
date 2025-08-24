'use client'

import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { OptimizationPanel } from '@/components/optimization/OptimizationPanel'

export default function OptimizationPage() {
  return (
    <DashboardLayout>
      <div className="p-6">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Strategy Optimization</h1>
          <p className="text-gray-600 mt-2">Find optimal parameters for your trading strategies</p>
        </div>
        
        <OptimizationPanel />
      </div>
    </DashboardLayout>
  )
}