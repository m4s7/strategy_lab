//! Reporting and analysis module

pub mod generator;
pub mod templates;
pub mod export;

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::path::PathBuf;

use crate::backtesting::BacktestResult;
use crate::optimization::OptimizationReport;

/// Report format options
#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub enum ReportFormat {
    Html,
    Pdf,
    Json,
    Csv,
    Markdown,
}

/// Complete report structure
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Report {
    pub metadata: ReportMetadata,
    pub summary: ExecutiveSummary,
    pub backtest_results: Option<BacktestReport>,
    pub optimization_results: Option<OptimizationReport>,
    pub risk_analysis: RiskAnalysis,
    pub recommendations: Vec<Recommendation>,
}

/// Report metadata
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ReportMetadata {
    pub generated_at: DateTime<Utc>,
    pub strategy_name: String,
    pub version: String,
    pub author: String,
    pub data_period: DataPeriod,
}

/// Executive summary
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExecutiveSummary {
    pub total_return: f64,
    pub sharpe_ratio: f64,
    pub max_drawdown: f64,
    pub win_rate: f64,
    pub profit_factor: f64,
    pub key_findings: Vec<String>,
}

/// Backtest-specific report
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BacktestReport {
    pub results: BacktestResult,
    pub equity_curve: Vec<(DateTime<Utc>, f64)>,
    pub trade_analysis: TradeAnalysis,
    pub period_returns: Vec<PeriodReturn>,
}

/// Trade analysis
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TradeAnalysis {
    pub total_trades: u32,
    pub winning_trades: u32,
    pub losing_trades: u32,
    pub avg_win: f64,
    pub avg_loss: f64,
    pub largest_win: f64,
    pub largest_loss: f64,
    pub avg_duration_minutes: f64,
    pub trades_per_day: f64,
}

/// Period returns
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PeriodReturn {
    pub period: String,
    pub return_pct: f64,
    pub trades: u32,
    pub sharpe: f64,
}

/// Risk analysis
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RiskAnalysis {
    pub value_at_risk_95: f64,
    pub conditional_var_95: f64,
    pub max_consecutive_losses: u32,
    pub recovery_factor: f64,
    pub downside_deviation: f64,
    pub tail_ratio: f64,
}

/// Recommendations
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Recommendation {
    pub category: RecommendationCategory,
    pub priority: Priority,
    pub title: String,
    pub description: String,
    pub impact: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum RecommendationCategory {
    RiskManagement,
    ParameterOptimization,
    DataQuality,
    Performance,
    Implementation,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum Priority {
    Critical,
    High,
    Medium,
    Low,
}

/// Data period
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DataPeriod {
    pub start: DateTime<Utc>,
    pub end: DateTime<Utc>,
    pub total_days: u32,
    pub trading_days: u32,
}

Impl Report {
    /// Generate a comprehensive report
    pub fn generate(
        backtest: Option<BacktestResult>,
        optimization: Option<OptimizationReport>,
        strategy_name: String,
    ) -> Self {
        // Implementation would generate full report
        todo!("Implement report generation")
    }
    
    /// Export report to file
    pub fn export(&self, path: PathBuf, format: ReportFormat) -> Result<(), Box<dyn std::error::Error>> {
        match format {
            ReportFormat::Html => self.export_html(path),
            ReportFormat::Json => self.export_json(path),
            ReportFormat::Csv => self.export_csv(path),
            ReportFormat::Markdown => self.export_markdown(path),
            ReportFormat::Pdf => self.export_pdf(path),
        }
    }
    
    fn export_html(&self, path: PathBuf) -> Result<(), Box<dyn std::error::Error>> {
        // Generate HTML report
        todo!("Implement HTML export")
    }
    
    fn export_json(&self, path: PathBuf) -> Result<(), Box<dyn std::error::Error>> {
        let json = serde_json::to_string_pretty(self)?;
        std::fs::write(path, json)?;
        Ok(())
    }
    
    fn export_csv(&self, path: PathBuf) -> Result<(), Box<dyn std::error::Error>> {
        // Export key metrics to CSV
        todo!("Implement CSV export")
    }
    
    fn export_markdown(&self, path: PathBuf) -> Result<(), Box<dyn std::error::Error>> {
        // Generate Markdown report
        todo!("Implement Markdown export")
    }
    
    fn export_pdf(&self, path: PathBuf) -> Result<(), Box<dyn std::error::Error>> {
        // Generate PDF report
        todo!("Implement PDF export")
    }
}