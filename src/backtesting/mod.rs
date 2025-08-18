//! Backtesting engine with HFTBacktest integration
//! 
//! This module implements Story 2.2: Strategy Execution Engine
//! Provides accurate tick-by-tick backtesting with realistic transaction costs
//! Processes 100K-500K ticks per second with nanosecond precision

pub mod engine;
pub mod executor;
pub mod models;
pub mod metrics;
pub mod report;

pub use engine::{BacktestEngine, BacktestConfig, BacktestResult};
pub use executor::{StrategyExecutor, ExecutionContext};
pub use models::{TransactionCostModel, SlippageModel, LatencyModel};
pub use metrics::{PerformanceMetrics, RiskMetrics, TradeStatistics};
pub use report::{BacktestReport, ReportGenerator};