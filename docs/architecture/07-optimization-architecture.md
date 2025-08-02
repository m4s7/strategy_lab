# Strategy Lab Technical Architecture - Optimization Architecture

## Optimization Framework Overview

The optimization architecture provides multiple algorithms for finding optimal strategy parameters, leveraging parallel processing across 16 CPU cores for efficient parameter space exploration.

## Parallel Processing Framework

### Base Parallel Optimizer

```python
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import List, Tuple, Callable, Dict, Any
import numpy as np

class ParallelOptimizer:
    """Base class for parallel optimization algorithms"""
    
    def __init__(self, n_cores: int = None):
        self.n_cores = n_cores or mp.cpu_count()
        self.executor = ProcessPoolExecutor(max_workers=self.n_cores)
        self.results_cache = {}
        
    def optimize(self, 
                 objective_func: Callable,
                 parameter_space: Dict[str, Any],
                 config: OptimizationConfig) -> OptimizationResults:
        """Run optimization using parallel processing"""
        raise NotImplementedError("Subclasses must implement optimize")
    
    def _worker_function(self, 
                        params: Dict[str, Any],
                        data_path: str,
                        strategy_name: str) -> Tuple[Dict, float]:
        """Worker function for parallel execution"""
        try:
            # Create strategy instance
            strategy = strategy_registry.get_strategy(strategy_name, params)
            
            # Run backtest
            engine = BacktestingEngine(self.backtest_config)
            engine.setup_engine(data_path, strategy)
            results = engine.run_backtest()
            
            # Extract optimization metric
            metric_value = self._extract_metric(results)
            
            return params, metric_value
            
        except Exception as e:
            logger.error(f"Worker failed with params {params}: {e}")
            return params, float('-inf')
    
    def _extract_metric(self, results: BacktestResults) -> float:
        """Extract optimization metric from results"""
        metric_name = self.config.optimization_metric
        
        if metric_name == 'sharpe_ratio':
            return results.performance_metrics.sharpe_ratio
        elif metric_name == 'total_pnl':
            return results.performance_metrics.total_pnl
        elif metric_name == 'calmar_ratio':
            return results.performance_metrics.calmar_ratio
        else:
            raise ValueError(f"Unknown metric: {metric_name}")
    
    def shutdown(self):
        """Clean shutdown of executor"""
        self.executor.shutdown(wait=True)
```

## Grid Search Optimization

### Grid Search Implementation

```python
class GridSearchOptimizer(ParallelOptimizer):
    """Grid search with parallel execution"""
    
    def optimize(self, 
                 objective_func: Callable,
                 parameter_space: Dict[str, Any],
                 config: GridSearchConfig) -> GridSearchResults:
        """Perform exhaustive grid search"""
        # Generate parameter grid
        param_grid = self._generate_parameter_grid(parameter_space)
        total_combinations = len(param_grid)
        
        logger.info(f"Grid search: {total_combinations} parameter combinations")
        
        # Submit parallel jobs
        futures = []
        for params in param_grid:
            # Check cache first
            param_hash = self._hash_params(params)
            if param_hash in self.results_cache:
                continue
                
            future = self.executor.submit(
                self._worker_function,
                params,
                config.data_path,
                config.strategy_name
            )
            futures.append((params, future))
        
        # Collect results with progress tracking
        results = []
        completed = 0
        
        for future in as_completed([f[1] for f in futures]):
            completed += 1
            
            # Find corresponding params
            params = next(p for p, f in futures if f == future)[0]
            
            try:
                _, metric_value = future.result(timeout=config.timeout_seconds)
                results.append({
                    'params': params,
                    'metric_value': metric_value,
                    'timestamp': time.time()
                })
                
                # Update progress
                if completed % 10 == 0:
                    progress = completed / total_combinations * 100
                    logger.info(f"Grid search progress: {progress:.1f}%")
                    
            except Exception as e:
                logger.error(f"Failed to get result for {params}: {e}")
        
        # Sort by metric value
        results.sort(key=lambda x: x['metric_value'], reverse=True)
        
        return GridSearchResults(
            best_params=results[0]['params'] if results else None,
            best_score=results[0]['metric_value'] if results else None,
            all_results=results,
            total_evaluated=len(results),
            optimization_time=time.time() - start_time
        )
    
    def _generate_parameter_grid(self, 
                                parameter_space: Dict[str, Any]) -> List[Dict]:
        """Generate all parameter combinations"""
        import itertools
        
        # Extract parameter ranges
        param_names = []
        param_values = []
        
        for name, spec in parameter_space.items():
            param_names.append(name)
            
            if isinstance(spec, dict):
                # Range specification
                values = np.arange(
                    spec['min'],
                    spec['max'] + spec['step'],
                    spec['step']
                ).tolist()
            else:
                # List of values
                values = spec
                
            param_values.append(values)
        
        # Generate all combinations
        combinations = []
        for values in itertools.product(*param_values):
            param_dict = dict(zip(param_names, values))
            combinations.append(param_dict)
        
        return combinations
```

