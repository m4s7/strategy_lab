use axum::{
    extract::{ws::{WebSocket, Message}, WebSocketUpgrade, Path, Query},
    http::StatusCode,
    response::{Html, IntoResponse, Json},
    routing::{get, post},
    Router,
};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::RwLock;
use uuid::Uuid;

use crate::monitoring::{
    progress::ProgressManager,
    metrics::MetricsCollector,
    websocket::WebSocketServer,
};

pub struct DashboardServer {
    progress_manager: Arc<ProgressManager>,
    metrics_collector: Arc<RwLock<MetricsCollector>>,
    websocket_server: Arc<WebSocketServer>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct DashboardData {
    pub system_overview: SystemOverview,
    pub active_jobs: Vec<JobSummary>,
    pub recent_completions: Vec<JobSummary>,
    pub performance_metrics: PerformanceMetrics,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct SystemOverview {
    pub uptime_seconds: u64,
    pub cpu_usage: f64,
    pub memory_usage_mb: u64,
    pub memory_available_mb: u64,
    pub active_connections: usize,
    pub total_jobs_today: usize,
    pub system_health: HealthStatus,
}

#[derive(Debug, Serialize, Deserialize)]
pub enum HealthStatus {
    Healthy,
    Warning,
    Critical,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct JobSummary {
    pub job_id: String,
    pub job_type: String,
    pub strategy_name: String,
    pub status: String,
    pub progress_percent: f64,
    pub estimated_remaining_ms: u64,
    pub started_at: Option<u64>,
    pub completed_at: Option<u64>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct PerformanceMetrics {
    pub jobs_per_hour: f64,
    pub average_completion_time_ms: u64,
    pub success_rate: f64,
    pub resource_efficiency: f64,
}

#[derive(Debug, Deserialize)]
pub struct JobControlRequest {
    pub action: String, // "pause", "resume", "cancel"
}

impl DashboardServer {
    pub fn new(
        progress_manager: Arc<ProgressManager>,
        metrics_collector: Arc<RwLock<MetricsCollector>>,
        websocket_server: Arc<WebSocketServer>,
    ) -> Self {
        Self {
            progress_manager,
            metrics_collector,
            websocket_server,
        }
    }

    pub fn router(self: Arc<Self>) -> Router {
        Router::new()
            .route("/", get(Self::dashboard_html))
            .route("/api/dashboard", get({
                let server = Arc::clone(&self);
                move || server.get_dashboard_data()
            }))
            .route("/api/jobs", get({
                let server = Arc::clone(&self);
                move || server.get_all_jobs()
            }))
            .route("/api/jobs/:job_id", get({
                let server = Arc::clone(&self);
                move |path| server.get_job_details(path)
            }))
            .route("/api/jobs/:job_id/control", post({
                let server = Arc::clone(&self);
                move |path, body| server.control_job(path, body)
            }))
            .route("/api/system/metrics", get({
                let server = Arc::clone(&self);
                move || server.get_system_metrics()
            }))
            .route("/ws", get({
                let server = Arc::clone(&self);
                move |ws| server.websocket_handler(ws)
            }))
    }

    async fn dashboard_html() -> Html<&'static str> {
        Html(include_str!("../../static/dashboard.html"))
    }

    async fn get_dashboard_data(self: Arc<Self>) -> Result<Json<DashboardData>, StatusCode> {
        let active_jobs = self.progress_manager.get_active_jobs().await;
        let all_jobs = self.progress_manager.get_all_jobs().await;
        
        let mut collector = self.metrics_collector.write().await;
        let system_metrics = collector.collect_system_metrics();
        let performance_summary = collector.get_performance_summary();

        let job_summaries: Vec<JobSummary> = active_jobs.into_iter().map(|job| {
            JobSummary {
                job_id: job.job_id,
                job_type: format!("{:?}", job.job_type),
                strategy_name: job.metadata.strategy_name,
                status: format!("{:?}", job.status),
                progress_percent: job.progress.percentage,
                estimated_remaining_ms: job.progress.estimated_remaining_ms,
                started_at: job.timestamps.started,
                completed_at: job.timestamps.completed,
            }
        }).collect();

        let recent_completions: Vec<JobSummary> = all_jobs.into_iter()
            .filter(|job| matches!(job.status, crate::monitoring::progress::JobStatus::Completed))
            .take(10)
            .map(|job| {
                JobSummary {
                    job_id: job.job_id,
                    job_type: format!("{:?}", job.job_type),
                    strategy_name: job.metadata.strategy_name,
                    status: format!("{:?}", job.status),
                    progress_percent: job.progress.percentage,
                    estimated_remaining_ms: 0,
                    started_at: job.timestamps.started,
                    completed_at: job.timestamps.completed,
                }
            })
            .collect();

        let system_health = if system_metrics.cpu_usage > 90.0 || system_metrics.memory_usage > 30_000_000_000 {
            HealthStatus::Critical
        } else if system_metrics.cpu_usage > 70.0 || system_metrics.memory_usage > 20_000_000_000 {
            HealthStatus::Warning
        } else {
            HealthStatus::Healthy
        };

        let dashboard_data = DashboardData {
            system_overview: SystemOverview {
                uptime_seconds: performance_summary.uptime_seconds,
                cpu_usage: system_metrics.cpu_usage,
                memory_usage_mb: system_metrics.memory_usage / 1_000_000,
                memory_available_mb: 32_000, // Hardcoded for now
                active_connections: self.websocket_server.get_connection_count().await,
                total_jobs_today: performance_summary.metrics_collected,
                system_health,
            },
            active_jobs: job_summaries,
            recent_completions,
            performance_metrics: PerformanceMetrics {
                jobs_per_hour: 12.5, // Mock data
                average_completion_time_ms: 45000,
                success_rate: 0.95,
                resource_efficiency: 0.82,
            },
        };

        Ok(Json(dashboard_data))
    }

    async fn get_all_jobs(self: Arc<Self>) -> Result<Json<Vec<JobSummary>>, StatusCode> {
        let jobs = self.progress_manager.get_all_jobs().await;
        
        let job_summaries: Vec<JobSummary> = jobs.into_iter().map(|job| {
            JobSummary {
                job_id: job.job_id,
                job_type: format!("{:?}", job.job_type),
                strategy_name: job.metadata.strategy_name,
                status: format!("{:?}", job.status),
                progress_percent: job.progress.percentage,
                estimated_remaining_ms: job.progress.estimated_remaining_ms,
                started_at: job.timestamps.started,
                completed_at: job.timestamps.completed,
            }
        }).collect();

        Ok(Json(job_summaries))
    }

    async fn get_job_details(
        self: Arc<Self>, 
        Path(job_id): Path<String>
    ) -> Result<Json<crate::monitoring::progress::ProgressTracker>, StatusCode> {
        match self.progress_manager.get_job_status(&job_id).await {
            Some(job) => Ok(Json(job)),
            None => Err(StatusCode::NOT_FOUND),
        }
    }

    async fn control_job(
        self: Arc<Self>,
        Path(job_id): Path<String>,
        Json(request): Json<JobControlRequest>,
    ) -> Result<Json<serde_json::Value>, StatusCode> {
        let result = match request.action.as_str() {
            "pause" => self.progress_manager.pause_job(&job_id).await,
            "resume" => self.progress_manager.resume_job(&job_id).await,
            "cancel" => self.progress_manager.cancel_job(&job_id).await,
            _ => return Err(StatusCode::BAD_REQUEST),
        };

        match result {
            Ok(_) => Ok(Json(serde_json::json!({
                "status": "success",
                "message": format!("Job {} {}", job_id, request.action)
            }))),
            Err(e) => {
                eprintln!("Error controlling job {}: {}", job_id, e);
                Err(StatusCode::INTERNAL_SERVER_ERROR)
            }
        }
    }

    async fn get_system_metrics(self: Arc<Self>) -> Result<Json<crate::monitoring::metrics::SystemMetrics>, StatusCode> {
        let mut collector = self.metrics_collector.write().await;
        let metrics = collector.collect_system_metrics();
        Ok(Json(metrics))
    }

    async fn websocket_handler(
        self: Arc<Self>,
        ws: WebSocketUpgrade,
    ) -> impl IntoResponse {
        ws.on_upgrade(move |socket| async move {
            let client_id = Uuid::new_v4().to_string();
            if let Err(e) = self.handle_websocket(socket, client_id).await {
                eprintln!("WebSocket error: {}", e);
            }
        })
    }

    async fn handle_websocket(
        self: Arc<Self>,
        socket: WebSocket,
        client_id: String,
    ) -> Result<(), Box<dyn std::error::Error>> {
        // Convert axum WebSocket to tokio-tungstenite format for compatibility
        // For now, we'll implement a simple version
        
        let (mut sender, mut receiver) = socket.split();
        
        // Subscribe to updates
        let mut progress_receiver = self.progress_manager.subscribe_to_updates();
        
        // Handle progress updates
        tokio::spawn(async move {
            while let Ok(update) = progress_receiver.recv().await {
                let message = serde_json::json!({
                    "type": "progress_update",
                    "job_id": update.job_id,
                    "timestamp": update.timestamp
                });
                
                if let Ok(text) = serde_json::to_string(&message) {
                    if sender.send(Message::Text(text)).await.is_err() {
                        break;
                    }
                }
            }
        });

        // Handle incoming messages
        while let Some(msg) = receiver.next().await {
            match msg {
                Ok(Message::Text(text)) => {
                    // Handle client requests
                    if let Ok(request) = serde_json::from_str::<serde_json::Value>(&text) {
                        // Process request and send response
                        let response = serde_json::json!({
                            "type": "response",
                            "data": "acknowledged"
                        });
                        
                        if let Ok(response_text) = serde_json::to_string(&response) {
                            let _ = sender.send(Message::Text(response_text)).await;
                        }
                    }
                }
                Ok(Message::Close(_)) => break,
                Err(_) => break,
                _ => {}
            }
        }

        Ok(())
    }
}

// Simple HTML dashboard (in practice, this would be a separate file)
const DASHBOARD_HTML: &str = r#"
<!DOCTYPE html>
<html>
<head>
    <title>Strategy Lab Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
        .header { background: #2196F3; color: white; padding: 20px; margin: -20px -20px 20px -20px; }
        .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .metric-card { background: #f5f5f5; padding: 20px; border-radius: 8px; }
        .metric-value { font-size: 2em; font-weight: bold; color: #2196F3; }
        .jobs-section { margin-top: 30px; }
        .job-item { background: white; border: 1px solid #ddd; padding: 15px; margin-bottom: 10px; border-radius: 4px; }
        .progress-bar { background: #ddd; height: 20px; border-radius: 10px; overflow: hidden; }
        .progress-fill { background: #4CAF50; height: 100%; transition: width 0.3s; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Strategy Lab Dashboard</h1>
        <p>Real-time monitoring and control</p>
    </div>
    
    <div class="metrics" id="metrics">
        <!-- Metrics will be loaded here -->
    </div>
    
    <div class="jobs-section">
        <h2>Active Jobs</h2>
        <div id="active-jobs">
            <!-- Jobs will be loaded here -->
        </div>
    </div>

    <script>
        // Simple dashboard JavaScript
        function loadDashboard() {
            fetch('/api/dashboard')
                .then(response => response.json())
                .then(data => updateDashboard(data))
                .catch(error => console.error('Error loading dashboard:', error));
        }

        function updateDashboard(data) {
            const metrics = document.getElementById('metrics');
            metrics.innerHTML = `
                <div class="metric-card">
                    <div class="metric-value">${data.system_overview.cpu_usage.toFixed(1)}%</div>
                    <div>CPU Usage</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${(data.system_overview.memory_usage_mb / 1000).toFixed(1)}GB</div>
                    <div>Memory Usage</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${data.active_jobs.length}</div>
                    <div>Active Jobs</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${data.system_overview.active_connections}</div>
                    <div>WebSocket Connections</div>
                </div>
            `;

            const jobsContainer = document.getElementById('active-jobs');
            jobsContainer.innerHTML = data.active_jobs.map(job => `
                <div class="job-item">
                    <h3>${job.strategy_name} (${job.job_type})</h3>
                    <p>Status: ${job.status} | Progress: ${job.progress_percent.toFixed(1)}%</p>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${job.progress_percent}%"></div>
                    </div>
                </div>
            `).join('');
        }

        // Load dashboard on page load
        loadDashboard();
        
        // Refresh every 5 seconds
        setInterval(loadDashboard, 5000);
    </script>
</body>
</html>
"#;