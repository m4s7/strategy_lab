"""Genetic algorithm optimization implementation."""

import logging
import random
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import numpy as np

from ..core.parameter_space import ParameterSpace
from ..core.results import OptimizationResult, OptimizationResultSet

logger = logging.getLogger(__name__)

# Try to import DEAP, but make it optional
try:
    from deap import algorithms, base, creator, tools

    DEAP_AVAILABLE = True
except ImportError:
    DEAP_AVAILABLE = False
    logger.warning("DEAP not installed, using built-in genetic algorithm")


@dataclass
class GeneticAlgorithmConfig:
    """Configuration for genetic algorithm optimization."""

    population_size: int = 100
    generations: int = 50
    crossover_prob: float = 0.8
    mutation_prob: float = 0.2
    selection_method: str = "tournament"  # tournament, roulette, rank
    tournament_size: int = 3
    elite_size: int = 5  # Number of best individuals to preserve
    random_seed: int | None = None
    parallel: bool = True
    n_workers: int | None = None
    verbose: bool = True

    # Multi-objective settings
    multi_objective: bool = False
    crowding_distance: bool = True  # For NSGA-II diversity

    # Convergence criteria
    fitness_tolerance: float = 1e-6
    stagnation_generations: int = 10  # Stop if no improvement
    min_diversity: float = 0.01  # Stop if population too similar


@dataclass
class Individual:
    """Represents an individual in the population."""

    genes: list[float]  # Encoded parameters
    fitness: float | tuple[float, ...] | None = None
    parameters: dict[str, Any] | None = None
    generation: int = 0

    def __lt__(self, other):
        """For sorting individuals by fitness."""
        if self.fitness is None or other.fitness is None:
            return False
        if isinstance(self.fitness, tuple):
            # Multi-objective: use first objective for basic sorting
            return self.fitness[0] < other.fitness[0]
        return self.fitness < other.fitness


@dataclass
class PopulationStats:
    """Statistics for a population."""

    generation: int
    best_fitness: float | tuple[float, ...]
    average_fitness: float | tuple[float, ...]
    worst_fitness: float | tuple[float, ...]
    diversity: float
    convergence_rate: float = 0.0


class GeneticEncoder:
    """Encodes/decodes between parameters and genes."""

    def __init__(self, parameter_space: ParameterSpace):
        """Initialize encoder.

        Args:
            parameter_space: Parameter space to encode
        """
        self.parameter_space = parameter_space
        self._setup_encoding()

    def _setup_encoding(self):
        """Setup encoding for each parameter."""
        self.encodings = []

        for param in self.parameter_space.parameters:
            if param.__class__.__name__ == "ContinuousParameter":
                # Map to [0, 1] range
                self.encodings.append(
                    {
                        "type": "continuous",
                        "name": param.name,
                        "min": param.min_value,
                        "max": param.max_value,
                    }
                )
            elif param.__class__.__name__ == "DiscreteParameter":
                # Map to [0, 1] range
                self.encodings.append(
                    {
                        "type": "discrete",
                        "name": param.name,
                        "min": param.min_value,
                        "max": param.max_value,
                        "step": param.step,
                    }
                )
            elif param.__class__.__name__ == "CategoricalParameter":
                # Map to integer indices
                self.encodings.append(
                    {
                        "type": "categorical",
                        "name": param.name,
                        "values": param.values,
                        "n_values": len(param.values),
                    }
                )

    def encode(self, parameters: dict[str, Any]) -> list[float]:
        """Encode parameters to genes.

        Args:
            parameters: Parameter dictionary

        Returns:
            List of encoded genes
        """
        genes = []

        for encoding in self.encodings:
            value = parameters[encoding["name"]]

            if encoding["type"] == "continuous" or encoding["type"] == "discrete":
                # Normalize to [0, 1]
                gene = (value - encoding["min"]) / (encoding["max"] - encoding["min"])
                genes.append(gene)

            elif encoding["type"] == "categorical":
                # Encode as index normalized to [0, 1]
                index = encoding["values"].index(value)
                gene = (
                    index / (encoding["n_values"] - 1)
                    if encoding["n_values"] > 1
                    else 0.0
                )
                genes.append(gene)

        return genes

    def decode(self, genes: list[float]) -> dict[str, Any]:
        """Decode genes to parameters.

        Args:
            genes: List of genes

        Returns:
            Parameter dictionary
        """
        parameters = {}

        for i, encoding in enumerate(self.encodings):
            gene = genes[i]

            if encoding["type"] == "continuous":
                # Denormalize from [0, 1]
                value = encoding["min"] + gene * (encoding["max"] - encoding["min"])
                parameters[encoding["name"]] = value

            elif encoding["type"] == "discrete":
                # Denormalize and round to nearest valid value
                continuous_value = encoding["min"] + gene * (
                    encoding["max"] - encoding["min"]
                )
                # Round to nearest step
                n_steps = round((continuous_value - encoding["min"]) / encoding["step"])
                value = encoding["min"] + n_steps * encoding["step"]
                # Ensure within bounds
                value = max(encoding["min"], min(encoding["max"], value))
                parameters[encoding["name"]] = int(value)

            elif encoding["type"] == "categorical":
                # Decode from index
                index = round(gene * (encoding["n_values"] - 1))
                index = max(0, min(encoding["n_values"] - 1, index))
                parameters[encoding["name"]] = encoding["values"][index]

        return parameters

    @property
    def n_genes(self) -> int:
        """Get number of genes."""
        return len(self.encodings)


