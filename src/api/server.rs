//! HTTP server implementation

use axum::{
    Router,
    http::{header, Method},
};
use tower_http::cors::{CorsLayer, Any};
use std::net::SocketAddr;
use tracing::info;

use super::{ApiState, create_router};

/// Start the API server
pub async fn start_server(port: u16) -> Result<(), Box<dyn std::error::Error>> {
    // Create shared state
    let state = ApiState {
        strategies: Default::default(),
        backtest_results: Default::default(),
        system_metrics: Default::default(),
    };
    
    // Configure CORS
    let cors = CorsLayer::new()
        .allow_origin(Any)
        .allow_methods([Method::GET, Method::POST, Method::PUT, Method::DELETE])
        .allow_headers([header::CONTENT_TYPE, header::AUTHORIZATION]);
    
    // Create app with middleware
    let app = create_router(state)
        .layer(cors);
    
    // Start server
    let addr = SocketAddr::from(([0, 0, 0, 0], port));
    info!("API server listening on {}", addr);
    
    axum::Server::bind(&addr)
        .serve(app.into_make_service())
        .await?;
    
    Ok(())
}