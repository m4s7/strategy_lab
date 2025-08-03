"""Tests for genetic algorithm optimization."""

import numpy as np
import pytest

from strategy_lab.optimization.algorithms.genetic_algorithm import (
    GeneticAlgorithmConfig,
    GeneticAlgorithmOptimizer,
    GeneticEncoder,
    Individual,
    PopulationStats,
)
from strategy_lab.optimization.core.parameter_space import (
    CategoricalParameter,
    ContinuousParameter,
    DiscreteParameter,
    ParameterSpace,
)


class TestGeneticEncoder:
    """Test GeneticEncoder class."""

    @pytest.fixture
    def mixed_space(self):
        """Create mixed parameter space."""
        return ParameterSpace(
            [
                ContinuousParameter("alpha", 0.0, 1.0, 0.1),
                DiscreteParameter("window", 10, 50, 10),
                CategoricalParameter("method", ["fast", "slow", "medium"]),
            ]
        )

    def test_encoding_decoding(self, mixed_space):
        """Test parameter encoding and decoding."""
        encoder = GeneticEncoder(mixed_space)

        # Test parameters
        params = {"alpha": 0.5, "window": 30, "method": "slow"}

        # Encode
        genes = encoder.encode(params)
        assert len(genes) == 3
        assert 0 <= genes[0] <= 1  # Normalized alpha
        assert 0 <= genes[1] <= 1  # Normalized window
        assert 0 <= genes[2] <= 1  # Normalized method index

        # Decode
        decoded = encoder.decode(genes)
        assert abs(decoded["alpha"] - 0.5) < 0.01
        assert decoded["window"] == 30
        assert decoded["method"] == "slow"

    def test_continuous_encoding(self):
        """Test continuous parameter encoding."""
        space = ParameterSpace([ContinuousParameter("x", -10.0, 10.0, 0.1)])
        encoder = GeneticEncoder(space)

        # Encode boundary values
        assert encoder.encode({"x": -10.0})[0] == 0.0
        assert encoder.encode({"x": 10.0})[0] == 1.0
        assert abs(encoder.encode({"x": 0.0})[0] - 0.5) < 0.01

        # Decode
        assert abs(encoder.decode([0.0])["x"] - (-10.0)) < 0.01
        assert abs(encoder.decode([1.0])["x"] - 10.0) < 0.01

    def test_discrete_encoding(self):
        """Test discrete parameter encoding."""
        space = ParameterSpace([DiscreteParameter("n", 0, 100, 25)])
        encoder = GeneticEncoder(space)

        # Valid values: 0, 25, 50, 75, 100
        assert encoder.encode({"n": 0})[0] == 0.0
        assert encoder.encode({"n": 100})[0] == 1.0
        assert abs(encoder.encode({"n": 50})[0] - 0.5) < 0.01

        # Decode with rounding
        assert encoder.decode([0.0])["n"] == 0
        assert encoder.decode([0.24])["n"] == 25  # Should round to nearest
        assert encoder.decode([0.51])["n"] == 50
        assert encoder.decode([1.0])["n"] == 100

    def test_categorical_encoding(self):
        """Test categorical parameter encoding."""
        space = ParameterSpace([CategoricalParameter("cat", ["A", "B", "C", "D"])])
        encoder = GeneticEncoder(space)

        # Encode categories
        assert encoder.encode({"cat": "A"})[0] == 0.0
        assert abs(encoder.encode({"cat": "B"})[0] - 0.333) < 0.01
        assert abs(encoder.encode({"cat": "C"})[0] - 0.667) < 0.01
        assert encoder.encode({"cat": "D"})[0] == 1.0

        # Decode
        assert encoder.decode([0.0])["cat"] == "A"
        assert encoder.decode([0.4])["cat"] == "B"  # Rounds to nearest
        assert encoder.decode([0.7])["cat"] == "C"
        assert encoder.decode([1.0])["cat"] == "D"


class TestIndividual:
    """Test Individual class."""

    def test_individual_creation(self):
        """Test individual creation."""
        ind = Individual(genes=[0.1, 0.5, 0.9], fitness=1.5)
        assert len(ind.genes) == 3
        assert ind.fitness == 1.5
        assert ind.generation == 0

    def test_individual_comparison(self):
        """Test individual comparison."""
        ind1 = Individual(genes=[0.1], fitness=1.0)
        ind2 = Individual(genes=[0.2], fitness=2.0)
        ind3 = Individual(genes=[0.3], fitness=None)

        assert ind1 < ind2
        assert not ind2 < ind1
        assert not ind1 < ind3  # None fitness

        # Multi-objective
        ind4 = Individual(genes=[0.4], fitness=(1.0, 2.0))
        ind5 = Individual(genes=[0.5], fitness=(2.0, 1.0))
        assert ind4 < ind5  # Compares first objective


