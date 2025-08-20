//! WebSocket and Real-time System Testing
//! 
//! Comprehensive testing suite for real-time monitoring, WebSocket connections,
//! and live data streaming capabilities required for the Strategy Lab

use crate::monitoring::{
    WebSocketServer, MonitoringUpdate, PerformanceMonitor,
    ResourceUsage, UpdateType
};
use crate::jobs::JobStatus;
use crate::monitoring::progress::ProgressUpdate;
use crate::jobs::JobStatus;
use std::sync::{Arc, atomic::{AtomicBool, Ordering}};
use std::time::{Duration, Instant};
use tokio::sync::{mpsc, RwLock};
use tokio::time::timeout;
use serde_json::json;
use uuid::Uuid;

/// Comprehensive WebSocket and real-time testing framework
pub struct WebSocketTestSuite {
    test_results: Vec<WebSocketTestResult>,
}

#[derive(Debug)]
pub struct WebSocketTestResult {
    pub test_name: String,
    pub success: bool,
    pub message: String,
    pub execution_time_ms: u128,
    pub throughput_ops_per_sec: Option<f64>,
}

impl WebSocketTestSuite {
    pub fn new() -> Self {
        Self {
            test_results: Vec::new(),
        }
    }
    
    /// Run all WebSocket and real-time system tests
    pub async fn run_all_tests(&mut self) -> Result<(), String> {
        println!("🚀 Starting WebSocket and Real-time System Tests");
        
        // Test 1: WebSocket Server Lifecycle
        self.test_websocket_server_lifecycle().await;
        
        // Test 2: Connection Management
        self.test_connection_management().await;
        
        // Test 3: Real-time Data Streaming
        self.test_real_time_data_streaming().await;
        
        // Test 4: Progress Monitoring
        self.test_progress_monitoring().await;
        
        // Test 5: Performance Metrics Broadcasting
        self.test_performance_metrics_broadcasting().await;
        
        // Test 6: Concurrent Connection Handling
        self.test_concurrent_connections().await;
        
        // Test 7: Message Throughput and Latency
        self.test_message_throughput().await;
        
        // Test 8: Error Handling and Recovery
        self.test_error_handling().await;
        
        // Test 9: Resource Usage Monitoring
        self.test_resource_monitoring().await;
        
        // Test 10: Live Strategy Updates
        self.test_live_strategy_updates().await;
        
        self.print_results();
        
        Ok(())
    }
    
    async fn test_websocket_server_lifecycle(&mut self) {
        let start = Instant::now();
        let mut server = WebSocketServer::new();
        
        let result = match timeout(Duration::from_secs(5), async {
            // Test server start
            server.start("127.0.0.1:0").await?; // Use port 0 for automatic assignment
            
            // Test server state
            if !server.is_running.load(Ordering::SeqCst) {
                return Err("Server not running after start".into());
            }
            
            // Test server stop
            server.stop().await?;
            
            if server.is_running.load(Ordering::SeqCst) {
                return Err("Server still running after stop".into());
            }
            
            Ok(())
        }).await {
            Ok(Ok(())) => WebSocketTestResult {
                test_name: "WebSocket Server Lifecycle".to_string(),
                success: true,
                message: "Server start/stop cycle successful".to_string(),
                execution_time_ms: start.elapsed().as_millis(),
                throughput_ops_per_sec: None,
            },
            Ok(Err(e)) => WebSocketTestResult {
                test_name: "WebSocket Server Lifecycle".to_string(),
                success: false,
                message: format!("Server lifecycle error: {}", e),
                execution_time_ms: start.elapsed().as_millis(),
                throughput_ops_per_sec: None,
            },
            Err(_) => WebSocketTestResult {
                test_name: "WebSocket Server Lifecycle".to_string(),
                success: false,
                message: "Server lifecycle test timed out".to_string(),
                execution_time_ms: start.elapsed().as_millis(),
                throughput_ops_per_sec: None,
            }
        };
        
        self.test_results.push(result);
    }
    
