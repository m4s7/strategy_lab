'use client'

import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { StrategyLibrary } from '@/components/strategy/StrategyLibrary'

export default function StrategiesPage() {
  return (
    <DashboardLayout>
      <div className="p-6">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Strategy Management</h1>
          <p className="text-gray-600 mt-2">Create, edit, and manage your trading strategies</p>
        </div>
        
        <StrategyLibrary />
      </div>
    </DashboardLayout>
  )
}