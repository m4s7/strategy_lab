# UI_036: Genetic Algorithm Optimization

## Story
As a trader, I want to use genetic algorithms for strategy optimization so that I can efficiently explore large parameter spaces and find optimal combinations through evolutionary methods.

## Acceptance Criteria
1. Configure genetic algorithm parameters (population, generations, mutation)
2. Define fitness functions and selection criteria
3. Execute genetic optimization with real-time evolution tracking
4. Visualize population evolution and convergence
5. Analyze gene distribution and dominant traits
6. Compare genetic results with grid search
7. Export optimal genomes and parameters
8. Support multi-objective optimization

## Technical Requirements

### Frontend Components
```typescript
// components/optimization/GeneticOptimizationSetup.tsx
interface GeneticConfig {
  id: string;
  name: string;
  strategyId: string;
  populationSize: number;
  maxGenerations: number;
  eliteSize: number;
  mutationRate: number;
  crossoverRate: number;
  selectionMethod: 'tournament' | 'roulette' | 'rank';
  fitnessFunction: FitnessConfig;
  parameters: GeneticParameter[];
  constraints: Constraint[];
  multiObjective?: MultiObjectiveConfig;
}

interface GeneticParameter {
  name: string;
  type: 'continuous' | 'discrete' | 'binary';
  min?: number;
  max?: number;
  values?: any[];
  encoding: 'real' | 'binary' | 'gray';
  precision?: number;
}

export function GeneticOptimizationSetup({ strategyId }: { strategyId: string }) {
  const [config, setConfig] = useState<GeneticConfig>({
    populationSize: 100,
    maxGenerations: 50,
    eliteSize: 10,
    mutationRate: 0.1,
    crossoverRate: 0.8,
    selectionMethod: 'tournament',
    parameters: []
  });

  const [preview, setPreview] = useState<GeneticPreview>();

  // Calculate optimization preview
  useEffect(() => {
    const preview = calculateGeneticPreview(config);
    setPreview(preview);
  }, [config]);

  return (
    <div className="genetic-optimization-setup">
      <Card>
        <CardHeader>
          <CardTitle>Genetic Algorithm Configuration</CardTitle>
          <CardDescription>
            Configure evolutionary optimization parameters
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="algorithm">
            <TabsList>
              <TabsTrigger value="algorithm">Algorithm</TabsTrigger>
              <TabsTrigger value="parameters">Parameters</TabsTrigger>
              <TabsTrigger value="fitness">Fitness</TabsTrigger>
              <TabsTrigger value="advanced">Advanced</TabsTrigger>
            </TabsList>

            <TabsContent value="algorithm">
              <AlgorithmConfiguration
                config={config}
                onChange={setConfig}
                preview={preview}
              />
            </TabsContent>

            <TabsContent value="parameters">
              <GeneticParameterSetup
                parameters={config.parameters}
                onChange={(params) => setConfig({...config, parameters: params})}
              />
            </TabsContent>

            <TabsContent value="fitness">
              <FitnessConfiguration
                fitness={config.fitnessFunction}
                onChange={(fitness) => setConfig({...config, fitnessFunction: fitness})}
              />
            </TabsContent>

            <TabsContent value="advanced">
              <AdvancedGeneticSettings
                config={config}
                onChange={setConfig}
              />
            </TabsContent>
          </Tabs>

          <div className="mt-6 flex justify-between">
            <Button variant="outline" onClick={saveConfiguration}>
              Save Configuration
            </Button>
            <Button onClick={startGeneticOptimization}>
              Start Evolution
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
```

