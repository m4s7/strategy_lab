//! Strategy Lab API Server
//! 
//! REST API server for the Strategy Lab frontend

use axum::{
    extract::{State, Path},
    http::StatusCode,
    response::Json,
    routing::{get, post, put, delete},
    Router,
};
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use tokio::sync::RwLock;
use tower_http::cors::CorsLayer;
use std::collections::HashMap;
use uuid::Uuid;
use chrono::Utc;

// API Models
#[derive(Debug, Clone, Serialize, Deserialize)]
struct Strategy {
    id: String,
    name: String,
    description: Option<String>,
    #[serde(rename = "type")]
    strategy_type: String,
    status: String,
    sharpe: Option<f64>,
    win_rate: Option<f64>,
    total_trades: Option<i32>,
    last_modified: String,
    parameters: HashMap<String, serde_json::Value>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct BacktestRequest {
    strategy: String,
    initial_capital: Option<f64>,
    start_date: Option<String>,
    end_date: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct BacktestResult {
    id: String,
    status: String,
    strategy: String,
    metrics: BacktestMetrics,
    equity_curve: Vec<EquityPoint>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct BacktestMetrics {
    total_return: f64,
    total_return_amount: f64,
    sharpe_ratio: f64,
    max_drawdown: f64,
    win_rate: f64,
    total_trades: i32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct EquityPoint {
    day: i32,
    value: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct OptimizationRequest {
    method: String,
    parameters: HashMap<String, serde_json::Value>,
    objective: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct OptimizationResult {
    id: String,
    status: String,
    progress: f64,
    best_result: Option<HashMap<String, f64>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct SystemMetrics {
    timestamp: String,
    cpu_usage: f64,
    memory_used: f64,
    memory_total: f64,
    disk_io: f64,
    threads_active: i32,
}

// Application State
#[derive(Clone)]
struct AppState {
    strategies: Arc<RwLock<Vec<Strategy>>>,
    backtests: Arc<RwLock<HashMap<String, BacktestResult>>>,
    optimizations: Arc<RwLock<HashMap<String, OptimizationResult>>>,
}

impl AppState {
    fn new() -> Self {
        let mut strategies = Vec::new();
        
        // Add default strategies
        strategies.push(Strategy {
            id: "1".to_string(),
            name: "Order Book Imbalance".to_string(),
            description: Some("Trades based on bid-ask volume imbalances".to_string()),
            strategy_type: "order_book".to_string(),
            status: "active".to_string(),
            sharpe: Some(1.80),
            win_rate: Some(0.62),
            total_trades: Some(1250),
            last_modified: "2024-01-15".to_string(),
            parameters: HashMap::new(),
        });
        
        strategies.push(Strategy {
            id: "2".to_string(),
            name: "Bid-Ask Bounce".to_string(),
            description: Some("Mean reversion strategy on bid-ask spread".to_string()),
            strategy_type: "mean_reversion".to_string(),
            status: "active".to_string(),
            sharpe: Some(1.50),
            win_rate: Some(0.58),
            total_trades: Some(890),
            last_modified: "2024-01-14".to_string(),
            parameters: HashMap::new(),
        });

        Self {
            strategies: Arc::new(RwLock::new(strategies)),
            backtests: Arc::new(RwLock::new(HashMap::new())),
            optimizations: Arc::new(RwLock::new(HashMap::new())),
        }
    }
}

// API Handlers

// Strategies
async fn get_strategies(State(state): State<AppState>) -> Json<Vec<Strategy>> {
    let strategies = state.strategies.read().await;
    Json(strategies.clone())
}

// Create strategy request struct
#[derive(Debug, Clone, Serialize, Deserialize)]
struct CreateStrategyRequest {
    name: String,
    description: Option<String>,
    #[serde(rename = "type")]
    strategy_type: String,
    status: Option<String>,
    parameters: Option<HashMap<String, serde_json::Value>>,
}

async fn create_strategy(
    State(state): State<AppState>,
    Json(request): Json<CreateStrategyRequest>,
) -> (StatusCode, Json<Strategy>) {
    let strategy = Strategy {
        id: Uuid::new_v4().to_string(),
        name: request.name,
        description: request.description,
        strategy_type: request.strategy_type,
        status: request.status.unwrap_or_else(|| "draft".to_string()),
        sharpe: None,
        win_rate: None,
        total_trades: None,
        last_modified: Utc::now().format("%Y-%m-%d").to_string(),
        parameters: request.parameters.unwrap_or_default(),
    };
    
    let mut strategies = state.strategies.write().await;
    strategies.push(strategy.clone());
    
    (StatusCode::CREATED, Json(strategy))
}

// Update strategy request struct
#[derive(Debug, Clone, Serialize, Deserialize)]
struct UpdateStrategyRequest {
    name: Option<String>,
    description: Option<String>,
    #[serde(rename = "type")]
    strategy_type: Option<String>,
    status: Option<String>,
    sharpe: Option<f64>,
    win_rate: Option<f64>,
    total_trades: Option<i32>,
    parameters: Option<HashMap<String, serde_json::Value>>,
}

async fn update_strategy(
    State(state): State<AppState>,
    Path(id): Path<String>,
    Json(request): Json<UpdateStrategyRequest>,
) -> Result<Json<Strategy>, StatusCode> {
    let mut strategies = state.strategies.write().await;
    
    if let Some(existing) = strategies.iter_mut().find(|s| s.id == id) {
        if let Some(name) = request.name {
            existing.name = name;
        }
        if let Some(description) = request.description {
            existing.description = Some(description);
        }
        if let Some(strategy_type) = request.strategy_type {
            existing.strategy_type = strategy_type;
        }
        if let Some(status) = request.status {
            existing.status = status;
        }
        if let Some(sharpe) = request.sharpe {
            existing.sharpe = Some(sharpe);
        }
        if let Some(win_rate) = request.win_rate {
            existing.win_rate = Some(win_rate);
        }
        if let Some(total_trades) = request.total_trades {
            existing.total_trades = Some(total_trades);
        }
        if let Some(parameters) = request.parameters {
            existing.parameters = parameters;
        }
        existing.last_modified = Utc::now().format("%Y-%m-%d").to_string();
        Ok(Json(existing.clone()))
    } else {
        Err(StatusCode::NOT_FOUND)
    }
}

async fn delete_strategy(
    State(state): State<AppState>,
    Path(id): Path<String>,
) -> StatusCode {
    let mut strategies = state.strategies.write().await;
    strategies.retain(|s| s.id != id);
    StatusCode::NO_CONTENT
}

// Backtesting
async fn run_backtest(
    State(state): State<AppState>,
    Json(request): Json<BacktestRequest>,
) -> (StatusCode, Json<BacktestResult>) {
    let result = BacktestResult {
        id: Uuid::new_v4().to_string(),
        status: "completed".to_string(),
        strategy: request.strategy,
        metrics: BacktestMetrics {
            total_return: 0.245,
            total_return_amount: 24500.0,
            sharpe_ratio: 1.82,
            max_drawdown: -0.083,
            win_rate: 0.62,
            total_trades: 500,
        },
        equity_curve: (0..100).map(|i| EquityPoint {
            day: i + 1,
            value: 100000.0 + (24500.0 * (i as f64 / 100.0)),
        }).collect(),
    };
    
    let mut backtests = state.backtests.write().await;
    backtests.insert(result.id.clone(), result.clone());
    
    (StatusCode::CREATED, Json(result))
}

async fn get_backtest_status(
    State(state): State<AppState>,
    Path(id): Path<String>,
) -> Result<Json<BacktestResult>, StatusCode> {
    let backtests = state.backtests.read().await;
    backtests.get(&id)
        .cloned()
        .map(Json)
        .ok_or(StatusCode::NOT_FOUND)
}

// Optimization
async fn start_optimization(
    State(state): State<AppState>,
    Json(_request): Json<OptimizationRequest>,
) -> (StatusCode, Json<OptimizationResult>) {
    let result = OptimizationResult {
        id: Uuid::new_v4().to_string(),
        status: "running".to_string(),
        progress: 0.0,
        best_result: None,
    };
    
    let mut optimizations = state.optimizations.write().await;
    optimizations.insert(result.id.clone(), result.clone());
    
    (StatusCode::CREATED, Json(result))
}

async fn get_optimization_status(
    State(state): State<AppState>,
    Path(id): Path<String>,
) -> Result<Json<OptimizationResult>, StatusCode> {
    let mut optimizations = state.optimizations.write().await;
    
    if let Some(opt) = optimizations.get_mut(&id) {
        // Simulate progress
        opt.progress = (opt.progress + 10.0).min(100.0);
        if opt.progress >= 100.0 {
            opt.status = "completed".to_string();
            opt.best_result = Some(HashMap::from([
                ("sharpe".to_string(), 2.15),
                ("lookback_period".to_string(), 60.0),
            ]));
        }
        Ok(Json(opt.clone()))
    } else {
        Err(StatusCode::NOT_FOUND)
    }
}

// System Monitoring
async fn get_system_metrics() -> Json<SystemMetrics> {
    use sysinfo::System;
    
    let mut sys = System::new_all();
    sys.refresh_all();
    
    let cpu_usage = sys.global_cpu_usage() as f64;
    let memory_used = sys.used_memory() as f64 / 1_073_741_824.0; // Convert to GB
    let memory_total = sys.total_memory() as f64 / 1_073_741_824.0;
    
    Json(SystemMetrics {
        timestamp: Utc::now().to_rfc3339(),
        cpu_usage,
        memory_used,
        memory_total,
        disk_io: rand::random::<f64>() * 200.0,
        threads_active: 12,
    })
}

// Health check
async fn health_check() -> &'static str {
    "healthy"
}

#[tokio::main]
async fn main() {
    // Initialize tracing
    tracing_subscriber::fmt::init();

    // Create application state
    let state = AppState::new();

    // Build router
    let app = Router::new()
        // Health
        .route("/health", get(health_check))
        
        // Strategies
        .route("/api/strategies", get(get_strategies).post(create_strategy))
        .route("/api/strategies/:id", put(update_strategy).delete(delete_strategy))
        
        // Backtesting
        .route("/api/backtest", post(run_backtest))
        .route("/api/backtest/:id", get(get_backtest_status))
        
        // Optimization
        .route("/api/optimization", post(start_optimization))
        .route("/api/optimization/:id", get(get_optimization_status))
        
        // Monitoring
        .route("/api/monitor", get(get_system_metrics))
        
        // Add state and CORS
        .with_state(state)
        .layer(CorsLayer::permissive());

    // Start server
    let addr = "0.0.0.0:8001";
    println!("API Server listening on http://{}", addr);
    
    axum::Server::bind(&addr.parse().unwrap())
        .serve(app.into_make_service())
        .await
        .unwrap();
}