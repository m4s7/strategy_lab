//! Genetic algorithm optimization

use crate::backtesting::{BacktestEngine, BacktestConfig, BacktestResult, PerformanceMetrics};
use crate::strategy::Strategy;
use crate::strategy::config::ParameterValue;
use crate::optimization::{OptimizationResult, ParameterSet, ObjectiveFunction};
use rand::prelude::*;
use rayon::prelude::*;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use tracing::{info, debug};

/// Genetic algorithm configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GeneticConfig {
    /// Population size
    pub population_size: usize,
    
    /// Number of generations
    pub generations: usize,
    
    /// Mutation rate (0.0 to 1.0)
    pub mutation_rate: f64,
    
    /// Crossover rate (0.0 to 1.0)
    pub crossover_rate: f64,
    
    /// Selection strategy
    pub selection_strategy: SelectionStrategy,
    
    /// Elite individuals to preserve
    pub elite_size: usize,
    
    /// Tournament size for selection
    pub tournament_size: usize,
    
    /// Objective function
    pub objective: ObjectiveFunction,
    
    /// Parameter bounds
    pub parameter_bounds: HashMap<String, (f64, f64)>,
}

/// Selection strategies
#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub enum SelectionStrategy {
    Tournament,
    RouletteWheel,
    RankBased,
}

/// Individual in the genetic algorithm
#[derive(Debug, Clone)]
struct Individual {
    parameters: ParameterSet,
    fitness: Option<f64>,
    backtest_result: Option<BacktestResult>,
}

impl Individual {
    fn new(parameters: ParameterSet) -> Self {
        Self {
            parameters,
            fitness: None,
            backtest_result: None,
        }
    }
    
    /// Create random individual
    fn random(bounds: &HashMap<String, (f64, f64)>) -> Self {
        let mut rng = thread_rng();
        let mut parameters = HashMap::new();
        
        for (name, (min, max)) in bounds {
            let value = rng.gen_range(*min..=*max);
            parameters.insert(name.clone(), ParameterValue::Float(value));
        }
        
        Self::new(ParameterSet { parameters })
    }
}

/// Genetic algorithm optimizer
pub struct GeneticOptimizer {
    config: GeneticConfig,
    population: Vec<Individual>,
    generation: usize,
    best_individual: Option<Individual>,
    history: Vec<GenerationStats>,
}

impl GeneticOptimizer {
    pub fn new(config: GeneticConfig) -> Self {
        // Initialize random population
        let population: Vec<Individual> = (0..config.population_size)
            .map(|_| Individual::random(&config.parameter_bounds))
            .collect();
        
        Self {
            config,
            population,
            generation: 0,
            best_individual: None,
            history: Vec::new(),
        }
    }
    
    /// Run genetic algorithm optimization
    pub async fn optimize<S, F>(
        &mut self,
        strategy_factory: F,
        backtest_config: BacktestConfig,
        data_path: &str,
    ) -> Result<Vec<OptimizationResult>, Box<dyn std::error::Error>>
    where
        S: Strategy + Send + 'static,
        F: Fn(ParameterSet) -> S + Send + Sync + 'static,
    {
        info!("Starting genetic algorithm optimization");
        info!("Population size: {}, Generations: {}", 
            self.config.population_size, self.config.generations);
        
        for gen in 0..self.config.generations {
            self.generation = gen;
            debug!("Generation {}/{}", gen + 1, self.config.generations);
            
            // Evaluate fitness
            self.evaluate_population(&strategy_factory, &backtest_config, data_path).await?;
            
            // Record statistics
            let stats = self.calculate_stats();
            self.history.push(stats.clone());
            
            info!("Gen {}: Best fitness: {:.4}, Avg: {:.4}",
                gen, stats.best_fitness, stats.avg_fitness);
            
            // Check for convergence
            if self.check_convergence() {
                info!("Converged at generation {}", gen);
                break;
            }
            
            // Selection and reproduction
            let new_population = self.evolve();
            self.population = new_population;
        }
        
        // Convert to optimization results
        let results = self.population.iter()
            .filter_map(|ind| {
                if let (Some(fitness), Some(result)) = (ind.fitness, &ind.backtest_result) {
                    Some(OptimizationResult {
                        parameters: ind.parameters.clone(),
                        backtest_result: result.clone(),
                        objective_value: fitness,
                        timestamp: chrono::Utc::now(),
                        metrics: PerformanceMetrics::new(),
                        equity_curve: Vec::new(),
                        trade_analysis: None,
                        parameter_sensitivity: None,
                    })
                } else {
                    None
                }
            })
            .collect();
        
        Ok(results)
    }
    
