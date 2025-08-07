import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from typing import Optional, Dict, Any

from .connection_manager import connection_manager
from ..core.dependencies import get_current_request_id

logger = logging.getLogger(__name__)

# WebSocket router
websocket_router = APIRouter()


@websocket_router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: Optional[str] = None
):
    """
    Main WebSocket endpoint for real-time communication.
    
    Args:
        websocket: WebSocket connection
        client_id: Optional client identifier
    """
    actual_client_id = await connection_manager.connect(websocket, client_id)
    
    try:
        while True:
            # Wait for message from client
            raw_message = await websocket.receive_text()
            
            # Handle the message
            await connection_manager.handle_message(actual_client_id, raw_message)
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket client {actual_client_id} disconnected")
        await connection_manager.disconnect(actual_client_id)
        
    except Exception as e:
        logger.error(f"WebSocket error for client {actual_client_id}: {e}")
        await connection_manager.disconnect(actual_client_id)


# HTTP endpoints for WebSocket management and monitoring
http_router = APIRouter(prefix="/websocket", tags=["websocket"])


@http_router.get("/stats")
async def get_websocket_stats():
    """Get WebSocket connection statistics."""
    try:
        stats = await connection_manager.get_connection_stats()
        return {
            "status": "success",
            "data": stats
        }
    except Exception as e:
        logger.error(f"Error getting WebSocket stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@http_router.post("/broadcast")
async def broadcast_message(
    topic: str,
    message: Dict[str, Any]
):
    """
    Broadcast a message to all subscribers of a topic.
    
    Args:
        topic: Target topic
        message: Message data to broadcast
    """
    try:
        from datetime import datetime
        from .connection_manager import WebSocketMessage
        
        ws_message = WebSocketMessage(
            type="data",
            topic=topic,
            data=message,
            timestamp=datetime.utcnow().isoformat()
        )
        
        await connection_manager.broadcast_to_topic(topic, ws_message)
        
        return {
            "status": "success",
            "message": f"Broadcasted to topic '{topic}'"
        }
        
    except Exception as e:
        logger.error(f"Error broadcasting message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@http_router.get("/topics")
async def get_active_topics():
    """Get list of active topics with subscriber counts."""
    try:
        stats = await connection_manager.get_connection_stats()
        topics_info = {}
        
        for topic in stats["topics"]:
            subscriber_count = len(connection_manager.subscriptions.get(topic, set()))
            topics_info[topic] = {
                "subscribers": subscriber_count,
                "active": subscriber_count > 0
            }
        
        return {
            "status": "success",
            "data": {
                "total_topics": len(topics_info),
                "topics": topics_info
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting topics info: {e}")
        raise HTTPException(status_code=500, detail=str(e))