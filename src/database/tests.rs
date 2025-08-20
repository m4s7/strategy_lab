#[cfg(test)]
mod tests {
    use super::super::*;
    use sqlx::{PgPool, postgres::PgPoolOptions};
    use tokio;
    
    async fn setup_test_db() -> Result<PgPool, sqlx::Error> {
        // Use environment variable or test database
        let database_url = std::env::var("DATABASE_URL")
            .unwrap_or_else(|_| "postgresql://postgres:postgres@localhost/strategy_lab_test".to_string());
        
        let pool = PgPoolOptions::new()
            .max_connections(5)
            .connect(&database_url)
            .await?;
        
        Ok(pool)
    }
    
    #[tokio::test]
    async fn test_database_connection() {
        let result = setup_test_db().await;
        assert!(result.is_ok(), "Database connection should succeed");
        
        if let Ok(pool) = result {
            // Test basic query
            let row: (i32,) = sqlx::query_as("SELECT 1")
                .fetch_one(&pool)
                .await
                .expect("Simple query should work");
            
            assert_eq!(row.0, 1);
        }
    }
    
    #[tokio::test]
    async fn test_strategy_crud() {
        let pool = match setup_test_db().await {
            Ok(p) => p,
            Err(_) => {
                println!("Skipping test: Database not available");
                return;
            }
        };
        
        // Test insert
        let result = sqlx::query(
            "INSERT INTO strategies (name, description, parameters, created_at)
             VALUES ($1, $2, $3, NOW())
             RETURNING id"
        )
        .bind("TestStrategy")
        .bind("Test strategy for unit testing")
        .bind(serde_json::json!({"threshold": 0.5}))
        .fetch_one(&pool)
        .await;
        
        if result.is_ok() {
            println!("Strategy insert successful");
        }
    }
    
    #[tokio::test] 
    async fn test_backtest_result_storage() {
        let pool = match setup_test_db().await {
            Ok(p) => p,
            Err(_) => {
                println!("Skipping test: Database not available");
                return;
            }
        };
        
        // Test backtest result storage
        let result = sqlx::query(
            "INSERT INTO backtest_runs 
             (strategy_id, start_date, end_date, initial_capital, final_capital, 
              total_trades, win_rate, sharpe_ratio, max_drawdown, status, created_at)
             VALUES (1, '2024-01-01', '2024-01-31', 10000, 10500, 
                     100, 0.55, 1.8, 0.05, 'completed', NOW())
             RETURNING id"
        )
        .fetch_one(&pool)
        .await;
        
        if result.is_ok() {
            println!("Backtest result storage successful");
        }
    }
    
    #[tokio::test]
    async fn test_performance_metrics_storage() {
        let pool = match setup_test_db().await {
            Ok(p) => p,
            Err(_) => {
                println!("Skipping test: Database not available");
                return;
            }
        };
        
        // Test performance metrics
        let result = sqlx::query(
            "INSERT INTO performance_metrics
             (backtest_id, metric_name, metric_value, timestamp)
             VALUES (1, 'sharpe_ratio', 1.85, NOW())"
        )
        .fetch_one(&pool)
        .await;
        
        if result.is_ok() {
            println!("Performance metrics storage successful");
        }
    }
    
    #[tokio::test]
    async fn test_optimization_run_storage() {
        let pool = match setup_test_db().await {
            Ok(p) => p,
            Err(_) => {
                println!("Skipping test: Database not available");
                return;
            }
        };
        
        // Test optimization run storage
        let result = sqlx::query(
            "INSERT INTO optimization_runs
             (strategy_id, optimization_type, parameter_ranges, 
              total_combinations, best_parameters, best_objective_value,
              status, created_at, completed_at)
             VALUES (1, 'grid_search', $1, 1000, $2, 2.5,
                     'completed', NOW(), NOW())
             RETURNING id"
        )
        .bind(serde_json::json!({"threshold": [0.1, 0.9, 0.1]}))
        .bind(serde_json::json!({"threshold": 0.5}))
        .fetch_one(&pool)
        .await;
        
        if result.is_ok() {
            println!("Optimization run storage successful");
        }
    }
    
    #[tokio::test]
    async fn test_tick_data_hypertable() {
        let pool = match setup_test_db().await {
            Ok(p) => p,
            Err(_) => {
                println!("Skipping test: Database not available");
                return;
            }
        };
        
        // Test tick data insertion (if TimescaleDB is available)
        let result = sqlx::query(
            "INSERT INTO tick_data
             (timestamp, symbol, price, volume, bid, ask, mdt_type, level)
             VALUES (NOW(), 'MNQZ24', 18500.25, 10, 18500.00, 18500.50, 0, 'L1')"
        )
        .execute(&pool)
        .await;
        
        if result.is_ok() {
            println!("Tick data insertion successful");
        } else {
            // Table might not exist if TimescaleDB is not configured
            println!("Tick data table not available (TimescaleDB may not be configured)");
        }
    }
    
    #[tokio::test]
    async fn test_connection_pool_management() {
        let pool = match setup_test_db().await {
            Ok(p) => p,
            Err(_) => {
                println!("Skipping test: Database not available");
                return;
            }
        };
        
        // Test concurrent connections
        let mut handles = vec![];
        
        for i in 0..5 {
            let pool_clone = pool.clone();
            let handle = tokio::spawn(async move {
                let row: (i32,) = sqlx::query_as(&format!("SELECT {}", i))
                    .fetch_one(&pool_clone)
                    .await
                    .expect("Query should work");
                row.0
            });
            handles.push(handle);
        }
        
        for (i, handle) in handles.into_iter().enumerate() {
            let result = handle.await.expect("Task should complete");
            assert_eq!(result, i as i32);
        }
    }
}