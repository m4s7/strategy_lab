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
pub mod websocket_tests;
pub mod dashboard;
pub mod types;

pub use monitor::{PerformanceMonitor, MonitorConfig};
pub use metrics::{SystemMetrics, OptimizationMetrics};
pub use resource::{ResourceMonitor, ResourceUsage};
pub use progress::ProgressTracker;
pub use websocket::WebSocketServer;
pub use dashboard::DashboardData;
pub use types::{MonitoringUpdate, UpdateType};