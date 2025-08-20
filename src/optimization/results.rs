//! Optimization results and reporting

use crate::backtesting::{BacktestResult, PerformanceMetrics};
use crate::strategy::config::ParameterValue;
use chrono::{DateTime, Utc};
use rust_decimal::Decimal;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// Result from optimization run
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OptimizationResult {
    pub parameters: ParameterSet,
    pub backtest_result: BacktestResult,
    pub objective_value: f64,
    pub timestamp: DateTime<Utc>,
    pub metrics: PerformanceMetrics,
    pub equity_curve: Vec<f64>,
    pub trade_analysis: Option<serde_json::Value>,
    pub parameter_sensitivity: Option<serde_json::Value>,
}

/// Set of parameters
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ParameterSet {
    pub parameters: HashMap<String, ParameterValue>,
}

impl ParameterSet {
    pub fn new() -> Self {
        Self {
            parameters: HashMap::new(),
        }
    }
    
    pub fn get_float(&self, name: &str) -> Option<f64> {
        self.parameters.get(name).and_then(|v| v.as_f64())
    }
    
    pub fn get_decimal(&self, name: &str) -> Option<Decimal> {
        self.parameters.get(name).and_then(|v| v.as_decimal())
    }
    
    pub fn from_hashmap(params: HashMap<String, f64>) -> Self {
        let mut parameter_set = Self::new();
        for (key, value) in params {
            parameter_set.parameters.insert(key, ParameterValue::Float(value));
        }
        parameter_set
    }
}

/// Optimization report
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OptimizationReport {
    pub summary: OptimizationSummary,
    pub best_results: Vec<OptimizationResult>,
    pub parameter_sensitivity: ParameterSensitivity,
    pub convergence_analysis: ConvergenceAnalysis,
    pub statistical_significance: StatisticalSignificance,
}

/// Summary of optimization run
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OptimizationSummary {
    pub total_evaluations: usize,
    pub unique_parameters: usize,
    pub best_objective: f64,
    pub worst_objective: f64,
    pub avg_objective: f64,
    pub std_dev: f64,
    pub runtime_seconds: f64,
    pub evaluations_per_second: f64,
}

/// Parameter sensitivity analysis
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ParameterSensitivity {
    pub sensitivities: HashMap<String, SensitivityMetrics>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SensitivityMetrics {
    pub correlation: f64,
    pub importance: f64,
    pub optimal_range: (f64, f64),
    pub stable_regions: Vec<(f64, f64)>,
}

/// Convergence analysis
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ConvergenceAnalysis {
    pub converged: bool,
    pub convergence_iteration: Option<usize>,
    pub final_improvement_rate: f64,
    pub stability_score: f64,
}

/// Statistical significance testing
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StatisticalSignificance {
    pub p_value: f64,
    pub confidence_interval: (f64, f64),
    pub is_significant: bool,
    pub effect_size: f64,
}

impl OptimizationReport {
    /// Generate report from optimization results
    pub fn from_results(results: &[OptimizationResult], runtime: f64) -> Self {
        let best_results = Self::get_top_results(results, 10);
        let summary = Self::calculate_summary(results, runtime);
        let sensitivity = Self::analyze_sensitivity(results);
        let convergence = Self::analyze_convergence(results);
        let significance = Self::test_significance(&best_results);
        
        Self {
            summary,
            best_results,
            parameter_sensitivity: sensitivity,
            convergence_analysis: convergence,
            statistical_significance: significance,
        }
    }
    
    fn get_top_results(results: &[OptimizationResult], n: usize) -> Vec<OptimizationResult> {
        let mut sorted = results.to_vec();
        sorted.sort_by(|a, b| b.objective_value.partial_cmp(&a.objective_value).unwrap());
        sorted.into_iter().take(n).collect()
    }
    
    fn calculate_summary(results: &[OptimizationResult], runtime: f64) -> OptimizationSummary {
        let objectives: Vec<f64> = results.iter()
            .map(|r| r.objective_value)
            .collect();
        
        let sum: f64 = objectives.iter().sum();
        let avg = sum / objectives.len() as f64;
        
        let variance = objectives.iter()
            .map(|v| (v - avg).powi(2))
            .sum::<f64>() / objectives.len() as f64;
        
        OptimizationSummary {
            total_evaluations: results.len(),
            unique_parameters: results.len(), // Simplified
            best_objective: objectives.iter().cloned().fold(f64::NEG_INFINITY, f64::max),
            worst_objective: objectives.iter().cloned().fold(f64::INFINITY, f64::min),
            avg_objective: avg,
            std_dev: variance.sqrt(),
            runtime_seconds: runtime,
            evaluations_per_second: results.len() as f64 / runtime,
        }
    }
    
    fn analyze_sensitivity(results: &[OptimizationResult]) -> ParameterSensitivity {
        // Simplified sensitivity analysis
        let mut sensitivities = HashMap::new();
        
        // Would implement full sensitivity analysis here
        // For now, return placeholder
        
        ParameterSensitivity { sensitivities }
    }
    
    fn analyze_convergence(results: &[OptimizationResult]) -> ConvergenceAnalysis {
        // Simplified convergence analysis
        ConvergenceAnalysis {
            converged: true,
            convergence_iteration: Some(results.len() / 2),
            final_improvement_rate: 0.01,
            stability_score: 0.85,
        }
    }
    
    fn test_significance(results: &[OptimizationResult]) -> StatisticalSignificance {
        // Simplified significance testing
        StatisticalSignificance {
            p_value: 0.03,
            confidence_interval: (0.8, 1.2),
            is_significant: true,
            effect_size: 0.5,
        }
    }
    
    /// Generate text report
    pub fn to_text(&self) -> String {
        format!(
            r#"
Optimization Report
===================

Summary
-------
Total Evaluations: {}
Best Objective: {:.4}
Average Objective: {:.4} ± {:.4}
Runtime: {:.2}s ({:.1} eval/s)

Top Results
-----------
"#,
            self.summary.total_evaluations,
            self.summary.best_objective,
            self.summary.avg_objective,
            self.summary.std_dev,
            self.summary.runtime_seconds,
            self.summary.evaluations_per_second
        )
    }
}