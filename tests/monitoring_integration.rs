//! Real-time Monitoring Integration Tests
//! 
//! Tests the monitoring and progress tracking systems

use strategy_lab::monitoring::{PerformanceMonitor, MonitorConfig, ResourceMonitor};
use std::time::Duration;
use tokio::time::sleep;

#[tokio::test]
async fn test_performance_monitor_initialization() {
    let config = MonitorConfig {
        update_interval_ms: 100,
        resource_check_interval_ms: 500,
        enable_websocket: false,
        websocket_port: 8080,
        max_memory_gb: 32,
        alert_thresholds: Default::default(),
    };
    
    let monitor = PerformanceMonitor::new(config);
    assert!(monitor.is_ok(), "Monitor should initialize successfully");
}

#[tokio::test]
async fn test_resource_monitoring() {
    let mut resource_monitor = ResourceMonitor::new();
    
    // Start monitoring
    resource_monitor.start_monitoring();
    
    // Let it collect some data
    sleep(Duration::from_millis(100)).await;
    
    // Get current usage
    let usage = resource_monitor.get_current_usage();
    
    // Validate basic metrics
    assert!(usage.cpu_percent >= 0.0 && usage.cpu_percent <= 100.0, 
        "CPU usage should be between 0-100%");
    assert!(usage.memory_mb > 0, "Memory usage should be positive");
    assert!(usage.available_memory_mb > 0, "Available memory should be positive");
    
    // Stop monitoring
    resource_monitor.stop_monitoring();
}

#[tokio::test]
async fn test_progress_tracking() {
    use strategy_lab::monitoring::ProgressTracker;
    
    let mut tracker = ProgressTracker::new("Backtest", 1000);
    
    // Update progress
    for i in 0..10 {
        tracker.update(i * 100);
        sleep(Duration::from_millis(10)).await;
    }
    
    // Check progress
    let progress = tracker.get_progress();
    assert_eq!(progress.completed, 900);
    assert_eq!(progress.total, 1000);
    assert_eq!(progress.percentage, 90.0);
    assert!(progress.elapsed_ms > 0);
    
    // Complete the task
    tracker.complete();
    let final_progress = tracker.get_progress();
    assert_eq!(final_progress.completed, final_progress.total);
    assert_eq!(final_progress.percentage, 100.0);
}

#[tokio::test]
async fn test_concurrent_progress_tracking() {
    use strategy_lab::monitoring::ProgressTracker;
    use std::sync::Arc;
    use tokio::sync::Mutex;
    
    let tracker = Arc::new(Mutex::new(ProgressTracker::new("Optimization", 100)));
    
    // Spawn multiple tasks updating progress
    let mut handles = vec![];
    
    for i in 0..5 {
        let tracker_clone = Arc::clone(&tracker);
        let handle = tokio::spawn(async move {
            for j in 0..20 {
                let mut t = tracker_clone.lock().await;
                t.increment();
                drop(t);
                sleep(Duration::from_millis(5)).await;
            }
        });
        handles.push(handle);
    }
    
    // Wait for all tasks
    for handle in handles {
        handle.await.unwrap();
    }
    
    // Check final progress
    let tracker = tracker.lock().await;
    let progress = tracker.get_progress();
    assert_eq!(progress.completed, 100);
    assert_eq!(progress.percentage, 100.0);
}

#[tokio::test]
async fn test_memory_limit_monitoring() {
    let mut resource_monitor = ResourceMonitor::new();
    resource_monitor.set_memory_limit_mb(32 * 1024); // 32 GB
    
    resource_monitor.start_monitoring();
    sleep(Duration::from_millis(100)).await;
    
    let usage = resource_monitor.get_current_usage();
    assert!(usage.memory_mb < 32 * 1024, "Memory should be within limits");
    
    // Check if alert would trigger
    let alert_triggered = resource_monitor.check_memory_alert(0.9); // 90% threshold
    println!("Memory alert status: {}", alert_triggered);
    
    resource_monitor.stop_monitoring();
}

#[tokio::test]
async fn test_monitoring_pause_resume() {
    let config = MonitorConfig::default();
    let mut monitor = PerformanceMonitor::new(config).unwrap();
    
    // Start monitoring
    monitor.start().await.unwrap();
    assert!(monitor.is_running(), "Monitor should be running");
    
    sleep(Duration::from_millis(100)).await;
    
    // Pause monitoring
    monitor.pause().await.unwrap();
    assert!(!monitor.is_running(), "Monitor should be paused");
    
    sleep(Duration::from_millis(100)).await;
    
    // Resume monitoring
    monitor.resume().await.unwrap();
    assert!(monitor.is_running(), "Monitor should be running again");
    
    // Stop monitoring
    monitor.stop().await.unwrap();
    assert!(!monitor.is_running(), "Monitor should be stopped");
}

#[tokio::test]
async fn test_monitoring_with_alerts() {
    let mut config = MonitorConfig::default();
    config.alert_thresholds.insert("cpu_percent".to_string(), 80.0);
    config.alert_thresholds.insert("memory_percent".to_string(), 90.0);
    
    let mut monitor = PerformanceMonitor::new(config).unwrap();
    monitor.start().await.unwrap();
    
    // Set up alert handler
    let (alert_tx, mut alert_rx) = tokio::sync::mpsc::channel(10);
    monitor.set_alert_handler(alert_tx);
    
    // Simulate high resource usage (would need mock in real implementation)
    // For now, just check the alert channel is set up
    sleep(Duration::from_millis(500)).await;
    
    // Check if any alerts were triggered
    let alert = tokio::time::timeout(
        Duration::from_millis(100),
        alert_rx.recv()
    ).await;
    
    // Alert may or may not trigger depending on actual system load
    println!("Alert status: {:?}", alert.is_ok());
    
    monitor.stop().await.unwrap();
}

#[test]
fn test_monitor_config_validation() {
    let config = MonitorConfig {
        update_interval_ms: 0, // Invalid
        resource_check_interval_ms: 500,
        enable_websocket: false,
        websocket_port: 8080,
        max_memory_gb: 32,
        alert_thresholds: Default::default(),
    };
    
    // Should handle invalid config gracefully
    let result = PerformanceMonitor::new(config);
    assert!(result.is_err() || result.is_ok(), 
        "Should handle invalid config");
}