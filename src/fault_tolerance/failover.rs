//! Failover Management for High Availability

use std::sync::Arc;
use tokio::sync::RwLock;
use std::collections::HashMap;
use std::time::{Duration, Instant};

#[derive(Debug, Clone)]
pub struct FailoverConfig {
    pub health_check_interval: Duration,
    pub failover_timeout: Duration,
    pub max_consecutive_failures: u32,
    pub recovery_period: Duration,
}

impl Default for FailoverConfig {
    fn default() -> Self {
        Self {
            health_check_interval: Duration::from_secs(5),
            failover_timeout: Duration::from_secs(30),
            max_consecutive_failures: 3,
            recovery_period: Duration::from_secs(60),
        }
    }
}

#[derive(Debug, Clone)]
pub struct ServiceEndpoint {
    pub id: String,
    pub url: String,
    pub priority: u32,
    pub healthy: bool,
    pub last_check: Option<Instant>,
    pub consecutive_failures: u32,
}

pub struct FailoverManager {
    config: FailoverConfig,
    endpoints: Arc<RwLock<Vec<ServiceEndpoint>>>,
    active_endpoint: Arc<RwLock<Option<String>>>,
    health_check_results: Arc<RwLock<HashMap<String, bool>>>,
}

impl FailoverManager {
    pub fn new(config: FailoverConfig) -> Self {
        Self {
            config,
            endpoints: Arc::new(RwLock::new(Vec::new())),
            active_endpoint: Arc::new(RwLock::new(None)),
            health_check_results: Arc::new(RwLock::new(HashMap::new())),
        }
    }

    pub async fn add_endpoint(&self, endpoint: ServiceEndpoint) {
        let mut endpoints = self.endpoints.write().await;
        endpoints.push(endpoint);
        endpoints.sort_by_key(|e| e.priority);
    }

    pub async fn get_active_endpoint(&self) -> Option<ServiceEndpoint> {
        let active_id = self.active_endpoint.read().await;
        if let Some(id) = active_id.as_ref() {
            let endpoints = self.endpoints.read().await;
            return endpoints.iter().find(|e| &e.id == id).cloned();
        }
        None
    }

    pub async fn failover(&self) -> Result<ServiceEndpoint, String> {
        let mut endpoints = self.endpoints.write().await;
        
        // Mark current endpoint as unhealthy
        if let Some(active_id) = self.active_endpoint.read().await.as_ref() {
            if let Some(endpoint) = endpoints.iter_mut().find(|e| &e.id == active_id) {
                endpoint.healthy = false;
                endpoint.consecutive_failures += 1;
            }
        }

        // Find next healthy endpoint
        for endpoint in endpoints.iter_mut() {
            if endpoint.healthy || self.should_retry_endpoint(endpoint) {
                // Perform health check
                if self.check_endpoint_health(&endpoint.url).await {
                    endpoint.healthy = true;
                    endpoint.consecutive_failures = 0;
                    endpoint.last_check = Some(Instant::now());
                    
                    let mut active = self.active_endpoint.write().await;
                    *active = Some(endpoint.id.clone());
                    
                    return Ok(endpoint.clone());
                } else {
                    endpoint.consecutive_failures += 1;
                    endpoint.last_check = Some(Instant::now());
                }
            }
        }

        Err("No healthy endpoints available".to_string())
    }

    fn should_retry_endpoint(&self, endpoint: &ServiceEndpoint) -> bool {
        if endpoint.consecutive_failures >= self.config.max_consecutive_failures {
            if let Some(last_check) = endpoint.last_check {
                return last_check.elapsed() >= self.config.recovery_period;
            }
        }
        true
    }

    async fn check_endpoint_health(&self, url: &str) -> bool {
        // Simulate health check - in production, this would make an actual HTTP request
        tokio::time::sleep(Duration::from_millis(10)).await;
        
        // For now, return true 90% of the time to simulate mostly healthy services
        rand::random::<f32>() > 0.1
    }

    pub async fn start_health_monitoring(&self) {
        let endpoints = self.endpoints.clone();
        let interval = self.config.health_check_interval;
        let health_results = self.health_check_results.clone();

        tokio::spawn(async move {
            let mut interval = tokio::time::interval(interval);
            
            loop {
                interval.tick().await;
                
                let mut endpoints = endpoints.write().await;
                let mut results = health_results.write().await;
                
                for endpoint in endpoints.iter_mut() {
                    let health = Self::perform_health_check(&endpoint.url).await;
                    results.insert(endpoint.id.clone(), health);
                    
                    if health {
                        endpoint.healthy = true;
                        endpoint.consecutive_failures = 0;
                    } else {
                        endpoint.consecutive_failures += 1;
                        if endpoint.consecutive_failures >= 3 {
                            endpoint.healthy = false;
                        }
                    }
                    
                    endpoint.last_check = Some(Instant::now());
                }
            }
        });
    }

    async fn perform_health_check(url: &str) -> bool {
        // Simulate health check
        tokio::time::sleep(Duration::from_millis(5)).await;
        rand::random::<f32>() > 0.05 // 95% success rate
    }

    pub async fn get_all_endpoints(&self) -> Vec<ServiceEndpoint> {
        self.endpoints.read().await.clone()
    }

    pub async fn reset_endpoint(&self, id: &str) -> Result<(), String> {
        let mut endpoints = self.endpoints.write().await;
        
        if let Some(endpoint) = endpoints.iter_mut().find(|e| e.id == id) {
            endpoint.healthy = true;
            endpoint.consecutive_failures = 0;
            endpoint.last_check = None;
            Ok(())
        } else {
            Err(format!("Endpoint {} not found", id))
        }
    }
}

use rand::Rng as _;