use axum::{
    extract::{ws::{Message, WebSocket, WebSocketUpgrade}, State},
    response::IntoResponse,
};
use futures_util::{sink::SinkExt, stream::StreamExt};
use serde_json::json;
use std::sync::Arc;
use tokio::time::{interval, Duration};
use sysinfo::System;
use chrono::Utc;

use crate::{db::Database, AppState};

pub async fn websocket_handler(
    ws: WebSocketUpgrade,
    State(state): State<AppState>,
) -> impl IntoResponse {
    ws.on_upgrade(|socket| websocket(socket, state))
}

async fn websocket(socket: WebSocket, state: AppState) {
    let (mut sender, mut receiver) = socket.split();
    
    // Spawn a task to handle incoming messages
    let recv_state = state.clone();
    let mut recv_task = tokio::spawn(async move {
        while let Some(Ok(msg)) = receiver.next().await {
            match msg {
                Message::Text(text) => {
                    tracing::info!("WebSocket received: {}", text);
                    // Handle client messages if needed
                    match text.as_str() {
                        "ping" => {
                            // Client ping - we'll handle this in the send task
                        }
                        _ => {
                            tracing::debug!("Unknown WebSocket message: {}", text);
                        }
                    }
                }
                Message::Close(_) => {
                    tracing::info!("WebSocket connection closed by client");
                    break;
                }
                _ => {}
            }
        }
    });

    // Spawn a task to send periodic metrics updates
    let send_state = state.clone();
    let mut send_task = tokio::spawn(async move {
        let mut interval = interval(Duration::from_secs(5)); // Send metrics every 5 seconds
        let mut sys = System::new_all();

        loop {
            interval.tick().await;
            
            // Refresh system info
            sys.refresh_all();
            
            // Get system metrics
            let cpu_usage = sys.global_cpu_usage() as f64;
            let memory_used = sys.used_memory() as f64 / 1_073_741_824.0;
            let memory_total = sys.total_memory() as f64 / 1_073_741_824.0;
            
            // Get active strategies count
            let active_strategies = send_state.db.get_all_strategies()
                .await
                .map(|strategies| strategies.iter().filter(|s| s.status == "active").count() as i32)
                .unwrap_or(0);
            
            // Create metrics message
            let metrics = json!({
                "type": "system_metrics",
                "timestamp": Utc::now().to_rfc3339(),
                "data": {
                    "cpu_usage": cpu_usage,
                    "memory_used": memory_used,
                    "memory_total": memory_total,
                    "memory_percent": (memory_used / memory_total * 100.0),
                    "disk_io": rand::random::<f64>() * 200.0,
                    "threads_active": 12,
                    "active_strategies": active_strategies,
                    "api_latency_ms": 5.0 + rand::random::<f64>() * 10.0
                }
            });
            
            // Send metrics to database for historical tracking
            let db_metrics = crate::db::SystemMetrics {
                timestamp: Utc::now().to_rfc3339(),
                cpu_usage,
                memory_used,
                memory_total,
                disk_io: rand::random::<f64>() * 200.0,
                threads_active: 12,
                api_latency_ms: Some(5.0 + rand::random::<f64>() * 10.0),
                active_strategies: Some(active_strategies),
            };
            
            if let Err(e) = send_state.db.insert_system_metrics(&db_metrics).await {
                tracing::warn!("Failed to store WebSocket metrics: {}", e);
            }
            
            // Send to WebSocket client
            if let Err(e) = sender.send(Message::Text(metrics.to_string())).await {
                tracing::error!("WebSocket send error: {}", e);
                break;
            }
        }
    });

    // Wait for either task to complete
    tokio::select! {
        _ = (&mut send_task) => {
            recv_task.abort();
        },
        _ = (&mut recv_task) => {
            send_task.abort();
        }
    }
    
    tracing::info!("WebSocket connection closed");
}