'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import { ChevronDown, ChevronRight, Info, Eye, EyeOff, Layers, HelpCircle } from 'lucide-react'
import { cn } from '@/lib/utils'

interface Section {
  id: string
  title: string
  complexity: 'basic' | 'intermediate' | 'advanced'
  description: string
  content: React.ReactNode
  helpText?: string
}

interface ProgressiveDisclosureProps {
  sections: Section[]
  defaultExpandedLevel?: 'basic' | 'intermediate' | 'advanced' | 'all'
}

export function ProgressiveDisclosure({ 
  sections, 
  defaultExpandedLevel = 'basic' 
}: ProgressiveDisclosureProps) {
  const [expandedSections, setExpandedSections] = useState<Set<string>>(() => {
    const initial = new Set<string>()
    sections.forEach(section => {
      if (defaultExpandedLevel === 'all' || 
          (defaultExpandedLevel === 'basic' && section.complexity === 'basic') ||
          (defaultExpandedLevel === 'intermediate' && ['basic', 'intermediate'].includes(section.complexity))) {
        initial.add(section.id)
      }
    })
    return initial
  })
  
  const [viewMode, setViewMode] = useState<'simple' | 'detailed'>('simple')
  
  const toggleSection = (sectionId: string) => {
    setExpandedSections(prev => {
      const next = new Set(prev)
      if (next.has(sectionId)) {
        next.delete(sectionId)
      } else {
        next.add(sectionId)
      }
      return next
    })
  }
  
  const expandByComplexity = (level: 'basic' | 'intermediate' | 'advanced' | 'all') => {
    const newExpanded = new Set<string>()
    sections.forEach(section => {
      if (level === 'all' || 
          (level === 'basic' && section.complexity === 'basic') ||
          (level === 'intermediate' && ['basic', 'intermediate'].includes(section.complexity)) ||
          (level === 'advanced')) {
        newExpanded.add(section.id)
      }
    })
    setExpandedSections(newExpanded)
  }
  
  const getComplexityColor = (complexity: string) => {
    switch (complexity) {
      case 'basic': return 'bg-green-100 text-green-800'
      case 'intermediate': return 'bg-yellow-100 text-yellow-800'
      case 'advanced': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }
  
  return (
    <TooltipProvider>
      <div className="space-y-4">
        {/* Controls */}
        <Card>
          <CardContent className="pt-6">
            <div className="flex justify-between items-center">
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => expandByComplexity('basic')}
                  className="flex items-center gap-1"
                >
                  <Layers className="h-3 w-3" />
                  Basic
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => expandByComplexity('intermediate')}
                  className="flex items-center gap-1"
                >
                  <Layers className="h-3 w-3" />
                  Intermediate
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => expandByComplexity('advanced')}
                  className="flex items-center gap-1"
                >
                  <Layers className="h-3 w-3" />
                  Advanced
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => expandByComplexity('all')}
                >
                  Show All
                </Button>
              </div>
              
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-500">View Mode:</span>
                <Button
                  variant={viewMode === 'simple' ? 'default' : 'ghost'}
                  size="sm"
                  onClick={() => setViewMode('simple')}
                >
                  <Eye className="h-3 w-3 mr-1" />
                  Simple
                </Button>
                <Button
                  variant={viewMode === 'detailed' ? 'default' : 'ghost'}
                  size="sm"
                  onClick={() => setViewMode('detailed')}
                >
                  <EyeOff className="h-3 w-3 mr-1" />
                  Detailed
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
        
        {/* Sections */}
        {sections.map((section) => {
          const isExpanded = expandedSections.has(section.id)
          
          return (
            <Card key={section.id} className="overflow-hidden">
              <CardHeader 
                className="cursor-pointer hover:bg-gray-50 transition-colors"
                onClick={() => toggleSection(section.id)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    {isExpanded ? 
                      <ChevronDown className="h-5 w-5 text-gray-500" /> : 
                      <ChevronRight className="h-5 w-5 text-gray-500" />
                    }
                    <div>
                      <div className="flex items-center gap-2">
                        <CardTitle className="text-lg">{section.title}</CardTitle>
                        <Badge 
                          variant="outline" 
                          className={cn("text-xs", getComplexityColor(section.complexity))}
                        >
                          {section.complexity}
                        </Badge>
                        {section.helpText && (
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <HelpCircle className="h-4 w-4 text-gray-400 cursor-help" />
                            </TooltipTrigger>
                            <TooltipContent className="max-w-xs">
                              <p>{section.helpText}</p>
                            </TooltipContent>
                          </Tooltip>
                        )}
                      </div>
                      {(viewMode === 'detailed' || isExpanded) && (
                        <CardDescription className="mt-1">
                          {section.description}
                        </CardDescription>
                      )}
                    </div>
                  </div>
                </div>
              </CardHeader>
              
              {isExpanded && (
                <CardContent className="pt-0">
                  <div className="border-t pt-4">
                    {section.content}
                  </div>
                </CardContent>
              )}
            </Card>
          )
        })}
        
        {/* Cognitive Load Indicator */}
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div className="text-sm text-gray-500">
                Cognitive Load:
              </div>
              <div className="flex items-center gap-2">
                <div className="w-32 h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div 
                    className={cn(
                      "h-full transition-all duration-300",
                      expandedSections.size <= 2 ? "bg-green-500 w-1/3" :
                      expandedSections.size <= 4 ? "bg-yellow-500 w-2/3" :
                      "bg-red-500 w-full"
                    )}
                  />
                </div>
                <span className="text-sm font-medium">
                  {expandedSections.size <= 2 ? "Low" :
                   expandedSections.size <= 4 ? "Medium" : "High"}
                </span>
              </div>
            </div>
            <p className="text-xs text-gray-400 mt-2">
              {expandedSections.size} of {sections.length} sections expanded
            </p>
          </CardContent>
        </Card>
      </div>
    </TooltipProvider>
  )
}