### Adaptive Grid Search

```python
class AdaptiveGridSearch(GridSearchOptimizer):
    """Grid search with adaptive refinement"""
    
    def optimize(self, 
                 objective_func: Callable,
                 parameter_space: Dict[str, Any],
                 config: AdaptiveGridConfig) -> GridSearchResults:
        """Multi-stage grid search with refinement"""
        best_params = None
        
        for stage in range(config.num_stages):
            logger.info(f"Adaptive grid search stage {stage + 1}/{config.num_stages}")
            
            # Adjust parameter space around best params
            if stage > 0 and best_params:
                parameter_space = self._refine_parameter_space(
                    parameter_space,
                    best_params,
                    config.refinement_factor
                )
            
            # Run grid search for this stage
            stage_results = super().optimize(
                objective_func,
                parameter_space,
                config
            )
            
            # Update best params
            if stage_results.best_params:
                best_params = stage_results.best_params
            
        return stage_results
    
    def _refine_parameter_space(self,
                               original_space: Dict,
                               center_params: Dict,
                               factor: float) -> Dict:
        """Refine parameter space around best params"""
        refined_space = {}
        
        for name, spec in original_space.items():
            if name in center_params:
                center = center_params[name]
                
                # Calculate new range
                original_range = spec['max'] - spec['min']
                new_range = original_range * factor
                
                refined_space[name] = {
                    'min': max(spec['min'], center - new_range / 2),
                    'max': min(spec['max'], center + new_range / 2),
                    'step': spec['step'] * factor
                }
            else:
                refined_space[name] = spec
        
        return refined_space
```

## Genetic Algorithm Optimization

### DEAP-based Genetic Algorithm

