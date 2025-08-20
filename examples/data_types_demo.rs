//! Demonstration of the high-performance data types module
//! 
//! This example shows how to use the optimized data structures for
//! processing millions of tick records efficiently.

use strategy_lab::data::*;
use rust_decimal::Decimal;
use std::time::{SystemTime, Instant};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("🚀 High-Performance Futures Data Processing Demo");
    println!("================================================\n");
    
    // 1. Create sample tick data
    println!("📊 Creating sample tick data...");
    let sample_ticks = create_sample_data(10_000)?;
    println!("   ✓ Generated {} sample ticks", sample_ticks.len());
    
    // 2. Demonstrate different validation levels
    println!("\n🔍 Testing validation performance...");
    test_validation_levels(&sample_ticks)?;
    
    // 3. Demonstrate batch processing
    println!("\n⚡ Testing batch processing...");
    test_batch_processing(&sample_ticks)?;
    
    // 4. Demonstrate processed tick computation
    println!("\n🧮 Testing processed tick computation...");
    test_processed_ticks(&sample_ticks)?;
    
    // 5. Show memory efficiency
    println!("\n💾 Memory efficiency analysis...");
    analyze_memory_efficiency(&sample_ticks)?;
    
    // 6. Performance benchmark simulation
    println!("\n🏎️  Performance benchmark simulation...");
    simulate_target_performance()?;
    
    println!("\n✅ Demo completed successfully!");
    Ok(())
}

fn create_sample_data(count: usize) -> Result<Vec<TickData>, Box<dyn std::error::Error>> {
    let mut ticks = Vec::with_capacity(count);
    let base_timestamp = system_time_to_nanos(SystemTime::now());
    
    // Create realistic MNQ futures data
    let mut price = Decimal::from(17050); // Typical MNQ price
    
    for i in 0..count {
        // Simulate price movement with small random walks
        let price_change = match i % 10 {
            0..=3 => 0,      // No change
            4..=5 => 1,      // Up 1 tick (0.25 points)
            6..=7 => -1,     // Down 1 tick
            8 => 2,          // Up 2 ticks
            9 => -2,         // Down 2 ticks
            _ => 0,
        };
        price += Decimal::from(price_change);
        
        let level = if i % 5 == 0 { DataLevel::L2 } else { DataLevel::L1 };
        let mdt = match i % 6 {
            0 => MarketDataType::Trade,
            1 => MarketDataType::BidQuote,
            2 => MarketDataType::AskQuote,
            3 => MarketDataType::ImpliedBid,
            4 => MarketDataType::ImpliedAsk,
            _ => MarketDataType::Trade,
        };
        
        let volume = match mdt {
            MarketDataType::Trade => 1 + (i % 50) as i32, // Trade sizes 1-50
            _ => 10 + (i % 100) as i32, // Quote sizes 10-109
        };
        
        let timestamp = base_timestamp + (i as i64 * 100_000); // 100 microsecond intervals
        
        let mut tick = TickData::new(
            level,
            mdt,
            timestamp,
            price,
            volume,
            format!("{:02}{}", ((i / 1000) % 12) + 1, 23), // Rotating contract months
        );
        
        // Add L2 specific data
        if level == DataLevel::L2 {
            tick = tick.with_l2_data(
                match i % 3 {
                    0 => OrderBookOperation::Add,
                    1 => OrderBookOperation::Update,
                    _ => OrderBookOperation::Remove,
                },
                ((i % 10) + 1) as u8, // Depth levels 1-10
            );
            
            // Sometimes add market maker
            if i % 7 == 0 {
                tick = tick.with_market_maker(format!("MM{}", i % 5));
            }
        }
        
        ticks.push(tick);
    }
    
    Ok(ticks)
}

fn test_validation_levels(ticks: &[TickData]) -> Result<(), Box<dyn std::error::Error>> {
    let levels = [
        (ValidationLevel::None, "None (Maximum Performance)"),
        (ValidationLevel::Basic, "Basic (Essential Checks)"),
        (ValidationLevel::Standard, "Standard (Production)"),
        (ValidationLevel::Strict, "Strict (Full Audit)"),
    ];
    
    for (level, description) in levels {
        let start = Instant::now();
        let mut validator = TickDataValidator::new(level);
        
        let results = validator.validate_batch(ticks, 0);
        let duration = start.elapsed();
        
        let valid_count = results.iter().filter(|r| r.is_valid).count();
        let throughput = ticks.len() as f64 / duration.as_secs_f64();
        
        println!("   {} - {}", description, level as u8);
        println!("     ⏱️  Time: {:?}", duration);
        println!("     📈 Throughput: {:.0} ticks/sec", throughput);
        println!("     ✅ Valid: {}/{} ({:.1}%)", valid_count, ticks.len(), 
                (valid_count as f64 / ticks.len() as f64) * 100.0);
        
        if level == ValidationLevel::Strict {
            let metrics = validator.get_metrics();
            println!("     📊 L1/L2 split: {}/{}", metrics.l1_records, metrics.l2_records);
            println!("     🎯 Target met: {}", metrics.meets_performance_targets());
        }
    }
    
    Ok(())
}

