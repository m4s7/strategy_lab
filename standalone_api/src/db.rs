use sqlx::{PgPool, postgres::PgPoolOptions};
use std::env;
use uuid::Uuid;
use chrono::{DateTime, Utc};
use serde_json::Value as JsonValue;
use std::collections::HashMap;

#[derive(Debug, Clone)]
pub struct Database {
    pub pool: PgPool,
}

impl Database {
    pub async fn new() -> Result<Self, sqlx::Error> {
        let database_url = env::var("DATABASE_URL")
            .unwrap_or_else(|_| "postgresql://strategy_user:strategy_pass@localhost:5432/strategy_lab".to_string());
        
        let pool = PgPoolOptions::new()
            .max_connections(10)
            .connect(&database_url)
            .await?;
        
        Ok(Database { pool })
    }
    
    // Strategy operations
    pub async fn get_all_strategies(&self) -> Result<Vec<Strategy>, sqlx::Error> {
        let strategies = sqlx::query_as!(
            Strategy,
            r#"
            SELECT 
                id,
                name,
                description,
                strategy_type as "strategy_type",
                status,
                sharpe,
                win_rate,
                total_trades,
                parameters as "parameters: JsonValue",
                created_at,
                updated_at
            FROM strategies
            ORDER BY updated_at DESC
            "#
        )
        .fetch_all(&self.pool)
        .await?;
        
        Ok(strategies)
    }
    
    pub async fn get_strategy(&self, id: Uuid) -> Result<Option<Strategy>, sqlx::Error> {
        let strategy = sqlx::query_as!(
            Strategy,
            r#"
            SELECT 
                id,
                name,
                description,
                strategy_type as "strategy_type",
                status,
                sharpe,
                win_rate,
                total_trades,
                parameters as "parameters: JsonValue",
                created_at,
                updated_at
            FROM strategies
            WHERE id = $1
            "#,
            id
        )
        .fetch_optional(&self.pool)
        .await?;
        
        Ok(strategy)
    }
    
