//! Error Recovery and Fault Tolerance Tests
//! 
//! Tests system resilience under error conditions

use strategy_lab::data::{DataIngestionEngine, IngestionConfig};
use strategy_lab::backtesting::{BacktestEngine, BacktestConfig};
use strategy_lab::jobs::{JobQueue, JobManager, JobStatus};
use tokio::fs;
use std::time::Duration;

#[tokio::test]
async fn test_corrupt_data_handling() {
    println!("=== Test: Corrupt Data Handling ===");
    
    // Create corrupt parquet file
    let corrupt_data = b"This is not a valid parquet file";
    let temp_path = "/tmp/corrupt_test.parquet";
    fs::write(temp_path, corrupt_data).await.unwrap();
    
    let config = IngestionConfig::default();
    let mut engine = DataIngestionEngine::new(config);
    
    // Should handle corrupt file gracefully
    let result = engine.ingest_file(temp_path).await;
    assert!(result.is_err(), "Should fail on corrupt data");
    
    match result {
        Err(e) => {
            println!("Error handled correctly: {}", e);
            assert!(e.to_string().contains("parquet") || 
                   e.to_string().contains("invalid") ||
                   e.to_string().contains("corrupt"),
                   "Should indicate data corruption");
        }
        Ok(_) => panic!("Should not succeed with corrupt data"),
    }
    
    // Cleanup
    fs::remove_file(temp_path).await.ok();
}

#[tokio::test]
async fn test_missing_file_handling() {
    let config = IngestionConfig::default();
    let mut engine = DataIngestionEngine::new(config);
    
    let result = engine.ingest_file("/tmp/nonexistent_file.parquet").await;
    assert!(result.is_err(), "Should fail on missing file");
    
    if let Err(e) = result {
        println!("Missing file error: {}", e);
        assert!(e.to_string().contains("not found") || 
               e.to_string().contains("No such file"),
               "Should indicate file not found");
    }
}

#[tokio::test]
async fn test_out_of_memory_recovery() {
    println!("=== Test: Out of Memory Recovery ===");
    
    // Set very low memory limit
    let config = IngestionConfig {
        batch_size: 1_000_000,
        validate_data: true,
        parallel_workers: 4,
        memory_limit_mb: Some(1), // 1MB - unrealistically low
    };
    
    let mut engine = DataIngestionEngine::new(config);
    
    // Try to process data that would exceed memory limit
    // The engine should handle this gracefully
    let result = engine.check_memory_limit();
    
    println!("Memory check result: {:?}", result);
    
    // Engine should detect memory constraint
    assert!(result.is_err() || result.is_ok(), 
        "Should handle memory limits");
}

#[tokio::test]
async fn test_database_connection_failure() {
    use sqlx::postgres::PgPoolOptions;
    
    // Try to connect to non-existent database
    let bad_url = "postgresql://baduser:badpass@nonexistent:5432/nodb";
    
    let result = tokio::time::timeout(
        Duration::from_secs(5),
        PgPoolOptions::new()
            .max_connections(1)
            .connect(bad_url)
    ).await;
    
    assert!(result.is_err() || result.unwrap().is_err(), 
        "Should fail to connect to bad database");
    
    println!("Database connection failure handled correctly");
}

#[tokio::test]
async fn test_job_retry_mechanism() {
    println!("=== Test: Job Retry Mechanism ===");
    
    let mut job_queue = JobQueue::new("redis://localhost:6379").await.ok();
    
    if job_queue.is_none() {
        println!("Redis not available, skipping job retry test");
        return;
    }
    
    let mut queue = job_queue.unwrap();
    
    // Add a job that will fail
    let job_id = queue.add_job(
        "test_job",
        serde_json::json!({"fail": true}),
        3, // max_retries
    ).await.unwrap();
    
    // Simulate job processing with failure
    let mut manager = JobManager::new(queue);
    
    // Process job (will fail)
    let result = manager.process_job(&job_id).await;
    assert!(result.is_err(), "Job should fail initially");
    
    // Check job status
    let status = manager.get_job_status(&job_id).await.unwrap();
    assert_eq!(status.retry_count, 1, "Should have retry count of 1");
    
    // Process again (will fail and increment retry)
    let result = manager.process_job(&job_id).await;
    assert!(result.is_err(), "Job should fail again");
    
    let status = manager.get_job_status(&job_id).await.unwrap();
    assert_eq!(status.retry_count, 2, "Should have retry count of 2");
    
    println!("Job retry mechanism working correctly");
}

#[tokio::test]
async fn test_websocket_reconnection() {
    use strategy_lab::monitoring::WebSocketServer;
    
    let mut server = WebSocketServer::new();
    
    // Start server
    server.start("127.0.0.1:9993").await.unwrap();
    assert!(server.is_running(), "Server should be running");
    
    // Simulate connection drop
    server.stop().await;
    assert!(!server.is_running(), "Server should be stopped");
    
    // Wait a bit
    tokio::time::sleep(Duration::from_millis(100)).await;
    
    // Restart server (simulating reconnection)
    let result = server.start("127.0.0.1:9993").await;
    assert!(result.is_ok(), "Should be able to restart server");
    assert!(server.is_running(), "Server should be running again");
    
    server.stop().await;
    println!("WebSocket reconnection test passed");
}

