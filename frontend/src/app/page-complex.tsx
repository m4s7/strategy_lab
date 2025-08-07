import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { TrendingUp, Activity, BarChart3, Zap } from "lucide-react";

export default function Home() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Dashboard</h2>
        <p className="text-muted-foreground">
          Welcome to Strategy Lab - Your trading backtesting platform
        </p>
      </div>
      
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <Card className="p-6">
          <div className="flex items-center space-x-2">
            <TrendingUp className="h-5 w-5 text-success" />
            <h3 className="text-sm font-medium text-muted-foreground">
              Total Return
            </h3>
          </div>
          <div className="mt-2">
            <p className="text-2xl font-bold">$12,456</p>
            <p className="text-sm text-success">+12.34%</p>
          </div>
        </Card>
        
        <Card className="p-6">
          <div className="flex items-center space-x-2">
            <Activity className="h-5 w-5 text-primary" />
            <h3 className="text-sm font-medium text-muted-foreground">
              Active Strategies
            </h3>
          </div>
          <div className="mt-2">
            <p className="text-2xl font-bold">3</p>
            <p className="text-sm text-muted-foreground">Running</p>
          </div>
        </Card>
        
        <Card className="p-6">
          <div className="flex items-center space-x-2">
            <BarChart3 className="h-5 w-5 text-chart-1" />
            <h3 className="text-sm font-medium text-muted-foreground">
              Win Rate
            </h3>
          </div>
          <div className="mt-2">
            <p className="text-2xl font-bold">67.8%</p>
            <p className="text-sm text-success">+2.3%</p>
          </div>
        </Card>
        
        <Card className="p-6">
          <div className="flex items-center space-x-2">
            <Zap className="h-5 w-5 text-warning" />
            <h3 className="text-sm font-medium text-muted-foreground">
              Avg Trade Time
            </h3>
          </div>
          <div className="mt-2">
            <p className="text-2xl font-bold">2.4m</p>
            <p className="text-sm text-muted-foreground">Minutes</p>
          </div>
        </Card>
      </div>
      
      <div className="grid gap-6 md:grid-cols-2">
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">Recent Backtests</h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm">Order Book Scalper</span>
              <span className="text-sm text-success">+8.4%</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm">Bid-Ask Bounce</span>
              <span className="text-sm text-success">+12.1%</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm">Volume Imbalance</span>
              <span className="text-sm text-destructive">-2.3%</span>
            </div>
          </div>
        </Card>
        
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">Quick Actions</h3>
          <div className="space-y-3">
            <Button className="w-full justify-start">
              Run New Backtest
            </Button>
            <Button variant="outline" className="w-full justify-start">
              Configure Strategy
            </Button>
            <Button variant="outline" className="w-full justify-start">
              View Market Data
            </Button>
          </div>
        </Card>
      </div>
    </div>
  );
}
