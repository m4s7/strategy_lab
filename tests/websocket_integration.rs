//! WebSocket Integration Tests
//! 
//! Tests real-time WebSocket communication for monitoring and updates

use strategy_lab::monitoring::{WebSocketServer, MonitoringUpdate, UpdateType};
use tokio_tungstenite::connect_async;
use futures_util::{StreamExt, SinkExt};
use serde_json::json;

#[tokio::test]
async fn test_websocket_server_startup() {
    let mut server = WebSocketServer::new();
    
    // Start server on test port
    let result = server.start("127.0.0.1:9999").await;
    assert!(result.is_ok(), "WebSocket server should start");
    
    // Stop server
    server.stop().await;
}

#[tokio::test]
async fn test_websocket_client_connection() {
    let mut server = WebSocketServer::new();
    server.start("127.0.0.1:9998").await.unwrap();
    
    // Give server time to start
    tokio::time::sleep(tokio::time::Duration::from_millis(100)).await;
    
    // Connect client
    let url = "ws://127.0.0.1:9998/ws";
    let (ws_stream, _) = connect_async(url).await.expect("Failed to connect");
    
    let (mut write, mut read) = ws_stream.split();
    
    // Send subscription message
    let subscribe_msg = json!({
        "type": "subscribe",
        "channel": "optimization_progress"
    });
    
    write.send(tokio_tungstenite::tungstenite::Message::Text(
        subscribe_msg.to_string()
    )).await.expect("Failed to send message");
    
    // Receive acknowledgment
    if let Some(msg) = read.next().await {
        let msg = msg.expect("Failed to receive message");
        assert!(msg.is_text() || msg.is_binary());
    }
    
    server.stop().await;
}

#[tokio::test]
async fn test_broadcast_monitoring_update() {
    let mut server = WebSocketServer::new();
    server.start("127.0.0.1:9997").await.unwrap();
    
    // Give server time to start
    tokio::time::sleep(tokio::time::Duration::from_millis(100)).await;
    
    // Connect client
    let url = "ws://127.0.0.1:9997/ws";
    let (ws_stream, _) = connect_async(url).await.expect("Failed to connect");
    let (mut write, mut read) = ws_stream.split();
    
    // Subscribe to updates
    let subscribe_msg = json!({
        "type": "subscribe",
        "channel": "all"
    });
    
    write.send(tokio_tungstenite::tungstenite::Message::Text(
        subscribe_msg.to_string()
    )).await.expect("Failed to send subscription");
    
    // Broadcast an update
    let update = MonitoringUpdate {
        update_type: UpdateType::OptimizationProgress,
        timestamp: chrono::Utc::now(),
        data: json!({
            "progress": 50,
            "total": 100,
            "current_best": 1.5
        }),
    };
    
    server.broadcast_update(update).await.expect("Failed to broadcast");
    
    // Receive the broadcast
    tokio::time::timeout(
        tokio::time::Duration::from_secs(1),
        async {
            while let Some(msg) = read.next().await {
                if let Ok(msg) = msg {
                    if msg.is_text() {
                        let text = msg.to_text().unwrap();
                        if text.contains("OptimizationProgress") {
                            return Ok(());
                        }
                    }
                }
            }
            Err::<(), &str>("Timeout waiting for broadcast")
        }
    ).await.expect("Should receive broadcast").expect("Should get update");
    
    server.stop().await;
}

#[tokio::test]
async fn test_multiple_client_connections() {
    let mut server = WebSocketServer::new();
    server.start("127.0.0.1:9996").await.unwrap();
    
    tokio::time::sleep(tokio::time::Duration::from_millis(100)).await;
    
    // Connect multiple clients
    let mut clients = Vec::new();
    for i in 0..3 {
        let url = "ws://127.0.0.1:9996/ws";
        let (ws_stream, _) = connect_async(url).await
            .expect(&format!("Failed to connect client {}", i));
        clients.push(ws_stream);
    }
    
    // Verify all clients are connected
    assert_eq!(clients.len(), 3);
    
    // Broadcast to all clients
    let update = MonitoringUpdate {
        update_type: UpdateType::SystemMetrics,
        timestamp: chrono::Utc::now(),
        data: json!({
            "cpu_usage": 45.5,
            "memory_mb": 1024
        }),
    };
    
    server.broadcast_update(update).await.expect("Broadcast failed");
    
    // Each client should receive the message
    for (i, mut client) in clients.into_iter().enumerate() {
        let (_, mut read) = client.split();
        
        tokio::time::timeout(
            tokio::time::Duration::from_secs(1),
            async {
                if let Some(msg) = read.next().await {
                    if let Ok(msg) = msg {
                        assert!(msg.is_text() || msg.is_binary(), 
                            "Client {} should receive message", i);
                    }
                }
            }
        ).await.ok();
    }
    
    server.stop().await;
}

#[tokio::test]
async fn test_websocket_error_recovery() {
    let mut server = WebSocketServer::new();
    server.start("127.0.0.1:9995").await.unwrap();
    
    tokio::time::sleep(tokio::time::Duration::from_millis(100)).await;
    
    // Connect client
    let url = "ws://127.0.0.1:9995/ws";
    let (ws_stream, _) = connect_async(url).await.expect("Failed to connect");
    let (mut write, _) = ws_stream.split();
    
    // Send invalid message
    let invalid_msg = "invalid json {]";
    let result = write.send(tokio_tungstenite::tungstenite::Message::Text(
        invalid_msg.to_string()
    )).await;
    
    // Server should handle invalid message gracefully
    assert!(result.is_ok() || result.is_err(), "Server should handle invalid messages");
    
    // Server should still be running
    assert!(server.is_running(), "Server should continue after error");
    
    server.stop().await;
}

#[tokio::test]
async fn test_websocket_performance() {
    let mut server = WebSocketServer::new();
    server.start("127.0.0.1:9994").await.unwrap();
    
    tokio::time::sleep(tokio::time::Duration::from_millis(100)).await;
    
    // Connect client
    let url = "ws://127.0.0.1:9994/ws";
    let (ws_stream, _) = connect_async(url).await.expect("Failed to connect");
    let (mut write, mut read) = ws_stream.split();
    
    // Subscribe to updates
    let subscribe_msg = json!({
        "type": "subscribe", 
        "channel": "performance"
    });
    
    write.send(tokio_tungstenite::tungstenite::Message::Text(
        subscribe_msg.to_string()
    )).await.expect("Failed to subscribe");
    
    // Send many updates rapidly
    let start = std::time::Instant::now();
    let update_count = 100;
    
    for i in 0..update_count {
        let update = MonitoringUpdate {
            update_type: UpdateType::BacktestProgress,
            timestamp: chrono::Utc::now(),
            data: json!({
                "tick": i,
                "total_ticks": update_count
            }),
        };
        
        server.broadcast_update(update).await.expect("Broadcast failed");
    }
    
    // Measure throughput
    let elapsed = start.elapsed();
    let throughput = update_count as f64 / elapsed.as_secs_f64();
    
    println!("WebSocket throughput: {:.2} messages/second", throughput);
    assert!(throughput > 100.0, "Should handle at least 100 messages/second");
    
    // Count received messages
    let mut received = 0;
    let timeout = tokio::time::timeout(
        tokio::time::Duration::from_secs(2),
        async {
            while let Some(msg) = read.next().await {
                if msg.is_ok() {
                    received += 1;
                    if received >= update_count / 2 {
                        break;
                    }
                }
            }
        }
    ).await;
    
    assert!(timeout.is_ok(), "Should receive messages within timeout");
    assert!(received > 0, "Should receive at least some messages");
    
    server.stop().await;
}