class TestGeneticAlgorithmOptimizer:
    """Test GeneticAlgorithmOptimizer class."""

    @pytest.fixture
    def simple_space(self):
        """Create simple parameter space."""
        return ParameterSpace(
            [
                ContinuousParameter("x", -5.0, 5.0, 0.1),
                ContinuousParameter("y", -5.0, 5.0, 0.1),
            ]
        )

    @pytest.fixture
    def sphere_function(self):
        """Create sphere optimization function (minimize x^2 + y^2)."""

        def objective(x, y):
            return -(x**2 + y**2)  # Negative for maximization

        return objective

    def test_initialization(self):
        """Test optimizer initialization."""
        config = GeneticAlgorithmConfig(
            population_size=50, generations=10, random_seed=42
        )
        optimizer = GeneticAlgorithmOptimizer(config)

        assert optimizer.config.population_size == 50
        assert optimizer.config.generations == 10
        assert optimizer.config.random_seed == 42

    def test_population_initialization(self, simple_space):
        """Test population initialization."""
        optimizer = GeneticAlgorithmOptimizer(
            GeneticAlgorithmConfig(population_size=20)
        )
        encoder = GeneticEncoder(simple_space)

        population = optimizer._initialize_population(encoder)

        assert len(population) == 20
        for ind in population:
            assert len(ind.genes) == 2
            assert all(0 <= g <= 1 for g in ind.genes)
            assert ind.fitness is None

    def test_simple_optimization(self, simple_space, sphere_function):
        """Test simple optimization problem."""
        config = GeneticAlgorithmConfig(
            population_size=20, generations=10, random_seed=42, verbose=False
        )
        optimizer = GeneticAlgorithmOptimizer(config)

        results = optimizer.optimize(sphere_function, simple_space)

        # Check results
        assert results.size > 0

        # Best solution should be near (0, 0)
        best = results.get_best_results("objective", n=1)[0]
        assert abs(best.parameters["x"]) < 1.0
        assert abs(best.parameters["y"]) < 1.0

        # Check optimizer tracked best individual
        assert optimizer.best_individual is not None
        assert optimizer.best_individual.fitness is not None

    def test_tournament_selection(self):
        """Test tournament selection."""
        optimizer = GeneticAlgorithmOptimizer(
            GeneticAlgorithmConfig(selection_method="tournament", tournament_size=3)
        )

        # Create test population
        population = [
            Individual([0.1], fitness=1.0),
            Individual([0.2], fitness=2.0),
            Individual([0.3], fitness=3.0),
            Individual([0.4], fitness=0.5),
        ]

        selected = optimizer._tournament_selection(population, 10)

        assert len(selected) == 10
        # Higher fitness individuals should be selected more often
        fitness_values = [ind.fitness for ind in selected]
        assert np.mean(fitness_values) > 1.5  # Above average

    def test_crossover(self):
        """Test crossover operation."""
        optimizer = GeneticAlgorithmOptimizer()

        parent1_genes = [0.1, 0.2, 0.3]
        parent2_genes = [0.7, 0.8, 0.9]

        child1, child2 = optimizer._crossover(parent1_genes, parent2_genes)

        assert len(child1) == 3
        assert len(child2) == 3

        # Each gene should come from one parent
        for i in range(3):
            assert child1[i] in [parent1_genes[i], parent2_genes[i]] and child2[i] in [
                parent1_genes[i],
                parent2_genes[i],
            ]

    def test_mutation(self):
        """Test mutation operation."""
        optimizer = GeneticAlgorithmOptimizer(GeneticAlgorithmConfig(random_seed=42))

        original_genes = [0.5, 0.5, 0.5]
        mutated = optimizer._mutate(original_genes)

        assert len(mutated) == 3
        assert all(0 <= g <= 1 for g in mutated)
        # At least one gene should be different (with high probability)
        assert any(abs(mutated[i] - original_genes[i]) > 0.01 for i in range(3))

    def test_multi_objective(self):
        """Test multi-objective optimization."""

        def multi_objective(x, y):
            # Two objectives: minimize x^2 and minimize (y-1)^2
            return {"obj1": -(x**2), "obj2": -((y - 1) ** 2)}

        space = ParameterSpace(
            [
                ContinuousParameter("x", -2.0, 2.0, 0.1),
                ContinuousParameter("y", -2.0, 2.0, 0.1),
            ]
        )

        config = GeneticAlgorithmConfig(
            population_size=20, generations=5, multi_objective=True, verbose=False
        )
        optimizer = GeneticAlgorithmOptimizer(config)

        results = optimizer.optimize(multi_objective, space)

        assert results.size > 0
        # Should have results with trade-offs between objectives
        df = results.to_dataframe()
        assert "metric_obj1" in df.columns
        assert "metric_obj2" in df.columns

    def test_convergence_detection(self, simple_space, sphere_function):
        """Test convergence detection."""
        config = GeneticAlgorithmConfig(
            population_size=10,
            generations=100,  # High number, but should converge early
            stagnation_generations=5,
            fitness_tolerance=1e-4,
            verbose=False,
        )
        optimizer = GeneticAlgorithmOptimizer(config)

        results = optimizer.optimize(sphere_function, simple_space)

        # Should converge before max generations
        assert len(optimizer.population_stats) < 100

        # Check stagnation in final generations
        if len(optimizer.population_stats) > 5:
            final_stats = optimizer.population_stats[-5:]
            fitness_values = [s.best_fitness for s in final_stats]
            assert max(fitness_values) - min(fitness_values) < 0.01

    def test_population_stats(self):
        """Test population statistics calculation."""
        optimizer = GeneticAlgorithmOptimizer()

        population = [
            Individual([0.1, 0.2], fitness=1.0),
            Individual([0.3, 0.4], fitness=2.0),
            Individual([0.5, 0.6], fitness=1.5),
            Individual([0.7, 0.8], fitness=0.5),
        ]

        stats = optimizer._calculate_stats(population, generation=5)

        assert stats.generation == 5
        assert stats.best_fitness == 2.0
        assert stats.worst_fitness == 0.5
        assert abs(stats.average_fitness - 1.25) < 0.01
        assert stats.diversity > 0  # Should have some diversity
