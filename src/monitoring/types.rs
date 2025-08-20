//! Common types for monitoring module

use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};

/// Update message for monitoring system
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MonitoringUpdate {
    pub update_type: UpdateType,
    pub timestamp: DateTime<Utc>,
    pub data: serde_json::Value,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum UpdateType {
    SystemMetrics,
    OptimizationProgress,
    ResourceUsage,
    TradeExecution,
    Alert,
    Status,
}

impl MonitoringUpdate {
    pub fn new(update_type: UpdateType, data: serde_json::Value) -> Self {
        Self {
            update_type,
            timestamp: Utc::now(),
            data,
        }
    }
    
    pub fn system_metrics(metrics: serde_json::Value) -> Self {
        Self::new(UpdateType::SystemMetrics, metrics)
    }
    
    pub fn optimization_progress(progress: serde_json::Value) -> Self {
        Self::new(UpdateType::OptimizationProgress, progress)
    }
    
    pub fn resource_usage(usage: serde_json::Value) -> Self {
        Self::new(UpdateType::ResourceUsage, usage)
    }
}