//! High-performance data ingestion benchmarks
//! 
//! These benchmarks validate that the system can process 7-10M tick records
//! in under 2 minutes while keeping memory usage under 32GB.

use criterion::{black_box, criterion_group, criterion_main, Criterion, BenchmarkId};
use strategy_lab::data::*;
use rust_decimal::Decimal;
use std::time::SystemTime;

/// Generate synthetic tick data for benchmarking
fn generate_test_ticks(count: usize) -> Vec<TickData> {
    let mut ticks = Vec::with_capacity(count);
    let base_timestamp = system_time_to_nanos(SystemTime::now());
    
    for i in 0..count {
        let tick = TickData::new(
            if i % 4 == 0 { DataLevel::L2 } else { DataLevel::L1 },
            if i % 3 == 0 { MarketDataType::Trade } else { MarketDataType::BidQuote },
            base_timestamp + (i as i64 * 1_000_000), // 1ms intervals
            Decimal::from(17000 + (i % 100) as i32), // Price around 17000-17100
            100 + (i % 50) as i32, // Volume 100-150
            format!("{:02}{}", (i % 12) + 1, (i % 4) + 20), // Contract months
        );
        
        ticks.push(if i % 4 == 0 {
            // Add L2 data for every 4th tick
            tick.with_l2_data(OrderBookOperation::Add, (i % 10) as u8 + 1)
        } else {
            tick
        });
    }
    
    ticks
}

/// Benchmark individual tick validation
fn benchmark_single_tick_validation(c: &mut Criterion) {
    let tick = TickData::new(
        DataLevel::L1,
        MarketDataType::Trade,
        system_time_to_nanos(SystemTime::now()),
        Decimal::from(17050),
        150,
        "0623".to_string(),
    );
    
    let mut group = c.benchmark_group("single_tick_validation");
    
    for level in [ValidationLevel::None, ValidationLevel::Basic, ValidationLevel::Standard, ValidationLevel::Strict] {
        group.bench_with_input(
            BenchmarkId::new("validation_level", format!("{:?}", level)),
            &level,
            |b, &level| {
                let mut validator = TickDataValidator::new(level);
                b.iter(|| {
                    black_box(validator.validate_tick(black_box(&tick), 0))
                });
            },
        );
    }
    
    group.finish();
}

/// Benchmark batch validation with different sizes
fn benchmark_batch_validation(c: &mut Criterion) {
    let mut group = c.benchmark_group("batch_validation");
    
    for batch_size in [1_000, 10_000, 100_000, 1_000_000] {
        let ticks = generate_test_ticks(batch_size);
        
        group.throughput(criterion::Throughput::Elements(batch_size as u64));
        group.bench_with_input(
            BenchmarkId::new("sequential", batch_size),
            &ticks,
            |b, ticks| {
                b.iter(|| {
                    let mut validator = TickDataValidator::new_production();
                    black_box(validator.validate_batch(black_box(ticks), 0))
                });
            },
        );
        
        group.bench_with_input(
            BenchmarkId::new("parallel", batch_size),
            &ticks,
            |b, ticks| {
                b.iter(|| {
                    let mut validator = TickDataValidator::new_high_throughput();
                    black_box(validator.validate_batch_parallel(black_box(ticks), 0))
                });
            },
        );
    }
    
    group.finish();
}

/// Benchmark memory efficiency and allocation patterns
fn benchmark_memory_efficiency(c: &mut Criterion) {
    let mut group = c.benchmark_group("memory_efficiency");
    
    // Test with different tick sizes to measure memory overhead
    for tick_count in [100_000, 500_000, 1_000_000] {
        let ticks = generate_test_ticks(tick_count);
        
        group.bench_with_input(
            BenchmarkId::new("memory_footprint", tick_count),
            &ticks,
            |b, ticks| {
                b.iter(|| {
                    let total_memory: usize = ticks.iter()
                        .map(|tick| black_box(tick.memory_size()))
                        .sum();
                    black_box(total_memory)
                });
            },
        );
    }
    
    group.finish();
}

/// Benchmark the fast validation path
fn benchmark_fast_validation(c: &mut Criterion) {
    let ticks = generate_test_ticks(1_000_000);
    
    let mut group = c.benchmark_group("validation_comparison");
    
    group.throughput(criterion::Throughput::Elements(1_000_000));
    
    group.bench_function("fast_validate", |b| {
        b.iter(|| {
            let valid_count: usize = ticks.iter()
                .map(|tick| if fast_validate_tick(black_box(tick)) { 1 } else { 0 })
                .sum();
            black_box(valid_count)
        });
    });
    
    group.bench_function("full_validate", |b| {
        b.iter(|| {
            let mut validator = TickDataValidator::new_high_throughput();
            let results = validator.validate_batch(black_box(&ticks), 0);
            let valid_count = results.iter().filter(|r| r.is_valid).count();
            black_box(valid_count)
        });
    });
    
    group.finish();
}

/// Benchmark ProcessedTick creation and computation
fn benchmark_processed_tick_creation(c: &mut Criterion) {
    let mut group = c.benchmark_group("processed_tick");
    
    let base_tick = TickData::new(
        DataLevel::L1,
        MarketDataType::Trade,
        system_time_to_nanos(SystemTime::now()),
        Decimal::from(17050),
        150,
        "0623".to_string(),
    );
    
    let prev_tick = TickData::new(
        DataLevel::L1,
        MarketDataType::Trade,
        system_time_to_nanos(SystemTime::now()) - 1_000_000, // 1ms earlier
        Decimal::from(17049),
        140,
        "0623".to_string(),
    );
    
    group.bench_function("create_processed_tick", |b| {
        b.iter(|| {
            black_box(ProcessedTick::from_tick(
                black_box(base_tick.clone()),
                Some(black_box(&prev_tick))
            ))
        });
    });
    
    group.finish();
}

/// Benchmark target: 7-10M records in under 2 minutes
fn benchmark_target_performance(c: &mut Criterion) {
    // Generate 7M records (minimum target)
    let ticks = generate_test_ticks(7_000_000);
    
    let mut group = c.benchmark_group("target_performance");
    group.sample_size(10); // Reduce sample size for large benchmarks
    group.measurement_time(std::time::Duration::from_secs(150)); // 2.5 minute timeout
    
    group.bench_function("7M_records_validation", |b| {
        b.iter(|| {
            let mut validator = TickDataValidator::new_high_throughput();
            let results = validator.validate_batch_parallel(black_box(&ticks), 0);
            let performance = validator.meets_performance_requirements();
            black_box((results.len(), performance))
        });
    });
    
    group.finish();
}

criterion_group!(
    benches,
    benchmark_single_tick_validation,
    benchmark_batch_validation,
    benchmark_memory_efficiency,
    benchmark_fast_validation,
    benchmark_processed_tick_creation,
    benchmark_target_performance
);

criterion_main!(benches);