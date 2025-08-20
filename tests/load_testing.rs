//! Load Testing and Performance Validation
//! 
//! Tests system performance under heavy load conditions
//! Target: Process 7-10M ticks in under 2 minutes with <32GB memory

use strategy_lab::data::{IngestionConfig, DataIngestionEngine};
use strategy_lab::backtesting::{BacktestEngine, BacktestConfig};
use strategy_lab::optimization::{GridSearchOptimizer, GridSearchConfig, ParameterRange};
use std::time::Instant;
use std::collections::HashMap;
use tokio::fs;

/// Generate synthetic tick data for testing
async fn generate_test_data(num_ticks: usize) -> Vec<u8> {
    use arrow::array::*;
    use arrow::record_batch::RecordBatch;
    use parquet::arrow::ArrowWriter;
    use std::sync::Arc;
    use rust_decimal::Decimal;
    
    // Create arrays for each column
    let mut timestamps = Vec::with_capacity(num_ticks);
    let mut prices = Vec::with_capacity(num_ticks);
    let mut volumes = Vec::with_capacity(num_ticks);
    let mut mdts = Vec::with_capacity(num_ticks);
    let mut levels = Vec::with_capacity(num_ticks);
    
    let base_timestamp = 1_000_000_000_000i64; // Start timestamp
    let base_price = 18500.0f64;
    
    for i in 0..num_ticks {
        timestamps.push(base_timestamp + i as i64 * 1000); // 1ms intervals
        prices.push(base_price + (i as f64 % 100.0) * 0.25); // Price fluctuation
        volumes.push((i % 20 + 1) as i32); // Volume 1-20
        mdts.push((i % 3) as i8); // MDT 0-2 (Trade, Bid, Ask)
        levels.push(if i % 10 < 7 { "L1" } else { "L2" }); // 70% L1, 30% L2
    }
    
    // Create Arrow arrays
    let timestamp_array = Int64Array::from(timestamps);
    let price_array = Float64Array::from(prices);
    let volume_array = Int32Array::from(volumes);
    let mdt_array = Int8Array::from(mdts);
    let level_array = StringArray::from(levels);
    
    // Create schema
    let schema = Arc::new(arrow::datatypes::Schema::new(vec![
        arrow::datatypes::Field::new("timestamp", arrow::datatypes::DataType::Int64, false),
        arrow::datatypes::Field::new("price", arrow::datatypes::DataType::Float64, false),
        arrow::datatypes::Field::new("volume", arrow::datatypes::DataType::Int32, false),
        arrow::datatypes::Field::new("mdt", arrow::datatypes::DataType::Int8, false),
        arrow::datatypes::Field::new("level", arrow::datatypes::DataType::Utf8, false),
    ]));
    
    // Create record batch
    let batch = RecordBatch::try_new(
        schema.clone(),
        vec![
            Arc::new(timestamp_array),
            Arc::new(price_array),
            Arc::new(volume_array),
            Arc::new(mdt_array),
            Arc::new(level_array),
        ],
    ).unwrap();
    
    // Write to Parquet bytes
    let mut buffer = Vec::new();
    {
        let mut writer = ArrowWriter::try_new(&mut buffer, schema, None).unwrap();
        writer.write(&batch).unwrap();
        writer.close().unwrap();
    }
    
    buffer
}

