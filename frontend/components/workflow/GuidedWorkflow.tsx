'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  CheckCircle, Circle, ArrowRight, ArrowLeft, 
  AlertTriangle, Info, Zap, BookOpen, Play, 
  BarChart3, Target, FileText, Rocket
} from 'lucide-react'
import { cn } from '@/lib/utils'

interface WorkflowStep {
  id: string
  title: string
  description: string
  icon: React.ReactNode
  status: 'pending' | 'in_progress' | 'completed' | 'skipped'
  required: boolean
  estimatedTime: string
  component?: React.ReactNode
  validation?: () => { valid: boolean; message?: string }
  helpContent?: string
}

interface WorkflowProps {
  title: string
  description: string
  onComplete?: (results: any) => void
}

export function GuidedWorkflow({ title, description, onComplete }: WorkflowProps) {
  const [currentStep, setCurrentStep] = useState(0)
  const [completedSteps, setCompletedSteps] = useState<Set<string>>(new Set())
  const [workflowData, setWorkflowData] = useState<Record<string, any>>({});
  const [showHelp, setShowHelp] = useState(false)
  
  // Define workflow steps
  const steps: WorkflowStep[] = [
    {
      id: 'data_selection',
      title: 'Select Data',
      description: 'Choose historical data period and instruments',
      icon: <BookOpen className="h-5 w-5" />,
      status: 'pending',
      required: true,
      estimatedTime: '2 min',
      helpContent: 'Select the time period and futures contracts you want to backtest. Longer periods provide more statistical significance.',
      validation: () => {
        if (!workflowData.dataSelected) {
          return { valid: false, message: 'Please select data before proceeding' }
        }
        return { valid: true }
      },
    },
    {
      id: 'strategy_config',
      title: 'Configure Strategy',
      description: 'Set up strategy parameters and rules',
      icon: <Target className="h-5 w-5" />,
      status: 'pending',
      required: true,
      estimatedTime: '5 min',
      helpContent: 'Configure your strategy parameters. Use the recommended defaults if you\'re unsure.',
      validation: () => {
        if (!workflowData.strategyConfigured) {
          return { valid: false, message: 'Strategy configuration is required' }
        }
        return { valid: true }
      },
    },
    {
      id: 'risk_settings',
      title: 'Risk Management',
      description: 'Define position sizing and risk limits',
      icon: <AlertTriangle className="h-5 w-5" />,
      status: 'pending',
      required: true,
      estimatedTime: '3 min',
      helpContent: 'Set your risk parameters including position size, stop loss, and maximum drawdown limits.',
    },
    {
      id: 'optimization',
      title: 'Parameter Optimization',
      description: 'Optional: Optimize strategy parameters',
      icon: <Zap className="h-5 w-5" />,
      status: 'pending',
      required: false,
      estimatedTime: '10-30 min',
      helpContent: 'Use optimization to find the best parameter values. This step is optional but recommended.',
    },
    {
      id: 'backtest',
      title: 'Run Backtest',
      description: 'Execute strategy on historical data',
      icon: <Play className="h-5 w-5" />,
      status: 'pending',
      required: true,
      estimatedTime: '1-5 min',
      helpContent: 'Run the backtest with your configured settings. Processing time depends on data size.',
    },
    {
      id: 'analysis',
      title: 'Analyze Results',
      description: 'Review performance metrics and statistics',
      icon: <BarChart3 className="h-5 w-5" />,
      status: 'pending',
      required: true,
      estimatedTime: '5 min',
      helpContent: 'Review the backtest results including returns, risk metrics, and trade analysis.',
    },
    {
      id: 'report',
      title: 'Generate Report',
      description: 'Create and export detailed report',
      icon: <FileText className="h-5 w-5" />,
      status: 'pending',
      required: false,
      estimatedTime: '2 min',
      helpContent: 'Generate a comprehensive report of your backtest results in various formats.',
    },
  ]
  
  const handleNext = () => {
    const step = steps[currentStep]
    
    // Validate current step if required
    if (step.validation) {
      const validation = step.validation()
      if (!validation.valid) {
        alert(validation.message || 'Please complete this step before proceeding')
        return
      }
    }
    
    // Mark step as completed
    setCompletedSteps(prev => new Set([...prev, step.id]))
    
    // Move to next step
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1)
    } else {
      // Workflow complete
      if (onComplete) {
        onComplete(workflowData)
      }
    }
  }
  
  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1)
    }
  }
  
  const handleSkip = () => {
    const step = steps[currentStep]
    if (!step.required) {
      setCurrentStep(currentStep + 1)
    }
  }
  
  const calculateProgress = () => {
    return (completedSteps.size / steps.filter(s => s.required).length) * 100
  }
  
  const estimateTotalTime = () => {
    return steps
      .filter(s => s.required)
      .reduce((total, step) => {
        const match = step.estimatedTime.match(/(\d+)/)
        return total + (match ? parseInt(match[1]) : 0)
      }, 0)
  }
  
  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex justify-between items-start">
            <div>
              <CardTitle className="text-2xl">{title}</CardTitle>
              <CardDescription className="mt-2">{description}</CardDescription>
            </div>
            <Badge variant="outline" className="flex items-center gap-1">
              <Rocket className="h-3 w-3" />
              Guided Mode
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Progress Bar */}
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span>Overall Progress</span>
                <span>{Math.round(calculateProgress())}%</span>
              </div>
              <Progress value={calculateProgress()} className="h-2" />
              <p className="text-xs text-gray-500 mt-1">
                Estimated total time: {estimateTotalTime()} minutes
              </p>
            </div>
            
            {/* Step Indicators */}
            <div className="flex items-center justify-between overflow-x-auto">
              {steps.map((step, index) => {
                const isCompleted = completedSteps.has(step.id)
                const isCurrent = index === currentStep
                const isPending = !isCompleted && !isCurrent
                
                return (
                  <div key={step.id} className="flex items-center">
                    <button
                      onClick={() => isCompleted && setCurrentStep(index)}
                      className={cn(
                        "flex flex-col items-center p-2 rounded-lg transition-colors min-w-[80px]",
                        isCurrent && "bg-blue-50",
                        isCompleted && "cursor-pointer hover:bg-gray-50"
                      )}
                      disabled={!isCompleted && !isCurrent}
                    >
                      <div className={cn(
                        "w-10 h-10 rounded-full flex items-center justify-center mb-1",
                        isCompleted && "bg-green-100 text-green-600",
                        isCurrent && "bg-blue-100 text-blue-600",
                        isPending && "bg-gray-100 text-gray-400"
                      )}>
                        {isCompleted ? <CheckCircle className="h-5 w-5" /> :
                         isCurrent ? step.icon :
                         <Circle className="h-5 w-5" />}
                      </div>
                      <span className={cn(
                        "text-xs text-center",
                        isCurrent && "font-semibold",
                        isPending && "text-gray-400"
                      )}>
                        {step.title}
                      </span>
                      {!step.required && (
                        <Badge variant="outline" className="text-xs mt-1">Optional</Badge>
                      )}
                    </button>
                    {index < steps.length - 1 && (
                      <ArrowRight className="h-4 w-4 mx-2 text-gray-300" />
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        </CardContent>
      </Card>
      
      {/* Current Step Content */}
      <Card>
        <CardHeader>
          <div className="flex justify-between items-start">
            <div className="flex items-center gap-3">
              <div className={cn(
                "w-12 h-12 rounded-full flex items-center justify-center",
                "bg-blue-100 text-blue-600"
              )}>
                {steps[currentStep].icon}
              </div>
              <div>
                <CardTitle>Step {currentStep + 1}: {steps[currentStep].title}</CardTitle>
                <CardDescription>{steps[currentStep].description}</CardDescription>
              </div>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowHelp(!showHelp)}
            >
              <Info className="h-4 w-4 mr-1" />
              Help
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {showHelp && steps[currentStep].helpContent && (
            <Alert className="mb-4">
              <Info className="h-4 w-4" />
              <AlertTitle>Help</AlertTitle>
              <AlertDescription>
                {steps[currentStep].helpContent}
              </AlertDescription>
            </Alert>
          )}
          
          {/* Step-specific content would go here */}
          <div className="min-h-[200px] flex items-center justify-center border-2 border-dashed rounded-lg">
            <p className="text-gray-500">
              {steps[currentStep].component || `[${steps[currentStep].title} interface would be displayed here]`}
            </p>
          </div>
          
          {/* Action Buttons */}
          <div className="flex justify-between mt-6">
            <Button
              variant="outline"
              onClick={handlePrevious}
              disabled={currentStep === 0}
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Previous
            </Button>
            
            <div className="flex gap-2">
              {!steps[currentStep].required && currentStep < steps.length - 1 && (
                <Button
                  variant="ghost"
                  onClick={handleSkip}
                >
                  Skip
                </Button>
              )}
              
              <Button onClick={handleNext}>
                {currentStep === steps.length - 1 ? 'Complete' : 'Next'}
                <ArrowRight className="h-4 w-4 ml-2" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
      
      {/* Quick Actions */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-500">
              Estimated time for this step: {steps[currentStep].estimatedTime}
            </div>
            <div className="flex gap-2">
              <Button variant="outline" size="sm">
                Save Progress
              </Button>
              <Button variant="ghost" size="sm">
                Exit Guided Mode
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}