```python
from deap import base, creator, tools, algorithms
import random

class GeneticOptimizer(ParallelOptimizer):
    """Genetic algorithm optimization using DEAP"""
    
    def __init__(self, n_cores: int = None):
        super().__init__(n_cores)
        self._setup_deap()
    
    def _setup_deap(self):
        """Configure DEAP for strategy optimization"""
        # Create fitness and individual types
        creator.create("FitnessMax", base.Fitness, weights=(1.0,))
        creator.create("Individual", list, fitness=creator.FitnessMax)
        
        self.toolbox = base.Toolbox()
        
        # Register parallel evaluation
        self.toolbox.register("map", self.executor.map)
    
    def optimize(self, 
                 objective_func: Callable,
                 parameter_space: Dict[str, Any],
                 config: GeneticConfig) -> GeneticResults:
        """Run genetic algorithm optimization"""
        # Register genetic operators
        self._register_operators(parameter_space)
        
        # Initialize population
        population = self.toolbox.population(n=config.population_size)
        
        # Statistics tracking
        stats = tools.Statistics(lambda ind: ind.fitness.values)
        stats.register("avg", np.mean)
        stats.register("std", np.std)
        stats.register("min", np.min)
        stats.register("max", np.max)
        
        # Hall of fame to track best individuals
        hof = tools.HallOfFame(config.hall_of_fame_size)
        
        # Run evolution
        logger.info(f"Starting genetic optimization: {config.generations} generations")
        
        population, logbook = algorithms.eaSimple(
            population=population,
            toolbox=self.toolbox,
            cxpb=config.crossover_prob,
            mutpb=config.mutation_prob,
            ngen=config.generations,
            stats=stats,
            halloffame=hof,
            verbose=True
        )
        
        # Extract best solution
        best_individual = hof[0]
        best_params = self._decode_individual(best_individual, parameter_space)
        best_fitness = best_individual.fitness.values[0]
        
        return GeneticResults(
            best_params=best_params,
            best_score=best_fitness,
            population_history=logbook,
            hall_of_fame=[self._decode_individual(ind, parameter_space) 
                         for ind in hof],
            final_population=population
        )
    
    def _register_operators(self, parameter_space: Dict[str, Any]):
        """Register genetic operators for parameter optimization"""
        # Gene attributes
        for param_name, spec in parameter_space.items():
            if isinstance(spec, dict):
                self.toolbox.register(
                    f"attr_{param_name}",
                    random.uniform,
                    spec['min'],
                    spec['max']
                )
            else:
                self.toolbox.register(
                    f"attr_{param_name}",
                    random.choice,
                    spec
                )
        
        # Individual generator
        attr_names = [f"attr_{name}" for name in parameter_space.keys()]
        self.toolbox.register(
            "individual",
            tools.initCycle,
            creator.Individual,
            [getattr(self.toolbox, attr) for attr in attr_names],
            n=1
        )
        
        # Population generator
        self.toolbox.register("population", tools.initRepeat, list, self.toolbox.individual)
        
        # Genetic operators
        self.toolbox.register("evaluate", self._evaluate_individual, parameter_space=parameter_space)
        self.toolbox.register("mate", tools.cxTwoPoint)
        self.toolbox.register("mutate", self._mutate_individual, parameter_space=parameter_space)
        self.toolbox.register("select", tools.selTournament, tournsize=3)
    
    def _evaluate_individual(self, 
                           individual: List[float],
                           parameter_space: Dict[str, Any]) -> Tuple[float,]:
        """Evaluate fitness of individual"""
        # Decode individual to parameters
        params = self._decode_individual(individual, parameter_space)
        
        # Run backtest
        _, fitness = self._worker_function(
            params,
            self.config.data_path,
            self.config.strategy_name
        )
        
        return (fitness,)
    
    def _mutate_individual(self,
                          individual: List[float],
                          parameter_space: Dict[str, Any]) -> Tuple[List[float],]:
        """Custom mutation operator"""
        for i, (param_name, spec) in enumerate(parameter_space.items()):
            if random.random() < self.config.gene_mutation_prob:
                if isinstance(spec, dict):
                    # Gaussian mutation for continuous parameters
                    sigma = (spec['max'] - spec['min']) * 0.1
                    individual[i] += random.gauss(0, sigma)
                    individual[i] = max(spec['min'], min(spec['max'], individual[i]))
                else:
                    # Random choice for discrete parameters
                    individual[i] = random.choice(spec)
        
        return (individual,)
```

## Walk-Forward Analysis

### Walk-Forward Implementation

