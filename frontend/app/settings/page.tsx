'use client'

import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { Settings, User, Shield, Database, Zap } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Switch } from '@/components/ui/switch'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

export default function SettingsPage() {
  return (
    <DashboardLayout>
      <div className="p-6">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
          <p className="text-gray-600 mt-2">Configure your Strategy Lab environment</p>
        </div>
        
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <Card className="p-6">
              <div className="flex items-center mb-4">
                <User className="w-5 h-5 mr-2" />
                <h3 className="text-lg font-semibold">User Profile</h3>
              </div>
              <div className="space-y-4">
                <div>
                  <Label htmlFor="name">Display Name</Label>
                  <Input id="name" defaultValue="Strategy Trader" />
                </div>
                <div>
                  <Label htmlFor="role">Role</Label>
                  <Input id="role" defaultValue="Quantitative Analyst" />
                </div>
                <div>
                  <Label htmlFor="timezone">Timezone</Label>
                  <Input id="timezone" defaultValue="America/New_York" />
                </div>
              </div>
            </Card>

            <Card className="p-6">
              <div className="flex items-center mb-4">
                <Zap className="w-5 h-5 mr-2" />
                <h3 className="text-lg font-semibold">Performance Settings</h3>
              </div>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <Label>High-Performance Mode</Label>
                    <p className="text-sm text-gray-600">Use maximum system resources</p>
                  </div>
                  <Switch defaultChecked />
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <Label>Parallel Processing</Label>
                    <p className="text-sm text-gray-600">Enable multi-core optimization</p>
                  </div>
                  <Switch defaultChecked />
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <Label>Memory Optimization</Label>
                    <p className="text-sm text-gray-600">Optimize memory usage for large datasets</p>
                  </div>
                  <Switch />
                </div>
                <div>
                  <Label htmlFor="threads">Thread Count</Label>
                  <Input id="threads" type="number" defaultValue="8" />
                </div>
              </div>
            </Card>

            <Card className="p-6">
              <div className="flex items-center mb-4">
                <Database className="w-5 h-5 mr-2" />
                <h3 className="text-lg font-semibold">Data Settings</h3>
              </div>
              <div className="space-y-4">
                <div>
                  <Label htmlFor="dataPath">Data Directory</Label>
                  <Input id="dataPath" defaultValue="/data/strategy_lab" />
                </div>
                <div>
                  <Label htmlFor="cacheSize">Cache Size (MB)</Label>
                  <Input id="cacheSize" type="number" defaultValue="2048" />
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <Label>Auto-backup</Label>
                    <p className="text-sm text-gray-600">Automatically backup data daily</p>
                  </div>
                  <Switch defaultChecked />
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <Label>Data Compression</Label>
                    <p className="text-sm text-gray-600">Compress stored data to save space</p>
                  </div>
                  <Switch defaultChecked />
                </div>
              </div>
            </Card>
          </div>

          <div className="space-y-6">
            <Card className="p-6">
              <div className="flex items-center mb-4">
                <Shield className="w-5 h-5 mr-2" />
                <h3 className="text-lg font-semibold">Security</h3>
              </div>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <Label>Two-Factor Auth</Label>
                    <p className="text-sm text-gray-600">Extra security layer</p>
                  </div>
                  <Switch />
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <Label>Session Timeout</Label>
                    <p className="text-sm text-gray-600">Auto-logout after inactivity</p>
                  </div>
                  <Switch defaultChecked />
                </div>
                <Button variant="outline" className="w-full">
                  Change Password
                </Button>
              </div>
            </Card>

            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">Quick Actions</h3>
              <div className="space-y-3">
                <Button className="w-full">
                  Save All Settings
                </Button>
                <Button variant="outline" className="w-full">
                  Reset to Defaults
                </Button>
                <Button variant="outline" className="w-full">
                  Export Configuration
                </Button>
              </div>
            </Card>

            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">System Info</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Version</span>
                  <span>v2.1.0</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Build</span>
                  <span>2024.08.24</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Uptime</span>
                  <span>2h 45m</span>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </DashboardLayout>
  )
}