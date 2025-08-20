//! Context-sensitive help system

use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use crate::workflow::WorkflowStep;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HelpSystem {
    content_database: HashMap<String, HelpContent>,
    contextual_tips: HashMap<String, Vec<QuickTip>>,
    explanations: HashMap<String, ContextualExplanation>,
    user_preferences: UserHelpPreferences,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HelpContent {
    pub id: String,
    pub title: String,
    pub content: String,
    pub content_type: HelpContentType,
    pub difficulty_level: HelpDifficultyLevel,
    pub tags: Vec<String>,
    pub related_topics: Vec<String>,
    pub examples: Vec<HelpExample>,
    pub interactive_elements: Vec<InteractiveElement>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum HelpContentType {
    QuickTip,
    DetailedExplanation,
    StepByStepGuide,
    VideoTutorial,
    InteractiveDemo,
    TroubleshootingGuide,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub enum HelpDifficultyLevel {
    Beginner,
    Intermediate,
    Advanced,
    Expert,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct QuickTip {
    pub id: String,
    pub trigger: TriggerCondition,
    pub content: String,
    pub timing: TipTiming,
    pub priority: TipPriority,
    pub dismissible: bool,
    pub show_once: bool,
    pub context_filters: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum TriggerCondition {
    Hover(String),
    Focus(String),
    FirstVisit(String),
    OnError(String),
    OnValue(String, String),
    Custom(String),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum TipTiming {
    Immediate,
    Delayed(u32),
    OnAction,
    Contextual,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub enum TipPriority {
    High,
    Medium,
    Low,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContextualExplanation {
    pub metric_name: String,
    pub simple_explanation: String,
    pub trading_relevance: String,
    pub interpretation_guide: String,
    pub common_mistakes: Vec<String>,
    pub related_concepts: Vec<String>,
    pub value_interpretations: HashMap<String, ValueInterpretation>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ValueInterpretation {
    pub range: String,
    pub meaning: String,
    pub implications: String,
    pub recommendations: Vec<String>,
    pub warning_level: WarningLevel,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub enum WarningLevel {
    Safe,
    Caution,
    Warning,
    Critical,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HelpExample {
    pub title: String,
    pub description: String,
    pub code_snippet: Option<String>,
    pub expected_result: String,
    pub common_pitfalls: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct InteractiveElement {
    pub element_type: InteractiveElementType,
    pub content: serde_json::Value,
    pub validation: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum InteractiveElementType {
    GuidedTour,
    HandsOnExercise,
    DecisionSimulation,
    ConceptExplanation,
    ParameterPlayground,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HelpContext {
    pub current_step: String,
    pub user_level: HelpDifficultyLevel,
    pub recent_errors: Vec<String>,
    pub completed_steps: Vec<String>,
    pub user_preferences: UserHelpPreferences,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UserHelpPreferences {
    pub preferred_content_types: Vec<HelpContentType>,
    pub difficulty_level: HelpDifficultyLevel,
    pub show_tips: bool,
    pub auto_explain: bool,
    pub verbose_mode: bool,
    pub dismissed_tips: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DecisionPoint {
    pub step_id: String,
    pub decision_type: DecisionType,
    pub available_options: Vec<DecisionOption>,
    pub context: HashMap<String, serde_json::Value>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum DecisionType {
    ParameterSelection,
    ValidationMethod,
    AnalysisApproach,
    OptimizationStrategy,
    RiskManagement,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DecisionOption {
    pub id: String,
    pub name: String,
    pub description: String,
    pub pros: Vec<String>,
    pub cons: Vec<String>,
    pub when_to_use: String,
    pub complexity_level: HelpDifficultyLevel,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Recommendation {
    pub recommendation_type: RecommendationType,
    pub content: String,
    pub reasoning: String,
    pub confidence: f64,
    pub applicable_contexts: Vec<String>,
    pub examples: Vec<HelpExample>,
    pub related_concepts: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum RecommendationType {
    BestPractice,
    Warning,
    Suggestion,
    Requirement,
    Optimization,
}

impl HelpSystem {
    pub fn new() -> Self {
        let mut system = Self {
            content_database: HashMap::new(),
            contextual_tips: HashMap::new(),
            explanations: HashMap::new(),
            user_preferences: UserHelpPreferences::default(),
        };
        
        system.initialize_default_content();
        system
    }
    
    /// Get contextual help for a workflow step
    pub fn get_contextual_help(&self, step: &WorkflowStep, context: &HelpContext) -> Option<HelpContent> {
        let help_key = format!("{}_{}", step.step_type.as_str(), context.user_level.as_str());
        self.content_database.get(&help_key).cloned()
            .or_else(|| self.content_database.get(&step.step_type.as_str()).cloned())
    }
    
    /// Get recommendations for a decision point
    pub fn get_recommendations(&self, step: &WorkflowStep, decision_point: &DecisionPoint) -> Vec<Recommendation> {
        let mut recommendations = Vec::new();
        
        match decision_point.decision_type {
            DecisionType::ParameterSelection => {
                recommendations.extend(self.get_parameter_recommendations(step, decision_point));
            }
            DecisionType::OptimizationStrategy => {
                recommendations.extend(self.get_optimization_recommendations(step, decision_point));
            }
            DecisionType::ValidationMethod => {
                recommendations.extend(self.get_validation_recommendations(step, decision_point));
            }
            _ => {}
        }
        
        recommendations
    }
    
    /// Get quick tips for specific context
    pub fn get_quick_tips(&self, step_id: &str, context: &HelpContext) -> Vec<QuickTip> {
        self.contextual_tips.get(step_id)
            .map(|tips| {
                tips.iter()
                    .filter(|tip| self.should_show_tip(tip, context))
                    .cloned()
                    .collect()
            })
            .unwrap_or_default()
    }
    
    /// Get explanation for a specific concept or metric
    pub fn get_explanation(&self, concept: &str) -> Option<&ContextualExplanation> {
        self.explanations.get(concept)
    }
    
    /// Get explanation with value-specific interpretation
    pub fn get_value_explanation(&self, concept: &str, value: f64) -> Option<(ContextualExplanation, ValueInterpretation)> {
        if let Some(explanation) = self.explanations.get(concept) {
            let value_interpretation = explanation.value_interpretations.iter()
                .find(|(range, _)| self.value_in_range(value, range))
                .map(|(_, interpretation)| interpretation.clone());
            
            if let Some(interpretation) = value_interpretation {
                return Some((explanation.clone(), interpretation));
            }
        }
        None
    }
    
    /// Check if a tip should be shown based on context
    fn should_show_tip(&self, tip: &QuickTip, context: &HelpContext) -> bool {
        // Check if tip was dismissed
        if tip.show_once && context.user_preferences.dismissed_tips.contains(&tip.id) {
            return false;
        }
        
        // Check if user preferences allow tips
        if !context.user_preferences.show_tips {
            return false;
        }
        
        // Check context filters
        if !tip.context_filters.is_empty() {
            let context_match = tip.context_filters.iter()
                .any(|filter| context.completed_steps.contains(filter) || context.recent_errors.contains(filter));
            if !context_match {
                return false;
            }
        }
        
        true
    }
    
    /// Check if value falls within a range specification
    fn value_in_range(&self, value: f64, range_spec: &str) -> bool {
        match range_spec {
            "< 0" => value < 0.0,
            "0-0.5" => value >= 0.0 && value <= 0.5,
            "0.5-1.0" => value > 0.5 && value <= 1.0,
            "1.0-2.0" => value > 1.0 && value <= 2.0,
            "> 2.0" => value > 2.0,
            "< -20%" => value < -0.2,
            "-20% to -10%" => value >= -0.2 && value <= -0.1,
            "-10% to -5%" => value > -0.1 && value <= -0.05,
            "> -5%" => value > -0.05,
            _ => false, // Unknown range specification
        }
    }
    
    /// Get parameter selection recommendations
    fn get_parameter_recommendations(&self, _step: &WorkflowStep, decision_point: &DecisionPoint) -> Vec<Recommendation> {
        let mut recommendations = Vec::new();
        
        // Example parameter recommendations
        if let Some(strategy_type) = decision_point.context.get("strategy_type") {
            if strategy_type.as_str() == Some("mean_reversion") {
                recommendations.push(Recommendation {
                    recommendation_type: RecommendationType::BestPractice,
                    content: "For mean reversion strategies, use lookback periods between 10-50 bars".to_string(),
                    reasoning: "Shorter periods capture noise, longer periods miss opportunities".to_string(),
                    confidence: 0.8,
                    applicable_contexts: vec!["mean_reversion".to_string()],
                    examples: vec![],
                    related_concepts: vec!["lookback_period".to_string(), "mean_reversion".to_string()],
                });
            }
        }
        
        recommendations
    }
    
    /// Get optimization strategy recommendations
    fn get_optimization_recommendations(&self, _step: &WorkflowStep, _decision_point: &DecisionPoint) -> Vec<Recommendation> {
        vec![
            Recommendation {
                recommendation_type: RecommendationType::BestPractice,
                content: "Start with grid search for small parameter spaces (<1000 combinations)".to_string(),
                reasoning: "Grid search is thorough and easy to understand for beginners".to_string(),
                confidence: 0.9,
                applicable_contexts: vec!["small_parameter_space".to_string()],
                examples: vec![],
                related_concepts: vec!["grid_search".to_string(), "parameter_optimization".to_string()],
            },
            Recommendation {
                recommendation_type: RecommendationType::Suggestion,
                content: "Use genetic algorithms for large parameter spaces (>10,000 combinations)".to_string(),
                reasoning: "Genetic algorithms can find good solutions without exhaustive search".to_string(),
                confidence: 0.7,
                applicable_contexts: vec!["large_parameter_space".to_string()],
                examples: vec![],
                related_concepts: vec!["genetic_algorithm".to_string(), "parameter_optimization".to_string()],
            }
        ]
    }
    
    /// Get validation method recommendations
    fn get_validation_recommendations(&self, _step: &WorkflowStep, _decision_point: &DecisionPoint) -> Vec<Recommendation> {
        vec![
            Recommendation {
                recommendation_type: RecommendationType::Requirement,
                content: "Always perform walk-forward analysis for production strategies".to_string(),
                reasoning: "Walk-forward analysis tests robustness across different market conditions".to_string(),
                confidence: 1.0,
                applicable_contexts: vec!["production_deployment".to_string()],
                examples: vec![],
                related_concepts: vec!["walk_forward".to_string(), "out_of_sample".to_string()],
            }
        ]
    }
    
    /// Initialize default help content
    fn initialize_default_content(&mut self) {
        // Data ingestion help
        self.content_database.insert("DataIngestion".to_string(), HelpContent {
            id: "data_ingestion_help".to_string(),
            title: "Data Ingestion Guide".to_string(),
            content: "Learn how to load and validate historical market data for backtesting".to_string(),
            content_type: HelpContentType::StepByStepGuide,
            difficulty_level: HelpDifficultyLevel::Beginner,
            tags: vec!["data".to_string(), "parquet".to_string(), "validation".to_string()],
            related_topics: vec!["data_validation".to_string(), "file_formats".to_string()],
            examples: vec![
                HelpExample {
                    title: "Loading a Parquet file".to_string(),
                    description: "Select a Parquet file containing MNQ tick data".to_string(),
                    code_snippet: None,
                    expected_result: "Data loaded and validated successfully".to_string(),
                    common_pitfalls: vec![
                        "File path doesn't exist".to_string(),
                        "Invalid file format".to_string(),
                    ],
                }
            ],
            interactive_elements: vec![],
        });
        
        // Parameter optimization help
        self.content_database.insert("ParameterOptimization".to_string(), HelpContent {
            id: "param_opt_help".to_string(),
            title: "Parameter Optimization".to_string(),
            content: "Systematic approach to finding optimal strategy parameters".to_string(),
            content_type: HelpContentType::DetailedExplanation,
            difficulty_level: HelpDifficultyLevel::Intermediate,
            tags: vec!["optimization".to_string(), "parameters".to_string()],
            related_topics: vec!["grid_search".to_string(), "genetic_algorithm".to_string()],
            examples: vec![],
            interactive_elements: vec![],
        });
        
        // Quick tips
        let mut data_tips = Vec::new();
        data_tips.push(QuickTip {
            id: "file_size_tip".to_string(),
            trigger: TriggerCondition::Focus("data_file".to_string()),
            content: "For reliable results, use files with at least 30 days of data".to_string(),
            timing: TipTiming::Immediate,
            priority: TipPriority::Medium,
            dismissible: true,
            show_once: false,
            context_filters: vec![],
        });
        
        self.contextual_tips.insert("data-ingestion".to_string(), data_tips);
        
        // Contextual explanations
        self.explanations.insert("sharpe_ratio".to_string(), ContextualExplanation {
            metric_name: "Sharpe Ratio".to_string(),
            simple_explanation: "Risk-adjusted return measure".to_string(),
            trading_relevance: "Higher values indicate better return per unit of risk".to_string(),
            interpretation_guide: "Values >1.0 are good, >2.0 are excellent for trading strategies".to_string(),
            common_mistakes: vec![
                "Ignoring the time period of calculation".to_string(),
                "Comparing Sharpe ratios across different asset classes".to_string(),
            ],
            related_concepts: vec!["volatility".to_string(), "risk_adjusted_return".to_string()],
            value_interpretations: HashMap::from([
                ("< 0".to_string(), ValueInterpretation {
                    range: "< 0".to_string(),
                    meaning: "Negative risk-adjusted returns".to_string(),
                    implications: "Strategy loses money compared to risk-free rate".to_string(),
                    recommendations: vec!["Review strategy logic".to_string()],
                    warning_level: WarningLevel::Critical,
                }),
                ("0-0.5".to_string(), ValueInterpretation {
                    range: "0-0.5".to_string(),
                    meaning: "Poor risk-adjusted performance".to_string(),
                    implications: "Strategy barely beats risk-free rate".to_string(),
                    recommendations: vec!["Consider parameter optimization".to_string()],
                    warning_level: WarningLevel::Warning,
                }),
                ("0.5-1.0".to_string(), ValueInterpretation {
                    range: "0.5-1.0".to_string(),
                    meaning: "Acceptable performance".to_string(),
                    implications: "Strategy shows promise but has room for improvement".to_string(),
                    recommendations: vec!["Validate with out-of-sample data".to_string()],
                    warning_level: WarningLevel::Caution,
                }),
                ("1.0-2.0".to_string(), ValueInterpretation {
                    range: "1.0-2.0".to_string(),
                    meaning: "Good risk-adjusted performance".to_string(),
                    implications: "Strategy has solid risk-adjusted returns".to_string(),
                    recommendations: vec!["Proceed with additional validation".to_string()],
                    warning_level: WarningLevel::Safe,
                }),
                ("> 2.0".to_string(), ValueInterpretation {
                    range: "> 2.0".to_string(),
                    meaning: "Excellent performance".to_string(),
                    implications: "Very strong risk-adjusted returns".to_string(),
                    recommendations: vec!["Verify for overfitting".to_string()],
                    warning_level: WarningLevel::Caution,
                }),
            ]),
        });
        
        self.explanations.insert("max_drawdown".to_string(), ContextualExplanation {
            metric_name: "Maximum Drawdown".to_string(),
            simple_explanation: "Largest peak-to-trough decline".to_string(),
            trading_relevance: "Shows worst-case loss from equity peak".to_string(),
            interpretation_guide: "Lower (less negative) values are better".to_string(),
            common_mistakes: vec![
                "Confusing drawdown with volatility".to_string(),
                "Not considering drawdown duration".to_string(),
            ],
            related_concepts: vec!["risk_management".to_string(), "position_sizing".to_string()],
            value_interpretations: HashMap::from([
                ("> -5%".to_string(), ValueInterpretation {
                    range: "> -5%".to_string(),
                    meaning: "Very low drawdown".to_string(),
                    implications: "Excellent risk control".to_string(),
                    recommendations: vec!["Monitor for overly conservative strategy".to_string()],
                    warning_level: WarningLevel::Safe,
                }),
                ("-10% to -5%".to_string(), ValueInterpretation {
                    range: "-10% to -5%".to_string(),
                    meaning: "Good drawdown control".to_string(),
                    implications: "Reasonable risk level for most strategies".to_string(),
                    recommendations: vec!["Acceptable for live trading".to_string()],
                    warning_level: WarningLevel::Safe,
                }),
                ("-20% to -10%".to_string(), ValueInterpretation {
                    range: "-20% to -10%".to_string(),
                    meaning: "Moderate drawdown".to_string(),
                    implications: "Higher risk - ensure adequate capital".to_string(),
                    recommendations: vec!["Consider position sizing adjustments".to_string()],
                    warning_level: WarningLevel::Caution,
                }),
                ("< -20%".to_string(), ValueInterpretation {
                    range: "< -20%".to_string(),
                    meaning: "High drawdown".to_string(),
                    implications: "Significant risk - may be difficult to trade psychologically".to_string(),
                    recommendations: vec!["Review risk management rules".to_string()],
                    warning_level: WarningLevel::Critical,
                }),
            ]),
        });
    }
    
    /// Update user preferences
    pub fn update_user_preferences(&mut self, preferences: UserHelpPreferences) {
        self.user_preferences = preferences;
    }
    
    /// Mark tip as dismissed
    pub fn dismiss_tip(&mut self, tip_id: &str) {
        if !self.user_preferences.dismissed_tips.contains(&tip_id.to_string()) {
            self.user_preferences.dismissed_tips.push(tip_id.to_string());
        }
    }
}

impl Default for HelpSystem {
    fn default() -> Self {
        Self::new()
    }
}

impl Default for UserHelpPreferences {
    fn default() -> Self {
        Self {
            preferred_content_types: vec![HelpContentType::QuickTip, HelpContentType::StepByStepGuide],
            difficulty_level: HelpDifficultyLevel::Beginner,
            show_tips: true,
            auto_explain: true,
            verbose_mode: false,
            dismissed_tips: Vec::new(),
        }
    }
}

impl HelpDifficultyLevel {
    fn as_str(&self) -> &'static str {
        match self {
            HelpDifficultyLevel::Beginner => "beginner",
            HelpDifficultyLevel::Intermediate => "intermediate",
            HelpDifficultyLevel::Advanced => "advanced",
            HelpDifficultyLevel::Expert => "expert",
        }
    }
}

use crate::workflow::WorkflowStepType;

impl WorkflowStepType {
    fn as_str(&self) -> &str {
        match self {
            WorkflowStepType::DataIngestion => "DataIngestion",
            WorkflowStepType::StrategyConfiguration => "StrategyConfiguration",
            WorkflowStepType::ParameterOptimization => "ParameterOptimization",
            WorkflowStepType::Backtesting => "Backtesting",
            WorkflowStepType::StatisticalValidation => "StatisticalValidation",
            WorkflowStepType::ResultsAnalysis => "ResultsAnalysis",
            WorkflowStepType::DeploymentPrep => "DeploymentPrep",
            WorkflowStepType::Custom(name) => name,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_help_system_creation() {
        let help_system = HelpSystem::new();
        assert!(!help_system.content_database.is_empty());
        assert!(!help_system.explanations.is_empty());
    }
    
    #[test]
    fn test_value_range_checking() {
        let help_system = HelpSystem::new();
        assert!(help_system.value_in_range(0.75, "0.5-1.0"));
        assert!(!help_system.value_in_range(1.5, "0.5-1.0"));
        assert!(help_system.value_in_range(-0.15, "-20% to -10%"));
    }
    
    #[test]
    fn test_sharpe_ratio_explanation() {
        let help_system = HelpSystem::new();
        let explanation = help_system.get_explanation("sharpe_ratio");
        assert!(explanation.is_some());
        
        let (_, value_interpretation) = help_system.get_value_explanation("sharpe_ratio", 1.5).unwrap();
        assert_eq!(value_interpretation.range, "1.0-2.0");
        assert_eq!(value_interpretation.warning_level, WarningLevel::Safe);
    }
}