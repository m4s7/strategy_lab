'use client'

import { Bell, Search, User, LogOut } from 'lucide-react'
import { Button } from '@/components/ui/button'

export function Header() {
  return (
    <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6">
      {/* Search Bar */}
      <div className="flex items-center flex-1 max-w-lg">
        <div className="relative w-full">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
          <input
            type="text"
            placeholder="Search strategies, backtests, or data..."
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
      </div>

      {/* Right Side Actions */}
      <div className="flex items-center space-x-4">
        {/* Notifications */}
        <Button variant="ghost" size="sm" className="relative">
          <Bell className="h-5 w-5 text-gray-500" />
          <span className="absolute -top-1 -right-1 h-3 w-3 bg-red-500 rounded-full text-xs text-white flex items-center justify-center">
            3
          </span>
        </Button>

        {/* User Profile */}
        <div className="flex items-center space-x-3">
          <div className="text-right">
            <p className="text-sm font-medium text-gray-900">Strategy Trader</p>
            <p className="text-xs text-gray-500">Quantitative Analyst</p>
          </div>
          <Button variant="ghost" size="sm" className="rounded-full p-2">
            <User className="h-5 w-5 text-gray-500" />
          </Button>
        </div>

        {/* Logout */}
        <Button variant="ghost" size="sm">
          <LogOut className="h-4 w-4 text-gray-500" />
        </Button>
      </div>
    </header>
  )
}