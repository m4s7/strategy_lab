"use client";

import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  useWebSocketStatus,
  useWebSocketSubscription,
  useWebSocketDebug,
} from "@/lib/websocket/hooks";

export function WebSocketDemo() {
  const [testTopic, setTestTopic] = useState("test:demo");
  const { isConnected, connect } = useWebSocketStatus();
  const { data: testData } = useWebSocketSubscription(testTopic);
  const { messageHistory, connectionStats, clearHistory } = useWebSocketDebug();

  const sendTestMessage = async () => {
    try {
      const response = await fetch("/api/v1/websocket/broadcast", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          topic: testTopic,
          message: {
            test: true,
            timestamp: new Date().toISOString(),
            data: `Test message from frontend at ${new Date().toLocaleTimeString()}`,
          },
        }),
      });

      if (!response.ok) {
        console.error("Failed to send test message");
      }
    } catch (error) {
      console.error("Error sending test message:", error);
    }
  };

  return (
    <div className="space-y-6">
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">
          WebSocket Connection Demo
        </h3>

        <div className="space-y-4">
          <div className="flex items-center gap-4">
            <Badge variant={isConnected ? "success" : "destructive"}>
              {isConnected ? "Connected" : "Disconnected"}
            </Badge>

            {!isConnected && (
              <Button onClick={connect} size="sm">
                Connect WebSocket
              </Button>
            )}
          </div>

          {connectionStats && (
            <div className="text-sm text-muted-foreground">
              <p>Status: {connectionStats.status}</p>
              <p>
                Subscriptions:{" "}
                {connectionStats.subscriptions.join(", ") || "None"}
              </p>
            </div>
          )}
        </div>
      </Card>

      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Topic Testing</h3>

        <div className="space-y-4">
          <div className="flex gap-2">
            <Input
              placeholder="Enter topic name"
              value={testTopic}
              onChange={(e) => setTestTopic(e.target.value)}
              className="flex-1"
            />
            <Button onClick={sendTestMessage} disabled={!isConnected} size="sm">
              Send Test Message
            </Button>
          </div>

          {testData && (
            <div className="p-3 bg-muted rounded">
              <p className="text-sm font-medium mb-2">
                Latest data for {testTopic}:
              </p>
              <pre className="text-xs overflow-auto">
                {JSON.stringify(testData, null, 2)}
              </pre>
            </div>
          )}
        </div>
      </Card>

      <Card className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">Message History</h3>
          <Button variant="outline" size="sm" onClick={clearHistory}>
            Clear History
          </Button>
        </div>

        <ScrollArea className="h-64 w-full border rounded p-2">
          {messageHistory.length === 0 ? (
            <p className="text-sm text-muted-foreground">No messages yet</p>
          ) : (
            <div className="space-y-2">
              {messageHistory.slice(-20).map((msg, index) => (
                <div
                  key={index}
                  className="text-xs font-mono p-2 bg-muted rounded"
                >
                  <div className="flex items-center gap-2 mb-1">
                    <Badge variant="outline" className="text-xs">
                      {msg.type}
                    </Badge>
                    {msg.topic && (
                      <Badge variant="secondary" className="text-xs">
                        {msg.topic}
                      </Badge>
                    )}
                    <span className="text-muted-foreground">
                      {new Date(msg.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                  {msg.data && (
                    <pre className="text-xs overflow-auto mt-1">
                      {JSON.stringify(msg.data, null, 2)}
                    </pre>
                  )}
                </div>
              ))}
            </div>
          )}
        </ScrollArea>
      </Card>
    </div>
  );
}
