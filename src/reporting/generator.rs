//! Report generation logic

use chrono::Utc;
use crate::backtesting::{BacktestResult, PerformanceMetrics};
use crate::optimization::OptimizationReport;
use super::*;

/// Report generator
pub struct ReportGenerator {
    strategy_name: String,
    author: String,
}

impl ReportGenerator {
    pub fn new(strategy_name: String, author: String) -> Self {
        Self {
            strategy_name,
            author,
        }
    }
    
    /// Generate executive summary from results
    pub fn generate_summary(&self, backtest: &BacktestResult) -> ExecutiveSummary {
        let key_findings = self.analyze_key_findings(backtest);
        
        ExecutiveSummary {
            total_return: backtest.total_return,
            sharpe_ratio: backtest.sharpe_ratio,
            max_drawdown: backtest.max_drawdown,
            win_rate: backtest.win_rate,
            profit_factor: backtest.profit_factor,
            key_findings,
        }
    }
    
    /// Analyze and generate key findings
    fn analyze_key_findings(&self, backtest: &BacktestResult) -> Vec<String> {
        let mut findings = Vec::new();
        
        // Analyze Sharpe ratio
        if backtest.sharpe_ratio > 2.0 {
            findings.push("Excellent risk-adjusted returns with Sharpe ratio > 2.0".to_string());
        } else if backtest.sharpe_ratio > 1.5 {
            findings.push("Good risk-adjusted returns with Sharpe ratio > 1.5".to_string());
        } else if backtest.sharpe_ratio < 1.0 {
            findings.push("Suboptimal risk-adjusted returns - consider parameter optimization".to_string());
        }
        
        // Analyze drawdown
        if backtest.max_drawdown.abs() > 20.0 {
            findings.push("High maximum drawdown exceeds 20% - implement stricter risk controls".to_string());
        } else if backtest.max_drawdown.abs() < 10.0 {
            findings.push("Well-controlled drawdown under 10%".to_string());
        }
        
        // Analyze win rate
        if backtest.win_rate > 0.6 {
            findings.push(format!("Strong win rate of {:.1}%", backtest.win_rate * 100.0));
        } else if backtest.win_rate < 0.4 {
            findings.push("Low win rate - strategy may benefit from entry/exit refinement".to_string());
        }
        
        // Analyze profit factor
        if backtest.profit_factor > 1.5 {
            findings.push("Robust profit factor indicates consistent edge".to_string());
        } else if backtest.profit_factor < 1.2 {
            findings.push("Profit factor near breakeven - strategy needs improvement".to_string());
        }
        
        findings
    }
    
    /// Generate risk analysis
    pub fn generate_risk_analysis(&self, backtest: &BacktestResult) -> RiskAnalysis {
        RiskAnalysis {
            value_at_risk_95: self.calculate_var(backtest, 0.95),
            conditional_var_95: self.calculate_cvar(backtest, 0.95),
            max_consecutive_losses: backtest.max_consecutive_losses,
            recovery_factor: backtest.total_return / backtest.max_drawdown.abs(),
            downside_deviation: self.calculate_downside_deviation(backtest),
            tail_ratio: self.calculate_tail_ratio(backtest),
        }
    }
    
    /// Calculate Value at Risk
    fn calculate_var(&self, backtest: &BacktestResult, confidence: f64) -> f64 {
        // Simplified VaR calculation
        // In production, would use actual return distribution
        let std_dev = backtest.return_std_dev;
        let z_score = 1.645; // 95% confidence
        backtest.avg_return - (z_score * std_dev)
    }
    
    /// Calculate Conditional Value at Risk
    fn calculate_cvar(&self, backtest: &BacktestResult, confidence: f64) -> f64 {
        // Simplified CVaR calculation
        self.calculate_var(backtest, confidence) * 1.25
    }
    
    /// Calculate downside deviation
    fn calculate_downside_deviation(&self, backtest: &BacktestResult) -> f64 {
        // Simplified calculation
        backtest.return_std_dev * 0.7 // Approximate
    }
    
    /// Calculate tail ratio
    fn calculate_tail_ratio(&self, backtest: &BacktestResult) -> f64 {
        // Ratio of 95th percentile gain to 95th percentile loss
        1.2 // Placeholder
    }
    
    /// Generate recommendations based on analysis
    pub fn generate_recommendations(&self, backtest: &BacktestResult) -> Vec<Recommendation> {
        let mut recommendations = Vec::new();
        
        // Risk management recommendations
        if backtest.max_drawdown.abs() > 15.0 {
            recommendations.push(Recommendation {
                category: RecommendationCategory::RiskManagement,
                priority: Priority::High,
                title: "Implement Dynamic Position Sizing".to_string(),
                description: "Consider Kelly Criterion or volatility-based position sizing to reduce drawdown".to_string(),
                impact: "Could reduce maximum drawdown by 20-30%".to_string(),
            });
        }
        
        // Performance recommendations
        if backtest.sharpe_ratio < 1.5 {
            recommendations.push(Recommendation {
                category: RecommendationCategory::ParameterOptimization,
                priority: Priority::Medium,
                title: "Optimize Strategy Parameters".to_string(),
                description: "Run genetic algorithm optimization to find better parameter combinations".to_string(),
                impact: "Potential to improve Sharpe ratio by 15-25%".to_string(),
            });
        }
        
        // Data quality recommendations
        if backtest.total_trades < 100 {
            recommendations.push(Recommendation {
                category: RecommendationCategory::DataQuality,
                priority: Priority::High,
                title: "Increase Sample Size".to_string(),
                description: "Test with longer historical period or lower timeframe for statistical significance".to_string(),
                impact: "Improve confidence in results".to_string(),
            });
        }
        
        // Implementation recommendations
        if backtest.avg_trade_duration < 60.0 {
            recommendations.push(Recommendation {
                category: RecommendationCategory::Implementation,
                priority: Priority::Critical,
                title: "Optimize Execution Infrastructure".to_string(),
                description: "Sub-minute holding periods require low-latency execution infrastructure".to_string(),
                impact: "Critical for strategy viability".to_string(),
            });
        }
        
        recommendations
    }
}