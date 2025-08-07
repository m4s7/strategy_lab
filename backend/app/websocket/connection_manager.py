import json
import uuid
import logging
from datetime import datetime
from typing import Dict, Set, List, Optional, Any
from collections import defaultdict
from fastapi import WebSocket, WebSocketDisconnect
import asyncio

from ..models.base import BaseModel
from pydantic import BaseModel as PydanticBaseModel

logger = logging.getLogger(__name__)


class WebSocketMessage(PydanticBaseModel):
    """WebSocket message structure."""

    type: str  # 'subscribe', 'unsubscribe', 'data', 'error', 'ping', 'pong'
    topic: Optional[str] = None
    data: Optional[Any] = None
    timestamp: str
    id: Optional[str] = None


class ConnectionManager:
    """Manages WebSocket connections and pub/sub system."""

    def __init__(self):
        # Active connections: client_id -> WebSocket
        self.active_connections: Dict[str, WebSocket] = {}

        # Subscriptions: topic -> Set[client_id]
        self.subscriptions: Dict[str, Set[str]] = defaultdict(set)

        # Client subscriptions: client_id -> Set[topic]
        self.client_subscriptions: Dict[str, Set[str]] = defaultdict(set)

        # Connection metadata
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}

        # Message queue for offline clients (optional)
        self.message_queue: Dict[str, List[WebSocketMessage]] = defaultdict(list)

        logger.info("WebSocket ConnectionManager initialized")

    async def connect(
        self, websocket: WebSocket, client_id: Optional[str] = None
    ) -> str:
        """
        Accept a new WebSocket connection.

        Args:
            websocket: WebSocket connection
            client_id: Optional client ID, generates UUID if not provided

        Returns:
            str: Client ID
        """
        if not client_id:
            client_id = str(uuid.uuid4())

        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.connection_metadata[client_id] = {
            "connected_at": datetime.utcnow().isoformat(),
            "last_ping": datetime.utcnow().isoformat(),
            "message_count": 0,
        }

        logger.info(f"WebSocket client {client_id} connected")

        # Send welcome message
        welcome_message = WebSocketMessage(
            type="data",
            topic="system:connection",
            data={
                "status": "connected",
                "client_id": client_id,
                "server_time": datetime.utcnow().isoformat(),
            },
            timestamp=datetime.utcnow().isoformat(),
            id=str(uuid.uuid4()),
        )
        await self.send_personal_message(client_id, welcome_message)

        return client_id

    async def disconnect(self, client_id: str):
        """
        Disconnect a client and clean up resources.

        Args:
            client_id: Client ID to disconnect
        """
        if client_id in self.active_connections:
            # Remove from active connections
            del self.active_connections[client_id]

            # Clean up subscriptions
            topics_to_cleanup = list(self.client_subscriptions[client_id])
            for topic in topics_to_cleanup:
                await self.unsubscribe(client_id, topic)

            # Clean up metadata
            if client_id in self.connection_metadata:
                del self.connection_metadata[client_id]

            # Clean up message queue
            if client_id in self.message_queue:
                del self.message_queue[client_id]

            logger.info(f"WebSocket client {client_id} disconnected and cleaned up")

    async def subscribe(self, client_id: str, topic: str) -> bool:
        """
        Subscribe a client to a topic.

        Args:
            client_id: Client ID
            topic: Topic to subscribe to

        Returns:
            bool: True if subscription successful
        """
        if client_id not in self.active_connections:
            logger.warning(f"Cannot subscribe inactive client {client_id} to {topic}")
            return False

        self.subscriptions[topic].add(client_id)
        self.client_subscriptions[client_id].add(topic)

        logger.info(f"Client {client_id} subscribed to topic '{topic}'")

        # Send subscription confirmation
        confirm_message = WebSocketMessage(
            type="data",
            topic="system:subscription",
            data={"action": "subscribed", "topic": topic, "client_id": client_id},
            timestamp=datetime.utcnow().isoformat(),
        )
        await self.send_personal_message(client_id, confirm_message)

        return True

    async def unsubscribe(self, client_id: str, topic: str) -> bool:
        """
        Unsubscribe a client from a topic.

        Args:
            client_id: Client ID
            topic: Topic to unsubscribe from

        Returns:
            bool: True if unsubscription successful
        """
        if topic in self.subscriptions:
            self.subscriptions[topic].discard(client_id)

            # Clean up empty topic subscriptions
            if not self.subscriptions[topic]:
                del self.subscriptions[topic]
                logger.info(f"Cleaned up empty topic '{topic}'")

        if client_id in self.client_subscriptions:
            self.client_subscriptions[client_id].discard(topic)

        logger.info(f"Client {client_id} unsubscribed from topic '{topic}'")
        return True

    async def send_personal_message(self, client_id: str, message: WebSocketMessage):
        """
        Send a message to a specific client.

        Args:
            client_id: Target client ID
            message: Message to send
        """
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            try:
                await websocket.send_text(message.model_dump_json())

                # Update metadata
                if client_id in self.connection_metadata:
                    self.connection_metadata[client_id]["message_count"] += 1

                logger.debug(
                    f"Sent message to client {client_id}: {message.type}:{message.topic}"
                )

            except Exception as e:
                logger.error(f"Error sending message to client {client_id}: {e}")
                await self.disconnect(client_id)

    async def broadcast_to_topic(self, topic: str, message: WebSocketMessage):
        """
        Broadcast a message to all subscribers of a topic.

        Args:
            topic: Target topic
            message: Message to broadcast
        """
        if topic not in self.subscriptions:
            logger.debug(f"No subscribers for topic '{topic}'")
            return

        subscribers = list(self.subscriptions[topic])
        logger.info(
            f"Broadcasting to {len(subscribers)} subscribers of topic '{topic}'"
        )

        # Send to all subscribers concurrently
        tasks = []
        for client_id in subscribers:
            if client_id in self.active_connections:
                tasks.append(self.send_personal_message(client_id, message))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def handle_message(self, client_id: str, raw_message: str):
        """
        Handle incoming message from client.

        Args:
            client_id: Source client ID
            raw_message: Raw message string
        """
        try:
            # Parse message
            message_data = json.loads(raw_message)
            message = WebSocketMessage(**message_data)

            logger.debug(
                f"Received message from {client_id}: {message.type}:{message.topic}"
            )

            # Handle different message types
            if message.type == "subscribe" and message.topic:
                await self.subscribe(client_id, message.topic)

            elif message.type == "unsubscribe" and message.topic:
                await self.unsubscribe(client_id, message.topic)

            elif message.type == "ping":
                # Respond with pong
                pong_message = WebSocketMessage(
                    type="pong",
                    data={"server_time": datetime.utcnow().isoformat()},
                    timestamp=datetime.utcnow().isoformat(),
                    id=message.id,
                )
                await self.send_personal_message(client_id, pong_message)

                # Update last ping time
                if client_id in self.connection_metadata:
                    self.connection_metadata[client_id][
                        "last_ping"
                    ] = datetime.utcnow().isoformat()

            else:
                logger.warning(f"Unknown message type from {client_id}: {message.type}")

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON from client {client_id}: {e}")
            error_message = WebSocketMessage(
                type="error",
                data={"message": "Invalid JSON format"},
                timestamp=datetime.utcnow().isoformat(),
            )
            await self.send_personal_message(client_id, error_message)

        except Exception as e:
            logger.error(f"Error handling message from client {client_id}: {e}")
            error_message = WebSocketMessage(
                type="error",
                data={"message": "Internal server error"},
                timestamp=datetime.utcnow().isoformat(),
            )
            await self.send_personal_message(client_id, error_message)

    async def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics."""
        return {
            "active_connections": len(self.active_connections),
            "total_subscriptions": sum(
                len(subscribers) for subscribers in self.subscriptions.values()
            ),
            "unique_topics": len(self.subscriptions),
            "topics": list(self.subscriptions.keys()),
            "connections": {
                client_id: {
                    "subscribed_topics": list(
                        self.client_subscriptions.get(client_id, set())
                    ),
                    "metadata": self.connection_metadata.get(client_id, {}),
                }
                for client_id in self.active_connections.keys()
            },
        }


# Global connection manager instance
connection_manager = ConnectionManager()