### Algorithm Configuration
```typescript
// components/optimization/AlgorithmConfiguration.tsx
export function AlgorithmConfiguration({ config, onChange, preview }) {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label>Population Size</Label>
          <Input
            type="number"
            value={config.populationSize}
            onChange={(e) => onChange({...config, populationSize: parseInt(e.target.value)})}
            min={10}
            max={1000}
          />
          <p className="text-xs text-muted-foreground mt-1">
            Number of individuals per generation
          </p>
        </div>

        <div>
          <Label>Max Generations</Label>
          <Input
            type="number"
            value={config.maxGenerations}
            onChange={(e) => onChange({...config, maxGenerations: parseInt(e.target.value)})}
            min={10}
            max={1000}
          />
          <p className="text-xs text-muted-foreground mt-1">
            Maximum evolution iterations
          </p>
        </div>

        <div>
          <Label>Elite Size</Label>
          <div className="flex items-center gap-2">
            <Slider
              value={[config.eliteSize]}
              onValueChange={([value]) => onChange({...config, eliteSize: value})}
              max={Math.floor(config.populationSize * 0.5)}
              min={1}
            />
            <span className="w-12 text-right">{config.eliteSize}</span>
          </div>
          <p className="text-xs text-muted-foreground mt-1">
            Best individuals preserved each generation
          </p>
        </div>

        <div>
          <Label>Selection Method</Label>
          <Select
            value={config.selectionMethod}
            onValueChange={(value) => onChange({...config, selectionMethod: value})}
          >
            <SelectItem value="tournament">Tournament Selection</SelectItem>
            <SelectItem value="roulette">Roulette Wheel</SelectItem>
            <SelectItem value="rank">Rank Selection</SelectItem>
          </Select>
        </div>
      </div>

      <div className="space-y-4">
        <div>
          <Label>Mutation Rate</Label>
          <div className="flex items-center gap-4">
            <Slider
              value={[config.mutationRate * 100]}
              onValueChange={([value]) => onChange({...config, mutationRate: value / 100})}
              max={50}
              min={0}
              step={1}
            />
            <span className="w-12 text-right">{(config.mutationRate * 100).toFixed(0)}%</span>
          </div>
        </div>

        <div>
          <Label>Crossover Rate</Label>
          <div className="flex items-center gap-4">
            <Slider
              value={[config.crossoverRate * 100]}
              onValueChange={([value]) => onChange({...config, crossoverRate: value / 100})}
              max={100}
              min={50}
              step={5}
            />
            <span className="w-12 text-right">{(config.crossoverRate * 100).toFixed(0)}%</span>
          </div>
        </div>
      </div>

      {preview && (
        <Alert>
          <Info className="h-4 w-4" />
          <AlertTitle>Optimization Preview</AlertTitle>
          <AlertDescription>
            Total evaluations: {preview.totalEvaluations.toLocaleString()}<br />
            Estimated time: {formatDuration(preview.estimatedTime)}<br />
            Search space coverage: {(preview.searchSpaceCoverage * 100).toFixed(1)}%
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
}
```

