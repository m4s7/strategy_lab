use criterion::{black_box, criterion_group, criterion_main, Criterion, BenchmarkId, Throughput};
use strategy_lab::data::types::{TickData, MarketDataType, DataLevel, ValidationLevel};
use strategy_lab::market::order_book::{OrderBook, OrderBookReconstructor};
use strategy_lab::strategy::examples::BidAskBounceStrategy;
use strategy_lab::strategy::traits::Strategy;
use strategy_lab::statistics::StatisticalAnalyzer;
use rust_decimal::Decimal;
use std::str::FromStr;
use std::collections::HashMap;
use std::time::{SystemTime, UNIX_EPOCH};

fn generate_test_ticks(count: usize) -> Vec<TickData> {
    let mut ticks = Vec::with_capacity(count);
    let base_price = 4500.0;
    let mut current_price = base_price;
    let start_time = SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_nanos() as i64;
    
    for i in 0..count {
        // Simulate realistic price movement
        let price_change = (i as f64 * 0.01).sin() * 0.25; // Small oscillations
        current_price = base_price + price_change;
        
        let tick = TickData::new(
            if i % 10 == 0 { DataLevel::L2 } else { DataLevel::L1 },
            if i % 3 == 0 { MarketDataType::Trade } else { MarketDataType::BidQuote },
            start_time + (i as i64 * 1_000_000), // 1ms intervals
            Decimal::from_f64(current_price).unwrap_or(Decimal::from(4500)),
            10 + (i % 20) as i32, // Volume between 10-30
            "0624".to_string(),
        );
        
        ticks.push(tick);
    }
    
    ticks
}

fn bench_tick_validation(c: &mut Criterion) {
    let mut group = c.benchmark_group("tick_validation");
    
    for size in [1000, 10000, 100000].iter() {
        let ticks = generate_test_ticks(*size);
        
        group.throughput(Throughput::Elements(*size as u64));
        group.bench_with_input(
            BenchmarkId::new("basic_validation", size),
            size,
            |b, _| {
                b.iter(|| {
                    for tick in &ticks {
                        let _result = strategy_lab::data::types::validation::validate_tick(
                            black_box(tick), 
                            ValidationLevel::Basic
                        );
                    }
                })
            },
        );
        
        group.bench_with_input(
            BenchmarkId::new("strict_validation", size),
            size,
            |b, _| {
                b.iter(|| {
                    for tick in &ticks {
                        let _result = strategy_lab::data::types::validation::validate_tick(
                            black_box(tick), 
                            ValidationLevel::Strict
                        );
                    }
                })
            },
        );
    }
    
    group.finish();
}

fn bench_order_book_reconstruction(c: &mut Criterion) {
    let mut group = c.benchmark_group("order_book_reconstruction");
    
    for size in [1000, 10000, 50000].iter() {
        let ticks = generate_test_ticks(*size);
        
        group.throughput(Throughput::Elements(*size as u64));
        group.bench_with_input(
            BenchmarkId::new("reconstruct_order_book", size),
            size,
            |b, _| {
                b.iter(|| {
                    let mut book = OrderBook::new("MNQZ24".to_string());
                    let mut reconstructor = OrderBookReconstructor::new();
                    
                    for tick in &ticks {
                        let _result = reconstructor.process_tick(black_box(tick), &mut book);
                    }
                    
                    black_box(book);
                })
            },
        );
    }
    
    group.finish();
}

fn bench_strategy_signal_generation(c: &mut Criterion) {
    let mut group = c.benchmark_group("strategy_signals");
    
    // Set up test data
    let ticks = generate_test_ticks(1000);
    let mut book = OrderBook::new("MNQZ24".to_string());
    book.add_bid_level(Decimal::from_str("4500.00").unwrap(), 100, 1000);
    book.add_ask_level(Decimal::from_str("4500.25").unwrap(), 80, 1000);
    let snapshot = book.snapshot();
    
    let mut strategy = BidAskBounceStrategy::new();
    let mut params = HashMap::new();
    params.insert("bounce_threshold".to_string(), 0.3);
    params.insert("volume_threshold".to_string(), 50.0);
    strategy.set_parameters(params);
    
    group.bench_function("bid_ask_bounce_strategy", |b| {
        b.iter(|| {
            for tick in &ticks {
                let _signal = strategy.generate_signal(black_box(tick), black_box(&snapshot));
            }
        })
    });
    
    group.finish();
}