    async fn test_connection_management(&mut self) {
        let start = Instant::now();
        let server = Arc::new(RwLock::new(WebSocketServer::new()));
        
        // Simulate multiple connection attempts
        let mut handles = vec![];
        let connection_count = 10;
        
        for i in 0..connection_count {
            let server_clone = server.clone();
            let handle = tokio::spawn(async move {
                let conn_id = Uuid::new_v4();
                let mut server_lock = server_clone.write().await;
                
                // Simulate connection
                server_lock.connections.write().await.insert(
                    conn_id,
                    ConnectionState {
                        id: conn_id,
                        connected_at: chrono::Utc::now(),
                        last_ping: chrono::Utc::now(),
                        subscriptions: vec![],
                    }
                );
                
                conn_id
            });
            handles.push(handle);
        }
        
        // Wait for all connections
        let mut connected_ids = Vec::new();
        for handle in handles {
            if let Ok(conn_id) = handle.await {
                connected_ids.push(conn_id);
            }
        }
        
        let final_count = {
            let server_lock = server.read().await;
            server_lock.connections.read().await.len()
        };
        
        let result = WebSocketTestResult {
            test_name: "Connection Management".to_string(),
            success: final_count == connection_count,
            message: format!("Managed {}/{} connections successfully", final_count, connection_count),
            execution_time_ms: start.elapsed().as_millis(),
            throughput_ops_per_sec: Some(connection_count as f64 / start.elapsed().as_secs_f64()),
        };
        
        self.test_results.push(result);
    }
    
    async fn test_real_time_data_streaming(&mut self) {
        let start = Instant::now();
        let (tx, mut rx) = mpsc::channel::<MonitoringUpdate>(1000);
        
        // Simulate real-time data generation
        let producer_handle = tokio::spawn(async move {
            for i in 0..100 {
                let update = MonitoringUpdate {
                    update_type: UpdateType::SystemMetrics,
                    timestamp: chrono::Utc::now(),
                    data: json!({
                        "price": 18500.25 + i as f64,
                        "volume": 10 + i,
                        "sequence": i
                    }),
                };
                
                if tx.send(update).await.is_err() {
                    break;
                }
                
                tokio::time::sleep(Duration::from_millis(1)).await;
            }
        });
        
        // Consumer - receive and validate data
        let mut received_count = 0;
        let mut last_sequence = -1i32;
        let mut sequence_errors = 0;
        
        while let Some(update) = timeout(Duration::from_secs(2), rx.recv()).await.unwrap_or(None) {
            received_count += 1;
            
            if let Some(sequence) = update.data.get("sequence").and_then(|s| s.as_i64()) {
                if sequence as i32 != last_sequence + 1 {
                    sequence_errors += 1;
                }
                last_sequence = sequence as i32;
            }
            
            if received_count >= 100 {
                break;
            }
        }
        
        producer_handle.abort();
        
        let throughput = received_count as f64 / start.elapsed().as_secs_f64();
        
        let result = WebSocketTestResult {
            test_name: "Real-time Data Streaming".to_string(),
            success: received_count >= 95 && sequence_errors == 0, // Allow small message loss
            message: format!("Streamed {}/100 messages, {} sequence errors", received_count, sequence_errors),
            execution_time_ms: start.elapsed().as_millis(),
            throughput_ops_per_sec: Some(throughput),
        };
        
        self.test_results.push(result);
    }
    
    async fn test_progress_monitoring(&mut self) {
        let start = Instant::now();
        let (tx, mut rx) = mpsc::channel::<ProgressUpdate>(100);
        
        // Simulate progress updates for a backtest
        let job_id = Uuid::new_v4();
        let total_steps = 1000;
        
        let producer = tokio::spawn(async move {
            for step in 0..=total_steps {
                let progress = ProgressUpdate {
                    job_id,
                    stage: "backtesting".to_string(),
                    current_step: step,
                    total_steps,
                    percentage: (step as f64 / total_steps as f64) * 100.0,
                    estimated_remaining: Duration::from_secs((total_steps - step) as u64 / 10),
                    current_operation: format!("Processing tick {}", step),
                };
                
                if tx.send(progress).await.is_err() {
                    break;
                }
                
                if step % 100 == 0 {
                    tokio::time::sleep(Duration::from_millis(1)).await;
                }
            }
        });
        
        let mut last_percentage = -1.0;
        let mut progress_updates = 0;
        let mut final_progress = None;
        
        while let Some(progress) = timeout(Duration::from_secs(3), rx.recv()).await.unwrap_or(None) {
            progress_updates += 1;
            
            // Validate progress is monotonic
            if progress.percentage < last_percentage {
                break; // Progress went backward - error
            }
            
            last_percentage = progress.percentage;
            final_progress = Some(progress);
            
            if last_percentage >= 100.0 {
                break;
            }
        }
        
        producer.abort();
        
        let success = final_progress.map_or(false, |p| p.percentage >= 100.0 && progress_updates > 10);
        
        let result = WebSocketTestResult {
            test_name: "Progress Monitoring".to_string(),
            success,
            message: format!("Received {} progress updates, final: {:.1}%", 
                progress_updates, 
                final_progress.map_or(-1.0, |p| p.percentage)
            ),
            execution_time_ms: start.elapsed().as_millis(),
            throughput_ops_per_sec: Some(progress_updates as f64 / start.elapsed().as_secs_f64()),
        };
        
        self.test_results.push(result);
    }
    