    pub async fn create_strategy(&self, req: CreateStrategyRequest) -> Result<Strategy, sqlx::Error> {
        let id = Uuid::new_v4();
        let now = Utc::now();
        let parameters = req.parameters.unwrap_or_else(|| JsonValue::Object(Default::default()));
        
        let strategy = sqlx::query_as!(
            Strategy,
            r#"
            INSERT INTO strategies (id, name, description, strategy_type, status, parameters, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING 
                id,
                name,
                description,
                strategy_type as "strategy_type",
                status,
                sharpe,
                win_rate,
                total_trades,
                parameters as "parameters: JsonValue",
                created_at,
                updated_at
            "#,
            id,
            req.name,
            req.description,
            req.strategy_type,
            req.status.unwrap_or_else(|| "draft".to_string()),
            parameters,
            now,
            now
        )
        .fetch_one(&self.pool)
        .await?;
        
        Ok(strategy)
    }
    
    pub async fn update_strategy(&self, id: Uuid, req: UpdateStrategyRequest) -> Result<Option<Strategy>, sqlx::Error> {
        // Build dynamic update query based on provided fields
        let strategy = sqlx::query_as!(
            Strategy,
            r#"
            UPDATE strategies 
            SET 
                name = COALESCE($2, name),
                description = COALESCE($3, description),
                strategy_type = COALESCE($4, strategy_type),
                status = COALESCE($5, status),
                sharpe = COALESCE($6, sharpe),
                win_rate = COALESCE($7, win_rate),
                total_trades = COALESCE($8, total_trades),
                parameters = COALESCE($9, parameters),
                updated_at = NOW()
            WHERE id = $1
            RETURNING 
                id,
                name,
                description,
                strategy_type as "strategy_type",
                status,
                sharpe,
                win_rate,
                total_trades,
                parameters as "parameters: JsonValue",
                created_at,
                updated_at
            "#,
            id,
            req.name,
            req.description,
            req.strategy_type,
            req.status,
            req.sharpe,
            req.win_rate,
            req.total_trades,
            req.parameters
        )
        .fetch_optional(&self.pool)
        .await?;
        
        Ok(strategy)
    }
    
    pub async fn delete_strategy(&self, id: Uuid) -> Result<bool, sqlx::Error> {
        let result = sqlx::query!(
            "DELETE FROM strategies WHERE id = $1",
            id
        )
        .execute(&self.pool)
        .await?;
        
        Ok(result.rows_affected() > 0)
    }
    
    // Backtest operations
    pub async fn create_backtest(&self, req: BacktestRequest) -> Result<BacktestResult, sqlx::Error> {
        let id = Uuid::new_v4();
        let strategy_id = Uuid::parse_str(&req.strategy).ok();
        
        // Simulate backtest results
        let metrics = BacktestMetrics {
            total_return: 0.245,
            total_return_amount: 24500.0,
            sharpe_ratio: 1.82,
            max_drawdown: -0.083,
            win_rate: 0.62,
            total_trades: 500,
        };
        
        // Insert backtest record
        sqlx::query!(
            r#"
            INSERT INTO backtests (
                id, strategy_id, status, initial_capital, 
                start_date, end_date, total_return, total_return_amount,
                sharpe_ratio, max_drawdown, win_rate, total_trades,
                created_at, completed_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, NOW(), NOW())
            "#,
            id,
            strategy_id,
            "completed",
            req.initial_capital.unwrap_or(100000.0),
            req.start_date.and_then(|s| chrono::NaiveDate::parse_from_str(&s, "%Y-%m-%d").ok()),
            req.end_date.and_then(|s| chrono::NaiveDate::parse_from_str(&s, "%Y-%m-%d").ok()),
            metrics.total_return,
            metrics.total_return_amount,
            metrics.sharpe_ratio,
            metrics.max_drawdown,
            metrics.win_rate,
            metrics.total_trades
        )
        .execute(&self.pool)
        .await?;
        
        // Insert equity curve points
        let mut equity_points = Vec::new();
        let base_time = Utc::now();
        for i in 0..100 {
            let time = base_time - chrono::Duration::days(100 - i);
            let value = 100000.0 + (24500.0 * (i as f64 / 100.0));
            
            sqlx::query!(
                "INSERT INTO equity_points (backtest_id, time, value, day_number) VALUES ($1, $2, $3, $4)",
                id,
                time,
                value,
                i as i32 + 1
            )
            .execute(&self.pool)
            .await?;
            
            equity_points.push(EquityPoint {
                day: i + 1,
                value,
            });
        }
        
        Ok(BacktestResult {
            id: id.to_string(),
            status: "completed".to_string(),
            strategy: req.strategy,
            metrics,
            equity_curve: equity_points,
        })
    }
    
    // System metrics operations
    pub async fn insert_system_metrics(&self, metrics: &SystemMetrics) -> Result<(), sqlx::Error> {
        sqlx::query!(
            r#"
            INSERT INTO system_metrics (
                time, cpu_usage, memory_used, memory_total, 
                disk_io, threads_active, api_latency_ms, active_strategies
            )
            VALUES (NOW(), $1, $2, $3, $4, $5, $6, $7)
            "#,
            metrics.cpu_usage,
            metrics.memory_used,
            metrics.memory_total,
            metrics.disk_io,
            metrics.threads_active,
            metrics.api_latency_ms,
            metrics.active_strategies
        )
        .execute(&self.pool)
        .await?;
        
        Ok(())
    }
    
    pub async fn get_recent_metrics(&self, minutes: i32) -> Result<Vec<SystemMetrics>, sqlx::Error> {
        let interval = format!("{} minutes", minutes);
        let metrics = sqlx::query_as!(
            SystemMetricsRow,
            r#"
            SELECT 
                time as "time!",
                cpu_usage as "cpu_usage!",
                memory_used as "memory_used!",
                memory_total as "memory_total!",
                disk_io as "disk_io!",
                threads_active as "threads_active!",
                api_latency_ms,
                active_strategies
            FROM system_metrics
            WHERE time > NOW() - INTERVAL '1 minute' * $1
            ORDER BY time DESC
            "#,
            minutes
        )
        .fetch_all(&self.pool)
        .await?;
        
        Ok(metrics.into_iter().map(|m| m.into()).collect())
    }
}

// Data models
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct Strategy {
    pub id: Uuid,
    pub name: String,
    pub description: Option<String>,
    pub strategy_type: String,
    pub status: String,
    pub sharpe: Option<f64>,
    pub win_rate: Option<f64>,
    pub total_trades: Option<i32>,
    pub parameters: JsonValue,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

#[derive(Debug, Clone, serde::Deserialize)]
pub struct CreateStrategyRequest {
    pub name: String,
    pub description: Option<String>,
    #[serde(rename = "type")]
    pub strategy_type: String,
    pub status: Option<String>,
    pub parameters: Option<JsonValue>,
}

#[derive(Debug, Clone, serde::Deserialize)]
pub struct UpdateStrategyRequest {
    pub name: Option<String>,
    pub description: Option<String>,
    #[serde(rename = "type")]
    pub strategy_type: Option<String>,
    pub status: Option<String>,
    pub sharpe: Option<f64>,
    pub win_rate: Option<f64>,
    pub total_trades: Option<i32>,
    pub parameters: Option<JsonValue>,
}

#[derive(Debug, Clone, serde::Deserialize)]
pub struct BacktestRequest {
    pub strategy: String,
    pub initial_capital: Option<f64>,
    pub start_date: Option<String>,
    pub end_date: Option<String>,
}

#[derive(Debug, Clone, serde::Serialize)]
pub struct BacktestResult {
    pub id: String,
    pub status: String,
    pub strategy: String,
    pub metrics: BacktestMetrics,
    pub equity_curve: Vec<EquityPoint>,
}

#[derive(Debug, Clone, serde::Serialize)]
pub struct BacktestMetrics {
    pub total_return: f64,
    pub total_return_amount: f64,
    pub sharpe_ratio: f64,
    pub max_drawdown: f64,
    pub win_rate: f64,
    pub total_trades: i32,
}

#[derive(Debug, Clone, serde::Serialize)]
pub struct EquityPoint {
    pub day: i64,
    pub value: f64,
}

#[derive(Debug, Clone, serde::Serialize)]
pub struct SystemMetrics {
    pub timestamp: String,
    pub cpu_usage: f64,
    pub memory_used: f64,
    pub memory_total: f64,
    pub disk_io: f64,
    pub threads_active: i32,
    pub api_latency_ms: Option<f64>,
    pub active_strategies: Option<i32>,
}

// Helper struct for database queries
struct SystemMetricsRow {
    pub time: DateTime<Utc>,
    pub cpu_usage: f64,
    pub memory_used: f64,
    pub memory_total: f64,
    pub disk_io: f64,
    pub threads_active: i32,
    pub api_latency_ms: Option<f64>,
    pub active_strategies: Option<i32>,
}

impl From<SystemMetricsRow> for SystemMetrics {
    fn from(row: SystemMetricsRow) -> Self {
        SystemMetrics {
            timestamp: row.time.to_rfc3339(),
            cpu_usage: row.cpu_usage,
            memory_used: row.memory_used,
            memory_total: row.memory_total,
            disk_io: row.disk_io,
            threads_active: row.threads_active,
            api_latency_ms: row.api_latency_ms,
            active_strategies: row.active_strategies,
        }
    }
}