fn bench_statistical_analysis(c: &mut Criterion) {
    let mut group = c.benchmark_group("statistical_analysis");
    
    let analyzer = StatisticalAnalyzer::new();
    
    for size in [1000, 10000, 100000].iter() {
        let returns: Vec<f64> = (0..*size)
            .map(|i| (i as f64 * 0.01).sin() * 0.02) // Simulated returns
            .collect();
        
        group.throughput(Throughput::Elements(*size as u64));
        
        group.bench_with_input(
            BenchmarkId::new("mean_calculation", size),
            &returns,
            |b, data| {
                b.iter(|| {
                    let _mean = analyzer.mean(black_box(data));
                })
            },
        );
        
        group.bench_with_input(
            BenchmarkId::new("standard_deviation", size),
            &returns,
            |b, data| {
                b.iter(|| {
                    let _std = analyzer.standard_deviation(black_box(data));
                })
            },
        );
        
        group.bench_with_input(
            BenchmarkId::new("sharpe_ratio", size),
            &returns,
            |b, data| {
                b.iter(|| {
                    let _sharpe = analyzer.sharpe_ratio(black_box(data), 0.02);
                })
            },
        );
        
        if *size <= 10000 { // Limit expensive operations
            group.bench_with_input(
                BenchmarkId::new("value_at_risk", size),
                &returns,
                |b, data| {
                    b.iter(|| {
                        let _var = analyzer.value_at_risk(black_box(data), 0.95);
                    })
                },
            );
        }
    }
    
    group.finish();
}

fn bench_order_book_operations(c: &mut Criterion) {
    let mut group = c.benchmark_group("order_book_operations");
    
    group.bench_function("add_remove_levels", |b| {
        b.iter(|| {
            let mut book = OrderBook::new("MNQZ24".to_string());
            
            // Add levels
            for i in 0..100 {
                let price = Decimal::from_str(&format!("4500.{:02}", i)).unwrap();
                book.add_bid_level(price, 10 + i, 1000 + i as i64);
                book.add_ask_level(price + Decimal::from_str("0.25").unwrap(), 8 + i, 1000 + i as i64);
            }
            
            // Update levels
            for i in 0..50 {
                let price = Decimal::from_str(&format!("4500.{:02}", i)).unwrap();
                book.update_bid_level(price, 20 + i, 2000 + i as i64);
            }
            
            // Remove levels
            for i in 50..100 {
                let price = Decimal::from_str(&format!("4500.{:02}", i)).unwrap();
                book.remove_bid_level(price, 3000 + i as i64);
                book.remove_ask_level(price + Decimal::from_str("0.25").unwrap(), 3000 + i as i64);
            }
            
            black_box(book);
        })
    });
    
    group.bench_function("book_snapshot", |b| {
        let mut book = OrderBook::new("MNQZ24".to_string());
        
        // Populate book
        for i in 0..50 {
            let bid_price = Decimal::from_str(&format!("4499.{:02}", 99 - i)).unwrap();
            let ask_price = Decimal::from_str(&format!("4500.{:02}", i)).unwrap();
            book.add_bid_level(bid_price, 10 + i, 1000 + i as i64);
            book.add_ask_level(ask_price, 8 + i, 1000 + i as i64);
        }
        
        b.iter(|| {
            let _snapshot = book.snapshot();
        })
    });
    
    group.finish();
}

fn bench_memory_usage(c: &mut Criterion) {
    let mut group = c.benchmark_group("memory_usage");
    
    group.bench_function("large_tick_vector", |b| {
        b.iter(|| {
            let ticks = generate_test_ticks(1_000_000);
            black_box(ticks);
        })
    });
    
    group.bench_function("deep_order_book", |b| {
        b.iter(|| {
            let mut book = OrderBook::new("MNQZ24".to_string());
            
            // Create deep order book (1000 levels each side)
            for i in 0..1000 {
                let bid_price = Decimal::from_str(&format!("4499.{:03}", 999 - i)).unwrap();
                let ask_price = Decimal::from_str(&format!("4500.{:03}", i)).unwrap();
                book.add_bid_level(bid_price, 10 + (i % 100), 1000 + i as i64);
                book.add_ask_level(ask_price, 8 + (i % 100), 1000 + i as i64);
            }
            
            black_box(book);
        })
    });
    
    group.finish();
}