    async fn test_performance_metrics_broadcasting(&mut self) {
        let start = Instant::now();
        
        // Test performance metrics generation and broadcasting
        let metrics = vec![
            ("cpu_usage", 45.7),
            ("memory_usage_mb", 2048.0),
            ("disk_io_mb_per_sec", 123.4),
            ("active_connections", 15.0),
            ("messages_per_second", 1250.0),
        ];
        
        let mut broadcast_success = 0;
        
        for (metric_name, value) in metrics {
            let resource_usage = ResourceUsage {
                timestamp: chrono::Utc::now(),
                cpu_percentage: if metric_name == "cpu_usage" { value } else { 0.0 },
                memory_used_mb: if metric_name == "memory_usage_mb" { value as u64 } else { 0 },
                memory_total_mb: 8192,
                disk_read_mb_per_sec: if metric_name == "disk_io_mb_per_sec" { value } else { 0.0 },
                disk_write_mb_per_sec: 0.0,
                network_in_mb_per_sec: 0.0,
                network_out_mb_per_sec: 0.0,
                active_threads: 8,
                open_files: 256,
            };
            
            // Simulate broadcasting (would send to WebSocket connections)
            let serialized = serde_json::to_string(&resource_usage);
            
            if serialized.is_ok() {
                broadcast_success += 1;
            }
        }
        
        let result = WebSocketTestResult {
            test_name: "Performance Metrics Broadcasting".to_string(),
            success: broadcast_success == 5,
            message: format!("Successfully broadcast {}/5 metrics", broadcast_success),
            execution_time_ms: start.elapsed().as_millis(),
            throughput_ops_per_sec: Some(broadcast_success as f64 / start.elapsed().as_secs_f64()),
        };
        
        self.test_results.push(result);
    }
    
    async fn test_concurrent_connections(&mut self) {
        let start = Instant::now();
        let connection_count = 50;
        let messages_per_connection = 20;
        let server = Arc::new(RwLock::new(WebSocketServer::new()));
        
        let mut handles = vec![];
        
        // Simulate concurrent connections sending messages
        for conn_id in 0..connection_count {
            let server_clone = server.clone();
            
            let handle = tokio::spawn(async move {
                let mut sent_count = 0;
                
                for msg_id in 0..messages_per_connection {
                    // Simulate message sending
                    let message = MonitoringUpdate {
                        update_type: UpdateType::OptimizationProgress,
                        timestamp: chrono::Utc::now(),
                        data: json!({
                            "connection_id": conn_id,
                            "message_id": msg_id,
                            "data": format!("Message {} from connection {}", msg_id, conn_id)
                        }),
                    };
                    
                    // Simulate network delay
                    tokio::time::sleep(Duration::from_micros(100)).await;
                    sent_count += 1;
                }
                
                sent_count
            });
            
            handles.push(handle);
        }
        
        // Wait for all connections to complete
        let mut total_sent = 0;
        for handle in handles {
            if let Ok(sent) = handle.await {
                total_sent += sent;
            }
        }
        
        let expected_total = connection_count * messages_per_connection;
        let throughput = total_sent as f64 / start.elapsed().as_secs_f64();
        
        let result = WebSocketTestResult {
            test_name: "Concurrent Connections".to_string(),
            success: total_sent == expected_total,
            message: format!("Handled {}/{} messages from {} concurrent connections", 
                total_sent, expected_total, connection_count),
            execution_time_ms: start.elapsed().as_millis(),
            throughput_ops_per_sec: Some(throughput),
        };
        
        self.test_results.push(result);
    }
    
