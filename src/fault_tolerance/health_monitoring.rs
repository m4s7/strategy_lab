//! Health Monitoring and System Health Checks

use std::sync::Arc;
use tokio::sync::RwLock;
use std::collections::HashMap;
use std::time::{Duration, Instant};
use serde::{Serialize, Deserialize};

#[derive(Debug, Clone, Copy, PartialEq, Serialize, Deserialize)]
pub enum ComponentStatus {
    Healthy,
    Degraded,
    Unhealthy,
    Unknown,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ComponentHealth {
    pub name: String,
    pub status: ComponentStatus,
    pub last_check: Option<Instant>,
    pub message: Option<String>,
    pub metrics: HashMap<String, f64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SystemHealth {
    pub overall_status: ComponentStatus,
    pub components: HashMap<String, ComponentHealth>,
    pub timestamp: Instant,
    pub uptime: Duration,
}

pub struct HealthMonitor {
    components: Arc<RwLock<HashMap<String, ComponentHealth>>>,
    check_intervals: Arc<RwLock<HashMap<String, Duration>>>,
    start_time: Instant,
}

impl HealthMonitor {
    pub fn new() -> Self {
        Self {
            components: Arc::new(RwLock::new(HashMap::new())),
            check_intervals: Arc::new(RwLock::new(HashMap::new())),
            start_time: Instant::now(),
        }
    }

    pub async fn register_component(&self, name: String, check_interval: Duration) {
        let component = ComponentHealth {
            name: name.clone(),
            status: ComponentStatus::Unknown,
            last_check: None,
            message: None,
            metrics: HashMap::new(),
        };

        let mut components = self.components.write().await;
        components.insert(name.clone(), component);

        let mut intervals = self.check_intervals.write().await;
        intervals.insert(name, check_interval);
    }

    pub async fn update_component_health(
        &self,
        name: &str,
        status: ComponentStatus,
        message: Option<String>,
        metrics: HashMap<String, f64>,
    ) {
        let mut components = self.components.write().await;
        
        if let Some(component) = components.get_mut(name) {
            component.status = status;
            component.last_check = Some(Instant::now());
            component.message = message;
            component.metrics = metrics;
        }
    }

    pub async fn get_system_health(&self) -> SystemHealth {
        let components = self.components.read().await;
        let mut overall_status = ComponentStatus::Healthy;

        // Determine overall system status
        for component in components.values() {
            match component.status {
                ComponentStatus::Unhealthy => {
                    overall_status = ComponentStatus::Unhealthy;
                    break;
                }
                ComponentStatus::Degraded => {
                    if overall_status == ComponentStatus::Healthy {
                        overall_status = ComponentStatus::Degraded;
                    }
                }
                _ => {}
            }
        }

        SystemHealth {
            overall_status,
            components: components.clone(),
            timestamp: Instant::now(),
            uptime: self.start_time.elapsed(),
        }
    }

    pub async fn check_database_health(&self) -> ComponentStatus {
        // Simulate database health check
        tokio::time::sleep(Duration::from_millis(5)).await;
        
        let health = if rand::random::<f32>() > 0.05 {
            ComponentStatus::Healthy
        } else if rand::random::<f32>() > 0.5 {
            ComponentStatus::Degraded
        } else {
            ComponentStatus::Unhealthy
        };

        self.update_component_health(
            "database",
            health,
            Some(format!("Database status: {:?}", health)),
            HashMap::from([
                ("connection_pool_size".to_string(), 20.0),
                ("active_connections".to_string(), 5.0),
                ("query_latency_ms".to_string(), 2.5),
            ]),
        ).await;

        health
    }

    pub async fn check_cache_health(&self) -> ComponentStatus {
        // Simulate cache health check
        tokio::time::sleep(Duration::from_millis(3)).await;
        
        let health = if rand::random::<f32>() > 0.02 {
            ComponentStatus::Healthy
        } else {
            ComponentStatus::Degraded
        };

        self.update_component_health(
            "cache",
            health,
            Some(format!("Cache status: {:?}", health)),
            HashMap::from([
                ("hit_rate".to_string(), 0.95),
                ("memory_usage_mb".to_string(), 512.0),
                ("eviction_rate".to_string(), 0.01),
            ]),
        ).await;

        health
    }

    pub async fn check_message_queue_health(&self) -> ComponentStatus {
        // Simulate message queue health check
        tokio::time::sleep(Duration::from_millis(3)).await;
        
        let health = ComponentStatus::Healthy;

        self.update_component_health(
            "message_queue",
            health,
            Some("Message queue operational".to_string()),
            HashMap::from([
                ("queue_depth".to_string(), 150.0),
                ("processing_rate".to_string(), 1000.0),
                ("error_rate".to_string(), 0.001),
            ]),
        ).await;

        health
    }

    pub async fn start_monitoring(&self) {
        let components = self.components.clone();
        let intervals = self.check_intervals.clone();

        // Database health check
        let db_monitor = self.clone_for_monitoring();
        tokio::spawn(async move {
            let mut interval = tokio::time::interval(Duration::from_secs(10));
            loop {
                interval.tick().await;
                db_monitor.check_database_health().await;
            }
        });

        // Cache health check
        let cache_monitor = self.clone_for_monitoring();
        tokio::spawn(async move {
            let mut interval = tokio::time::interval(Duration::from_secs(5));
            loop {
                interval.tick().await;
                cache_monitor.check_cache_health().await;
            }
        });

        // Message queue health check
        let mq_monitor = self.clone_for_monitoring();
        tokio::spawn(async move {
            let mut interval = tokio::time::interval(Duration::from_secs(5));
            loop {
                interval.tick().await;
                mq_monitor.check_message_queue_health().await;
            }
        });
    }

    fn clone_for_monitoring(&self) -> Self {
        Self {
            components: self.components.clone(),
            check_intervals: self.check_intervals.clone(),
            start_time: self.start_time,
        }
    }

    pub async fn get_component_health(&self, name: &str) -> Option<ComponentHealth> {
        let components = self.components.read().await;
        components.get(name).cloned()
    }

    pub async fn is_system_healthy(&self) -> bool {
        let health = self.get_system_health().await;
        health.overall_status == ComponentStatus::Healthy
    }
}

use rand::Rng as _;