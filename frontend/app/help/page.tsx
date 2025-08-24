'use client'

import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { HelpCircle, BookOpen, MessageCircle, Video, FileText, ExternalLink } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'

export default function HelpPage() {
  return (
    <DashboardLayout>
      <div className="p-6">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Help & Documentation</h1>
          <p className="text-gray-600 mt-2">Resources to help you get the most out of Strategy Lab</p>
        </div>
        
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          <Card className="p-6 hover:shadow-lg transition-shadow cursor-pointer">
            <div className="flex items-center mb-4">
              <BookOpen className="w-8 h-8 text-blue-600 mr-3" />
              <h3 className="text-lg font-semibold">Documentation</h3>
            </div>
            <p className="text-gray-600 mb-4">Comprehensive guides and API reference</p>
            <Button variant="outline" className="w-full">
              View Docs <ExternalLink className="w-4 h-4 ml-2" />
            </Button>
          </Card>

          <Card className="p-6 hover:shadow-lg transition-shadow cursor-pointer">
            <div className="flex items-center mb-4">
              <Video className="w-8 h-8 text-green-600 mr-3" />
              <h3 className="text-lg font-semibold">Video Tutorials</h3>
            </div>
            <p className="text-gray-600 mb-4">Step-by-step video walkthroughs</p>
            <Button variant="outline" className="w-full">
              Watch Videos <ExternalLink className="w-4 h-4 ml-2" />
            </Button>
          </Card>

          <Card className="p-6 hover:shadow-lg transition-shadow cursor-pointer">
            <div className="flex items-center mb-4">
              <MessageCircle className="w-8 h-8 text-purple-600 mr-3" />
              <h3 className="text-lg font-semibold">Support</h3>
            </div>
            <p className="text-gray-600 mb-4">Get help from our support team</p>
            <Button variant="outline" className="w-full">
              Contact Support <ExternalLink className="w-4 h-4 ml-2" />
            </Button>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">Quick Start Guide</h3>
            <div className="space-y-4">
              <div className="flex items-start">
                <div className="flex-shrink-0 w-8 h-8 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center font-semibold text-sm">
                  1
                </div>
                <div className="ml-4">
                  <h4 className="font-medium">Import Your Data</h4>
                  <p className="text-sm text-gray-600">Upload MNQ futures tick data through the Data Management page</p>
                </div>
              </div>
              <div className="flex items-start">
                <div className="flex-shrink-0 w-8 h-8 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center font-semibold text-sm">
                  2
                </div>
                <div className="ml-4">
                  <h4 className="font-medium">Create a Strategy</h4>
                  <p className="text-sm text-gray-600">Define your trading rules and parameters</p>
                </div>
              </div>
              <div className="flex items-start">
                <div className="flex-shrink-0 w-8 h-8 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center font-semibold text-sm">
                  3
                </div>
                <div className="ml-4">
                  <h4 className="font-medium">Run Backtest</h4>
                  <p className="text-sm text-gray-600">Test your strategy against historical data</p>
                </div>
              </div>
              <div className="flex items-start">
                <div className="flex-shrink-0 w-8 h-8 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center font-semibold text-sm">
                  4
                </div>
                <div className="ml-4">
                  <h4 className="font-medium">Optimize Parameters</h4>
                  <p className="text-sm text-gray-600">Find the best parameters using optimization algorithms</p>
                </div>
              </div>
              <div className="flex items-start">
                <div className="flex-shrink-0 w-8 h-8 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center font-semibold text-sm">
                  5
                </div>
                <div className="ml-4">
                  <h4 className="font-medium">Analyze Results</h4>
                  <p className="text-sm text-gray-600">Review performance metrics and make adjustments</p>
                </div>
              </div>
            </div>
          </Card>

          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">Frequently Asked Questions</h3>
            <div className="space-y-4">
              <details className="group">
                <summary className="cursor-pointer list-none font-medium hover:text-blue-600">
                  How much data can I process?
                </summary>
                <p className="mt-2 text-sm text-gray-600 pl-4">
                  Strategy Lab can handle 7-10M ticks in under 2 minutes with less than 32GB memory usage.
                </p>
              </details>
              <details className="group">
                <summary className="cursor-pointer list-none font-medium hover:text-blue-600">
                  What optimization methods are available?
                </summary>
                <p className="mt-2 text-sm text-gray-600 pl-4">
                  We support Grid Search, Genetic Algorithms, and Bayesian Optimization for parameter tuning.
                </p>
              </details>
              <details className="group">
                <summary className="cursor-pointer list-none font-medium hover:text-blue-600">
                  Can I export my results?
                </summary>
                <p className="mt-2 text-sm text-gray-600 pl-4">
                  Yes, you can export results in CSV, JSON, or PDF format with detailed performance metrics.
                </p>
              </details>
              <details className="group">
                <summary className="cursor-pointer list-none font-medium hover:text-blue-600">
                  Is real-time trading supported?
                </summary>
                <p className="mt-2 text-sm text-gray-600 pl-4">
                  Currently, Strategy Lab focuses on backtesting and optimization. Real-time trading integration is planned for future releases.
                </p>
              </details>
              <details className="group">
                <summary className="cursor-pointer list-none font-medium hover:text-blue-600">
                  How do I connect my data source?
                </summary>
                <p className="mt-2 text-sm text-gray-600 pl-4">
                  Go to Data Management, click "Connect Data Source", and follow the API integration guide for your provider.
                </p>
              </details>
            </div>
          </Card>
        </div>

        <Card className="p-6 mt-6">
          <div className="flex items-center mb-4">
            <FileText className="w-5 h-5 mr-2" />
            <h3 className="text-lg font-semibold">Keyboard Shortcuts</h3>
          </div>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
            <div>
              <kbd className="px-2 py-1 bg-gray-100 rounded">Ctrl + N</kbd>
              <span className="ml-2 text-gray-600">New Strategy</span>
            </div>
            <div>
              <kbd className="px-2 py-1 bg-gray-100 rounded">Ctrl + B</kbd>
              <span className="ml-2 text-gray-600">Run Backtest</span>
            </div>
            <div>
              <kbd className="px-2 py-1 bg-gray-100 rounded">Ctrl + O</kbd>
              <span className="ml-2 text-gray-600">Optimize</span>
            </div>
            <div>
              <kbd className="px-2 py-1 bg-gray-100 rounded">Ctrl + E</kbd>
              <span className="ml-2 text-gray-600">Export Results</span>
            </div>
            <div>
              <kbd className="px-2 py-1 bg-gray-100 rounded">Ctrl + /</kbd>
              <span className="ml-2 text-gray-600">Search</span>
            </div>
            <div>
              <kbd className="px-2 py-1 bg-gray-100 rounded">Esc</kbd>
              <span className="ml-2 text-gray-600">Cancel Operation</span>
            </div>
            <div>
              <kbd className="px-2 py-1 bg-gray-100 rounded">F1</kbd>
              <span className="ml-2 text-gray-600">Help</span>
            </div>
            <div>
              <kbd className="px-2 py-1 bg-gray-100 rounded">F11</kbd>
              <span className="ml-2 text-gray-600">Fullscreen</span>
            </div>
          </div>
        </Card>
      </div>
    </DashboardLayout>
  )
}