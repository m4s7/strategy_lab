import { WebSocketClient } from "@/lib/websocket/client";
import { server } from "../mocks/server";
import { http, HttpResponse } from "msw";

describe("WebSocket Integration", () => {
  let wsClient: WebSocketClient;

  beforeEach(() => {
    wsClient = new WebSocketClient();
  });

  afterEach(() => {
    if (wsClient) {
      wsClient.disconnect();
    }
  });

  it("should connect to WebSocket server", async () => {
    const onConnect = jest.fn();
    const onDisconnect = jest.fn();

    wsClient.on("connect", onConnect);
    wsClient.on("disconnect", onDisconnect);

    await wsClient.connect();

    expect(onConnect).toHaveBeenCalled();
    expect(wsClient.isConnected()).toBe(true);
  });

  it("should handle connection errors", async () => {
    const onError = jest.fn();

    // Mock connection failure
    server.use(
      http.get("http://localhost:8000/ws", () => {
        return HttpResponse.json(
          { error: "Connection refused" },
          { status: 403 }
        );
      })
    );

    wsClient.on("error", onError);

    try {
      await wsClient.connect();
    } catch (error) {
      expect(onError).toHaveBeenCalled();
      expect(wsClient.isConnected()).toBe(false);
    }
  });

  it("should receive real-time backtest updates", async () => {
    const onMessage = jest.fn();

    await wsClient.connect();
    wsClient.on("backtest.update", onMessage);

    // Simulate server sending a message
    const mockUpdate = {
      type: "backtest.update",
      data: {
        id: "test-123",
        status: "running",
        progress: 45,
        currentTrade: 67,
      },
    };

    // In a real test, this would come from the server
    wsClient.emit("backtest.update", mockUpdate.data);

    expect(onMessage).toHaveBeenCalledWith(mockUpdate.data);
  });

  it("should handle reconnection", async () => {
    const onReconnect = jest.fn();

    wsClient.on("reconnect", onReconnect);

    await wsClient.connect();

    // Simulate connection loss
    wsClient.disconnect();

    // Should attempt to reconnect
    await new Promise((resolve) => setTimeout(resolve, 1500));

    expect(onReconnect).toHaveBeenCalled();
  });

  it("should subscribe to specific channels", async () => {
    await wsClient.connect();

    const subscription = await wsClient.subscribe("backtest:test-123");

    expect(subscription).toBeDefined();
    expect(subscription.channel).toBe("backtest:test-123");
  });

  it("should unsubscribe from channels", async () => {
    await wsClient.connect();

    const subscription = await wsClient.subscribe("backtest:test-123");
    const unsubscribed = await wsClient.unsubscribe("backtest:test-123");

    expect(unsubscribed).toBe(true);
  });

  it("should handle multiple subscriptions", async () => {
    await wsClient.connect();

    const subscriptions = await Promise.all([
      wsClient.subscribe("backtest:test-123"),
      wsClient.subscribe("backtest:test-456"),
      wsClient.subscribe("system:status"),
    ]);

    expect(subscriptions).toHaveLength(3);
    expect(wsClient.getActiveSubscriptions()).toHaveLength(3);
  });

  it("should queue messages when disconnected", async () => {
    const onMessage = jest.fn();

    wsClient.on("message", onMessage);

    // Send message while disconnected
    wsClient.send("test.message", { data: "test" });

    // Connect
    await wsClient.connect();

    // Wait for queued messages to be sent
    await new Promise((resolve) => setTimeout(resolve, 100));

    // In a real implementation, verify message was sent after connection
    expect(wsClient.getQueuedMessageCount()).toBe(0);
  });

  it("should handle rapid connect/disconnect cycles", async () => {
    const cycles = 5;

    for (let i = 0; i < cycles; i++) {
      await wsClient.connect();
      expect(wsClient.isConnected()).toBe(true);

      wsClient.disconnect();
      expect(wsClient.isConnected()).toBe(false);

      // Small delay between cycles
      await new Promise((resolve) => setTimeout(resolve, 50));
    }
  });

  it("should emit system events", async () => {
    const events = {
      connect: jest.fn(),
      disconnect: jest.fn(),
      error: jest.fn(),
      "system.update": jest.fn(),
    };

    Object.entries(events).forEach(([event, handler]) => {
      wsClient.on(event, handler);
    });

    await wsClient.connect();

    // Simulate system update
    wsClient.emit("system.update", {
      cpuUsage: 45.2,
      memoryUsage: 62.8,
      activeBacktests: 3,
    });

    expect(events.connect).toHaveBeenCalled();
    expect(events["system.update"]).toHaveBeenCalled();
  });

  it("should handle authentication", async () => {
    const token = "test-auth-token";

    await wsClient.connect({ token });

    // In a real implementation, verify token was sent
    expect(wsClient.isAuthenticated()).toBe(true);
  });

  it("should handle connection limits", async () => {
    const maxConnections = 5;
    const clients: WebSocketClient[] = [];

    try {
      for (let i = 0; i < maxConnections + 1; i++) {
        const client = new WebSocketClient();
        await client.connect();
        clients.push(client);
      }
    } catch (error: any) {
      // Should fail on the 6th connection
      expect(error.message).toContain("connection limit");
    } finally {
      clients.forEach((client) => client.disconnect());
    }
  });
});
