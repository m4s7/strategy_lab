use crate::backtesting::{BacktestResult, PerformanceMetrics};
use chrono::{DateTime, Utc};
use rust_decimal::Decimal;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BacktestReport {
    pub summary: ReportSummary,
    pub performance: PerformanceMetrics,
    pub trades: Vec<TradeReport>,
    pub equity_curve: Vec<EquityPoint>,
    pub drawdown_curve: Vec<DrawdownPoint>,
    pub monthly_returns: HashMap<String, Decimal>,
    pub recommendations: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ReportSummary {
    pub strategy_name: String,
    pub test_period_start: DateTime<Utc>,
    pub test_period_end: DateTime<Utc>,
    pub total_ticks_processed: u64,
    pub total_trades: u32,
    pub final_pnl: Decimal,
    pub confidence_level: ConfidenceLevel,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TradeReport {
    pub entry_time: DateTime<Utc>,
    pub exit_time: DateTime<Utc>,
    pub side: String,
    pub entry_price: Decimal,
    pub exit_price: Decimal,
    pub quantity: u32,
    pub pnl: Decimal,
    pub duration_ms: u64,
    pub max_adverse_excursion: Decimal,
    pub max_favorable_excursion: Decimal,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EquityPoint {
    pub timestamp: DateTime<Utc>,
    pub equity: Decimal,
    pub cumulative_pnl: Decimal,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DrawdownPoint {
    pub timestamp: DateTime<Utc>,
    pub drawdown_pct: f64,
    pub underwater_duration_ms: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ConfidenceLevel {
    High,
    Medium,
    Low,
    VeryLow,
}

impl BacktestReport {
    pub fn from_result(result: &BacktestResult, strategy_name: &str) -> Self {
        let mut trades = Vec::new();
        let mut equity_curve = Vec::new();
        let mut drawdown_curve = Vec::new();
        let monthly_returns = HashMap::new(); // TODO: Calculate monthly returns

        // Convert trades
        for trade in &result.trades {
            trades.push(TradeReport {
                entry_time: DateTime::from_timestamp_nanos(trade.entry_timestamp as i64).unwrap(),
                exit_time: DateTime::from_timestamp_nanos(trade.exit_timestamp as i64).unwrap(),
                side: if trade.side == crate::strategy::orders::OrderSide::Buy { "Buy" } else { "Sell" }.to_string(),
                entry_price: trade.entry_price,
                exit_price: trade.exit_price,
                quantity: trade.quantity,
                pnl: trade.pnl,
                duration_ms: (trade.exit_timestamp - trade.entry_timestamp) / 1_000_000, // Convert from nanoseconds
                max_adverse_excursion: trade.max_adverse_excursion,
                max_favorable_excursion: trade.max_favorable_excursion,
            });
        }

        // Create equity curve from trades
        let mut cumulative_pnl = Decimal::ZERO;
        for (i, trade) in result.trades.iter().enumerate() {
            cumulative_pnl += trade.pnl;
            equity_curve.push(EquityPoint {
                timestamp: DateTime::from_timestamp_nanos(trade.exit_timestamp as i64).unwrap(),
                equity: result.initial_capital + cumulative_pnl,
                cumulative_pnl,
            });
        }

        // Calculate confidence level
        let confidence_level = match result.performance.sharpe_ratio {
            x if x > 2.0 => ConfidenceLevel::High,
            x if x > 1.0 => ConfidenceLevel::Medium,
            x if x > 0.5 => ConfidenceLevel::Low,
            _ => ConfidenceLevel::VeryLow,
        };

        let summary = ReportSummary {
            strategy_name: strategy_name.to_string(),
            test_period_start: DateTime::from_timestamp_nanos(result.start_time as i64).unwrap(),
            test_period_end: DateTime::from_timestamp_nanos(result.end_time as i64).unwrap(),
            total_ticks_processed: result.ticks_processed,
            total_trades: result.trades.len() as u32,
            final_pnl: cumulative_pnl,
            confidence_level,
        };

        Self {
            summary,
            performance: result.performance.clone(),
            trades,
            equity_curve,
            drawdown_curve,
            monthly_returns,
            recommendations: Self::generate_recommendations(&result.performance),
        }
    }

    fn generate_recommendations(metrics: &PerformanceMetrics) -> Vec<String> {
        let mut recommendations = Vec::new();

        if metrics.sharpe_ratio < 1.0 {
            recommendations.push("Consider adjusting strategy parameters to improve risk-adjusted returns".to_string());
        }

        if metrics.max_drawdown > 0.10 {
            recommendations.push("High maximum drawdown detected. Consider implementing risk management rules".to_string());
        }

        if metrics.win_rate < 0.4 {
            recommendations.push("Low win rate. Review entry and exit conditions".to_string());
        }

        if metrics.profit_factor < 1.2 {
            recommendations.push("Low profit factor. Consider optimizing position sizing or filtering trades".to_string());
        }

        if recommendations.is_empty() {
            recommendations.push("Strategy shows good performance characteristics. Consider live paper trading".to_string());
        }

        recommendations
    }

    pub fn to_html(&self) -> String {
        // Simple HTML report generation
        format!(
            r#"
<!DOCTYPE html>
<html>
<head>
    <title>Backtest Report - {}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .metric {{ margin: 10px 0; }}
        .section {{ margin: 30px 0; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <h1>Backtest Report: {}</h1>
    
    <div class="section">
        <h2>Summary</h2>
        <div class="metric">Total Trades: {}</div>
        <div class="metric">Final P&L: ${}</div>
        <div class="metric">Sharpe Ratio: {:.2}</div>
        <div class="metric">Max Drawdown: {:.2}%</div>
        <div class="metric">Win Rate: {:.1}%</div>
    </div>
    
    <div class="section">
        <h2>Recommendations</h2>
        <ul>
            {}
        </ul>
    </div>
</body>
</html>
            "#,
            self.summary.strategy_name,
            self.summary.strategy_name,
            self.summary.total_trades,
            self.summary.final_pnl,
            self.performance.sharpe_ratio,
            self.performance.max_drawdown * 100.0,
            self.performance.win_rate * 100.0,
            self.recommendations.iter().map(|r| format!("<li>{}</li>", r)).collect::<Vec<_>>().join("")
        )
    }
}