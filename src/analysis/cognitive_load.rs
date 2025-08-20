//! Cognitive load management for strategy analysis results

use crate::backtesting::BacktestResult;
use crate::optimization::OptimizationResult;
use crate::statistics::StatisticalTest;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use tracing::{info, debug};

/// Confidence level for result reliability
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ConfidenceLevel {
    VeryHigh,  // >95% confidence
    High,      // 90-95% confidence
    Medium,    // 70-90% confidence  
    Low,       // 50-70% confidence
    VeryLow,   // <50% confidence
}

impl ConfidenceLevel {
    pub fn from_percentage(pct: f64) -> Self {
        match pct {
            p if p >= 95.0 => ConfidenceLevel::VeryHigh,
            p if p >= 90.0 => ConfidenceLevel::High,
            p if p >= 70.0 => ConfidenceLevel::Medium,
            p if p >= 50.0 => ConfidenceLevel::Low,
            _ => ConfidenceLevel::VeryLow,
        }
    }
    
    pub fn to_percentage(&self) -> f64 {
        match self {
            ConfidenceLevel::VeryHigh => 97.5,
            ConfidenceLevel::High => 92.5,
            ConfidenceLevel::Medium => 80.0,
            ConfidenceLevel::Low => 60.0,
            ConfidenceLevel::VeryLow => 25.0,
        }
    }
    
    pub fn color_code(&self) -> &'static str {
        match self {
            ConfidenceLevel::VeryHigh => "#4CAF50", // Green
            ConfidenceLevel::High => "#8BC34A",     // Light Green
            ConfidenceLevel::Medium => "#FF9800",   // Orange
            ConfidenceLevel::Low => "#FF5722",      // Deep Orange
            ConfidenceLevel::VeryLow => "#F44336",  // Red
        }
    }
    
    pub fn icon(&self) -> &'static str {
        match self {
            ConfidenceLevel::VeryHigh => "✅",
            ConfidenceLevel::High => "✅",
            ConfidenceLevel::Medium => "⚠️",
            ConfidenceLevel::Low => "⚠️",
            ConfidenceLevel::VeryLow => "❌",
        }
    }
}

/// Multi-criteria ranking system for optimization results
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RankingCriteria {
    pub weights: HashMap<String, f64>,
    pub thresholds: HashMap<String, f64>,
    pub penalties: HashMap<String, f64>,
}

impl Default for RankingCriteria {
    fn default() -> Self {
        let mut weights = HashMap::new();
        weights.insert("sharpe_ratio".to_string(), 0.35);
        weights.insert("max_drawdown".to_string(), 0.25);
        weights.insert("win_rate".to_string(), 0.20);
        weights.insert("profit_factor".to_string(), 0.15);
        weights.insert("trade_frequency".to_string(), 0.05);
        
        let mut thresholds = HashMap::new();
        thresholds.insert("min_sharpe".to_string(), 0.5);
        thresholds.insert("max_drawdown".to_string(), -15.0);
        thresholds.insert("min_trades".to_string(), 50.0);
        
        let mut penalties = HashMap::new();
        penalties.insert("overfitting".to_string(), 0.3);
        penalties.insert("instability".to_string(), 0.2);
        penalties.insert("low_significance".to_string(), 0.25);
        
        Self { weights, thresholds, penalties }
    }
}

