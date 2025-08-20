//! Core backtesting engine implementation

use crate::data::{DataIngestionEngine, IngestionConfig, TickData};
use crate::market::{OrderBook};
use crate::market::order_book::OrderBookManager;
use crate::strategy::{Strategy, StrategyContext, Order, OrderSide};
use crate::strategy::traits::OrderFill;
use crate::backtesting::{
    StrategyExecutor, TransactionCostModel, PerformanceMetrics, BacktestReport
};
use chrono::{DateTime, Utc};
use rust_decimal::Decimal;
use serde::{Deserialize, Serialize};
use std::path::Path;
use std::time::Instant;
use tracing::{info, debug, warn};

/// Configuration for backtesting
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BacktestConfig {
    /// Start date for backtest
    pub start_date: DateTime<Utc>,
    
    /// End date for backtest
    pub end_date: DateTime<Utc>,
    
    /// Initial capital
    pub initial_capital: Decimal,
    
    /// Transaction cost model
    pub transaction_costs: TransactionCostConfig,
    
    /// Slippage configuration
    pub slippage: SlippageConfig,
    
    /// Latency simulation
    pub latency_ms: u32,
    
    /// Enable detailed logging
    pub detailed_logging: bool,
    
    /// Save trades to file
    pub save_trades: bool,
    
    /// Tick processing batch size
    pub batch_size: usize,
}

/// Transaction cost configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TransactionCostConfig {
    /// Commission per contract
    pub commission_per_contract: Decimal,
    
    /// Exchange fees
    pub exchange_fee: Decimal,
    
    /// Regulatory fees
    pub regulatory_fee: Decimal,
}

/// Slippage configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SlippageConfig {
    /// Fixed slippage in ticks
    pub fixed_slippage: Decimal,
    
    /// Variable slippage as percentage of volume
    pub volume_slippage: f64,
    
    /// Market impact coefficient
    pub market_impact: f64,
}

impl Default for BacktestConfig {
    fn default() -> Self {
        Self {
            start_date: Utc::now() - chrono::Duration::days(30),
            end_date: Utc::now(),
            initial_capital: Decimal::from(10000),
            transaction_costs: TransactionCostConfig {
                commission_per_contract: Decimal::from_str_exact("0.62").unwrap(),
                exchange_fee: Decimal::from_str_exact("0.35").unwrap(),
                regulatory_fee: Decimal::from_str_exact("0.03").unwrap(),
            },
            slippage: SlippageConfig {
                fixed_slippage: Decimal::from_str_exact("0.25").unwrap(),
                volume_slippage: 0.001,
                market_impact: 0.0001,
            },
            latency_ms: 1,
            detailed_logging: false,
            save_trades: true,
            batch_size: 10000,
        }
    }
}

/// Main backtesting engine
pub struct BacktestEngine {
    config: BacktestConfig,
    executor: StrategyExecutor,
    order_book_manager: OrderBookManager,
    metrics: PerformanceMetrics,
    tick_count: usize,
    start_time: Instant,
}

impl BacktestEngine {
    /// Create a new backtesting engine
    pub fn new(config: BacktestConfig) -> Self {
        let transaction_model = TransactionCostModel::from_config(&config.transaction_costs);
        let executor = StrategyExecutor::new(transaction_model, config.initial_capital);
        
        Self {
            config,
            executor,
            order_book_manager: OrderBookManager::new(true),
            metrics: PerformanceMetrics::new(),
            tick_count: 0,
            start_time: Instant::now(),
        }
    }
    
    /// Run backtest on historical data
    pub async fn run_backtest<S, P>(
        &mut self,
        strategy: &mut S,
        data_path: P,
    ) -> Result<BacktestResult, Box<dyn std::error::Error>>
    where
        S: Strategy,
        P: AsRef<Path>,
    {
        info!("Starting backtest from {} to {}", 
            self.config.start_date, self.config.end_date);
        
        self.start_time = Instant::now();
        
        // Load historical data
        let ticks = self.load_data(data_path).await?;
        info!("Loaded {} ticks for backtesting", ticks.len());
        
        // Reset strategy
        strategy.reset();
        
        // Process ticks in batches for performance
        let mut processed = 0;
        for batch in ticks.chunks(self.config.batch_size) {
            self.process_batch(strategy, batch)?;
            processed += batch.len();
            
            if processed % 100000 == 0 {
                let rate = self.calculate_processing_rate();
                debug!("Processed {} ticks, rate: {:.0} ticks/sec", processed, rate);
            }
        }
        
        // Generate final results
        let result = self.generate_results(strategy);
        
        let elapsed = self.start_time.elapsed();
        info!("Backtest completed in {:.2}s, processed {} ticks at {:.0} ticks/sec",
            elapsed.as_secs_f64(),
            self.tick_count,
            self.tick_count as f64 / elapsed.as_secs_f64()
        );
        
        Ok(result)
    }
    
    /// Load historical tick data
    async fn load_data<P: AsRef<Path>>(
        &self,
        path: P,
    ) -> Result<Vec<TickData>, Box<dyn std::error::Error>> {
        let config = IngestionConfig {
            batch_size: self.config.batch_size,
            parallel: true,
            ..Default::default()
        };
        
        let mut engine = DataIngestionEngine::new(config);
        let ticks = engine.ingest_file(path).await?;
        
        // Filter by date range
        let start_nanos = self.config.start_date.timestamp_nanos_opt().unwrap_or(0);
        let end_nanos = self.config.end_date.timestamp_nanos_opt().unwrap_or(i64::MAX);
        
        let filtered: Vec<_> = ticks.into_iter()
            .filter(|t| t.timestamp >= start_nanos && t.timestamp <= end_nanos)
            .collect();
        
        Ok(filtered)
    }
    