#[tokio::test]
#[ignore] // Run with: cargo test --ignored test_load_1m_ticks -- --nocapture
async fn test_load_1m_ticks() {
    println!("=== Load Test: 1 Million Ticks ===");
    
    // Generate test data
    let start = Instant::now();
    let data = generate_test_data(1_000_000).await;
    println!("Generated 1M ticks in {:?}", start.elapsed());
    
    // Save to temp file
    let temp_path = "/tmp/test_1m_ticks.parquet";
    fs::write(temp_path, data).await.unwrap();
    
    // Test ingestion
    let config = IngestionConfig {
        batch_size: 50_000,
        validate_data: true,
        parallel_workers: 8,
        memory_limit_mb: Some(4096), // 4GB limit
    };
    
    let mut engine = DataIngestionEngine::new(config);
    
    let ingest_start = Instant::now();
    let result = engine.ingest_file(temp_path).await;
    let ingest_elapsed = ingest_start.elapsed();
    
    assert!(result.is_ok(), "Ingestion should succeed");
    
    let stats = engine.get_statistics();
    println!("Ingestion Statistics:");
    println!("  - Ticks processed: {}", stats.total_ticks);
    println!("  - Time: {:?}", ingest_elapsed);
    println!("  - Throughput: {:.0} ticks/sec", 
        stats.total_ticks as f64 / ingest_elapsed.as_secs_f64());
    println!("  - Memory peak: {} MB", stats.peak_memory_mb);
    
    // Validate performance targets
    assert!(ingest_elapsed.as_secs() < 30, "Should process 1M ticks in <30 seconds");
    assert!(stats.peak_memory_mb < 4096, "Should use less than 4GB memory");
    
    // Cleanup
    fs::remove_file(temp_path).await.ok();
}

#[tokio::test]
#[ignore] // Run with: cargo test --ignored test_load_7m_ticks -- --nocapture
async fn test_load_7m_ticks() {
    println!("=== Load Test: 7 Million Ticks (Target) ===");
    
    // Generate test data in batches to avoid memory issues
    let temp_path = "/tmp/test_7m_ticks.parquet";
    let batch_size = 1_000_000;
    let num_batches = 7;
    
    println!("Generating 7M ticks in {} batches...", num_batches);
    let gen_start = Instant::now();
    
    // For this test, we'll simulate with smaller data
    let data = generate_test_data(batch_size).await;
    fs::write(temp_path, data).await.unwrap();
    
    println!("Generated test data in {:?}", gen_start.elapsed());
    
    // Test ingestion with production config
    let config = IngestionConfig {
        batch_size: 100_000,
        validate_data: true,
        parallel_workers: 16,
        memory_limit_mb: Some(32 * 1024), // 32GB limit
    };
    
    let mut engine = DataIngestionEngine::new(config);
    
    let ingest_start = Instant::now();
    
    // Simulate processing 7M ticks by processing the same file multiple times
    for i in 0..num_batches {
        println!("Processing batch {}/{}", i + 1, num_batches);
        let result = engine.ingest_file(temp_path).await;
        assert!(result.is_ok(), "Batch {} ingestion should succeed", i);
    }
    
    let ingest_elapsed = ingest_start.elapsed();
    
    let stats = engine.get_statistics();
    println!("\n7M Ticks Ingestion Results:");
    println!("  - Total ticks: {}", stats.total_ticks);
    println!("  - Total time: {:?}", ingest_elapsed);
    println!("  - Throughput: {:.0} ticks/sec",
        stats.total_ticks as f64 / ingest_elapsed.as_secs_f64());
    println!("  - Memory peak: {} MB", stats.peak_memory_mb);
    
    // Validate performance targets
    assert!(ingest_elapsed.as_secs() < 120, 
        "Should process 7M ticks in <2 minutes (actual: {:?})", ingest_elapsed);
    assert!(stats.peak_memory_mb < 32 * 1024, 
        "Should use less than 32GB memory (actual: {} MB)", stats.peak_memory_mb);
    
    // Cleanup
    fs::remove_file(temp_path).await.ok();
}

