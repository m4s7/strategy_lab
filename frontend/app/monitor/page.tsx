'use client'

import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { SystemMonitor } from '@/components/monitoring/SystemMonitor'

export default function MonitorPage() {
  return (
    <DashboardLayout>
      <div className="p-6">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">System Monitoring</h1>
          <p className="text-gray-600 mt-2">Real-time system performance and health monitoring</p>
        </div>
        
        <SystemMonitor />
      </div>
    </DashboardLayout>
  )
}