//! Performance testing and benchmarking module
//!
//! This module provides comprehensive performance testing capabilities for the Strategy Lab,
//! including load testing, memory profiling, and system benchmarking.

pub mod load_tests;

pub use load_tests::{LoadTestSuite, LoadTestResult};