### Genetic Optimization Execution
```typescript
// components/optimization/GeneticOptimizationExecution.tsx
interface Generation {
  id: number;
  population: Individual[];
  bestFitness: number;
  avgFitness: number;
  diversity: number;
  convergence: number;
}

interface Individual {
  id: string;
  genome: number[];
  parameters: Record<string, any>;
  fitness: number;
  age: number;
  parents?: [string, string];
}

export function GeneticOptimizationExecution({ configId }: { configId: string }) {
  const [execution, setExecution] = useState<GeneticExecution>();
  const [currentGeneration, setCurrentGeneration] = useState<Generation>();
  const [history, setHistory] = useState<Generation[]>([]);
  const [viewMode, setViewMode] = useState<'evolution' | 'population' | 'analysis'>('evolution');

  // WebSocket for real-time updates
  useEffect(() => {
    const ws = new WebSocket(`ws://localhost:8000/genetic/${configId}/stream`);

    ws.onmessage = (event) => {
      const update = JSON.parse(event.data);
      handleGeneticUpdate(update);
    };

    return () => ws.close();
  }, [configId]);

  const handleGeneticUpdate = (update: GeneticUpdate) => {
    switch (update.type) {
      case 'generation_complete':
        setCurrentGeneration(update.generation);
        setHistory(prev => [...prev, update.generation]);
        break;

      case 'evolution_complete':
        setExecution(prev => ({ ...prev, status: 'completed' }));
        break;
    }
  };

  return (
    <div className="genetic-optimization-execution">
      <GeneticExecutionControl
        execution={execution}
        onPause={pauseEvolution}
        onResume={resumeEvolution}
        onStop={stopEvolution}
      />

      <Tabs value={viewMode} onValueChange={setViewMode}>
        <TabsList>
          <TabsTrigger value="evolution">Evolution</TabsTrigger>
          <TabsTrigger value="population">Population</TabsTrigger>
          <TabsTrigger value="analysis">Analysis</TabsTrigger>
        </TabsList>

        <TabsContent value="evolution">
          <EvolutionProgress
            history={history}
            currentGeneration={currentGeneration}
          />
        </TabsContent>

        <TabsContent value="population">
          <PopulationVisualization
            generation={currentGeneration}
            history={history}
          />
        </TabsContent>

        <TabsContent value="analysis">
          <GeneticAnalysis
            history={history}
            finalPopulation={currentGeneration?.population}
          />
        </TabsContent>
      </Tabs>
    </div>
  );
}
```

### Evolution Progress Visualization
```typescript
// components/optimization/EvolutionProgress.tsx
export function EvolutionProgress({ history, currentGeneration }) {
  const evolutionData = useMemo(() => {
    return history.map(gen => ({
      generation: gen.id,
      bestFitness: gen.bestFitness,
      avgFitness: gen.avgFitness,
      worstFitness: Math.min(...gen.population.map(ind => ind.fitness)),
      diversity: gen.diversity,
      convergence: gen.convergence
    }));
  }, [history]);

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Evolution Progress</CardTitle>
          <CardDescription>
            Generation {currentGeneration?.id || 0} of {execution?.config.maxGenerations}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={evolutionData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="generation" />
              <YAxis yAxisId="fitness" />
              <YAxis yAxisId="diversity" orientation="right" />
              <Tooltip />
              <Legend />

              <Line
                yAxisId="fitness"
                type="monotone"
                dataKey="bestFitness"
                stroke="#8884d8"
                strokeWidth={2}
                name="Best Fitness"
              />
              <Line
                yAxisId="fitness"
                type="monotone"
                dataKey="avgFitness"
                stroke="#82ca9d"
                strokeWidth={2}
                name="Average Fitness"
              />
              <Line
                yAxisId="diversity"
                type="monotone"
                dataKey="diversity"
                stroke="#ffc658"
                strokeWidth={2}
                name="Diversity"
                strokeDasharray="5 5"
              />
            </LineChart>
          </ResponsiveContainer>

          <div className="grid grid-cols-4 gap-4 mt-6">
            <MetricCard
              title="Best Fitness"
              value={currentGeneration?.bestFitness.toFixed(3)}
              trend={getImprovementTrend(history)}
              icon={Trophy}
            />
            <MetricCard
              title="Population Diversity"
              value={`${(currentGeneration?.diversity * 100).toFixed(1)}%`}
              icon={Users}
            />
            <MetricCard
              title="Convergence"
              value={`${(currentGeneration?.convergence * 100).toFixed(1)}%`}
              icon={Target}
            />
            <MetricCard
              title="Generation Time"
              value={formatDuration(currentGeneration?.computeTime)}
              icon={Clock}
            />
          </div>
        </CardContent>
      </Card>

      <FitnessDistribution generation={currentGeneration} />
    </div>
  );
}