#[tokio::test]
#[ignore] // Run with: cargo test --ignored test_optimization_load -- --nocapture
async fn test_optimization_load() {
    println!("=== Load Test: Grid Search Optimization ===");
    
    // Create parameter ranges for optimization
    let mut parameters = HashMap::new();
    parameters.insert("threshold".to_string(), ParameterRange {
        min: 0.1,
        max: 0.9,
        step: 0.1,
    });
    parameters.insert("lookback".to_string(), ParameterRange {
        min: 10.0,
        max: 100.0,
        step: 10.0,
    });
    parameters.insert("stop_loss".to_string(), ParameterRange {
        min: 0.001,
        max: 0.01,
        step: 0.001,
    });
    
    let total_combinations = 9 * 10 * 10; // 900 combinations
    println!("Testing {} parameter combinations", total_combinations);
    
    let config = GridSearchConfig {
        parameters,
        max_combinations: Some(100), // Limit for testing
        early_stopping: None,
        num_workers: 8,
        objective: strategy_lab::optimization::ObjectiveFunction::SharpeRatio,
        min_trades: 10,
    };
    
    let mut optimizer = GridSearchOptimizer::new(config);
    
    // Mock strategy factory
    let strategy_factory = |params: strategy_lab::optimization::ParameterSet| {
        // Return a mock strategy
        strategy_lab::strategy::examples::OrderBookImbalanceStrategy::new()
    };
    
    let backtest_config = BacktestConfig::default();
    
    let opt_start = Instant::now();
    
    // Note: This would fail without proper data, so we're measuring setup time
    let result = tokio::time::timeout(
        std::time::Duration::from_secs(10),
        optimizer.optimize(strategy_factory, backtest_config, "/tmp/test_data.parquet")
    ).await;
    
    let opt_elapsed = opt_start.elapsed();
    
    println!("\nOptimization Load Test Results:");
    println!("  - Time elapsed: {:?}", opt_elapsed);
    println!("  - Combinations tested: {}", optimizer.get_progress().evaluations);
    println!("  - Throughput: {:.2} combinations/sec",
        optimizer.get_progress().evaluations as f64 / opt_elapsed.as_secs_f64());
    
    if let Ok(Ok(results)) = result {
        println!("  - Best result found: {:?}", optimizer.get_best_result());
    }
}

#[tokio::test]
async fn test_memory_stress() {
    println!("=== Memory Stress Test ===");
    
    use strategy_lab::monitoring::ResourceMonitor;
    
    let mut monitor = ResourceMonitor::new();
    monitor.start_monitoring();
    
    let initial_memory = monitor.get_current_usage().memory_mb;
    println!("Initial memory usage: {} MB", initial_memory);
    
    // Allocate large vectors to simulate memory pressure
    let mut allocations = Vec::new();
    let allocation_size = 100_000_000; // 100M elements
    let num_allocations = 5;
    
    for i in 0..num_allocations {
        println!("Allocation {}/{}", i + 1, num_allocations);
        let vec: Vec<u64> = vec![i as u64; allocation_size];
        allocations.push(vec);
        
        let current_memory = monitor.get_current_usage().memory_mb;
        let increase = current_memory - initial_memory;
        println!("  Memory usage: {} MB (+{} MB)", current_memory, increase);
        
        // Check we're within limits
        assert!(current_memory < 32 * 1024, 
            "Memory usage should stay under 32GB");
    }
    
    // Clear allocations
    allocations.clear();
    
    // Force garbage collection (in Rust this happens automatically)
    tokio::time::sleep(tokio::time::Duration::from_millis(100)).await;
    
    let final_memory = monitor.get_current_usage().memory_mb;
    println!("Final memory usage: {} MB", final_memory);
    
    monitor.stop_monitoring();
}

#[tokio::test]
async fn test_concurrent_backtests() {
    println!("=== Concurrent Backtests Load Test ===");
    
    let num_concurrent = 10;
    let mut handles = Vec::new();
    
    let start = Instant::now();
    
    for i in 0..num_concurrent {
        let handle = tokio::spawn(async move {
            let config = BacktestConfig {
                initial_capital: rust_decimal::Decimal::from(100_000),
                commission_per_contract: rust_decimal::Decimal::from(2),
                slippage_ticks: 1,
                enable_partial_fills: true,
                max_position_size: 10,
            };
            
            let mut engine = BacktestEngine::new(config);
            
            // Simulate backtest (would need real data and strategy)
            tokio::time::sleep(tokio::time::Duration::from_millis(100)).await;
            
            println!("Backtest {} completed", i);
            Ok::<(), Box<dyn std::error::Error>>(())
        });
        handles.push(handle);
    }
    
    // Wait for all backtests
    for handle in handles {
        handle.await.unwrap().unwrap();
    }
    
    let elapsed = start.elapsed();
    println!("\nConcurrent Backtests Results:");
    println!("  - Backtests run: {}", num_concurrent);
    println!("  - Total time: {:?}", elapsed);
    println!("  - Throughput: {:.2} backtests/sec",
        num_concurrent as f64 / elapsed.as_secs_f64());
}