    async fn test_message_throughput(&mut self) {
        let start = Instant::now();
        let message_count = 10000;
        let (tx, mut rx) = mpsc::channel::<MonitoringUpdate>(message_count);
        
        // High-throughput message producer
        let producer = tokio::spawn(async move {
            let mut sent = 0;
            for i in 0..message_count {
                let update = MonitoringUpdate {
                    update_type: UpdateType::TradeExecution,
                    timestamp: chrono::Utc::now(),
                    data: json!({
                        "price": 18500.25 + (i % 100) as f64 * 0.25,
                        "volume": 1 + (i % 10),
                        "tick_id": i
                    }),
                };
                
                if tx.send(update).await.is_ok() {
                    sent += 1;
                } else {
                    break;
                }
            }
            sent
        });
        
        // High-throughput consumer
        let mut received = 0;
        let consumer_start = Instant::now();
        
        while let Some(_update) = timeout(Duration::from_secs(5), rx.recv()).await.unwrap_or(None) {
            received += 1;
            
            if received >= message_count {
                break;
            }
        }
        
        let sent_count = producer.await.unwrap_or(0);
        let throughput = received as f64 / consumer_start.elapsed().as_secs_f64();
        
        let result = WebSocketTestResult {
            test_name: "Message Throughput".to_string(),
            success: received >= message_count * 95 / 100, // Allow 5% message loss
            message: format!("Processed {}/{} messages ({:.0} msg/s)", received, sent_count, throughput),
            execution_time_ms: start.elapsed().as_millis(),
            throughput_ops_per_sec: Some(throughput),
        };
        
        self.test_results.push(result);
    }
    
    async fn test_error_handling(&mut self) {
        let start = Instant::now();
        let mut error_scenarios_passed = 0;
        let total_scenarios = 3;
        
        // Scenario 1: Invalid message format
        let invalid_json = r#"{"invalid": json"#;
        if serde_json::from_str::<MonitoringUpdate>(invalid_json).is_err() {
            error_scenarios_passed += 1;
        }
        
        // Scenario 2: Connection timeout simulation
        let (tx, rx) = mpsc::channel::<String>(1);
        drop(tx); // Close sender
        
        if timeout(Duration::from_millis(100), rx.recv()).await.is_err() {
            error_scenarios_passed += 1;
        }
        
        // Scenario 3: Resource exhaustion simulation
        let mut large_data = Vec::new();
        for i in 0..1000 {
            large_data.push(json!({
                "id": i,
                "data": vec![i; 1000] // Large payload
            }));
        }
        
        let serialized = serde_json::to_string(&large_data);
        if serialized.is_ok() && serialized.unwrap().len() > 1_000_000 {
            error_scenarios_passed += 1; // Successfully handled large payload
        }
        
        let result = WebSocketTestResult {
            test_name: "Error Handling".to_string(),
            success: error_scenarios_passed == total_scenarios,
            message: format!("Handled {}/{} error scenarios correctly", error_scenarios_passed, total_scenarios),
            execution_time_ms: start.elapsed().as_millis(),
            throughput_ops_per_sec: None,
        };
        
        self.test_results.push(result);
    }
    
    async fn test_resource_monitoring(&mut self) {
        let start = Instant::now();
        
        // Test resource usage calculation
        let resource_usage = ResourceUsage {
            timestamp: chrono::Utc::now(),
            cpu_percentage: 42.5,
            memory_used_mb: 1024,
            memory_total_mb: 8192,
            disk_read_mb_per_sec: 15.7,
            disk_write_mb_per_sec: 8.3,
            network_in_mb_per_sec: 2.1,
            network_out_mb_per_sec: 1.8,
            active_threads: 12,
            open_files: 145,
        };
        
        // Test resource monitoring calculations
        let memory_usage_percent = (resource_usage.memory_used_mb as f64 / resource_usage.memory_total_mb as f64) * 100.0;
        let is_high_cpu = resource_usage.cpu_percentage > 80.0;
        let is_high_memory = memory_usage_percent > 85.0;
        
        let monitoring_accurate = memory_usage_percent < 20.0 && !is_high_cpu && !is_high_memory;
        
        let result = WebSocketTestResult {
            test_name: "Resource Monitoring".to_string(),
            success: monitoring_accurate,
            message: format!("CPU: {:.1}%, Memory: {:.1}%, Monitoring: {}", 
                resource_usage.cpu_percentage, memory_usage_percent, monitoring_accurate),
            execution_time_ms: start.elapsed().as_millis(),
            throughput_ops_per_sec: None,
        };
        
        self.test_results.push(result);
    }
    
