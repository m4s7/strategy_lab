'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Search, Plus, Edit2, Copy, Trash2, Play, FileCode } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'

interface Strategy {
  id: string
  name: string
  description: string
  type: 'momentum' | 'mean_reversion' | 'order_book' | 'statistical_arbitrage'
  status: 'active' | 'draft' | 'archived'
  lastModified: string
  performance: {
    sharpe: number
    winRate: number
    totalTrades: number
  }
}

export function StrategyLibrary() {
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedType, setSelectedType] = useState<string>('all')
  
  // Mock data - will be replaced with API call
  const strategies: Strategy[] = [
    {
      id: '1',
      name: 'Order Book Imbalance',
      description: 'Trades based on bid-ask volume imbalances',
      type: 'order_book',
      status: 'active',
      lastModified: '2024-01-15',
      performance: { sharpe: 1.8, winRate: 0.62, totalTrades: 1250 }
    },
    {
      id: '2',
      name: 'Bid-Ask Bounce',
      description: 'Mean reversion strategy on bid-ask spread',
      type: 'mean_reversion',
      status: 'active',
      lastModified: '2024-01-14',
      performance: { sharpe: 1.5, winRate: 0.58, totalTrades: 890 }
    },
    {
      id: '3',
      name: 'Momentum Breakout',
      description: 'Captures breakouts with volume confirmation',
      type: 'momentum',
      status: 'draft',
      lastModified: '2024-01-13',
      performance: { sharpe: 0, winRate: 0, totalTrades: 0 }
    },
  ]

  const filteredStrategies = strategies.filter(strategy => {
    const matchesSearch = strategy.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         strategy.description.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesType = selectedType === 'all' || strategy.type === selectedType
    return matchesSearch && matchesType
  })

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">Strategy Library</h2>
          <p className="text-gray-500">Manage and deploy your trading strategies</p>
        </div>
        <Button className="flex items-center gap-2">
          <Plus className="h-4 w-4" />
          New Strategy
        </Button>
      </div>

      {/* Filters */}
      <div className="flex gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <Input
            placeholder="Search strategies..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>
        <select
          value={selectedType}
          onChange={(e) => setSelectedType(e.target.value)}
          className="px-4 py-2 border rounded-md"
        >
          <option value="all">All Types</option>
          <option value="momentum">Momentum</option>
          <option value="mean_reversion">Mean Reversion</option>
          <option value="order_book">Order Book</option>
          <option value="statistical_arbitrage">Statistical Arbitrage</option>
        </select>
      </div>

      {/* Strategy Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredStrategies.map((strategy) => (
          <Card key={strategy.id} className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle className="text-lg">{strategy.name}</CardTitle>
                  <CardDescription className="mt-1">
                    {strategy.description}
                  </CardDescription>
                </div>
                <Badge 
                  variant={strategy.status === 'active' ? 'default' : 
                          strategy.status === 'draft' ? 'secondary' : 'outline'}
                >
                  {strategy.status}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {/* Performance Metrics */}
                {strategy.status === 'active' && (
                  <div className="grid grid-cols-3 gap-2 text-sm">
                    <div>
                      <p className="text-gray-500">Sharpe</p>
                      <p className="font-semibold">{strategy.performance.sharpe.toFixed(2)}</p>
                    </div>
                    <div>
                      <p className="text-gray-500">Win Rate</p>
                      <p className="font-semibold">{(strategy.performance.winRate * 100).toFixed(0)}%</p>
                    </div>
                    <div>
                      <p className="text-gray-500">Trades</p>
                      <p className="font-semibold">{strategy.performance.totalTrades}</p>
                    </div>
                  </div>
                )}
                
                {/* Metadata */}
                <div className="flex justify-between items-center text-sm text-gray-500">
                  <span className="capitalize">{strategy.type.replace('_', ' ')}</span>
                  <span>Modified {strategy.lastModified}</span>
                </div>
                
                {/* Actions */}
                <div className="flex gap-2 pt-2">
                  <Button size="sm" variant="outline" className="flex-1">
                    <Edit2 className="h-3 w-3 mr-1" />
                    Edit
                  </Button>
                  <Button size="sm" variant="outline" className="flex-1">
                    <Play className="h-3 w-3 mr-1" />
                    Backtest
                  </Button>
                  <Button size="sm" variant="ghost">
                    <Copy className="h-3 w-3" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Empty State */}
      {filteredStrategies.length === 0 && (
        <div className="text-center py-12">
          <FileCode className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold mb-2">No strategies found</h3>
          <p className="text-gray-500 mb-4">Try adjusting your search or filters</p>
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            Create New Strategy
          </Button>
        </div>
      )}
    </div>
  )
}