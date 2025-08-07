"use client";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Activity, Settings, Menu } from "lucide-react";
import { ConnectionStatus } from "@/components/websocket/connection-status";

interface HeaderProps {
  onMenuToggle?: () => void;
}

export function Header({ onMenuToggle }: HeaderProps) {
  return (
    <Card className="border-b rounded-none bg-card/50 backdrop-blur-sm">
      <div className="flex h-16 items-center justify-between px-6">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={onMenuToggle}
            className="md:hidden"
          >
            <Menu className="h-5 w-5" />
          </Button>
          <div className="flex items-center gap-2">
            <Activity className="h-6 w-6 text-primary" />
            <h1 className="text-xl font-bold">Strategy Lab</h1>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <div className="hidden md:flex items-center gap-4 text-sm text-muted-foreground">
            <span>Market: Closed</span>
            <span className="text-xs px-2 py-1 bg-muted rounded">MNQ</span>
          </div>
          <ConnectionStatus />
          <Button variant="ghost" size="icon">
            <Settings className="h-5 w-5" />
          </Button>
        </div>
      </div>
    </Card>
  );
}