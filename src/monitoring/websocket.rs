use tokio_tungstenite::{accept_async, WebSocketStream};
use tokio::net::TcpStream;
use tokio_tungstenite::tungstenite::{Message, Result};
use futures::{SinkExt, StreamExt};
use serde_json;
use std::collections::HashMap;
use std::sync::Arc;
use std::sync::atomic::{AtomicBool, Ordering};
use tokio::sync::{broadcast, RwLock};

use crate::monitoring::{
    progress::{ProgressManager, ProgressUpdate},
    metrics::{MetricsCollector, SystemMetrics},
};

pub struct WebSocketServer {
    progress_manager: Arc<ProgressManager>,
    metrics_collector: Arc<RwLock<MetricsCollector>>,
    connections: Arc<RwLock<HashMap<String, WebSocketConnection>>>,
    is_running: Arc<AtomicBool>,
}

impl WebSocketServer {
    pub fn new(
        progress_manager: Arc<ProgressManager>,
        metrics_collector: Arc<RwLock<MetricsCollector>>,
    ) -> Self {
        Self {
            progress_manager,
            metrics_collector,
            connections: Arc::new(RwLock::new(HashMap::new())),
            is_running: Arc::new(AtomicBool::new(false)),
        }
    }
    
    pub async fn start(&mut self, addr: &str) -> Result<(), Box<dyn std::error::Error>> {
        self.is_running.store(true, std::sync::atomic::Ordering::SeqCst);
        // WebSocket server implementation would go here
        Ok(())
    }
    
    pub async fn stop(&mut self) -> Result<(), Box<dyn std::error::Error>> {
        self.is_running.store(false, std::sync::atomic::Ordering::SeqCst);
        // Cleanup connections
        self.connections.write().await.clear();
        Ok(())
    }
}

#[derive(Debug)]
pub struct WebSocketConnection {
    pub client_id: String,
    pub subscriptions: Vec<SubscriptionType>,
    pub sender: broadcast::Sender<WebSocketMessage>,
}

#[derive(Debug, Clone)]
pub struct ConnectionState {
    pub id: uuid::Uuid,
    pub connected_at: chrono::DateTime<chrono::Utc>,
    pub last_ping: chrono::DateTime<chrono::Utc>,
    pub subscriptions: Vec<String>,
}

#[derive(Debug, Clone)]
pub enum SubscriptionType {
    ProgressUpdates,
    SystemMetrics,
    JobStatusUpdates(String), // specific job ID
    AllJobUpdates,
}

#[derive(Debug, Clone, serde::Serialize)]
#[serde(tag = "type")]
pub enum WebSocketMessage {
    ProgressUpdate {
        job_id: String,
        progress: crate::monitoring::progress::Progress,
    },
    SystemMetrics {
        metrics: SystemMetrics,
    },
    JobStatusUpdate {
        job_id: String,
        status: crate::monitoring::progress::JobStatus,
    },
    JobCompleted {
        job_id: String,
        final_metrics: Option<serde_json::Value>,
    },
    JobFailed {
        job_id: String,
        error: String,
    },
    Heartbeat {
        timestamp: u64,
    },
    Error {
        message: String,
    },
}

#[derive(Debug, serde::Deserialize)]
#[serde(tag = "type")]
pub enum WebSocketRequest {
    Subscribe {
        subscriptions: Vec<String>,
    },
    Unsubscribe {
        subscriptions: Vec<String>,
    },
    GetJobStatus {
        job_id: String,
    },
    GetAllJobs,
    GetSystemMetrics,
    ControlJob {
        job_id: String,
        action: JobAction,
    },
}

#[derive(Debug, serde::Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum JobAction {
    Pause,
    Resume,
    Cancel,
}

impl WebSocketServer {
    pub fn new(
        progress_manager: Arc<ProgressManager>,
        metrics_collector: Arc<RwLock<MetricsCollector>>,
    ) -> Self {
        Self {
            progress_manager,
            metrics_collector,
            connections: Arc::new(RwLock::new(HashMap::new())),
        }
    }