    /// Evaluate fitness for all individuals
    async fn evaluate_population<S, F>(
        &mut self,
        strategy_factory: &F,
        backtest_config: &BacktestConfig,
        data_path: &str,
    ) -> Result<(), Box<dyn std::error::Error>>
    where
        S: Strategy + Send + 'static,
        F: Fn(ParameterSet) -> S + Send + Sync,
    {
        // Parallel evaluation
        let results: Vec<_> = self.population
            .par_iter_mut()
            .map(|individual| {
                if individual.fitness.is_some() {
                    return Ok(());
                }
                
                let strategy = strategy_factory(individual.parameters.clone());
                
                // Run backtest
                let rt = tokio::runtime::Runtime::new().unwrap();
                let result = rt.block_on(async {
                    let mut engine = BacktestEngine::new(backtest_config.clone());
                    let mut strategy = strategy;
                    engine.run_backtest(&mut strategy, data_path).await
                });
                
                if let Ok(backtest_result) = result {
                    individual.fitness = Some(self.config.objective.calculate(&backtest_result));
                    individual.backtest_result = Some(backtest_result);
                }
                
                Ok(())
            })
            .collect::<Result<Vec<_>, _>>()?;
        
        // Update best individual
        if let Some(best) = self.population.iter()
            .filter(|ind| ind.fitness.is_some())
            .max_by(|a, b| a.fitness.partial_cmp(&b.fitness).unwrap())
        {
            if self.best_individual.is_none() || 
               best.fitness > self.best_individual.as_ref().unwrap().fitness 
            {
                self.best_individual = Some(best.clone());
            }
        }
        
        Ok(())
    }
    
    /// Evolve population to next generation
    fn evolve(&self) -> Vec<Individual> {
        let mut new_population = Vec::new();
        let mut rng = thread_rng();
        
        // Elitism - preserve best individuals
        let mut sorted = self.population.clone();
        sorted.sort_by(|a, b| b.fitness.partial_cmp(&a.fitness).unwrap());
        
        for i in 0..self.config.elite_size.min(sorted.len()) {
            new_population.push(sorted[i].clone());
        }
        
        // Generate rest of population
        while new_population.len() < self.config.population_size {
            // Selection
            let parent1 = self.select_parent();
            let parent2 = self.select_parent();
            
            // Crossover
            let mut offspring = if rng.gen::<f64>() < self.config.crossover_rate {
                self.crossover(&parent1, &parent2)
            } else {
                parent1.clone()
            };
            
            // Mutation
            if rng.gen::<f64>() < self.config.mutation_rate {
                self.mutate(&mut offspring);
            }
            
            new_population.push(offspring);
        }
        
        new_population
    }
    
    /// Select parent using configured strategy
    fn select_parent(&self) -> Individual {
        match self.config.selection_strategy {
            SelectionStrategy::Tournament => self.tournament_selection(),
            SelectionStrategy::RouletteWheel => self.roulette_selection(),
            SelectionStrategy::RankBased => self.rank_selection(),
        }
    }
    
    /// Tournament selection
    fn tournament_selection(&self) -> Individual {
        let mut rng = thread_rng();
        let tournament: Vec<_> = (0..self.config.tournament_size)
            .map(|_| self.population.choose(&mut rng).unwrap())
            .collect();
        
        tournament.into_iter()
            .max_by(|a, b| a.fitness.partial_cmp(&b.fitness).unwrap())
            .unwrap()
            .clone()
    }
    
