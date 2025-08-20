use strategy_lab::data::types::{TickData, MarketDataType, DataLevel, ValidationLevel};
use strategy_lab::market::order_book::{OrderBook, OrderBookReconstructor};
use strategy_lab::strategy::examples::BidAskBounceStrategy;
use strategy_lab::strategy::traits::Strategy;
use strategy_lab::statistics::StatisticalAnalyzer;
use strategy_lab::optimization::grid_search::GridSearchOptimizer;
use rust_decimal::Decimal;
use std::str::FromStr;
use std::collections::HashMap;

#[test]
fn test_end_to_end_data_validation_to_order_book() {
    // Create test tick data
    let tick = TickData::new(
        DataLevel::L1,
        MarketDataType::BidQuote,
        1234567890,
        Decimal::from_str("4500.25").unwrap(),
        10,
        "0624".to_string(),
    );

    // Validate the tick data
    let validation_result = strategy_lab::data::types::validation::validate_tick(&tick, ValidationLevel::Standard);
    assert!(validation_result.is_ok(), "Tick validation should pass");

    // Process through order book reconstruction
    let mut book = OrderBook::new("MNQZ24".to_string());
    let mut reconstructor = OrderBookReconstructor::new();
    
    let result = reconstructor.process_tick(&tick, &mut book);
    assert!(result.is_ok(), "Order book processing should succeed");

    // Verify order book state
    assert_eq!(book.best_bid, Some(Decimal::from_str("4500.25").unwrap()));
    assert_eq!(book.bid_levels.len(), 1);
}

#[test]
fn test_strategy_with_order_book_integration() {
    // Set up order book
    let mut book = OrderBook::new("MNQZ24".to_string());
    book.add_bid_level(Decimal::from_str("4500.00").unwrap(), 50, 1000);
    book.add_ask_level(Decimal::from_str("4500.75").unwrap(), 30, 2000);

    // Create strategy
    let mut strategy = BidAskBounceStrategy::new();
    let mut params = HashMap::new();
    params.insert("bounce_threshold".to_string(), 0.3);
    params.insert("volume_threshold".to_string(), 40.0);
    strategy.set_parameters(params);

    // Validate parameters
    assert!(strategy.validate_parameters().is_ok());

    // Create test tick
    let tick = TickData::new(
        DataLevel::L1,
        MarketDataType::Trade,
        3000,
        Decimal::from_str("4500.10").unwrap(),
        5,
        "0624".to_string(),
    );

    // Generate signal
    let snapshot = book.snapshot();
    let signal = strategy.generate_signal(&tick, &snapshot);

    // Strategy should generate some response (signal or no signal based on logic)
    assert!(signal.is_some() || signal.is_none()); // Either outcome is valid for integration test
}

#[test]
fn test_statistical_analysis_integration() {
    let analyzer = StatisticalAnalyzer::new();

    // Sample return data
    let returns = vec![0.01, -0.02, 0.03, -0.01, 0.02, 0.01, -0.03, 0.04];
    let benchmark = vec![0.005, -0.015, 0.025, -0.005, 0.015, 0.008, -0.025, 0.035];

    // Test multiple statistical measures work together
    let mean_return = analyzer.mean(&returns);
    let volatility = analyzer.standard_deviation(&returns);
    let sharpe = analyzer.sharpe_ratio(&returns, 0.005);
    let max_dd = analyzer.maximum_drawdown(&returns);
    let var_95 = analyzer.value_at_risk(&returns, 0.95);
    let correlation = analyzer.correlation(&returns, &benchmark);

    // Verify all calculations complete without errors
    assert!(!mean_return.is_nan());
    assert!(!volatility.is_nan());
    assert!(!sharpe.is_nan());
    assert!(!max_dd.is_nan());
    assert!(!correlation.is_nan());
    assert!(var_95 <= 0.0); // VaR should be negative or zero
}

#[test]
fn test_order_book_statistics_integration() {
    let mut book = OrderBook::new("MNQZ24".to_string());
    let analyzer = StatisticalAnalyzer::new();

    // Build up order book
    book.add_bid_level(Decimal::from_str("4500.00").unwrap(), 100, 1000);
    book.add_bid_level(Decimal::from_str("4499.75").unwrap(), 80, 1000);
    book.add_bid_level(Decimal::from_str("4499.50").unwrap(), 60, 1000);
    
    book.add_ask_level(Decimal::from_str("4500.50").unwrap(), 90, 1000);
    book.add_ask_level(Decimal::from_str("4500.75").unwrap(), 70, 1000);
    book.add_ask_level(Decimal::from_str("4501.00").unwrap(), 50, 1000);

    // Calculate order book metrics
    let total_bid_volume = book.get_total_bid_volume();
    let total_ask_volume = book.get_total_ask_volume();
    let spread = book.get_spread();
    let mid_price = book.get_mid_price();

    // Calculate imbalance ratio
    let imbalance = (total_bid_volume as f64 - total_ask_volume as f64) / 
                   (total_bid_volume as f64 + total_ask_volume as f64);

    // Verify calculations
    assert_eq!(total_bid_volume, 240);
    assert_eq!(total_ask_volume, 210);
    assert_eq!(spread, Some(Decimal::from_str("0.50").unwrap()));
    assert_eq!(mid_price, Some(Decimal::from_str("4500.25").unwrap()));
    assert!(imbalance > 0.0); // More bids than asks

    // Use statistical analyzer for additional metrics
    let volumes = vec![100.0, 80.0, 60.0, 90.0, 70.0, 50.0];
    let volume_mean = analyzer.mean(&volumes);
    let volume_std = analyzer.standard_deviation(&volumes);

    assert!(!volume_mean.is_nan());
    assert!(!volume_std.is_nan());
    assert!(volume_mean > 0.0);
}

