'use client';

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { FileText, History, Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Strategy } from "@/hooks/useStrategies";

interface StrategySelectorProps {
  strategies: Strategy[];
  selectedStrategy: Strategy | null;
  onSelectStrategy: (strategy: Strategy) => void;
  recentStrategies?: string[];
}

export function StrategySelector({
  strategies,
  selectedStrategy,
  onSelectStrategy,
  recentStrategies = []
}: StrategySelectorProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  // Get unique categories
  const categories = ['all', ...new Set(strategies.map(s => s.category))];

  // Filter strategies based on search and category
  const filteredStrategies = strategies.filter(strategy => {
    const matchesSearch = strategy.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          strategy.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = selectedCategory === 'all' || strategy.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  // Get recent strategy objects
  const recentStrategyObjects = recentStrategies
    .map(id => strategies.find(s => s.id === id))
    .filter(Boolean) as Strategy[];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Select Strategy</CardTitle>
        <CardDescription>
          Choose a trading strategy to configure and backtest
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Search and Filter */}
        <div className="flex space-x-2">
          <div className="relative flex-1">
            <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search strategies..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-8"
            />
          </div>
          <Select value={selectedCategory} onValueChange={setSelectedCategory}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Category" />
            </SelectTrigger>
            <SelectContent>
              {categories.map(category => (
                <SelectItem key={category} value={category}>
                  {category === 'all' ? 'All Categories' : category}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Recent Strategies */}
        {recentStrategyObjects.length > 0 && searchTerm === '' && selectedCategory === 'all' && (
          <div className="space-y-2">
            <div className="flex items-center space-x-2 text-sm text-muted-foreground">
              <History className="h-4 w-4" />
              <span>Recently Used</span>
            </div>
            <div className="grid gap-2">
              {recentStrategyObjects.slice(0, 3).map(strategy => (
                <Button
                  key={strategy.id}
                  variant={selectedStrategy?.id === strategy.id ? "secondary" : "outline"}
                  className="justify-start h-auto p-3"
                  onClick={() => onSelectStrategy(strategy)}
                >
                  <div className="text-left">
                    <div className="font-medium">{strategy.name}</div>
                    <div className="text-xs text-muted-foreground">
                      {strategy.category} • v{strategy.version}
                    </div>
                  </div>
                </Button>
              ))}
            </div>
          </div>
        )}

        {/* Strategy List */}
        <div className="space-y-2">
          <div className="text-sm text-muted-foreground">
            Available Strategies ({filteredStrategies.length})
          </div>
          <ScrollArea className="h-[300px] pr-4">
            <div className="grid gap-2">
              {filteredStrategies.map(strategy => (
                <div
                  key={strategy.id}
                  className={cn(
                    "p-3 rounded-lg border cursor-pointer transition-colors",
                    selectedStrategy?.id === strategy.id
                      ? "border-primary bg-primary/5"
                      : "border-border hover:bg-muted/50"
                  )}
                  onClick={() => onSelectStrategy(strategy)}
                >
                  <div className="flex items-start justify-between">
                    <div className="space-y-1">
                      <div className="font-medium">{strategy.name}</div>
                      <div className="text-sm text-muted-foreground">
                        {strategy.description}
                      </div>
                      <div className="flex items-center space-x-2 text-xs">
                        <Badge variant="outline">{strategy.category}</Badge>
                        <span className="text-muted-foreground">
                          v{strategy.version} • {strategy.author}
                        </span>
                      </div>
                    </div>
                    {strategy.documentation && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          // Open documentation modal or panel
                          console.log('Show docs for', strategy.id);
                        }}
                      >
                        <FileText className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </ScrollArea>
        </div>

        {/* Selected Strategy Details */}
        {selectedStrategy && (
          <div className="pt-4 border-t">
            <div className="space-y-2">
              <h4 className="font-medium">Selected Strategy</h4>
              <div className="p-3 bg-muted rounded-lg">
                <div className="font-medium">{selectedStrategy.name}</div>
                <div className="text-sm text-muted-foreground mt-1">
                  {selectedStrategy.parameters.length} configurable parameters
                </div>
                {selectedStrategy.documentation && (
                  <div className="text-sm mt-2">
                    {selectedStrategy.documentation}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function cn(...classes: (string | boolean | undefined)[]) {
  return classes.filter(Boolean).join(' ');
}