"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Wifi, WifiOff, Loader2, AlertTriangle, RefreshCw } from "lucide-react";
import { useWebSocketStatus } from "@/lib/websocket/hooks";

export function ConnectionStatus() {
  const {
    status,
    isConnected,
    isConnecting,
    isReconnecting,
    hasError,
    connect,
    disconnect,
  } = useWebSocketStatus();

  const getStatusIcon = () => {
    if (isConnecting || isReconnecting) {
      return <Loader2 className="h-4 w-4 animate-spin" />;
    }
    if (hasError) {
      return <AlertTriangle className="h-4 w-4" />;
    }
    if (isConnected) {
      return <Wifi className="h-4 w-4" />;
    }
    return <WifiOff className="h-4 w-4" />;
  };

  const getStatusVariant = () => {
    if (isConnected) return "success" as const;
    if (hasError) return "destructive" as const;
    if (isConnecting || isReconnecting) return "secondary" as const;
    return "outline" as const;
  };

  const getStatusText = () => {
    switch (status) {
      case "connected":
        return "Connected";
      case "connecting":
        return "Connecting...";
      case "reconnecting":
        return "Reconnecting...";
      case "disconnected":
        return "Disconnected";
      case "error":
        return "Connection Error";
      default:
        return "Unknown";
    }
  };

  return (
    <div className="flex items-center gap-2">
      <Badge variant={getStatusVariant()} className="gap-1">
        {getStatusIcon()}
        {getStatusText()}
      </Badge>

      {!isConnected && !isConnecting && !isReconnecting && (
        <Button
          variant="outline"
          size="sm"
          onClick={connect}
          className="h-6 px-2"
        >
          <RefreshCw className="h-3 w-3 mr-1" />
          Reconnect
        </Button>
      )}

      {isConnected && (
        <Button
          variant="outline"
          size="sm"
          onClick={disconnect}
          className="h-6 px-2"
        >
          Disconnect
        </Button>
      )}
    </div>
  );
}
