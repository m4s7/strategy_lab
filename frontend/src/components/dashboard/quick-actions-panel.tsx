'use client';

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { 
  Play, 
  BarChart3, 
  Settings, 
  Database,
  Activity,
  FileText,
  Plus
} from "lucide-react";
import Link from "next/link";

export function QuickActionsPanel() {
  const quickActions = [
    {
      title: "New Backtest",
      description: "Start a new backtest with strategy configuration",
      icon: Plus,
      href: "/backtests/new",
      variant: "default" as const,
      className: "bg-primary text-primary-foreground hover:bg-primary/90"
    },
    {
      title: "View Results",
      description: "Browse and analyze backtest results",
      icon: BarChart3,
      href: "/results",
      variant: "outline" as const
    },
    {
      title: "Strategy Config",
      description: "Configure trading strategies",
      icon: Settings,
      href: "/strategies",
      variant: "outline" as const
    },
    {
      title: "Data Management",
      description: "Manage market data sources",
      icon: Database,
      href: "/data",
      variant: "outline" as const
    },
    {
      title: "System Health",
      description: "Monitor system performance",
      icon: Activity,
      href: "/system",
      variant: "outline" as const
    },
    {
      title: "Documentation",
      description: "View API docs and guides",
      icon: FileText,
      href: "/docs",
      variant: "outline" as const
    }
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Quick Actions</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
          {quickActions.map((action) => {
            const Icon = action.icon;
            return (
              <Link key={action.title} href={action.href}>
                <Button
                  variant={action.variant}
                  className={`w-full h-auto p-4 flex flex-col items-start space-y-2 ${action.className || ''}`}
                >
                  <div className="flex items-center space-x-2 w-full">
                    <Icon className="h-5 w-5" />
                    <span className="font-medium text-left">
                      {action.title}
                    </span>
                  </div>
                  <p className="text-xs text-left opacity-70 leading-relaxed">
                    {action.description}
                  </p>
                </Button>
              </Link>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}