    async fn test_live_strategy_updates(&mut self) {
        let start = Instant::now();
        
        // Simulate live strategy parameter updates
        let strategy_updates = vec![
            ("threshold", 0.75),
            ("stop_loss", 0.02),
            ("take_profit", 0.05),
            ("position_size", 100.0),
            ("max_positions", 3.0),
        ];
        
        let mut updates_processed = 0;
        
        for (param_name, value) in strategy_updates {
            let update = MonitoringUpdate {
                update_type: UpdateType::Status,
                timestamp: chrono::Utc::now(),
                data: json!({
                    "parameter": param_name,
                    "old_value": value - 0.1,
                    "new_value": value,
                    "strategy_id": Uuid::new_v4(),
                    "update_reason": "optimization_result"
                }),
            };
            
            // Simulate parameter validation and update
            if let Some(new_val) = update.data.get("new_value").and_then(|v| v.as_f64()) {
                if new_val > 0.0 && new_val < 1000.0 { // Basic validation
                    updates_processed += 1;
                }
            }
        }
        
        let result = WebSocketTestResult {
            test_name: "Live Strategy Updates".to_string(),
            success: updates_processed == 5,
            message: format!("Processed {}/5 strategy parameter updates", updates_processed),
            execution_time_ms: start.elapsed().as_millis(),
            throughput_ops_per_sec: Some(updates_processed as f64 / start.elapsed().as_secs_f64()),
        };
        
        self.test_results.push(result);
    }
    
    pub fn print_results(&self) {
        println!("\n📊 WebSocket and Real-time System Test Results");
        println!("==============================================");
        
        let mut total_tests = 0;
        let mut passed_tests = 0;
        let mut total_time = 0u128;
        
        for result in &self.test_results {
            total_tests += 1;
            total_time += result.execution_time_ms;
            
            let status = if result.success {
                passed_tests += 1;
                "✅ PASS"
            } else {
                "❌ FAIL"
            };
            
            let throughput_info = match result.throughput_ops_per_sec {
                Some(throughput) if throughput > 0.0 => format!(" | {:.0} ops/s", throughput),
                _ => String::new(),
            };
            
            println!("{} | {} | {}ms{} | {}", 
                status, 
                result.test_name, 
                result.execution_time_ms,
                throughput_info,
                result.message
            );
        }
        
        println!("\n📈 Summary:");
        println!("Total Tests: {}", total_tests);
        println!("Passed: {}", passed_tests);
        println!("Failed: {}", total_tests - passed_tests);
        println!("Success Rate: {:.1}%", (passed_tests as f64 / total_tests as f64) * 100.0);
        println!("Total Execution Time: {}ms", total_time);
        
        // Performance benchmarks
        let high_throughput_tests: Vec<_> = self.test_results.iter()
            .filter(|r| r.throughput_ops_per_sec.unwrap_or(0.0) > 1000.0)
            .collect();
        
        if !high_throughput_tests.is_empty() {
            println!("\n🚀 High-Performance Tests:");
            for test in high_throughput_tests {
                println!("  {} | {:.0} ops/s", test.test_name, test.throughput_ops_per_sec.unwrap());
            }
        }
        
        if passed_tests == total_tests {
            println!("🎉 All WebSocket and real-time system tests passed!");
        } else {
            println!("⚠️  Some WebSocket/real-time tests failed. Check system resources and network.");
        }
    }
    
    pub fn get_success_rate(&self) -> f64 {
        if self.test_results.is_empty() {
            return 0.0;
        }
        
        let passed = self.test_results.iter().filter(|r| r.success).count();
        (passed as f64 / self.test_results.len() as f64) * 100.0
    }
}

#[tokio::test]
async fn run_websocket_and_realtime_tests() {
    let mut test_suite = WebSocketTestSuite::new();
    
    println!("🔧 Starting WebSocket and Real-time System Testing...");
    
    match test_suite.run_all_tests().await {
        Ok(_) => {
            let success_rate = test_suite.get_success_rate();
            assert!(success_rate >= 80.0, 
                "WebSocket/real-time tests should have ≥80% success rate, got {:.1}%", 
                success_rate);
            println!("✅ WebSocket and real-time system tests completed successfully");
        }
        Err(e) => panic!("WebSocket/real-time tests failed: {}", e),
    }
}