```python
class WalkForwardAnalyzer:
    """Walk-forward analysis implementation"""
    
    def __init__(self, 
                 optimizer: ParallelOptimizer,
                 config: WalkForwardConfig):
        self.optimizer = optimizer
        self.config = config
        
    def analyze(self, 
                strategy_class: Type[BaseStrategy],
                data_manager: DataManager,
                parameter_space: Dict[str, Any]) -> WalkForwardResults:
        """Perform walk-forward analysis"""
        results = []
        
        # Calculate windows
        windows = self._calculate_windows(
            data_manager.start_date,
            data_manager.end_date
        )
        
        logger.info(f"Walk-forward analysis: {len(windows)} windows")
        
        for i, window in enumerate(windows):
            logger.info(f"Processing window {i+1}/{len(windows)}")
            
            # In-sample optimization
            is_results = self._optimize_in_sample(
                strategy_class,
                data_manager,
                parameter_space,
                window['in_sample_start'],
                window['in_sample_end']
            )
            
            # Out-of-sample testing
            oos_results = self._test_out_of_sample(
                strategy_class,
                data_manager,
                is_results.best_params,
                window['out_sample_start'],
                window['out_sample_end']
            )
            
            # Store results
            results.append({
                'window_id': i,
                'in_sample_period': (window['in_sample_start'], window['in_sample_end']),
                'out_sample_period': (window['out_sample_start'], window['out_sample_end']),
                'optimal_params': is_results.best_params,
                'in_sample_performance': is_results.best_score,
                'out_sample_performance': oos_results.performance_metrics,
                'parameter_stability': self._calculate_stability(results, is_results.best_params)
            })
        
        # Analyze overall results
        analysis = self._analyze_results(results)
        
        return WalkForwardResults(
            windows=results,
            analysis=analysis,
            parameter_evolution=self._extract_parameter_evolution(results)
        )
    
    def _calculate_windows(self, 
                          start_date: str,
                          end_date: str) -> List[Dict[str, str]]:
        """Calculate walk-forward windows"""
        windows = []
        
        current_date = pd.Timestamp(start_date)
        end_timestamp = pd.Timestamp(end_date)
        
        while current_date + pd.Timedelta(days=self.config.total_days) <= end_timestamp:
            window = {
                'in_sample_start': current_date.strftime('%Y-%m-%d'),
                'in_sample_end': (current_date + pd.Timedelta(days=self.config.in_sample_days)).strftime('%Y-%m-%d'),
                'out_sample_start': (current_date + pd.Timedelta(days=self.config.in_sample_days)).strftime('%Y-%m-%d'),
                'out_sample_end': (current_date + pd.Timedelta(days=self.config.total_days)).strftime('%Y-%m-%d')
            }
            windows.append(window)
            
            # Step forward
            current_date += pd.Timedelta(days=self.config.step_days)
        
        return windows
    
    def _calculate_stability(self, 
                           previous_results: List[Dict],
                           current_params: Dict[str, Any]) -> float:
        """Calculate parameter stability score"""
        if not previous_results:
            return 1.0
        
        # Compare with previous window parameters
        prev_params = previous_results[-1]['optimal_params']
        
        # Calculate normalized distance
        distances = []
        for param_name, current_value in current_params.items():
            if param_name in prev_params:
                prev_value = prev_params[param_name]
                
                # Normalize by parameter range
                param_range = self.parameter_space[param_name]['max'] - self.parameter_space[param_name]['min']
                normalized_distance = abs(current_value - prev_value) / param_range
                distances.append(normalized_distance)
        
        # Stability score (inverse of average distance)
        avg_distance = np.mean(distances) if distances else 0
        stability = 1 / (1 + avg_distance)
        
        return stability
```

## Optimization Results Management

### Results Storage and Analysis

```python
@dataclass
class OptimizationResults:
    """Base class for optimization results"""
    best_params: Dict[str, Any]
    best_score: float
    optimization_time: float
    total_evaluated: int
    
    def save(self, filepath: str):
        """Save results to file"""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)

class OptimizationResultsManager:
    """Manages optimization results and history"""
    
    def __init__(self, results_dir: str):
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)
        
    def save_results(self, 
                    results: OptimizationResults,
                    strategy_name: str,
                    optimization_type: str) -> str:
        """Save optimization results with metadata"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{strategy_name}_{optimization_type}_{timestamp}.json"
        filepath = self.results_dir / filename
        
        # Add metadata
        full_results = {
            'metadata': {
                'strategy_name': strategy_name,
                'optimization_type': optimization_type,
                'timestamp': timestamp,
                'version': '1.0'
            },
            'results': results.to_dict()
        }
        
        with open(filepath, 'w') as f:
            json.dump(full_results, f, indent=2)
        
        logger.info(f"Saved optimization results to {filepath}")
        return str(filepath)
    
    def load_results(self, filepath: str) -> OptimizationResults:
        """Load optimization results from file"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Determine result type and reconstruct
        opt_type = data['metadata']['optimization_type']
        
        if opt_type == 'grid_search':
            return GridSearchResults(**data['results'])
        elif opt_type == 'genetic':
            return GeneticResults(**data['results'])
        elif opt_type == 'walk_forward':
            return WalkForwardResults(**data['results'])
        else:
            return OptimizationResults(**data['results'])
```