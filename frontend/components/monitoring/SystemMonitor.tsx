'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import {
  Cpu, HardDrive, Activity, Zap, AlertTriangle,
  CheckCircle, XCircle, Clock, Database, Server
} from 'lucide-react'
import {
  LineChart, Line, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer
} from 'recharts'

// Mock real-time data
const generateTimeSeriesData = () => {
  return Array.from({ length: 20 }, (_, i) => ({
    time: `${i}s`,
    cpu: Math.random() * 40 + 30,
    memory: Math.random() * 20 + 60,
    threads: Math.floor(Math.random() * 4 + 8),
  }))
}

export function SystemMonitor() {
  const [metrics, setMetrics] = useState({
    cpu: 45,
    memory: 12.3,
    disk: 145,
    threads: 12,
    cores: 8,
    ticksProcessed: 4523000,
    orderBookOps: 98500,
    latency: 0.8,
  })
  
  const [timeSeriesData, setTimeSeriesData] = useState(generateTimeSeriesData())
  const [alerts, setAlerts] = useState<Array<{ type: string; message: string }>>([]);

  // Simulate real-time updates
  useEffect(() => {
    const interval = setInterval(() => {
      setMetrics(prev => ({
        ...prev,
        cpu: Math.min(100, Math.max(0, prev.cpu + (Math.random() - 0.5) * 10)),
        memory: Math.min(32, Math.max(0, prev.memory + (Math.random() - 0.5) * 2)),
        ticksProcessed: prev.ticksProcessed + Math.floor(Math.random() * 10000),
        orderBookOps: prev.orderBookOps + Math.floor(Math.random() * 500),
        latency: Math.max(0.1, prev.latency + (Math.random() - 0.5) * 0.2),
      }))
      
      setTimeSeriesData(prev => [
        ...prev.slice(1),
        {
          time: '20s',
          cpu: Math.random() * 40 + 30,
          memory: Math.random() * 20 + 60,
          threads: Math.floor(Math.random() * 4 + 8),
        }
      ])
    }, 1000)
    
    return () => clearInterval(interval)
  }, [])

  // Check for alerts
  useEffect(() => {
    const newAlerts = []
    if (metrics.cpu > 80) {
      newAlerts.push({ type: 'warning', message: 'High CPU usage detected' })
    }
    if (metrics.memory > 28) {
      newAlerts.push({ type: 'warning', message: 'Memory usage approaching limit' })
    }
    if (metrics.latency > 2) {
      newAlerts.push({ type: 'error', message: 'High latency detected' })
    }
    setAlerts(newAlerts)
  }, [metrics])

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">System Monitor</h2>
          <p className="text-gray-500">Real-time performance and resource monitoring</p>
        </div>
        <div className="flex gap-2">
          <Badge variant="outline" className="flex items-center gap-1">
            <CheckCircle className="h-3 w-3 text-green-500" />
            All Systems Operational
          </Badge>
        </div>
      </div>

      {/* Alerts */}
      {alerts.length > 0 && (
        <div className="space-y-2">
          {alerts.map((alert, index) => (
            <Alert key={index} variant={alert.type === 'error' ? 'destructive' : 'default'}>
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>{alert.message}</AlertDescription>
            </Alert>
          ))}
        </div>
      )}

      {/* Resource Usage */}
      <div className="grid grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Cpu className="h-4 w-4" />
              CPU Usage
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="text-2xl font-bold">{metrics.cpu.toFixed(1)}%</div>
              <Progress value={metrics.cpu} className="h-2" />
              <p className="text-xs text-gray-500">{metrics.cores} cores active</p>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Server className="h-4 w-4" />
              Memory
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="text-2xl font-bold">{metrics.memory.toFixed(1)} GB</div>
              <Progress value={(metrics.memory / 32) * 100} className="h-2" />
              <p className="text-xs text-gray-500">of 32 GB</p>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <HardDrive className="h-4 w-4" />
              Disk I/O
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="text-2xl font-bold">{metrics.disk} MB/s</div>
              <div className="flex justify-between text-xs text-gray-500">
                <span>Read: 85 MB/s</span>
                <span>Write: 60 MB/s</span>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Zap className="h-4 w-4" />
              Threads
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="text-2xl font-bold">{metrics.threads}</div>
              <p className="text-xs text-gray-500">Active threads</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Performance Charts */}
      <div className="grid grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>CPU & Memory Usage</CardTitle>
            <CardDescription>Real-time resource utilization</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={timeSeriesData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="cpu"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  dot={false}
                  name="CPU %"
                />
                <Line
                  type="monotone"
                  dataKey="memory"
                  stroke="#10b981"
                  strokeWidth={2}
                  dot={false}
                  name="Memory %"
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle>Thread Activity</CardTitle>
            <CardDescription>Active thread count over time</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={timeSeriesData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis />
                <Tooltip />
                <Area
                  type="monotone"
                  dataKey="threads"
                  stroke="#8b5cf6"
                  fill="#8b5cf6"
                  fillOpacity={0.3}
                  name="Threads"
                />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Processing Metrics */}
      <Card>
        <CardHeader>
          <CardTitle>Processing Statistics</CardTitle>
          <CardDescription>Real-time data processing metrics</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-4 gap-6">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <Database className="h-4 w-4 text-gray-400" />
                <p className="text-sm text-gray-500">Ticks Processed</p>
              </div>
              <p className="text-xl font-semibold">
                {(metrics.ticksProcessed / 1000000).toFixed(2)}M
              </p>
              <p className="text-xs text-green-500">+10K/s</p>
            </div>
            
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <Activity className="h-4 w-4 text-gray-400" />
                <p className="text-sm text-gray-500">Order Book Ops</p>
              </div>
              <p className="text-xl font-semibold">
                {(metrics.orderBookOps / 1000).toFixed(1)}K/s
              </p>
              <p className="text-xs text-green-500">Normal</p>
            </div>
            
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <Clock className="h-4 w-4 text-gray-400" />
                <p className="text-sm text-gray-500">Avg Latency</p>
              </div>
              <p className="text-xl font-semibold">{metrics.latency.toFixed(1)}ms</p>
              <p className="text-xs text-yellow-500">Moderate</p>
            </div>
            
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <CheckCircle className="h-4 w-4 text-gray-400" />
                <p className="text-sm text-gray-500">Uptime</p>
              </div>
              <p className="text-xl font-semibold">99.9%</p>
              <p className="text-xs text-green-500">2h 45m</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Component Status */}
      <Card>
        <CardHeader>
          <CardTitle>Component Status</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <CheckCircle className="h-4 w-4 text-green-500" />
                <span className="text-sm">Data Ingestion Pipeline</span>
              </div>
              <Badge variant="outline" className="text-green-600">Operational</Badge>
            </div>
            
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <CheckCircle className="h-4 w-4 text-green-500" />
                <span className="text-sm">Order Book Reconstruction</span>
              </div>
              <Badge variant="outline" className="text-green-600">Operational</Badge>
            </div>
            
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <CheckCircle className="h-4 w-4 text-green-500" />
                <span className="text-sm">Backtesting Engine</span>
              </div>
              <Badge variant="outline" className="text-green-600">Idle</Badge>
            </div>
            
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-yellow-500" />
                <span className="text-sm">Optimization Engine</span>
              </div>
              <Badge variant="outline" className="text-yellow-600">Running</Badge>
            </div>
            
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <CheckCircle className="h-4 w-4 text-green-500" />
                <span className="text-sm">WebSocket Server</span>
              </div>
              <Badge variant="outline" className="text-green-600">Connected</Badge>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}