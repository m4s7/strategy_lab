//! WebSocket implementation for real-time updates

use axum::{
    extract::{
        ws::{Message, WebSocket, WebSocketUpgrade},
        State,
    },
    response::Response,
};
use futures::{sink::SinkExt, stream::StreamExt};
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use tokio::sync::broadcast;
use tracing::{debug, error};

use super::ApiState;
use crate::monitoring::ResourceMonitor;

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type")]
pub enum WsMessage {
    #[serde(rename = "metrics")]
    Metrics {
        cpu: f64,
        memory: f64,
        threads: usize,
        ticks_per_sec: u64,
    },
    #[serde(rename = "backtest_progress")]
    BacktestProgress {
        progress: f64,
        current_date: String,
        trades_executed: u32,
    },
    #[serde(rename = "optimization_update")]
    OptimizationUpdate {
        generation: u32,
        best_fitness: f64,
        evaluations: u32,
    },
    #[serde(rename = "error")]
    Error {
        message: String,
    },
}

/// WebSocket handler
pub async fn websocket_handler(
    ws: WebSocketUpgrade,
    State(state): State<ApiState>,
) -> Response {
    ws.on_upgrade(move |socket| handle_socket(socket, state))
}

/// Handle individual WebSocket connection
async fn handle_socket(socket: WebSocket, state: ApiState) {
    let (mut sender, mut receiver) = socket.split();
    let (tx, mut rx) = broadcast::channel::<WsMessage>(100);
    
    // Spawn task to send messages to client
    let mut send_task = tokio::spawn(async move {
        while let Ok(msg) = rx.recv().await {
            let json = serde_json::to_string(&msg).unwrap();
            if sender.send(Message::Text(json)).await.is_err() {
                break;
            }
        }
    });
    
    // Spawn task to monitor system metrics
    let tx_metrics = tx.clone();
    let monitor_task = tokio::spawn(async move {
        let monitor = ResourceMonitor::new();
        let mut interval = tokio::time::interval(std::time::Duration::from_secs(1));
        
        loop {
            interval.tick().await;
            let usage = monitor.get_current_usage();
            
            let msg = WsMessage::Metrics {
                cpu: usage.cpu_percent,
                memory: usage.memory_gb,
                threads: usage.active_threads,
                ticks_per_sec: 0, // Would get from actual processing
            };
            
            if tx_metrics.send(msg).is_err() {
                break;
            }
        }
    });
    
    // Handle incoming messages from client
    while let Some(Ok(msg)) = receiver.next().await {
        match msg {
            Message::Text(text) => {
                debug!("Received WebSocket message: {}", text);
                // Handle client messages here
            }
            Message::Close(_) => {
                debug!("WebSocket connection closed");
                break;
            }
            _ => {}
        }
    }
    
    // Cleanup
    send_task.abort();
    monitor_task.abort();
}

/// Broadcast message to all connected clients
pub fn broadcast_message(tx: &broadcast::Sender<WsMessage>, message: WsMessage) {
    let _ = tx.send(message);
}