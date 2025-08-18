//! Real-time performance monitoring module
//! 
//! This module implements Story 3.2: Performance Monitoring
//! Provides real-time monitoring of optimization progress and system resources
//! Supports pause, resume, and cancel operations for long-running backtests

pub mod monitor;
pub mod metrics;
pub mod resource;
pub mod progress;
pub mod websocket;
pub mod dashboard;

pub use monitor::{PerformanceMonitor, MonitorConfig};
pub use metrics::{SystemMetrics, OptimizationMetrics};
pub use resource::{ResourceMonitor, ResourceUsage};
pub use progress::{ProgressTracker, JobProgress};
pub use websocket::{WebSocketServer, MonitoringUpdate};
pub use dashboard::{DashboardData, MetricSnapshot};