    pub async fn handle_connection(
        &self,
        stream: TcpStream,
        client_id: String,
    ) -> Result<()> {
        let ws_stream = accept_async(stream).await?;
        let (mut ws_sender, mut ws_receiver) = ws_stream.split();
        
        let (client_sender, mut client_receiver) = broadcast::channel::<WebSocketMessage>(100);
        
        // Register the connection
        {
            let mut connections = self.connections.write().await;
            connections.insert(client_id.clone(), WebSocketConnection {
                client_id: client_id.clone(),
                subscriptions: Vec::new(),
                sender: client_sender.clone(),
            });
        }

        // Subscribe to progress updates
        let mut progress_receiver = self.progress_manager.subscribe_to_updates();
        
        // Spawn task to handle progress updates
        let client_sender_clone = client_sender.clone();
        let client_id_clone = client_id.clone();
        tokio::spawn(async move {
            while let Ok(progress_update) = progress_receiver.recv().await {
                let message = match progress_update.update_type {
                    crate::monitoring::progress::ProgressUpdateType::ProgressUpdated(progress) => {
                        WebSocketMessage::ProgressUpdate {
                            job_id: progress_update.job_id,
                            progress,
                        }
                    },
                    crate::monitoring::progress::ProgressUpdateType::StatusChanged(status) => {
                        WebSocketMessage::JobStatusUpdate {
                            job_id: progress_update.job_id,
                            status,
                        }
                    },
                    crate::monitoring::progress::ProgressUpdateType::JobCompleted => {
                        WebSocketMessage::JobCompleted {
                            job_id: progress_update.job_id,
                            final_metrics: None,
                        }
                    },
                    crate::monitoring::progress::ProgressUpdateType::JobFailed(error) => {
                        WebSocketMessage::JobFailed {
                            job_id: progress_update.job_id,
                            error,
                        }
                    },
                    _ => continue,
                };

                if let Err(_) = client_sender_clone.send(message) {
                    break; // Client disconnected
                }
            }
        });

        // Spawn task to send messages to WebSocket
        let client_id_clone2 = client_id.clone();
        tokio::spawn(async move {
            while let Ok(message) = client_receiver.recv().await {
                let json_message = match serde_json::to_string(&message) {
                    Ok(json) => json,
                    Err(_) => continue,
                };

                if let Err(_) = ws_sender.send(Message::Text(json_message)).await {
                    break; // Connection closed
                }
            }
        });

        // Handle incoming messages
        while let Some(message) = ws_receiver.next().await {
            match message? {
                Message::Text(text) => {
                    if let Err(e) = self.handle_text_message(&client_id, text, &client_sender).await {
                        eprintln!("Error handling WebSocket message: {}", e);
                    }
                },
                Message::Close(_) => {
                    break;
                },
                _ => {
                    // Ignore other message types
                }
            }
        }

        // Clean up connection
        {
            let mut connections = self.connections.write().await;
            connections.remove(&client_id);
        }

        Ok(())
    }

    async fn handle_text_message(
        &self,
        client_id: &str,
        text: String,
        sender: &broadcast::Sender<WebSocketMessage>,
    ) -> Result<()> {
        let request: WebSocketRequest = match serde_json::from_str(&text) {
            Ok(req) => req,
            Err(e) => {
                let _ = sender.send(WebSocketMessage::Error {
                    message: format!("Invalid request format: {}", e),
                });
                return Ok(());
            }
        };

        match request {
            WebSocketRequest::Subscribe { subscriptions } => {
                self.handle_subscribe(client_id, subscriptions).await;
            },
            WebSocketRequest::Unsubscribe { subscriptions } => {
                self.handle_unsubscribe(client_id, subscriptions).await;
            },
            WebSocketRequest::GetJobStatus { job_id } => {
                if let Some(status) = self.progress_manager.get_job_status(&job_id).await {
                    let _ = sender.send(WebSocketMessage::JobStatusUpdate {
                        job_id,
                        status: status.status,
                    });
                }
            },
            WebSocketRequest::GetAllJobs => {
                let jobs = self.progress_manager.get_all_jobs().await;
                for job in jobs {
                    let _ = sender.send(WebSocketMessage::JobStatusUpdate {
                        job_id: job.job_id,
                        status: job.status,
                    });
                }
            },
            WebSocketRequest::GetSystemMetrics => {
                let mut collector = self.metrics_collector.write().await;
                let metrics = collector.collect_system_metrics();
                let _ = sender.send(WebSocketMessage::SystemMetrics { metrics });
            },
            WebSocketRequest::ControlJob { job_id, action } => {
                let result = match action {
                    JobAction::Pause => self.progress_manager.pause_job(&job_id).await,
                    JobAction::Resume => self.progress_manager.resume_job(&job_id).await,
                    JobAction::Cancel => self.progress_manager.cancel_job(&job_id).await,
                };

                if let Err(e) = result {
                    let _ = sender.send(WebSocketMessage::Error {
                        message: format!("Failed to control job {}: {}", job_id, e),
                    });
                }
            },
        }

        Ok(())
    }