// Fitness distribution visualization
function FitnessDistribution({ generation }) {
  const distribution = useMemo(() => {
    if (!generation) return [];

    const fitnesses = generation.population.map(ind => ind.fitness);
    const bins = d3.histogram()
      .domain(d3.extent(fitnesses))
      .thresholds(20)(fitnesses);

    return bins.map(bin => ({
      range: `${bin.x0.toFixed(2)}-${bin.x1.toFixed(2)}`,
      count: bin.length,
      x0: bin.x0,
      x1: bin.x1
    }));
  }, [generation]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Fitness Distribution</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={distribution}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="range" angle={-45} textAnchor="end" height={60} />
            <YAxis />
            <Tooltip />
            <Bar dataKey="count" fill="#8884d8" />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
```

### Population Visualization
```typescript
// components/optimization/PopulationVisualization.tsx
export function PopulationVisualization({ generation, history }) {
  const [viewType, setViewType] = useState<'scatter' | 'parallel' | 'tree'>('scatter');
  const [selectedIndividuals, setSelectedIndividuals] = useState<Set<string>>(new Set());

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Population Analysis</CardTitle>
          <Select value={viewType} onValueChange={setViewType}>
            <SelectItem value="scatter">Parameter Space</SelectItem>
            <SelectItem value="parallel">Parallel Coordinates</SelectItem>
            <SelectItem value="tree">Family Tree</SelectItem>
          </Select>
        </CardHeader>
        <CardContent>
          {viewType === 'scatter' && (
            <ParameterSpaceScatter
              population={generation?.population}
              onSelect={setSelectedIndividuals}
            />
          )}

          {viewType === 'parallel' && (
            <ParallelCoordinates
              population={generation?.population}
              selectedIds={selectedIndividuals}
            />
          )}

          {viewType === 'tree' && (
            <FamilyTree
              history={history}
              currentGeneration={generation?.id}
            />
          )}
        </CardContent>
      </Card>

      {selectedIndividuals.size > 0 && (
        <IndividualComparison
          individuals={generation?.population.filter(ind =>
            selectedIndividuals.has(ind.id)
          )}
        />
      )}
    </div>
  );
}

// Parameter space scatter plot
function ParameterSpaceScatter({ population, onSelect }) {
  const [xParam, setXParam] = useState<string>();
  const [yParam, setYParam] = useState<string>();

  const scatterData = useMemo(() => {
    if (!population || !xParam || !yParam) return [];

    return population.map(ind => ({
      id: ind.id,
      x: ind.parameters[xParam],
      y: ind.parameters[yParam],
      fitness: ind.fitness,
      age: ind.age
    }));
  }, [population, xParam, yParam]);

  return (
    <div>
      <div className="flex gap-4 mb-4">
        <ParameterSelector
          label="X Axis"
          parameters={Object.keys(population?.[0]?.parameters || {})}
          value={xParam}
          onChange={setXParam}
        />
        <ParameterSelector
          label="Y Axis"
          parameters={Object.keys(population?.[0]?.parameters || {})}
          value={yParam}
          onChange={setYParam}
        />
      </div>

      <ResponsiveContainer width="100%" height={400}>
        <ScatterChart>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="x" name={xParam} />
          <YAxis dataKey="y" name={yParam} />
          <Tooltip />
          <Scatter
            data={scatterData}
            fill="#8884d8"
            onClick={(data) => onSelect(new Set([data.id]))}
          >
            {scatterData.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={getColorByFitness(entry.fitness)}
              />
            ))}
          </Scatter>
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
}
```

### Genetic Analysis
```typescript
// components/optimization/GeneticAnalysis.tsx
export function GeneticAnalysis({ history, finalPopulation }) {
  const [analysisType, setAnalysisType] = useState<'convergence' | 'diversity' | 'parameters'>('convergence');

  const analysis = useMemo(() => {
    if (!history || history.length === 0) return null;

    return {
      convergenceRate: calculateConvergenceRate(history),
      diversityTrend: calculateDiversityTrend(history),
      parameterEvolution: analyzeParameterEvolution(history),
      dominantGenes: findDominantGenes(finalPopulation),
      optimalParameters: findOptimalParameters(finalPopulation)
    };
  }, [history, finalPopulation]);

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Genetic Algorithm Analysis</CardTitle>
          <Tabs value={analysisType} onValueChange={setAnalysisType}>
            <TabsList>
              <TabsTrigger value="convergence">Convergence</TabsTrigger>
              <TabsTrigger value="diversity">Diversity</TabsTrigger>
              <TabsTrigger value="parameters">Parameters</TabsTrigger>
            </TabsList>
          </Tabs>
        </CardHeader>
        <CardContent>
          {analysisType === 'convergence' && (
            <ConvergenceAnalysis
              history={history}
              convergenceRate={analysis?.convergenceRate}
            />
          )}

          {analysisType === 'diversity' && (
            <DiversityAnalysis
              history={history}
              diversityTrend={analysis?.diversityTrend}
            />
          )}

          {analysisType === 'parameters' && (
            <ParameterDominance
              evolution={analysis?.parameterEvolution}
              dominantGenes={analysis?.dominantGenes}
            />
          )}
        </CardContent>
      </Card>

      <OptimalSolutionSummary
        optimalParameters={analysis?.optimalParameters}
        finalPopulation={finalPopulation}
      />
    </div>
  );
}