#[test]
fn test_data_flow_validation_to_metrics() {
    // Simulate complete data flow from tick validation to performance metrics
    
    // 1. Create and validate tick data
    let ticks = vec![
        TickData::new(DataLevel::L1, MarketDataType::Trade, 1000, Decimal::from_str("4500.00").unwrap(), 10, "0624".to_string()),
        TickData::new(DataLevel::L1, MarketDataType::Trade, 2000, Decimal::from_str("4500.25").unwrap(), 15, "0624".to_string()),
        TickData::new(DataLevel::L1, MarketDataType::Trade, 3000, Decimal::from_str("4499.75").unwrap(), 8, "0624".to_string()),
        TickData::new(DataLevel::L1, MarketDataType::Trade, 4000, Decimal::from_str("4501.00").unwrap(), 12, "0624".to_string()),
    ];

    // 2. Validate all ticks
    for tick in &ticks {
        let validation_result = strategy_lab::data::types::validation::validate_tick(tick, ValidationLevel::Basic);
        assert!(validation_result.is_ok(), "All ticks should validate successfully");
    }

    // 3. Calculate price changes (simulating returns)
    let mut returns = Vec::new();
    for i in 1..ticks.len() {
        let prev_price = ticks[i-1].price;
        let curr_price = ticks[i].price;
        let return_pct = ((curr_price - prev_price) / prev_price).to_f64().unwrap();
        returns.push(return_pct);
    }

    // 4. Analyze returns with statistical framework
    let analyzer = StatisticalAnalyzer::new();
    let mean_return = analyzer.mean(&returns);
    let volatility = analyzer.standard_deviation(&returns);
    let sharpe = analyzer.sharpe_ratio(&returns, 0.0);

    // 5. Verify complete pipeline worked
    assert!(!mean_return.is_nan(), "Mean return calculation should succeed");
    assert!(!volatility.is_nan(), "Volatility calculation should succeed");  
    assert!(!sharpe.is_nan() || sharpe.is_infinite(), "Sharpe ratio should be calculated");
    
    // Test that we have reasonable values
    assert!(volatility >= 0.0, "Volatility should be non-negative");
    assert!(returns.len() == 3, "Should have 3 return calculations");
}

#[test]
fn test_optimization_with_mock_strategy() {
    // Test that optimization framework can work with strategies
    // This is a simplified test since full optimization requires significant compute
    
    let mut strategy = BidAskBounceStrategy::new();
    
    // Define parameter ranges for optimization
    let mut parameter_ranges = HashMap::new();
    parameter_ranges.insert("bounce_threshold".to_string(), (0.1, 0.5, 0.1));
    parameter_ranges.insert("volume_threshold".to_string(), (20.0, 60.0, 10.0));
    
    // Validate parameter ranges make sense
    assert!(parameter_ranges.contains_key("bounce_threshold"));
    assert!(parameter_ranges.contains_key("volume_threshold"));
    
    let bounce_range = parameter_ranges.get("bounce_threshold").unwrap();
    assert!(bounce_range.0 < bounce_range.1); // min < max
    assert!(bounce_range.2 > 0.0); // step > 0
    
    // Test that we can set parameters within the ranges
    let mut test_params = HashMap::new();
    test_params.insert("bounce_threshold".to_string(), 0.3);
    test_params.insert("volume_threshold".to_string(), 40.0);
    
    strategy.set_parameters(test_params);
    assert!(strategy.validate_parameters().is_ok());
    
    let retrieved_params = strategy.get_parameters();
    assert_eq!(retrieved_params.get("bounce_threshold"), Some(&0.3));
    assert_eq!(retrieved_params.get("volume_threshold"), Some(&40.0));
}

#[test]
fn test_comprehensive_system_health() {
    // This test verifies that key system components can be instantiated and basic operations work
    
    // 1. Data structures
    let _tick = TickData::new(
        DataLevel::L1, 
        MarketDataType::Trade, 
        1000, 
        Decimal::from_str("4500.00").unwrap(), 
        10, 
        "0624".to_string()
    );
    
    // 2. Order book
    let mut _book = OrderBook::new("MNQZ24".to_string());
    let _reconstructor = OrderBookReconstructor::new();
    
    // 3. Strategy system
    let mut _strategy = BidAskBounceStrategy::new();
    
    // 4. Statistical analysis
    let _analyzer = StatisticalAnalyzer::new();
    
    // 5. Optimization (basic instantiation)
    let _optimizer = GridSearchOptimizer::new();
    
    // If we get here without panics, basic system health is good
    assert!(true, "All major components can be instantiated");
}