    async fn handle_subscribe(&self, client_id: &str, subscriptions: Vec<String>) {
        let mut connections = self.connections.write().await;
        if let Some(connection) = connections.get_mut(client_id) {
            for sub in subscriptions {
                let subscription_type = match sub.as_str() {
                    "progress_updates" => SubscriptionType::ProgressUpdates,
                    "system_metrics" => SubscriptionType::SystemMetrics,
                    "all_jobs" => SubscriptionType::AllJobUpdates,
                    _ if sub.starts_with("job_") => {
                        let job_id = sub.strip_prefix("job_").unwrap_or(&sub);
                        SubscriptionType::JobStatusUpdates(job_id.to_string())
                    },
                    _ => continue,
                };
                
                if !connection.subscriptions.contains(&subscription_type) {
                    connection.subscriptions.push(subscription_type);
                }
            }
        }
    }

    async fn handle_unsubscribe(&self, client_id: &str, subscriptions: Vec<String>) {
        let mut connections = self.connections.write().await;
        if let Some(connection) = connections.get_mut(client_id) {
            for sub in subscriptions {
                let subscription_type = match sub.as_str() {
                    "progress_updates" => SubscriptionType::ProgressUpdates,
                    "system_metrics" => SubscriptionType::SystemMetrics,
                    "all_jobs" => SubscriptionType::AllJobUpdates,
                    _ if sub.starts_with("job_") => {
                        let job_id = sub.strip_prefix("job_").unwrap_or(&sub);
                        SubscriptionType::JobStatusUpdates(job_id.to_string())
                    },
                    _ => continue,
                };
                
                connection.subscriptions.retain(|s| !matches!(s, subscription_type));
            }
        }
    }

    pub async fn broadcast_system_metrics(&self) {
        let mut collector = self.metrics_collector.write().await;
        let metrics = collector.collect_system_metrics();
        
        let message = WebSocketMessage::SystemMetrics { metrics };
        
        let connections = self.connections.read().await;
        for connection in connections.values() {
            if connection.subscriptions.contains(&SubscriptionType::SystemMetrics) {
                let _ = connection.sender.send(message.clone());
            }
        }
    }

    pub async fn start_heartbeat(&self) {
        let connections = self.connections.clone();
        
        tokio::spawn(async move {
            let mut interval = tokio::time::interval(tokio::time::Duration::from_secs(30));
            
            loop {
                interval.tick().await;
                
                let heartbeat = WebSocketMessage::Heartbeat {
                    timestamp: chrono::Utc::now().timestamp_millis() as u64,
                };
                
                let conns = connections.read().await;
                for connection in conns.values() {
                    let _ = connection.sender.send(heartbeat.clone());
                }
            }
        });
    }

    pub async fn get_connection_count(&self) -> usize {
        self.connections.read().await.len()
    }
}

// Comparison implementation for SubscriptionType (required for contains())
impl PartialEq for SubscriptionType {
    fn eq(&self, other: &Self) -> bool {
        match (self, other) {
            (SubscriptionType::ProgressUpdates, SubscriptionType::ProgressUpdates) => true,
            (SubscriptionType::SystemMetrics, SubscriptionType::SystemMetrics) => true,
            (SubscriptionType::AllJobUpdates, SubscriptionType::AllJobUpdates) => true,
            (SubscriptionType::JobStatusUpdates(a), SubscriptionType::JobStatusUpdates(b)) => a == b,
            _ => false,
        }
    }
}