//! Fault Tolerance and Error Recovery Module
//!
//! This module provides comprehensive error recovery, fault tolerance, and system resilience
//! capabilities for the Strategy Lab high-frequency trading system.

pub mod error_recovery;
pub mod circuit_breaker;
pub mod retry_mechanisms;
pub mod failover;
pub mod health_monitoring;
pub mod recovery_tests;

pub use error_recovery::{ErrorRecoveryManager, RecoveryStrategy, ErrorContext};
pub use circuit_breaker::{CircuitBreaker, CircuitState};
pub use retry_mechanisms::{RetryPolicy, RetryConfig, ExponentialBackoff};
pub use failover::{FailoverManager, FailoverConfig};
pub use health_monitoring::{HealthMonitor, SystemHealth, ComponentStatus};