class GeneticAlgorithmOptimizer:
    """Genetic algorithm optimization."""

    def __init__(self, config: GeneticAlgorithmConfig | None = None):
        """Initialize optimizer.

        Args:
            config: Algorithm configuration
        """
        self.config = config or GeneticAlgorithmConfig()

        # Set random seed
        if self.config.random_seed is not None:
            random.seed(self.config.random_seed)
            np.random.seed(self.config.random_seed)

        # Statistics tracking
        self.population_stats: list[PopulationStats] = []
        self.best_individual: Individual | None = None

    def optimize(
        self,
        objective_func: Callable[..., float | dict[str, float] | tuple[float, ...]],
        parameter_space: ParameterSpace,
        objectives: list[dict[str, Any]] | None = None,
    ) -> OptimizationResultSet:
        """Run genetic algorithm optimization.

        Args:
            objective_func: Objective function to optimize
            parameter_space: Parameter space
            objectives: List of objective configurations for multi-objective

        Returns:
            OptimizationResultSet with all evaluated individuals
        """
        # Setup encoder
        encoder = GeneticEncoder(parameter_space)

        # Initialize population
        population = self._initialize_population(encoder)

        # Evaluate initial population
        results = OptimizationResultSet()
        self._evaluate_population(population, objective_func, encoder, results)

        # Evolution loop
        converged = False
        stagnation_counter = 0
        best_fitness = self._get_best_fitness(population)

        for generation in range(self.config.generations):
            if self.config.verbose:
                logger.info(f"Generation {generation + 1}/{self.config.generations}")

            # Select parents
            parents = self._select_parents(population)

            # Create offspring
            offspring = self._create_offspring(parents, encoder)

            # Evaluate offspring
            self._evaluate_population(offspring, objective_func, encoder, results)

            # Create next generation
            population = self._create_next_generation(population, offspring)

            # Update statistics
            stats = self._calculate_stats(population, generation + 1)
            self.population_stats.append(stats)

            # Check convergence
            new_best_fitness = self._get_best_fitness(population)
            if self._check_convergence(best_fitness, new_best_fitness):
                stagnation_counter += 1
                if stagnation_counter >= self.config.stagnation_generations:
                    logger.info(
                        f"Converged after {generation + 1} generations (stagnation)"
                    )
                    converged = True
                    break
            else:
                stagnation_counter = 0
                best_fitness = new_best_fitness

            # Check diversity
            if stats.diversity < self.config.min_diversity:
                logger.info(
                    f"Converged after {generation + 1} generations (low diversity)"
                )
                converged = True
                break

            # Update best individual
            self._update_best_individual(population)

            if self.config.verbose:
                self._log_generation_stats(stats)

        if not converged and self.config.verbose:
            logger.info(f"Completed {self.config.generations} generations")

        return results

    def _initialize_population(self, encoder: GeneticEncoder) -> list[Individual]:
        """Initialize random population."""
        population = []

        for _ in range(self.config.population_size):
            # Random genes in [0, 1]
            genes = [random.random() for _ in range(encoder.n_genes)]
            individual = Individual(genes=genes, generation=0)
            population.append(individual)

        return population

    def _evaluate_population(
        self,
        population: list[Individual],
        objective_func: Callable,
        encoder: GeneticEncoder,
        results: OptimizationResultSet,
    ) -> None:
        """Evaluate fitness for population."""
        for individual in population:
            if individual.fitness is not None:
                continue  # Already evaluated

            # Decode parameters
            parameters = encoder.decode(individual.genes)
            individual.parameters = parameters

            # Evaluate
            start_time = time.time()
            try:
                result = objective_func(**parameters)

                # Handle different return types
                if isinstance(result, dict):
                    # Multi-objective as dictionary
                    if self.config.multi_objective:
                        # Extract objectives in order
                        individual.fitness = tuple(result.values())
                    else:
                        # Single objective - use first value
                        individual.fitness = next(iter(result.values()))
                    metrics = result
                elif isinstance(result, tuple):
                    # Multi-objective as tuple
                    individual.fitness = result
                    metrics = {f"obj_{i}": v for i, v in enumerate(result)}
                else:
                    # Single objective
                    individual.fitness = float(result)
                    metrics = {"objective": individual.fitness}

                # Store result
                opt_result = OptimizationResult(
                    parameters=parameters,
                    metrics=metrics,
                    execution_time=time.time() - start_time,
                )
                results.add_result(opt_result)

            except Exception as e:
                logger.error(f"Error evaluating {parameters}: {e}")
                individual.fitness = float("-inf")  # Worst possible fitness

    def _select_parents(self, population: list[Individual]) -> list[Individual]:
        """Select parents for reproduction."""
        n_parents = self.config.population_size

        if self.config.selection_method == "tournament":
            return self._tournament_selection(population, n_parents)
        if self.config.selection_method == "roulette":
            return self._roulette_selection(population, n_parents)
        if self.config.selection_method == "rank":
            return self._rank_selection(population, n_parents)
        raise ValueError(f"Unknown selection method: {self.config.selection_method}")

    def _tournament_selection(
        self, population: list[Individual], n_select: int
    ) -> list[Individual]:
        """Tournament selection."""
        selected = []

        for _ in range(n_select):
            # Random tournament
            tournament = random.sample(population, self.config.tournament_size)
            # Select best
            winner = max(
                tournament,
                key=lambda x: x.fitness if x.fitness is not None else float("-inf"),
            )
            selected.append(winner)

        return selected

    def _roulette_selection(
        self, population: list[Individual], n_select: int
    ) -> list[Individual]:
        """Roulette wheel selection."""
        # Get fitness values
        fitness_values = []
        for ind in population:
            if ind.fitness is None:
                fitness_values.append(0.0)
            elif isinstance(ind.fitness, tuple):
                fitness_values.append(ind.fitness[0])  # Use first objective
            else:
                fitness_values.append(ind.fitness)

        # Shift to make all positive
        min_fitness = min(fitness_values)
        if min_fitness < 0:
            fitness_values = [f - min_fitness + 1 for f in fitness_values]

        # Calculate probabilities
        total_fitness = sum(fitness_values)
        if total_fitness == 0:
            probabilities = [1.0 / len(population)] * len(population)
        else:
            probabilities = [f / total_fitness for f in fitness_values]

        # Select
        selected = []
        for _ in range(n_select):
            r = random.random()
            cumsum = 0
            for i, prob in enumerate(probabilities):
                cumsum += prob
                if r <= cumsum:
                    selected.append(population[i])
                    break

        return selected

    def _rank_selection(
        self, population: list[Individual], n_select: int
    ) -> list[Individual]:
        """Rank-based selection."""
        # Sort by fitness
        sorted_pop = sorted(
            population,
            key=lambda x: x.fitness if x.fitness is not None else float("-inf"),
        )

        # Assign rank probabilities
        n = len(sorted_pop)
        probabilities = [(i + 1) / (n * (n + 1) / 2) for i in range(n)]

        # Select based on rank
        selected = []
        for _ in range(n_select):
            r = random.random()
            cumsum = 0
            for i, prob in enumerate(probabilities):
                cumsum += prob
                if r <= cumsum:
                    selected.append(sorted_pop[i])
                    break

        return selected

    def _create_offspring(
        self, parents: list[Individual], encoder: GeneticEncoder
    ) -> list[Individual]:
        """Create offspring through crossover and mutation."""
        offspring = []

        # Create pairs for crossover
        for i in range(0, len(parents) - 1, 2):
            parent1 = parents[i]
            parent2 = parents[i + 1]

            # Crossover
            if random.random() < self.config.crossover_prob:
                child1_genes, child2_genes = self._crossover(
                    parent1.genes, parent2.genes
                )
            else:
                child1_genes = parent1.genes.copy()
                child2_genes = parent2.genes.copy()

            # Mutation
            if random.random() < self.config.mutation_prob:
                child1_genes = self._mutate(child1_genes)
            if random.random() < self.config.mutation_prob:
                child2_genes = self._mutate(child2_genes)

            # Create offspring
            offspring.append(Individual(genes=child1_genes))
            offspring.append(Individual(genes=child2_genes))

        return offspring[: self.config.population_size]  # Ensure correct size

    def _crossover(
        self, genes1: list[float], genes2: list[float]
    ) -> tuple[list[float], list[float]]:
        """Uniform crossover."""
        child1_genes = []
        child2_genes = []

        for g1, g2 in zip(genes1, genes2):
            if random.random() < 0.5:
                child1_genes.append(g1)
                child2_genes.append(g2)
            else:
                child1_genes.append(g2)
                child2_genes.append(g1)

        return child1_genes, child2_genes

    def _mutate(self, genes: list[float]) -> list[float]:
        """Gaussian mutation."""
        mutated = []

        for gene in genes:
            if random.random() < 0.5:  # Mutate this gene
                # Add Gaussian noise
                noise = random.gauss(0, 0.1)
                new_gene = gene + noise
                # Clamp to [0, 1]
                new_gene = max(0.0, min(1.0, new_gene))
                mutated.append(new_gene)
            else:
                mutated.append(gene)

        return mutated

    def _create_next_generation(
        self, population: list[Individual], offspring: list[Individual]
    ) -> list[Individual]:
        """Create next generation with elitism."""
        # Combine population and offspring
        all_individuals = population + offspring

        # Sort by fitness
        all_individuals.sort(
            key=lambda x: x.fitness if x.fitness is not None else float("-inf"),
            reverse=True,
        )

        # Select best for next generation
        next_generation = all_individuals[: self.config.population_size]

        # Update generation number
        for ind in next_generation:
            ind.generation += 1

        return next_generation

    def _calculate_stats(
        self, population: list[Individual], generation: int
    ) -> PopulationStats:
        """Calculate population statistics."""
        fitness_values = []
        for ind in population:
            if ind.fitness is not None:
                if isinstance(ind.fitness, tuple):
                    fitness_values.append(ind.fitness[0])  # Use first objective
                else:
                    fitness_values.append(ind.fitness)

        if not fitness_values:
            fitness_values = [0.0]

        # Calculate diversity as standard deviation of genes
        all_genes = np.array([ind.genes for ind in population])
        diversity = np.mean(np.std(all_genes, axis=0))

        return PopulationStats(
            generation=generation,
            best_fitness=max(fitness_values),
            average_fitness=np.mean(fitness_values),
            worst_fitness=min(fitness_values),
            diversity=diversity,
        )

    def _get_best_fitness(self, population: list[Individual]) -> float:
        """Get best fitness value."""
        fitness_values = []
        for ind in population:
            if ind.fitness is not None:
                if isinstance(ind.fitness, tuple):
                    fitness_values.append(ind.fitness[0])
                else:
                    fitness_values.append(ind.fitness)

        return max(fitness_values) if fitness_values else float("-inf")

    def _check_convergence(self, old_best: float, new_best: float) -> bool:
        """Check if converged."""
        return abs(new_best - old_best) < self.config.fitness_tolerance

    def _update_best_individual(self, population: list[Individual]) -> None:
        """Update best individual seen so far."""
        current_best = max(
            population,
            key=lambda x: x.fitness if x.fitness is not None else float("-inf"),
        )

        if (
            self.best_individual is None
            or current_best.fitness > self.best_individual.fitness
        ):
            self.best_individual = current_best

    def _log_generation_stats(self, stats: PopulationStats) -> None:
        """Log generation statistics."""
        logger.info(
            f"  Best: {stats.best_fitness:.4f}, "
            f"Avg: {stats.average_fitness:.4f}, "
            f"Diversity: {stats.diversity:.4f}"
        )
