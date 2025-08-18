'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  LayoutDashboard,
  LineChart,
  Settings,
  Database,
  Zap,
  BookOpen,
  Monitor,
  HelpCircle,
} from 'lucide-react'
import { cn } from '@/lib/utils'

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Strategies', href: '/strategies', icon: BookOpen },
  { name: 'Backtesting', href: '/backtest', icon: LineChart },
  { name: 'Optimization', href: '/optimization', icon: Zap },
  { name: 'Data Management', href: '/data', icon: Database },
  { name: 'Monitoring', href: '/monitor', icon: Monitor },
  { name: 'Settings', href: '/settings', icon: Settings },
  { name: 'Help', href: '/help', icon: HelpCircle },
]

export function Sidebar() {
  const pathname = usePathname()

  return (
    <div className="w-64 bg-gray-900 text-white">
      <div className="flex items-center justify-center h-16 border-b border-gray-800">
        <h2 className="text-xl font-bold">Strategy Lab</h2>
      </div>
      <nav className="mt-8">
        {navigation.map((item) => {
          const Icon = item.icon
          const isActive = pathname === item.href
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                'flex items-center px-6 py-3 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-gray-800 text-white border-l-4 border-blue-500'
                  : 'text-gray-300 hover:bg-gray-800 hover:text-white'
              )}
            >
              <Icon className="mr-3 h-5 w-5" />
              {item.name}
            </Link>
          )
        })}
      </nav>
      
      {/* System Status */}
      <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-800">
        <div className="text-xs text-gray-400">
          <div className="flex justify-between mb-2">
            <span>CPU Usage</span>
            <span className="text-green-400">45%</span>
          </div>
          <div className="flex justify-between mb-2">
            <span>Memory</span>
            <span className="text-yellow-400">12.3 GB</span>
          </div>
          <div className="flex justify-between">
            <span>Status</span>
            <span className="text-green-400">● Online</span>
          </div>
        </div>
      </div>
    </div>
  )
}