//! API request handlers

use axum::{
    extract::State,
    http::StatusCode,
    Json,
};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

use super::{ApiState, StrategyInfo, BacktestResult, SystemMetrics};
use crate::monitoring::ResourceMonitor;

#[derive(Debug, Deserialize)]
pub struct CreateStrategyRequest {
    pub name: String,
    pub description: String,
    pub parameters: serde_json::Value,
}

#[derive(Debug, Serialize)]
pub struct CreateStrategyResponse {
    pub id: String,
    pub message: String,
}

/// List all strategies
pub async fn list_strategies(
    State(state): State<ApiState>,
) -> Result<Json<Vec<StrategyInfo>>, StatusCode> {
    let strategies = state.strategies.read().await;
    Ok(Json(strategies.clone()))
}

/// Create a new strategy
pub async fn create_strategy(
    State(state): State<ApiState>,
    Json(req): Json<CreateStrategyRequest>,
) -> Result<Json<CreateStrategyResponse>, StatusCode> {
    let id = Uuid::new_v4().to_string();
    
    let strategy = StrategyInfo {
        id: id.clone(),
        name: req.name,
        description: req.description,
        parameters: req.parameters,
        status: "draft".to_string(),
    };
    
    let mut strategies = state.strategies.write().await;
    strategies.push(strategy);
    
    Ok(Json(CreateStrategyResponse {
        id,
        message: "Strategy created successfully".to_string(),
    }))
}

#[derive(Debug, Deserialize)]
pub struct RunBacktestRequest {
    pub strategy_id: String,
    pub start_date: String,
    pub end_date: String,
    pub initial_capital: f64,
}

#[derive(Debug, Serialize)]
pub struct RunBacktestResponse {
    pub backtest_id: String,
    pub message: String,
}

/// Run a backtest
pub async fn run_backtest(
    State(state): State<ApiState>,
    Json(req): Json<RunBacktestRequest>,
) -> Result<Json<RunBacktestResponse>, StatusCode> {
    let backtest_id = Uuid::new_v4().to_string();
    
    // In a real implementation, this would spawn a background task
    // For now, create a mock result
    let result = BacktestResult {
        id: backtest_id.clone(),
        strategy_id: req.strategy_id,
        start_date: req.start_date,
        end_date: req.end_date,
        total_return: 24.5,
        sharpe_ratio: 1.82,
        max_drawdown: -8.3,
        total_trades: 500,
    };
    
    let mut results = state.backtest_results.write().await;
    results.push(result);
    
    Ok(Json(RunBacktestResponse {
        backtest_id,
        message: "Backtest started".to_string(),
    }))
}

/// Get backtest results
pub async fn get_backtest_results(
    State(state): State<ApiState>,
) -> Result<Json<Vec<BacktestResult>>, StatusCode> {
    let results = state.backtest_results.read().await;
    Ok(Json(results.clone()))
}

#[derive(Debug, Deserialize)]
pub struct RunOptimizationRequest {
    pub strategy_id: String,
    pub optimization_type: String,
    pub parameters: serde_json::Value,
}

#[derive(Debug, Serialize)]
pub struct RunOptimizationResponse {
    pub optimization_id: String,
    pub message: String,
}

/// Run optimization
pub async fn run_optimization(
    State(_state): State<ApiState>,
    Json(req): Json<RunOptimizationRequest>,
) -> Result<Json<RunOptimizationResponse>, StatusCode> {
    let optimization_id = Uuid::new_v4().to_string();
    
    // In a real implementation, this would spawn optimization
    
    Ok(Json(RunOptimizationResponse {
        optimization_id,
        message: format!("Started {} optimization", req.optimization_type),
    }))
}

/// Get system metrics
pub async fn get_system_metrics(
    State(state): State<ApiState>,
) -> Result<Json<SystemMetrics>, StatusCode> {
    let monitor = ResourceMonitor::new();
    let usage = monitor.get_current_usage();
    
    let metrics = SystemMetrics {
        cpu_usage: usage.cpu_percent,
        memory_gb: usage.memory_gb,
        active_threads: usage.active_threads,
        ticks_processed: 0, // Would get from actual processing
    };
    
    // Update cached metrics
    let mut cached = state.system_metrics.write().await;
    *cached = metrics.clone();
    
    Ok(Json(metrics))
}