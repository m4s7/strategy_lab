//! Parameter optimization module
//! 
//! This module implements Story 3.1: Multi-Algorithm Optimization
//! Provides grid search and genetic algorithms for parameter exploration
//! Utilizes 12+ CPU cores with walk-forward validation

pub mod grid_search;
pub mod genetic;
pub mod walk_forward;
pub mod parallel;
pub mod objective;
pub mod results;

pub use grid_search::{GridSearchOptimizer, GridSearchConfig};
pub use genetic::{GeneticOptimizer, GeneticConfig};
pub use walk_forward::{WalkForwardAnalysis, WalkForwardConfig};
pub use parallel::{ParallelOptimizer, OptimizationJob};
pub use objective::{ObjectiveFunction, OptimizationObjective};
pub use results::{OptimizationResult, ParameterSet, OptimizationReport};