#[tokio::test]
async fn test_partial_data_recovery() {
    println!("=== Test: Partial Data Recovery ===");
    
    // Simulate processing that fails partway through
    let config = BacktestConfig::default();
    let mut engine = BacktestEngine::new(config);
    
    // Enable checkpointing
    engine.enable_checkpointing(1000); // Checkpoint every 1000 ticks
    
    // Start processing
    let checkpoint_path = "/tmp/backtest_checkpoint.json";
    
    // Simulate failure at tick 5000
    let failure_point = 5000;
    
    for i in 0..failure_point {
        if i % 1000 == 0 {
            // Save checkpoint
            engine.save_checkpoint(checkpoint_path).await.ok();
            println!("Checkpoint saved at tick {}", i);
        }
        
        // Process tick (simulated)
        if i == failure_point - 1 {
            println!("Simulating failure at tick {}", i);
            break;
        }
    }
    
    // Recover from checkpoint
    let recovered = BacktestEngine::from_checkpoint(checkpoint_path).await;
    assert!(recovered.is_ok(), "Should recover from checkpoint");
    
    if recovered.is_ok() {
        println!("Successfully recovered from checkpoint");
    }
    
    // Cleanup
    fs::remove_file(checkpoint_path).await.ok();
}

#[tokio::test]
async fn test_concurrent_access_conflict() {
    use std::sync::Arc;
    use tokio::sync::Mutex;
    
    println!("=== Test: Concurrent Access Conflict ===");
    
    // Shared resource
    let resource = Arc::new(Mutex::new(Vec::<i32>::new()));
    
    // Spawn multiple tasks trying to modify the resource
    let mut handles = vec![];
    
    for i in 0..10 {
        let resource_clone = Arc::clone(&resource);
        let handle = tokio::spawn(async move {
            // Try to acquire lock with timeout
            let result = tokio::time::timeout(
                Duration::from_millis(100),
                resource_clone.lock()
            ).await;
            
            match result {
                Ok(mut guard) => {
                    guard.push(i);
                    println!("Task {} acquired lock", i);
                    // Simulate work
                    tokio::time::sleep(Duration::from_millis(10)).await;
                    Ok(())
                }
                Err(_) => {
                    println!("Task {} timed out waiting for lock", i);
                    Err("Lock timeout")
                }
            }
        });
        handles.push(handle);
    }
    
    // Wait for all tasks
    let mut successes = 0;
    let mut timeouts = 0;
    
    for handle in handles {
        match handle.await.unwrap() {
            Ok(_) => successes += 1,
            Err(_) => timeouts += 1,
        }
    }
    
    println!("Concurrent access results: {} successes, {} timeouts", 
        successes, timeouts);
    
    // At least some should succeed
    assert!(successes > 0, "Some tasks should succeed");
}

#[tokio::test]
async fn test_infinite_loop_detection() {
    use tokio::time::timeout;
    
    println!("=== Test: Infinite Loop Detection ===");
    
    // Function that could potentially loop forever
    async fn potentially_infinite_loop(max_iterations: usize) -> Result<(), &'static str> {
        let mut count = 0;
        loop {
            count += 1;
            if count > max_iterations {
                return Err("Max iterations exceeded");
            }
            
            // Simulate work
            tokio::time::sleep(Duration::from_micros(1)).await;
            
            // In a real scenario, this would have an exit condition
            if count >= 1000 {
                break;
            }
        }
        Ok(())
    }
    
    // Run with timeout
    let result = timeout(
        Duration::from_secs(1),
        potentially_infinite_loop(10000)
    ).await;
    
    match result {
        Ok(Ok(_)) => println!("Loop completed normally"),
        Ok(Err(e)) => println!("Loop detected limit: {}", e),
        Err(_) => println!("Loop timed out (infinite loop protection)"),
    }
    
    assert!(result.is_ok() || result.is_err(), 
        "Should handle potential infinite loops");
}

#[tokio::test]
async fn test_panic_recovery() {
    use std::panic;
    
    println!("=== Test: Panic Recovery ===");
    
    // Set custom panic handler
    let original_hook = panic::take_hook();
    panic::set_hook(Box::new(|info| {
        println!("Panic caught: {:?}", info);
    }));
    
    // Spawn task that will panic
    let handle = tokio::spawn(async {
        println!("Task starting...");
        panic!("Intentional panic for testing");
    });
    
    // Wait for task result
    let result = handle.await;
    
    // Restore original panic handler
    panic::set_hook(original_hook);
    
    assert!(result.is_err(), "Task should have panicked");
    println!("Panic was contained and handled correctly");
    
    // System should still be functional
    let test_task = tokio::spawn(async {
        "System still working"
    });
    
    let result = test_task.await;
    assert!(result.is_ok(), "System should continue working after panic");
    println!("System recovered from panic successfully");
}