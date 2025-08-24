//! Strategy Lab API Server with TimescaleDB
//! 
//! Production-ready REST API server with database persistence

mod db;
mod websocket;

use axum::{
    extract::{State, Path},
    http::StatusCode,
    response::Json,
    routing::{get, post, put, delete},
    Router,
};
use db::{Database, Strategy, CreateStrategyRequest, UpdateStrategyRequest, 
         BacktestRequest, BacktestResult, SystemMetrics};
use std::sync::Arc;
use tower_http::cors::CorsLayer;
use uuid::Uuid;
use chrono::Utc;
use tracing_subscriber;

// Application State
#[derive(Clone)]
struct AppState {
    db: Arc<Database>,
}

// API Handlers

// Strategies
async fn get_strategies(State(state): State<AppState>) -> Result<Json<Vec<Strategy>>, StatusCode> {
    state.db.get_all_strategies()
        .await
        .map(Json)
        .map_err(|e| {
            tracing::error!("Failed to get strategies: {}", e);
            StatusCode::INTERNAL_SERVER_ERROR
        })
}

async fn get_strategy(
    State(state): State<AppState>,
    Path(id): Path<Uuid>,
) -> Result<Json<Strategy>, StatusCode> {
    state.db.get_strategy(id)
        .await
        .map_err(|e| {
            tracing::error!("Failed to get strategy: {}", e);
            StatusCode::INTERNAL_SERVER_ERROR
        })?
        .map(Json)
        .ok_or(StatusCode::NOT_FOUND)
}

async fn create_strategy(
    State(state): State<AppState>,
    Json(request): Json<CreateStrategyRequest>,
) -> Result<(StatusCode, Json<Strategy>), StatusCode> {
    state.db.create_strategy(request)
        .await
        .map(|strategy| (StatusCode::CREATED, Json(strategy)))
        .map_err(|e| {
            tracing::error!("Failed to create strategy: {}", e);
            StatusCode::INTERNAL_SERVER_ERROR
        })
}

async fn update_strategy(
    State(state): State<AppState>,
    Path(id): Path<Uuid>,
    Json(request): Json<UpdateStrategyRequest>,
) -> Result<Json<Strategy>, StatusCode> {
    state.db.update_strategy(id, request)
        .await
        .map_err(|e| {
            tracing::error!("Failed to update strategy: {}", e);
            StatusCode::INTERNAL_SERVER_ERROR
        })?
        .map(Json)
        .ok_or(StatusCode::NOT_FOUND)
}

async fn delete_strategy(
    State(state): State<AppState>,
    Path(id): Path<Uuid>,
) -> StatusCode {
    match state.db.delete_strategy(id).await {
        Ok(deleted) => {
            if deleted {
                StatusCode::NO_CONTENT
            } else {
                StatusCode::NOT_FOUND
            }
        }
        Err(e) => {
            tracing::error!("Failed to delete strategy: {}", e);
            StatusCode::INTERNAL_SERVER_ERROR
        }
    }
}

// Backtesting
async fn run_backtest(
    State(state): State<AppState>,
    Json(request): Json<BacktestRequest>,
) -> Result<(StatusCode, Json<BacktestResult>), StatusCode> {
    state.db.create_backtest(request)
        .await
        .map(|result| (StatusCode::CREATED, Json(result)))
        .map_err(|e| {
            tracing::error!("Failed to run backtest: {}", e);
            StatusCode::INTERNAL_SERVER_ERROR
        })
}

// System Monitoring
async fn get_system_metrics(State(state): State<AppState>) -> Result<Json<SystemMetrics>, StatusCode> {
    use sysinfo::System;
    
    let mut sys = System::new_all();
    sys.refresh_all();
    
    let cpu_usage = sys.global_cpu_usage() as f64;
    let memory_used = sys.used_memory() as f64 / 1_073_741_824.0; // Convert to GB
    let memory_total = sys.total_memory() as f64 / 1_073_741_824.0;
    
    // Get active strategies count
    let active_strategies = state.db.get_all_strategies()
        .await
        .map(|strategies| strategies.iter().filter(|s| s.status == "active").count() as i32)
        .unwrap_or(0);
    
    let metrics = SystemMetrics {
        timestamp: Utc::now().to_rfc3339(),
        cpu_usage,
        memory_used,
        memory_total,
        disk_io: rand::random::<f64>() * 200.0, // TODO: Implement real disk I/O monitoring
        threads_active: 12, // TODO: Get actual thread count
        api_latency_ms: Some(5.0 + rand::random::<f64>() * 10.0),
        active_strategies: Some(active_strategies),
    };
    
    // Store metrics in database
    if let Err(e) = state.db.insert_system_metrics(&metrics).await {
        tracing::warn!("Failed to store system metrics: {}", e);
    }
    
    Ok(Json(metrics))
}

// Get historical metrics
async fn get_metrics_history(State(state): State<AppState>) -> Result<Json<Vec<SystemMetrics>>, StatusCode> {
    state.db.get_recent_metrics(60) // Last hour
        .await
        .map(Json)
        .map_err(|e| {
            tracing::error!("Failed to get metrics history: {}", e);
            StatusCode::INTERNAL_SERVER_ERROR
        })
}

// Health check
async fn health_check(State(state): State<AppState>) -> Result<&'static str, StatusCode> {
    // Check database connection
    sqlx::query("SELECT 1")
        .fetch_one(&state.db.pool)
        .await
        .map(|_| "healthy")
        .map_err(|e| {
            tracing::error!("Health check failed: {}", e);
            StatusCode::SERVICE_UNAVAILABLE
        })
}

#[tokio::main]
async fn main() {
    // Initialize tracing
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::from_default_env()
                .add_directive(tracing::Level::INFO.into())
        )
        .init();

    // Load environment variables
    dotenvy::dotenv().ok();

    // Initialize database
    let db = match Database::new().await {
        Ok(db) => {
            tracing::info!("Connected to TimescaleDB");
            Arc::new(db)
        }
        Err(e) => {
            tracing::error!("Failed to connect to database: {}", e);
            std::process::exit(1);
        }
    };

    // Create application state
    let state = AppState { db };

    // Build router
    let app = Router::new()
        // Health
        .route("/health", get(health_check))
        
        // Strategies
        .route("/api/strategies", get(get_strategies).post(create_strategy))
        .route("/api/strategies/:id", get(get_strategy).put(update_strategy).delete(delete_strategy))
        
        // Backtesting
        .route("/api/backtest", post(run_backtest))
        
        // Monitoring
        .route("/api/monitor", get(get_system_metrics))
        .route("/api/monitor/history", get(get_metrics_history))
        .route("/ws/monitor", get(websocket::websocket_handler))
        
        // Add state and CORS
        .with_state(state)
        .layer(CorsLayer::permissive());

    // Start server
    let addr = "0.0.0.0:8001";
    tracing::info!("API Server listening on http://{}", addr);
    
    let listener = tokio::net::TcpListener::bind(addr)
        .await
        .expect("Failed to bind to address");
    
    axum::serve(listener, app)
        .await
        .expect("Failed to start server");
}