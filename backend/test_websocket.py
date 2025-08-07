#!/usr/bin/env python3
"""
WebSocket test script to verify functionality.
"""

import asyncio
import json
import websockets
import sys
from datetime import datetime


async def test_websocket_connection():
    """Test WebSocket connection and basic functionality."""
    uri = "ws://localhost:8000/ws"

    print("WebSocket Test Script")
    print("=" * 30)
    print(f"Connecting to {uri}")

    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to WebSocket server")

            # Test 1: Subscribe to a topic
            print("\n1. Testing topic subscription...")
            subscribe_message = {
                "type": "subscribe",
                "topic": "test:demo",
                "timestamp": datetime.utcnow().isoformat(),
            }
            await websocket.send(json.dumps(subscribe_message))
            print("   Sent subscription message")

            # Wait for subscription confirmation
            response = await websocket.recv()
            response_data = json.loads(response)
            print(
                f"   Received: {response_data['type']} - {response_data.get('data', {}).get('action', 'N/A')}"
            )

            # Test 2: Send ping and wait for pong
            print("\n2. Testing heartbeat...")
            ping_message = {
                "type": "ping",
                "timestamp": datetime.utcnow().isoformat(),
                "id": "test-ping-1",
            }
            await websocket.send(json.dumps(ping_message))
            print("   Sent ping message")

            # Wait for pong
            pong_response = await websocket.recv()
            pong_data = json.loads(pong_response)
            print(
                f"   Received pong: {pong_data['type']} (ID: {pong_data.get('id', 'N/A')})"
            )

            # Test 3: Subscribe to multiple topics
            print("\n3. Testing multiple subscriptions...")
            topics = ["system:status", "backtest:all", "test:multi"]
            for topic in topics:
                sub_msg = {
                    "type": "subscribe",
                    "topic": topic,
                    "timestamp": datetime.utcnow().isoformat(),
                }
                await websocket.send(json.dumps(sub_msg))

                # Wait for confirmation
                confirmation = await websocket.recv()
                conf_data = json.loads(confirmation)
                print(f"   Subscribed to {topic}: {conf_data['type']}")

            # Test 4: Test receiving broadcast messages
            print("\n4. Testing message broadcasting...")
            print("   Use the HTTP API to broadcast to 'test:demo':")
            print("   curl -X POST http://localhost:8000/api/v1/websocket/broadcast \\")
            print("        -H 'Content-Type: application/json' \\")
            print(
                '        -d \'{"topic": "test:demo", "message": {"test": true, "value": 42}}\''
            )

            # Wait for any messages for a few seconds
            print("   Waiting for messages (5 seconds)...")
            try:
                for i in range(5):
                    message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    msg_data = json.loads(message)
                    print(
                        f"   📨 Received: {msg_data['type']}:{msg_data.get('topic', 'N/A')} - {msg_data.get('data', {})}"
                    )
            except asyncio.TimeoutError:
                print(
                    "   No messages received (this is normal if no broadcasts were sent)"
                )

            # Test 5: Unsubscribe
            print("\n5. Testing unsubscription...")
            unsub_message = {
                "type": "unsubscribe",
                "topic": "test:demo",
                "timestamp": datetime.utcnow().isoformat(),
            }
            await websocket.send(json.dumps(unsub_message))
            print("   Sent unsubscription message for 'test:demo'")

            print("\n✅ All WebSocket tests completed successfully!")
            print("\nConnection will close in 2 seconds...")
            await asyncio.sleep(2)

    except websockets.exceptions.ConnectionRefused:
        print("❌ Could not connect to WebSocket server")
        print("   Make sure the FastAPI server is running on http://localhost:8000")
        sys.exit(1)

    except Exception as e:
        print(f"❌ WebSocket test failed: {e}")
        sys.exit(1)


async def test_websocket_stats():
    """Test WebSocket HTTP endpoints."""
    import aiohttp

    print("\nTesting WebSocket HTTP endpoints...")

    async with aiohttp.ClientSession() as session:
        try:
            # Test stats endpoint
            async with session.get(
                "http://localhost:8000/api/v1/websocket/stats"
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"📊 WebSocket Stats: {data['data']}")
                else:
                    print(f"❌ Stats endpoint failed: {response.status}")

            # Test topics endpoint
            async with session.get(
                "http://localhost:8000/api/v1/websocket/topics"
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"📋 Active Topics: {data['data']}")
                else:
                    print(f"❌ Topics endpoint failed: {response.status}")

        except aiohttp.ClientError as e:
            print(f"❌ HTTP test failed: {e}")


if __name__ == "__main__":
    print("Starting WebSocket tests...")
    print("Make sure the FastAPI server is running: python run_dev.py")
    print()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        loop.run_until_complete(test_websocket_connection())
        loop.run_until_complete(test_websocket_stats())
    finally:
        loop.close()