    /// Process a batch of ticks
    fn process_batch<S: Strategy>(
        &mut self,
        strategy: &mut S,
        ticks: &[TickData],
    ) -> Result<(), Box<dyn std::error::Error>> {
        for tick in ticks {
            // Update order book
            self.order_book_manager.process_tick(tick);
            let order_book = self.order_book_manager
                .get_or_create(&tick.contract_month)
                .get_state()
                .clone();
            
            // Create strategy context
            let context = StrategyContext {
                order_book,
                timestamp: tick.timestamp,
                session_high: None, // TODO: Track session stats
                session_low: None,
                session_volume: 0,
                contract: tick.contract_month.clone(),
                market_open: true,
            };
            
            // Execute strategy
            if let Some(order) = strategy.on_tick(tick, &context) {
                self.process_order(strategy, order, tick);
            }
            
            // Update metrics
            self.update_metrics(strategy, tick);
            
            self.tick_count += 1;
        }
        
        Ok(())
    }
    
    /// Process an order from strategy
    fn process_order<S: Strategy>(
        &mut self,
        strategy: &mut S,
        order: Order,
        tick: &TickData,
    ) {
        // Simulate order execution with slippage and latency
        let fill = self.executor.execute_order(order, tick, &self.config.slippage);
        
        if let Some(fill) = fill {
            // Notify strategy of fill
            strategy.on_order_fill(&fill);
            
            // Update metrics
            self.metrics.record_trade(&fill);
            
            if self.config.detailed_logging {
                debug!("Order filled: {:?} {} @ {} (slippage: {})",
                    fill.side, fill.quantity, fill.price, fill.slippage);
            }
        }
    }
    
    /// Update performance metrics
    fn update_metrics<S: Strategy>(&mut self, strategy: &S, tick: &TickData) {
        let position = strategy.get_position();
        let equity = self.executor.get_equity(position, tick.price);
        
        self.metrics.update_equity(equity, tick.timestamp);
        self.metrics.update_position(position);
    }
    
    /// Calculate current processing rate
    fn calculate_processing_rate(&self) -> f64 {
        let elapsed = self.start_time.elapsed().as_secs_f64();
        if elapsed > 0.0 {
            self.tick_count as f64 / elapsed
        } else {
            0.0
        }
    }
    
    /// Generate backtest results
    fn generate_results<S: Strategy>(&self, strategy: &S) -> BacktestResult {
        let strategy_metrics = strategy.get_metrics();
        let elapsed = self.start_time.elapsed();
        
        BacktestResult {
            initial_capital: self.config.initial_capital,
            final_capital: self.executor.get_current_capital(),
            total_pnl: strategy_metrics.total_pnl,
            total_trades: strategy_metrics.total_trades,
            winning_trades: strategy_metrics.winning_trades,
            losing_trades: strategy_metrics.losing_trades,
            win_rate: strategy_metrics.win_rate,
            sharpe_ratio: self.metrics.calculate_sharpe_ratio(),
            max_drawdown: strategy_metrics.max_drawdown,
            profit_factor: strategy_metrics.profit_factor,
            avg_trade_duration: strategy_metrics.avg_trade_duration,
            ticks_processed: self.tick_count,
            processing_time_secs: elapsed.as_secs_f64(),
            ticks_per_second: self.tick_count as f64 / elapsed.as_secs_f64(),
        }
    }
}

/// Result of a backtest run
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BacktestResult {
    pub initial_capital: Decimal,
    pub final_capital: Decimal,
    pub total_pnl: Decimal,
    pub total_trades: u32,
    pub winning_trades: u32,
    pub losing_trades: u32,
    pub win_rate: f64,
    pub sharpe_ratio: f64,
    pub max_drawdown: Decimal,
    pub profit_factor: f64,
    pub avg_trade_duration: f64,
    pub ticks_processed: usize,
    pub processing_time_secs: f64,
    pub ticks_per_second: f64,
}

impl Default for BacktestResult {
    fn default() -> Self {
        Self {
            initial_capital: Decimal::from(10000),
            final_capital: Decimal::from(10000),
            total_pnl: Decimal::ZERO,
            total_trades: 0,
            winning_trades: 0,
            losing_trades: 0,
            win_rate: 0.0,
            sharpe_ratio: 0.0,
            max_drawdown: Decimal::ZERO,
            profit_factor: 0.0,
            avg_trade_duration: 0.0,
            ticks_processed: 0,
            processing_time_secs: 0.0,
            ticks_per_second: 0.0,
        }
    }
}

impl BacktestResult {
    /// Generate a summary report
    pub fn summary(&self) -> String {
        format!(
            r#"
Backtest Results Summary
========================
Capital: {} → {} (PnL: {})
Return: {:.2}%

Trade Statistics:
- Total Trades: {}
- Win Rate: {:.2}%
- Winning: {} / Losing: {}
- Profit Factor: {:.2}
- Avg Duration: {:.1}s

Risk Metrics:
- Sharpe Ratio: {:.2}
- Max Drawdown: {}

Performance:
- Ticks Processed: {}
- Processing Time: {:.2}s
- Speed: {:.0} ticks/sec
"#,
            self.initial_capital,
            self.final_capital,
            self.total_pnl,
            (self.total_pnl / self.initial_capital * Decimal::from(100))
                .to_string().parse::<f64>().unwrap_or(0.0),
            self.total_trades,
            self.win_rate,
            self.winning_trades,
            self.losing_trades,
            self.profit_factor,
            self.avg_trade_duration,
            self.sharpe_ratio,
            self.max_drawdown,
            self.ticks_processed,
            self.processing_time_secs,
            self.ticks_per_second
        )
    }
}