fn bench_concurrent_operations(c: &mut Criterion) {
    let mut group = c.benchmark_group("concurrent_operations");
    
    group.bench_function("parallel_tick_validation", |b| {
        use rayon::prelude::*;
        
        let ticks = generate_test_ticks(10000);
        
        b.iter(|| {
            let results: Vec<_> = ticks
                .par_iter()
                .map(|tick| {
                    strategy_lab::data::types::validation::validate_tick(
                        tick, 
                        ValidationLevel::Basic
                    )
                })
                .collect();
            
            black_box(results);
        })
    });
    
    group.bench_function("parallel_statistical_analysis", |b| {
        use rayon::prelude::*;
        
        let analyzer = StatisticalAnalyzer::new();
        let data_chunks: Vec<Vec<f64>> = (0..100)
            .map(|chunk| {
                (0..1000)
                    .map(|i| ((chunk * 1000 + i) as f64 * 0.001).sin() * 0.02)
                    .collect()
            })
            .collect();
        
        b.iter(|| {
            let results: Vec<_> = data_chunks
                .par_iter()
                .map(|chunk| {
                    (
                        analyzer.mean(chunk),
                        analyzer.standard_deviation(chunk),
                        analyzer.sharpe_ratio(chunk, 0.02),
                    )
                })
                .collect();
            
            black_box(results);
        })
    });
    
    group.finish();
}

fn bench_real_world_simulation(c: &mut Criterion) {
    let mut group = c.benchmark_group("real_world_simulation");
    
    // Simulate processing 1 minute of MNQ data at ~1000 ticks/second
    group.bench_function("one_minute_mnq_simulation", |b| {
        b.iter(|| {
            let ticks = generate_test_ticks(60_000); // 1 minute at 1000 Hz
            let mut book = OrderBook::new("MNQZ24".to_string());
            let mut reconstructor = OrderBookReconstructor::new();
            
            let mut strategy = BidAskBounceStrategy::new();
            let mut params = HashMap::new();
            params.insert("bounce_threshold".to_string(), 0.3);
            params.insert("volume_threshold".to_string(), 50.0);
            strategy.set_parameters(params);
            
            let mut signals = Vec::new();
            let analyzer = StatisticalAnalyzer::new();
            let mut returns = Vec::new();
            let mut last_price = None;
            
            for tick in ticks {
                // Validate tick
                let _validation = strategy_lab::data::types::validation::validate_tick(&tick, ValidationLevel::Basic);
                
                // Update order book
                let _book_result = reconstructor.process_tick(&tick, &mut book);
                
                // Generate trading signals
                let snapshot = book.snapshot();
                if let Some(signal) = strategy.generate_signal(&tick, &snapshot) {
                    signals.push(signal);
                }
                
                // Calculate returns for statistical analysis
                if let Some(prev_price) = last_price {
                    let return_pct = ((tick.price - prev_price) / prev_price).to_f64().unwrap_or(0.0);
                    returns.push(return_pct);
                }
                last_price = Some(tick.price);
            }
            
            // Perform statistical analysis on returns
            if !returns.is_empty() {
                let _mean = analyzer.mean(&returns);
                let _volatility = analyzer.standard_deviation(&returns);
                let _sharpe = analyzer.sharpe_ratio(&returns, 0.0);
            }
            
            black_box((book, signals, returns));
        })
    });
    
    group.finish();
}

criterion_group!(
    benches,
    bench_tick_validation,
    bench_order_book_reconstruction,
    bench_strategy_signal_generation,
    bench_statistical_analysis,
    bench_order_book_operations,
    bench_memory_usage,
    bench_concurrent_operations,
    bench_real_world_simulation,
);
criterion_main!(benches);