/// Comprehensive result ranking with confidence indicators
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ResultRanking {
    pub composite_score: f64,
    pub individual_scores: HashMap<String, f64>,
    pub ranking_explanation: String,
    pub confidence_level: ConfidenceLevel,
    pub confidence_components: ConfidenceComponents,
    pub warnings: Vec<String>,
    pub recommendations: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ConfidenceComponents {
    pub statistical_significance: ConfidenceLevel,
    pub sample_size_adequacy: ConfidenceLevel,
    pub parameter_stability: ConfidenceLevel,
    pub out_of_sample_consistency: ConfidenceLevel,
    pub overall_confidence: ConfidenceLevel,
}

/// Progressive disclosure levels for result presentation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProgressiveDisclosure {
    pub level1_essential: EssentialMetrics,
    pub level2_detailed: DetailedMetrics,
    pub level3_advanced: AdvancedMetrics,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EssentialMetrics {
    pub composite_ranking: f64,
    pub key_metrics: HashMap<String, f64>,
    pub confidence_indicator: ConfidenceLevel,
    pub recommendation: RecommendationLevel,
    pub quick_summary: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DetailedMetrics {
    pub all_performance_metrics: HashMap<String, f64>,
    pub trade_analysis: TradeSummary,
    pub parameter_values: HashMap<String, f64>,
    pub statistical_tests: Vec<StatisticalValidation>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AdvancedMetrics {
    pub parameter_sensitivity: HashMap<String, f64>,
    pub robustness_tests: Vec<RobustnessTest>,
    pub debugging_info: HashMap<String, serde_json::Value>,
    pub raw_statistics: HashMap<String, f64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TradeSummary {
    pub total_trades: usize,
    pub winning_trades: usize,
    pub losing_trades: usize,
    pub avg_win: f64,
    pub avg_loss: f64,
    pub avg_duration_ms: f64,
    pub max_consecutive_wins: usize,
    pub max_consecutive_losses: usize,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StatisticalValidation {
    pub test_name: String,
    pub test_result: StatisticalTest,
    pub interpretation: String,
    pub confidence: ConfidenceLevel,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RobustnessTest {
    pub test_name: String,
    pub result: f64,
    pub threshold: f64,
    pub passed: bool,
    pub explanation: String,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub enum RecommendationLevel {
    StronglyRecommended,
    Recommended,
    Conditional,
    NotRecommended,
    StronglyDiscouraged,
}

impl RecommendationLevel {
    pub fn from_score(score: f64) -> Self {
        match score {
            s if s >= 85.0 => RecommendationLevel::StronglyRecommended,
            s if s >= 70.0 => RecommendationLevel::Recommended,
            s if s >= 50.0 => RecommendationLevel::Conditional,
            s if s >= 30.0 => RecommendationLevel::NotRecommended,
            _ => RecommendationLevel::StronglyDiscouraged,
        }
    }
    
    pub fn color_code(&self) -> &'static str {
        match self {
            RecommendationLevel::StronglyRecommended => "#4CAF50",
            RecommendationLevel::Recommended => "#8BC34A",
            RecommendationLevel::Conditional => "#FF9800",
            RecommendationLevel::NotRecommended => "#FF5722",
            RecommendationLevel::StronglyDiscouraged => "#F44336",
        }
    }
    
    pub fn description(&self) -> &'static str {
        match self {
            RecommendationLevel::StronglyRecommended => "Excellent strategy - ready for live testing",
            RecommendationLevel::Recommended => "Good strategy - verify with additional validation",
            RecommendationLevel::Conditional => "Promising but needs improvement",
            RecommendationLevel::NotRecommended => "Poor performance - significant issues",
            RecommendationLevel::StronglyDiscouraged => "Unsuitable for trading",
        }
    }
}

/// Cognitive load management engine
pub struct CognitiveLoadManager {
    ranking_criteria: RankingCriteria,
    explanation_templates: HashMap<String, ContextualExplanation>,
}

impl CognitiveLoadManager {
    pub fn new() -> Self {
        Self {
            ranking_criteria: RankingCriteria::default(),
            explanation_templates: Self::create_explanation_templates(),
        }
    }
    
    pub fn with_custom_criteria(criteria: RankingCriteria) -> Self {
        Self {
            ranking_criteria: criteria,
            explanation_templates: Self::create_explanation_templates(),
        }
    }
    
    /// Rank multiple optimization results with cognitive load management
    pub fn rank_results(&self, results: &[OptimizationResult]) -> Vec<(usize, ResultRanking)> {
        let mut ranked_results = Vec::new();
        
        info!("Ranking {} optimization results", results.len());
        
        for (index, result) in results.iter().enumerate() {
            let ranking = self.calculate_ranking(result);
            ranked_results.push((index, ranking));
        }
        
        // Sort by composite score (descending)
        ranked_results.sort_by(|a, b| b.1.composite_score.partial_cmp(&a.1.composite_score).unwrap());
        
        info!("Results ranked - top score: {:.2}", ranked_results.first().map_or(0.0, |(_, r)| r.composite_score));
        
        ranked_results
    }
    
    /// Calculate comprehensive ranking for a single result
    fn calculate_ranking(&self, result: &OptimizationResult) -> ResultRanking {
        let mut individual_scores = HashMap::new();
        let mut warnings = Vec::new();
        let mut recommendations = Vec::new();
        
        // Calculate individual metric scores (0-100 scale)
        let sharpe_score = self.score_sharpe_ratio(result.best_result.performance.sharpe_ratio);
        let drawdown_score = self.score_max_drawdown(result.best_result.performance.max_drawdown);
        let win_rate_score = self.score_win_rate(result.best_result.performance.win_rate);
        let profit_factor_score = self.score_profit_factor(result.best_result.performance.profit_factor);
        let trade_freq_score = self.score_trade_frequency(result.best_result.total_trades);
        
        individual_scores.insert("sharpe_ratio".to_string(), sharpe_score);
        individual_scores.insert("max_drawdown".to_string(), drawdown_score);
        individual_scores.insert("win_rate".to_string(), win_rate_score);
        individual_scores.insert("profit_factor".to_string(), profit_factor_score);
        individual_scores.insert("trade_frequency".to_string(), trade_freq_score);
        
        // Calculate composite score using weights
        let mut composite_score = 0.0;
        for (metric, score) in &individual_scores {
            if let Some(&weight) = self.ranking_criteria.weights.get(metric) {
                composite_score += score * weight;
            }
        }
        
        // Apply penalties for common issues
        let penalties = self.calculate_penalties(result);
        for (penalty_type, penalty_value) in penalties {
            if let Some(&penalty_weight) = self.ranking_criteria.penalties.get(&penalty_type) {
                composite_score *= (1.0 - penalty_weight * penalty_value);
                if penalty_value > 0.0 {
                    warnings.push(format!("Potential {} detected (penalty: {:.1}%)", penalty_type, penalty_value * 100.0));
                }
            }
        }
        
        // Generate confidence assessment
        let confidence_components = self.assess_confidence(result);
        let overall_confidence = self.calculate_overall_confidence(&confidence_components);
        
        // Generate recommendations
        recommendations.extend(self.generate_recommendations(result, &individual_scores, overall_confidence));
        
        // Create ranking explanation
        let ranking_explanation = self.generate_ranking_explanation(&individual_scores, composite_score, overall_confidence);
        
        ResultRanking {
            composite_score,
            individual_scores,
            ranking_explanation,
            confidence_level: overall_confidence,
            confidence_components,
            warnings,
            recommendations,
        }
    }
    
    fn score_sharpe_ratio(&self, sharpe: f64) -> f64 {
        match sharpe {
            s if s >= 2.0 => 100.0,
            s if s >= 1.5 => 85.0 + (s - 1.5) * 30.0,
            s if s >= 1.0 => 70.0 + (s - 1.0) * 30.0,
            s if s >= 0.5 => 50.0 + (s - 0.5) * 40.0,
            s if s >= 0.0 => s * 100.0,
            _ => 0.0,
        }
    }
    
    fn score_max_drawdown(&self, drawdown: f64) -> f64 {
        let dd_pct = drawdown.abs();
        match dd_pct {
            d if d <= 5.0 => 100.0,
            d if d <= 10.0 => 90.0 - (d - 5.0) * 4.0,
            d if d <= 15.0 => 70.0 - (d - 10.0) * 6.0,
            d if d <= 25.0 => 40.0 - (d - 15.0) * 2.0,
            _ => 0.0,
        }
    }
    
    fn score_win_rate(&self, win_rate: f64) -> f64 {
        let wr_pct = win_rate * 100.0;
        match wr_pct {
            w if w >= 70.0 => 100.0,
            w if w >= 60.0 => 85.0 + (w - 60.0) * 1.5,
            w if w >= 50.0 => 70.0 + (w - 50.0) * 1.5,
            w if w >= 40.0 => 50.0 + (w - 40.0) * 2.0,
            _ => win_rate * 100.0,
        }
    }
    
    fn score_profit_factor(&self, pf: f64) -> f64 {
        match pf {
            p if p >= 2.0 => 100.0,
            p if p >= 1.5 => 80.0 + (p - 1.5) * 40.0,
            p if p >= 1.2 => 60.0 + (p - 1.2) * 66.7,
            p if p >= 1.0 => 30.0 + (p - 1.0) * 150.0,
            _ => 0.0,
        }
    }
    
    fn score_trade_frequency(&self, trades: u32) -> f64 {
        match trades {
            t if t >= 200 => 100.0,
            t if t >= 100 => 80.0 + (t - 100) as f64 * 0.2,
            t if t >= 50 => 60.0 + (t - 50) as f64 * 0.4,
            t if t >= 20 => 30.0 + (t - 20) as f64 * 1.0,
            t if t >= 10 => t as f64 * 2.0,
            _ => 0.0,
        }
    }
    
    fn calculate_penalties(&self, result: &OptimizationResult) -> HashMap<String, f64> {
        let mut penalties = HashMap::new();
        
        // Overfitting penalty based on parameter count vs trades
        let param_count = result.parameters.len() as f64;
        let trade_count = result.best_result.total_trades as f64;
        let trades_per_param = trade_count / param_count.max(1.0);
        
        if trades_per_param < 10.0 {
            penalties.insert("overfitting".to_string(), 0.5);
        } else if trades_per_param < 20.0 {
            penalties.insert("overfitting".to_string(), 0.3);
        } else if trades_per_param < 30.0 {
            penalties.insert("overfitting".to_string(), 0.1);
        }
        
        // Instability penalty (placeholder - would need historical data)
        if result.best_result.performance.sharpe_ratio > 3.0 {
            penalties.insert("instability".to_string(), 0.2);
        }
        
        // Low significance penalty (would need statistical tests)
        if result.best_result.total_trades < 30 {
            penalties.insert("low_significance".to_string(), 0.4);
        }
        
        penalties
    }
    
    fn assess_confidence(&self, result: &OptimizationResult) -> ConfidenceComponents {
        // Statistical significance based on trade count and performance
        let stat_sig = if result.best_result.total_trades >= 100 && result.best_result.performance.sharpe_ratio > 1.0 {
            ConfidenceLevel::High
        } else if result.best_result.total_trades >= 50 {
            ConfidenceLevel::Medium
        } else {
            ConfidenceLevel::Low
        };
        
        // Sample size adequacy
        let sample_size = if result.best_result.total_trades >= 200 {
            ConfidenceLevel::VeryHigh
        } else if result.best_result.total_trades >= 100 {
            ConfidenceLevel::High
        } else if result.best_result.total_trades >= 50 {
            ConfidenceLevel::Medium
        } else {
            ConfidenceLevel::Low
        };
        
        // Parameter stability (simplified)
        let param_stability = if result.parameters.len() <= 3 {
            ConfidenceLevel::High
        } else if result.parameters.len() <= 5 {
            ConfidenceLevel::Medium
        } else {
            ConfidenceLevel::Low
        };
        
        // Out-of-sample consistency (would need walk-forward data)
        let oos_consistency = ConfidenceLevel::Medium;
        
        ConfidenceComponents {
            statistical_significance: stat_sig,
            sample_size_adequacy: sample_size,
            parameter_stability: param_stability,
            out_of_sample_consistency: oos_consistency,
            overall_confidence: stat_sig, // Simplified
        }
    }
    
    fn calculate_overall_confidence(&self, components: &ConfidenceComponents) -> ConfidenceLevel {
        let confidence_scores = vec![
            components.statistical_significance.to_percentage(),
            components.sample_size_adequacy.to_percentage(),
            components.parameter_stability.to_percentage(),
            components.out_of_sample_consistency.to_percentage(),
        ];
        
        let avg_confidence = confidence_scores.iter().sum::<f64>() / confidence_scores.len() as f64;
        ConfidenceLevel::from_percentage(avg_confidence)
    }
    
    fn generate_recommendations(&self, result: &OptimizationResult, scores: &HashMap<String, f64>, confidence: ConfidenceLevel) -> Vec<String> {
        let mut recommendations = Vec::new();
        
        // Sharpe ratio recommendations
        if let Some(&sharpe_score) = scores.get("sharpe_ratio") {
            if sharpe_score < 50.0 {
                recommendations.push("Consider strategies with higher risk-adjusted returns".to_string());
            }
        }
        
        // Drawdown recommendations  
        if let Some(&dd_score) = scores.get("max_drawdown") {
            if dd_score < 60.0 {
                recommendations.push("Reduce position sizing or add risk management rules".to_string());
            }
        }
        
        // Trade frequency recommendations
        if result.best_result.total_trades < 50 {
            recommendations.push("Increase sample size with more historical data or longer testing period".to_string());
        }
        
        // Confidence-based recommendations
        match confidence {
            ConfidenceLevel::VeryLow | ConfidenceLevel::Low => {
                recommendations.push("Perform additional validation before live trading".to_string());
            }
            ConfidenceLevel::Medium => {
                recommendations.push("Consider paper trading before live deployment".to_string());
            }
            _ => {}
        }
        
        recommendations
    }
    
    fn generate_ranking_explanation(&self, scores: &HashMap<String, f64>, composite: f64, confidence: ConfidenceLevel) -> String {
        let top_metric = scores.iter()
            .max_by(|a, b| a.1.partial_cmp(b.1).unwrap())
            .map(|(k, v)| (k.clone(), *v))
            .unwrap_or(("none".to_string(), 0.0));
        
        format!(
            "Composite score: {:.1}/100. Strongest performance in {} ({:.1}/100). Confidence: {:?}",
            composite, top_metric.0.replace('_', " "), top_metric.1, confidence
        )
    }
    
    /// Create progressive disclosure view for a result
    pub fn create_progressive_disclosure(&self, result: &OptimizationResult, ranking: &ResultRanking) -> ProgressiveDisclosure {
        let essential = self.create_essential_metrics(result, ranking);
        let detailed = self.create_detailed_metrics(result, ranking);
        let advanced = self.create_advanced_metrics(result, ranking);
        
        ProgressiveDisclosure {
            level1_essential: essential,
            level2_detailed: detailed,
            level3_advanced: advanced,
        }
    }
    
    fn create_essential_metrics(&self, result: &OptimizationResult, ranking: &ResultRanking) -> EssentialMetrics {
        let mut key_metrics = HashMap::new();
        key_metrics.insert("sharpe".to_string(), result.best_result.performance.sharpe_ratio);
        key_metrics.insert("max_drawdown".to_string(), result.best_result.performance.max_drawdown);
        key_metrics.insert("win_rate".to_string(), result.best_result.performance.win_rate * 100.0);
        
        let recommendation = RecommendationLevel::from_score(ranking.composite_score);
        let quick_summary = format!(
            "{:.1}/100 score - {} ({} trades)",
            ranking.composite_score,
            recommendation.description(),
            result.best_result.total_trades
        );
        
        EssentialMetrics {
            composite_ranking: ranking.composite_score,
            key_metrics,
            confidence_indicator: ranking.confidence_level,
            recommendation,
            quick_summary,
        }
    }
    
    fn create_detailed_metrics(&self, result: &OptimizationResult, _ranking: &ResultRanking) -> DetailedMetrics {
        let mut all_metrics = HashMap::new();
        all_metrics.insert("total_return".to_string(), result.best_result.performance.total_return);
        all_metrics.insert("sharpe_ratio".to_string(), result.best_result.performance.sharpe_ratio);
        all_metrics.insert("max_drawdown".to_string(), result.best_result.performance.max_drawdown);
        all_metrics.insert("win_rate".to_string(), result.best_result.performance.win_rate);
        all_metrics.insert("profit_factor".to_string(), result.best_result.performance.profit_factor);
        all_metrics.insert("avg_trade_return".to_string(), result.best_result.performance.avg_trade_return);
        
        let trade_summary = TradeSummary {
            total_trades: result.best_result.total_trades as usize,
            winning_trades: result.best_result.winning_trades as usize,
            losing_trades: (result.best_result.total_trades - result.best_result.winning_trades) as usize,
            avg_win: result.best_result.performance.avg_win,
            avg_loss: result.best_result.performance.avg_loss,
            avg_duration_ms: 0.0, // Would need trade-level data
            max_consecutive_wins: 0,
            max_consecutive_losses: 0,
        };
        
        DetailedMetrics {
            all_performance_metrics: all_metrics,
            trade_analysis: trade_summary,
            parameter_values: result.parameters.clone(),
            statistical_tests: Vec::new(), // Would populate with actual tests
        }
    }
    
    fn create_advanced_metrics(&self, result: &OptimizationResult, _ranking: &ResultRanking) -> AdvancedMetrics {
        let mut sensitivity = HashMap::new();
        for param_name in result.parameters.keys() {
            sensitivity.insert(param_name.clone(), 0.1); // Placeholder
        }
        
        AdvancedMetrics {
            parameter_sensitivity: sensitivity,
            robustness_tests: Vec::new(),
            debugging_info: HashMap::new(),
            raw_statistics: HashMap::new(),
        }
    }
    
    fn create_explanation_templates() -> HashMap<String, ContextualExplanation> {
        let mut templates = HashMap::new();
        
        templates.insert("sharpe_ratio".to_string(), ContextualExplanation {
            metric_name: "Sharpe Ratio".to_string(),
            simple_explanation: "Risk-adjusted return measure".to_string(),
            trading_relevance: "Higher values indicate better return per unit of risk".to_string(),
            interpretation_guide: "Values >1.0 are good, >2.0 are excellent for trading strategies".to_string(),
            common_mistakes: vec![
                "Ignoring the underlying volatility".to_string(),
                "Comparing across different timeframes".to_string(),
            ],
            value_ranges: HashMap::from([
                ("< 0.5".to_string(), ValueInterpretation {
                    meaning: "Poor risk-adjusted performance".to_string(),
                    implications: "Strategy may not be viable for live trading".to_string(),
                    recommendations: vec![
                        "Review strategy logic".to_string(),
                        "Consider parameter optimization".to_string(),
                    ],
                }),
                ("0.5 - 1.0".to_string(), ValueInterpretation {
                    meaning: "Acceptable risk-adjusted performance".to_string(),
                    implications: "Strategy shows promise but needs improvement".to_string(),
                    recommendations: vec![
                        "Optimize parameters".to_string(),
                        "Validate with out-of-sample data".to_string(),
                    ],
                }),
            ]),
        });
        
        templates
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContextualExplanation {
    pub metric_name: String,
    pub simple_explanation: String,
    pub trading_relevance: String,
    pub interpretation_guide: String,
    pub common_mistakes: Vec<String>,
    pub value_ranges: HashMap<String, ValueInterpretation>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ValueInterpretation {
    pub meaning: String,
    pub implications: String,
    pub recommendations: Vec<String>,
}

impl Default for CognitiveLoadManager {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::backtesting::PerformanceMetrics;
    use std::collections::HashMap;
    
    #[test]
    fn test_confidence_level_conversion() {
        assert_eq!(ConfidenceLevel::from_percentage(96.0), ConfidenceLevel::VeryHigh);
        assert_eq!(ConfidenceLevel::from_percentage(85.0), ConfidenceLevel::Medium);
        assert_eq!(ConfidenceLevel::from_percentage(40.0), ConfidenceLevel::VeryLow);
    }
    
    #[test]
    fn test_recommendation_level_from_score() {
        assert_eq!(RecommendationLevel::from_score(90.0), RecommendationLevel::StronglyRecommended);
        assert_eq!(RecommendationLevel::from_score(75.0), RecommendationLevel::Recommended);
        assert_eq!(RecommendationLevel::from_score(45.0), RecommendationLevel::Conditional);
        assert_eq!(RecommendationLevel::from_score(20.0), RecommendationLevel::StronglyDiscouraged);
    }
    
    #[test]
    fn test_sharpe_ratio_scoring() {
        let manager = CognitiveLoadManager::new();
        assert_eq!(manager.score_sharpe_ratio(2.0), 100.0);
        assert!(manager.score_sharpe_ratio(1.5) > 80.0);
        assert!(manager.score_sharpe_ratio(0.5) < 60.0);
        assert_eq!(manager.score_sharpe_ratio(-0.5), 0.0);
    }
}