//! Strategy Lab Server

use strategy_lab::api;
use tracing::Level;
use tracing_subscriber;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Initialize logging
    tracing_subscriber::fmt()
        .with_max_level(Level::INFO)
        .init();
    
    println!("🚀 Strategy Lab Server v{}", strategy_lab::VERSION);
    println!("Starting API server on port 8080...");
    
    // Start the server
    api::server::start_server(8080).await?;
    
    Ok(())
}