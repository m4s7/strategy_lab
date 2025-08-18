//! Core performance monitoring implementation

use crate::monitoring::{
    ResourceMonitor, ProgressTracker, SystemMetrics, OptimizationMetrics,
    WebSocketServer, MonitoringUpdate
};
use serde::{Deserialize, Serialize};
use std::sync::{Arc, Mutex};
use std::time::{Duration, Instant};
use tokio::sync::mpsc;
use tokio::time::interval;
use tracing::{info, debug, warn};

/// Configuration for performance monitoring
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MonitorConfig {
    /// Update interval in milliseconds
    pub update_interval_ms: u64,
    
    /// Enable resource monitoring
    pub monitor_resources: bool,
    
    /// Enable progress tracking
    pub track_progress: bool,
    
    /// WebSocket port for real-time updates
    pub websocket_port: Option<u16>,
    
    /// Resource usage thresholds
    pub resource_thresholds: ResourceThresholds,
    
    /// Save monitoring data to file
    pub save_to_file: bool,
}

/// Resource usage thresholds for alerts
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ResourceThresholds {
    pub max_cpu_percent: f64,
    pub max_memory_gb: f64,
    pub max_disk_io_mb_s: f64,
}

impl Default for MonitorConfig {
    fn default() -> Self {
        Self {
            update_interval_ms: 1000,
            monitor_resources: true,
            track_progress: true,
            websocket_port: Some(8080),
            resource_thresholds: ResourceThresholds {
                max_cpu_percent: 90.0,
                max_memory_gb: 48.0,
                max_disk_io_mb_s: 100.0,
            },
            save_to_file: true,
        }
    }
}

/// Main performance monitor
pub struct PerformanceMonitor {
    config: MonitorConfig,
    resource_monitor: ResourceMonitor,
    progress_tracker: Arc<Mutex<ProgressTracker>>,
    system_metrics: Arc<Mutex<SystemMetrics>>,
    optimization_metrics: Arc<Mutex<OptimizationMetrics>>,
    websocket_server: Option<WebSocketServer>,
    start_time: Instant,
    is_running: Arc<Mutex<bool>>,
    is_paused: Arc<Mutex<bool>>,
}

impl PerformanceMonitor {
    /// Create new performance monitor
    pub fn new(config: MonitorConfig) -> Self {
        let websocket_server = config.websocket_port.map(WebSocketServer::new);
        
        Self {
            config,
            resource_monitor: ResourceMonitor::new(),
            progress_tracker: Arc::new(Mutex::new(ProgressTracker::new())),
            system_metrics: Arc::new(Mutex::new(SystemMetrics::default())),
            optimization_metrics: Arc::new(Mutex::new(OptimizationMetrics::default())),
            websocket_server,
            start_time: Instant::now(),
            is_running: Arc::new(Mutex::new(false)),
            is_paused: Arc::new(Mutex::new(false)),
        }
    }
    
    /// Start monitoring
    pub async fn start(&mut self) -> Result<(), Box<dyn std::error::Error>> {
        *self.is_running.lock().unwrap() = true;
        *self.is_paused.lock().unwrap() = false;
        
        info!("Starting performance monitoring");
        
        // Start WebSocket server if configured
        if let Some(ref mut ws) = self.websocket_server {
            ws.start().await?;
        }
        
        // Start monitoring loop
        let (tx, mut rx) = mpsc::channel::<MonitoringUpdate>(100);
        
        // Spawn monitoring task
        let config = self.config.clone();
        let resource_monitor = self.resource_monitor.clone();
        let progress_tracker = Arc::clone(&self.progress_tracker);
        let system_metrics = Arc::clone(&self.system_metrics);
        let optimization_metrics = Arc::clone(&self.optimization_metrics);
        let is_running = Arc::clone(&self.is_running);
        let is_paused = Arc::clone(&self.is_paused);
        
        tokio::spawn(async move {
            let mut interval = interval(Duration::from_millis(config.update_interval_ms));
            
            while *is_running.lock().unwrap() {
                interval.tick().await;
                
                if *is_paused.lock().unwrap() {
                    continue;
                }
                
                // Collect metrics
                let update = Self::collect_metrics(
                    &resource_monitor,
                    &progress_tracker,
                    &system_metrics,
                    &optimization_metrics,
                    &config.resource_thresholds,
                ).await;
                
                // Send update
                if let Err(e) = tx.send(update).await {
                    warn!("Failed to send monitoring update: {}", e);
                }
            }
        });
        
        // Process updates
        tokio::spawn(async move {
            while let Some(update) = rx.recv().await {
                self.process_update(update).await;
            }
        });
        
        Ok(())
    }
    