// Parameter dominance analysis
function ParameterDominance({ evolution, dominantGenes }) {
  return (
    <div className="space-y-4">
      <div>
        <h4 className="text-sm font-medium mb-2">Dominant Gene Values</h4>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Parameter</TableHead>
              <TableHead>Dominant Value</TableHead>
              <TableHead>Frequency</TableHead>
              <TableHead>Avg Fitness</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {dominantGenes?.map(gene => (
              <TableRow key={gene.parameter}>
                <TableCell>{gene.parameter}</TableCell>
                <TableCell>{gene.dominantValue.toFixed(3)}</TableCell>
                <TableCell>
                  <Progress value={gene.frequency * 100} className="w-20" />
                </TableCell>
                <TableCell>{gene.avgFitness.toFixed(3)}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      <div>
        <h4 className="text-sm font-medium mb-2">Parameter Evolution</h4>
        <ParameterEvolutionHeatmap evolution={evolution} />
      </div>
    </div>
  );
}
```

### Backend Genetic Algorithm Engine
```python
# api/optimization/genetic_algorithm_engine.py
import numpy as np
from typing import List, Dict, Tuple
import random

class GeneticAlgorithmEngine:
    def __init__(self, config: GeneticConfig):
        self.config = config
        self.population = []
        self.generation = 0
        self.best_individual = None

    async def evolve(self) -> AsyncIterator[GeneticUpdate]:
        """Run genetic algorithm evolution"""
        # Initialize population
        self.population = self._initialize_population()

        for generation in range(self.config.max_generations):
            self.generation = generation

            # Evaluate fitness
            fitnesses = await self._evaluate_population(self.population)

            # Update best individual
            best_idx = np.argmax(fitnesses)
            if self.best_individual is None or fitnesses[best_idx] > self.best_individual.fitness:
                self.best_individual = self.population[best_idx]

            # Calculate generation statistics
            gen_stats = self._calculate_generation_stats(self.population, fitnesses)

            yield GeneticUpdate(
                type='generation_complete',
                generation=Generation(
                    id=generation,
                    population=self.population,
                    bestFitness=gen_stats['best'],
                    avgFitness=gen_stats['average'],
                    diversity=gen_stats['diversity'],
                    convergence=gen_stats['convergence']
                )
            )

            # Check termination criteria
            if self._should_terminate(gen_stats):
                break

            # Selection and reproduction
            self.population = self._evolve_population(self.population, fitnesses)

        yield GeneticUpdate(
            type='evolution_complete',
            bestIndividual=self.best_individual,
            finalPopulation=self.population
        )

    def _initialize_population(self) -> List[Individual]:
        """Create initial random population"""
        population = []

        for i in range(self.config.population_size):
            genome = self._create_random_genome()
            parameters = self._decode_genome(genome)

            population.append(Individual(
                id=f"gen0_ind{i}",
                genome=genome,
                parameters=parameters,
                fitness=0,
                age=0
            ))

        return population

    def _evolve_population(self, population: List[Individual], fitnesses: np.ndarray) -> List[Individual]:
        """Create next generation through selection, crossover, and mutation"""
        new_population = []

        # Elitism - preserve best individuals
        elite_indices = np.argsort(fitnesses)[-self.config.elite_size:]
        for idx in elite_indices:
            elite = population[idx]
            elite.age += 1
            new_population.append(elite)

        # Generate rest of population
        while len(new_population) < self.config.population_size:
            # Selection
            parent1 = self._select_parent(population, fitnesses)
            parent2 = self._select_parent(population, fitnesses)

            # Crossover
            if random.random() < self.config.crossover_rate:
                child1_genome, child2_genome = self._crossover(parent1.genome, parent2.genome)
            else:
                child1_genome = parent1.genome.copy()
                child2_genome = parent2.genome.copy()

            # Mutation
            child1_genome = self._mutate(child1_genome)
            if len(new_population) < self.config.population_size - 1:
                child2_genome = self._mutate(child2_genome)

            # Create new individuals
            child1 = Individual(
                id=f"gen{self.generation+1}_ind{len(new_population)}",
                genome=child1_genome,
                parameters=self._decode_genome(child1_genome),
                fitness=0,
                age=0,
                parents=(parent1.id, parent2.id)
            )
            new_population.append(child1)

            if len(new_population) < self.config.population_size:
                child2 = Individual(
                    id=f"gen{self.generation+1}_ind{len(new_population)}",
                    genome=child2_genome,
                    parameters=self._decode_genome(child2_genome),
                    fitness=0,
                    age=0,
                    parents=(parent1.id, parent2.id)
                )
                new_population.append(child2)

        return new_population

    def _select_parent(self, population: List[Individual], fitnesses: np.ndarray) -> Individual:
        """Select parent using configured selection method"""
        if self.config.selection_method == 'tournament':
            tournament_size = 3
            indices = np.random.choice(len(population), tournament_size, replace=False)
            winner_idx = indices[np.argmax(fitnesses[indices])]
            return population[winner_idx]

        elif self.config.selection_method == 'roulette':
            # Fitness proportionate selection
            probabilities = fitnesses / fitnesses.sum()
            selected_idx = np.random.choice(len(population), p=probabilities)
            return population[selected_idx]

        else:  # rank selection
            ranks = np.argsort(np.argsort(fitnesses))
            probabilities = ranks / ranks.sum()
            selected_idx = np.random.choice(len(population), p=probabilities)
            return population[selected_idx]

    def _crossover(self, parent1: np.ndarray, parent2: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Perform crossover between two parents"""
        if len(parent1) == 1:
            return parent1.copy(), parent2.copy()

        # Single-point crossover
        crossover_point = random.randint(1, len(parent1) - 1)
        child1 = np.concatenate([parent1[:crossover_point], parent2[crossover_point:]])
        child2 = np.concatenate([parent2[:crossover_point], parent1[crossover_point:]])

        return child1, child2

    def _mutate(self, genome: np.ndarray) -> np.ndarray:
        """Apply mutation to genome"""
        mutated = genome.copy()

        for i in range(len(genome)):
            if random.random() < self.config.mutation_rate:
                param_config = self.config.parameters[i]

                if param_config.type == 'continuous':
                    # Gaussian mutation
                    std = (param_config.max - param_config.min) * 0.1
                    mutated[i] += np.random.normal(0, std)
                    mutated[i] = np.clip(mutated[i], param_config.min, param_config.max)

                elif param_config.type == 'discrete':
                    # Random value selection
                    mutated[i] = random.choice(param_config.values)

                elif param_config.type == 'binary':
                    # Bit flip
                    mutated[i] = 1 - mutated[i]

        return mutated
```

## UI/UX Considerations
- Real-time evolution visualization
- Interactive population exploration
- Clear convergence indicators
- Parameter relationship visualization
- Comparison with other optimization methods
- Export functionality for results

## Testing Requirements
1. Genetic operators correctness
2. Selection method implementations
3. Fitness evaluation accuracy
4. Convergence detection
5. Multi-objective optimization
6. Performance with large populations

## Dependencies
- UI_001: Next.js foundation
- UI_002: FastAPI backend
- UI_032: Grid search setup
- UI_004: WebSocket infrastructure

## Story Points: 21

## Priority: Low

## Implementation Notes
- Consider using DEAP library for genetic algorithms
- Implement parallel fitness evaluation
- Add support for island model GA
- Cache fitness evaluations to avoid redundant calculations