fn test_batch_processing(ticks: &[TickData]) -> Result<(), Box<dyn std::error::Error>> {
    let mut validator = TickDataValidator::new_production();
    
    // Sequential processing
    let start = Instant::now();
    let sequential_results = validator.validate_batch(ticks, 0);
    let sequential_time = start.elapsed();
    
    // Parallel processing  
    let mut validator_parallel = TickDataValidator::new_high_throughput();
    let start = Instant::now();
    let parallel_results = validator_parallel.validate_batch_parallel(ticks, 0);
    let parallel_time = start.elapsed();
    
    let speedup = sequential_time.as_nanos() as f64 / parallel_time.as_nanos() as f64;
    
    println!("   📋 Sequential: {:?} ({:.0} ticks/sec)", 
             sequential_time, 
             ticks.len() as f64 / sequential_time.as_secs_f64());
    println!("   ⚡ Parallel: {:?} ({:.0} ticks/sec)", 
             parallel_time,
             ticks.len() as f64 / parallel_time.as_secs_f64());
    println!("   🚀 Speedup: {:.1}x", speedup);
    
    assert_eq!(sequential_results.len(), parallel_results.len());
    Ok(())
}

fn test_processed_ticks(ticks: &[TickData]) -> Result<(), Box<dyn std::error::Error>> {
    let mut processed_ticks = Vec::new();
    let mut prev_tick: Option<TickData> = None;
    
    let start = Instant::now();
    
    for tick in ticks.iter().take(1000) { // Process first 1000 for demo
        let processed = ProcessedTick::from_tick(tick.clone(), prev_tick.as_ref());
        processed_ticks.push(processed);
        prev_tick = Some(tick.clone());
    }
    
    let duration = start.elapsed();
    
    // Analyze processed tick statistics
    let avg_time_delta: f64 = processed_ticks.iter()
        .map(|pt| pt.time_delta_ns as f64)
        .sum::<f64>() / processed_ticks.len() as f64;
    
    let price_changes: Vec<i32> = processed_ticks.iter()
        .map(|pt| pt.price_delta_bps)
        .collect();
    
    let volatility = calculate_volatility(&price_changes);
    
    println!("   ⏱️  Processing time: {:?}", duration);
    println!("   📊 Average time delta: {:.2} μs", avg_time_delta / 1000.0);
    println!("   📈 Price volatility: {:.2} bps", volatility);
    
    Ok(())
}

fn calculate_volatility(price_changes: &[i32]) -> f64 {
    if price_changes.is_empty() {
        return 0.0;
    }
    
    let mean: f64 = price_changes.iter().map(|&x| x as f64).sum::<f64>() / price_changes.len() as f64;
    let variance: f64 = price_changes.iter()
        .map(|&x| {
            let diff = x as f64 - mean;
            diff * diff
        })
        .sum::<f64>() / price_changes.len() as f64;
    
    variance.sqrt()
}

fn analyze_memory_efficiency(ticks: &[TickData]) -> Result<(), Box<dyn std::error::Error>> {
    let total_memory: usize = ticks.iter().map(|t| t.memory_size()).sum();
    let avg_memory_per_tick = total_memory as f64 / ticks.len() as f64;
    
    // Estimate for 10M ticks
    let estimated_10m = (avg_memory_per_tick * 10_000_000.0) / (1024.0 * 1024.0 * 1024.0);
    
    println!("   📏 Average memory per tick: {:.1} bytes", avg_memory_per_tick);
    println!("   💾 Total sample memory: {:.2} MB", total_memory as f64 / (1024.0 * 1024.0));
    println!("   🎯 Estimated 10M ticks: {:.2} GB", estimated_10m);
    println!("   ✅ Within 32GB limit: {}", estimated_10m < 32.0);
    
    Ok(())
}

fn simulate_target_performance() -> Result<(), Box<dyn std::error::Error>> {
    println!("   🎯 Simulating 7M tick processing target...");
    
    // Create a smaller batch to simulate the performance
    let test_batch = 100_000; // 100k ticks for quick demo
    let sample_ticks = create_sample_data(test_batch)?;
    
    let mut validator = TickDataValidator::new_high_throughput();
    
    let start = Instant::now();
    let results = validator.validate_batch_parallel(&sample_ticks, 0);
    let duration = start.elapsed();
    
    let throughput = test_batch as f64 / duration.as_secs_f64();
    
    // Extrapolate to 7M
    let estimated_7m_time = 7_000_000.0 / throughput;
    let meets_target = estimated_7m_time < 120.0; // 2 minutes
    
    println!("   ⚡ {} ticks processed in {:?}", test_batch, duration);
    println!("   📈 Throughput: {:.0} ticks/sec", throughput);
    println!("   ⏰ Estimated 7M time: {:.1} seconds", estimated_7m_time);
    println!("   🎯 Meets <2min target: {}", meets_target);
    
    let valid_count = results.iter().filter(|r| r.is_valid).count();
    println!("   ✅ Success rate: {:.2}%", (valid_count as f64 / test_batch as f64) * 100.0);
    
    // Show final metrics
    let metrics = validator.get_metrics();
    println!("   📊 Final metrics:");
    println!("      - Memory efficiency: {:.1}%", metrics.memory_efficiency_pct);
    println!("      - Performance targets met: {}", metrics.meets_performance_targets());
    
    Ok(())
}