    /// Stop monitoring
    pub async fn stop(&mut self) {
        *self.is_running.lock().unwrap() = false;
        
        if let Some(ref mut ws) = self.websocket_server {
            ws.stop().await;
        }
        
        info!("Performance monitoring stopped");
    }
    
    /// Pause monitoring
    pub fn pause(&mut self) {
        *self.is_paused.lock().unwrap() = true;
        info!("Performance monitoring paused");
    }
    
    /// Resume monitoring
    pub fn resume(&mut self) {
        *self.is_paused.lock().unwrap() = false;
        info!("Performance monitoring resumed");
    }
    
    /// Collect current metrics
    async fn collect_metrics(
        resource_monitor: &ResourceMonitor,
        progress_tracker: &Arc<Mutex<ProgressTracker>>,
        system_metrics: &Arc<Mutex<SystemMetrics>>,
        optimization_metrics: &Arc<Mutex<OptimizationMetrics>>,
        thresholds: &ResourceThresholds,
    ) -> MonitoringUpdate {
        let resources = resource_monitor.get_current_usage();
        let progress = progress_tracker.lock().unwrap().get_all_progress();
        let sys_metrics = system_metrics.lock().unwrap().clone();
        let opt_metrics = optimization_metrics.lock().unwrap().clone();
        
        // Check for alerts
        let mut alerts = Vec::new();
        
        if resources.cpu_percent > thresholds.max_cpu_percent {
            alerts.push(format!(
                "High CPU usage: {:.1}% (threshold: {:.1}%)",
                resources.cpu_percent, thresholds.max_cpu_percent
            ));
        }
        
        if resources.memory_gb > thresholds.max_memory_gb {
            alerts.push(format!(
                "High memory usage: {:.1}GB (threshold: {:.1}GB)",
                resources.memory_gb, thresholds.max_memory_gb
            ));
        }
        
        MonitoringUpdate {
            timestamp: chrono::Utc::now(),
            resources,
            progress,
            system_metrics: sys_metrics,
            optimization_metrics: opt_metrics,
            alerts,
        }
    }
    
    /// Process monitoring update
    async fn process_update(&mut self, update: MonitoringUpdate) {
        // Log alerts
        for alert in &update.alerts {
            warn!("{}", alert);
        }
        
        // Send to WebSocket clients
        if let Some(ref mut ws) = self.websocket_server {
            ws.broadcast(update.clone()).await;
        }
        
        // Save to file if configured
        if self.config.save_to_file {
            self.save_update(&update).await;
        }
        
        debug!("Monitoring update processed: {} jobs active", update.progress.len());
    }
    
    /// Save monitoring update to file
    async fn save_update(&self, update: &MonitoringUpdate) {
        // Implementation would save to time-series database or file
    }
    
    /// Update job progress
    pub fn update_progress(&mut self, job_id: String, progress: f64, status: JobStatus) {
        self.progress_tracker.lock().unwrap()
            .update_progress(job_id, progress, status);
    }
    
    /// Add optimization metrics
    pub fn add_optimization_result(&mut self, result: OptimizationResultSummary) {
        self.optimization_metrics.lock().unwrap()
            .add_result(result);
    }
    
    /// Get current system metrics
    pub fn get_system_metrics(&self) -> SystemMetrics {
        self.system_metrics.lock().unwrap().clone()
    }
    
    /// Get resource usage
    pub fn get_resource_usage(&self) -> crate::monitoring::ResourceUsage {
        self.resource_monitor.get_current_usage()
    }
}

/// Job status
#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub enum JobStatus {
    Pending,
    Running,
    Paused,
    Completed,
    Failed,
    Cancelled,
}

/// Summary of optimization result for monitoring
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OptimizationResultSummary {
    pub job_id: String,
    pub objective_value: f64,
    pub parameters_evaluated: usize,
    pub duration_secs: f64,
}