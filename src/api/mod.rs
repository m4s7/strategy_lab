//! API server and WebSocket support

pub mod server;
pub mod websocket;
pub mod handlers;

use axum::{
    Router,
    routing::{get, post},
    http::StatusCode,
    Json,
};
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use tokio::sync::RwLock;

/// API state shared across handlers
#[derive(Clone)]
pub struct ApiState {
    pub strategies: Arc<RwLock<Vec<StrategyInfo>>>,
    pub backtest_results: Arc<RwLock<Vec<BacktestResult>>>,
    pub system_metrics: Arc<RwLock<SystemMetrics>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StrategyInfo {
    pub id: String,
    pub name: String,
    pub description: String,
    pub parameters: serde_json::Value,
    pub status: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BacktestResult {
    pub id: String,
    pub strategy_id: String,
    pub start_date: String,
    pub end_date: String,
    pub total_return: f64,
    pub sharpe_ratio: f64,
    pub max_drawdown: f64,
    pub total_trades: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SystemMetrics {
    pub cpu_usage: f64,
    pub memory_gb: f64,
    pub active_threads: usize,
    pub ticks_processed: u64,
}

impl Default for SystemMetrics {
    fn default() -> Self {
        Self {
            cpu_usage: 0.0,
            memory_gb: 0.0,
            active_threads: 0,
            ticks_processed: 0,
        }
    }
}

/// Create the API router
pub fn create_router(state: ApiState) -> Router {
    Router::new()
        .route("/api/strategies", get(handlers::list_strategies))
        .route("/api/strategies", post(handlers::create_strategy))
        .route("/api/backtest", post(handlers::run_backtest))
        .route("/api/backtest/results", get(handlers::get_backtest_results))
        .route("/api/optimize", post(handlers::run_optimization))
        .route("/api/metrics", get(handlers::get_system_metrics))
        .route("/ws", get(websocket::websocket_handler))
        .with_state(state)
}