    /// Roulette wheel selection
    fn roulette_selection(&self) -> Individual {
        let mut rng = thread_rng();
        let total_fitness: f64 = self.population.iter()
            .filter_map(|ind| ind.fitness)
            .sum();
        
        let mut cumulative = 0.0;
        let target = rng.gen::<f64>() * total_fitness;
        
        for individual in &self.population {
            if let Some(fitness) = individual.fitness {
                cumulative += fitness;
                if cumulative >= target {
                    return individual.clone();
                }
            }
        }
        
        self.population.last().unwrap().clone()
    }
    
    /// Rank-based selection
    fn rank_selection(&self) -> Individual {
        // Simplified rank selection
        self.tournament_selection()
    }
    
    /// Crossover two parents
    fn crossover(&self, parent1: &Individual, parent2: &Individual) -> Individual {
        let mut rng = thread_rng();
        let mut offspring_params = HashMap::new();
        
        for (name, value1) in &parent1.parameters.parameters {
            if let Some(value2) = parent2.parameters.parameters.get(name) {
                // Uniform crossover
                let use_parent1 = rng.gen::<bool>();
                offspring_params.insert(
                    name.clone(),
                    if use_parent1 { value1.clone() } else { value2.clone() }
                );
            } else {
                offspring_params.insert(name.clone(), value1.clone());
            }
        }
        
        Individual::new(ParameterSet { parameters: offspring_params })
    }
    
    /// Mutate an individual
    fn mutate(&self, individual: &mut Individual) {
        let mut rng = thread_rng();
        
        for (name, value) in &mut individual.parameters.parameters {
            if let Some((min, max)) = self.config.parameter_bounds.get(name) {
                if let ParameterValue::Float(v) = value {
                    // Gaussian mutation
                    let std_dev = (max - min) * 0.1;
                    let mutation = rng.gen_range(-std_dev..=std_dev);
                    *v = (*v + mutation).clamp(*min, *max);
                }
            }
        }
        
        // Reset fitness since parameters changed
        individual.fitness = None;
        individual.backtest_result = None;
    }
    
    /// Calculate generation statistics
    fn calculate_stats(&self) -> GenerationStats {
        let fitnesses: Vec<f64> = self.population.iter()
            .filter_map(|ind| ind.fitness)
            .collect();
        
        GenerationStats {
            generation: self.generation,
            best_fitness: fitnesses.iter().cloned().fold(f64::NEG_INFINITY, f64::max),
            worst_fitness: fitnesses.iter().cloned().fold(f64::INFINITY, f64::min),
            avg_fitness: fitnesses.iter().sum::<f64>() / fitnesses.len() as f64,
            std_dev: self.calculate_std_dev(&fitnesses),
        }
    }
    
    fn calculate_std_dev(&self, values: &[f64]) -> f64 {
        if values.is_empty() {
            return 0.0;
        }
        
        let mean = values.iter().sum::<f64>() / values.len() as f64;
        let variance = values.iter()
            .map(|v| (v - mean).powi(2))
            .sum::<f64>() / values.len() as f64;
        
        variance.sqrt()
    }
    
    /// Check for convergence
    fn check_convergence(&self) -> bool {
        if self.history.len() < 10 {
            return false;
        }
        
        // Check if best fitness hasn't improved in last 5 generations
        let recent = &self.history[self.history.len() - 5..];
        let improvements = recent.windows(2)
            .filter(|w| w[1].best_fitness > w[0].best_fitness * 1.001)
            .count();
        
        improvements == 0
    }
}

/// Statistics for a generation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GenerationStats {
    pub generation: usize,
    pub best_fitness: f64,
    pub worst_fitness: f64,
    pub avg_fitness: f64,
    pub std_dev: f64,
}