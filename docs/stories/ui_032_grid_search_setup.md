# UI_032: Grid Search Parameter Setup

## Story Details
- **Story ID**: UI_032
- **Status**: Done

## Story
As a trader, I want to define parameter ranges and constraints for grid search optimization so that I can systematically find optimal strategy parameters.

## Acceptance Criteria
1. Define parameter ranges with min/max/step values
2. Set up parameter constraints and dependencies
3. Create parameter groups for related settings
4. Estimate computational requirements
5. Save and load optimization configurations
6. Validate parameter combinations
7. Preview parameter space visualization
8. Support different parameter types (numeric, categorical, boolean)

## Technical Requirements

### Frontend Components
```typescript
// components/optimization/GridSearchSetup.tsx
interface ParameterDefinition {
  name: string;
  type: 'numeric' | 'categorical' | 'boolean';
  min?: number;
  max?: number;
  step?: number;
  values?: any[];
  default: any;
  description: string;
  group?: string;
}

interface OptimizationConfig {
  id: string;
  name: string;
  strategyId: string;
  parameters: ParameterDefinition[];
  constraints: Constraint[];
  objectives: OptimizationObjective[];
  searchSpace: SearchSpace;
}

export function GridSearchSetup({ strategyId }: { strategyId: string }) {
  const [parameters, setParameters] = useState<ParameterDefinition[]>([]);
  const [constraints, setConstraints] = useState<Constraint[]>([]);
  const [searchSpace, setSearchSpace] = useState<SearchSpace>();

  // Load strategy parameters
  useEffect(() => {
    loadStrategyParameters(strategyId).then(params => {
      setParameters(params);
      calculateSearchSpace(params);
    });
  }, [strategyId]);

  return (
    <div className="grid-search-setup">
      <Card>
        <CardHeader>
          <CardTitle>Grid Search Configuration</CardTitle>
          <CardDescription>
            Define parameter ranges for optimization
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="parameters">
            <TabsList>
              <TabsTrigger value="parameters">Parameters</TabsTrigger>
              <TabsTrigger value="constraints">Constraints</TabsTrigger>
              <TabsTrigger value="objectives">Objectives</TabsTrigger>
              <TabsTrigger value="preview">Preview</TabsTrigger>
            </TabsList>

            <TabsContent value="parameters">
              <ParameterConfiguration
                parameters={parameters}
                onChange={setParameters}
                onSearchSpaceUpdate={calculateSearchSpace}
              />
            </TabsContent>

            <TabsContent value="constraints">
              <ConstraintBuilder
                parameters={parameters}
                constraints={constraints}
                onChange={setConstraints}
              />
            </TabsContent>

            <TabsContent value="objectives">
              <ObjectiveSelector
                objectives={objectives}
                onChange={setObjectives}
              />
            </TabsContent>

            <TabsContent value="preview">
              <SearchSpacePreview
                searchSpace={searchSpace}
                constraints={constraints}
              />
            </TabsContent>
          </Tabs>

          <div className="mt-6 flex justify-between">
            <Button variant="outline" onClick={saveConfiguration}>
              Save Configuration
            </Button>
            <Button onClick={startOptimization}>
              Start Optimization
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
```

### Parameter Configuration
```typescript
// components/optimization/ParameterConfiguration.tsx
export function ParameterConfiguration({
  parameters,
  onChange,
  onSearchSpaceUpdate
}: ParameterConfigProps) {
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());

  const groupedParameters = useMemo(() => {
    return parameters.reduce((acc, param) => {
      const group = param.group || 'General';
      if (!acc[group]) acc[group] = [];
      acc[group].push(param);
      return acc;
    }, {} as Record<string, ParameterDefinition[]>);
  }, [parameters]);

  const updateParameter = (name: string, updates: Partial<ParameterDefinition>) => {
    const updated = parameters.map(p =>
      p.name === name ? { ...p, ...updates } : p
    );
    onChange(updated);
    onSearchSpaceUpdate(updated);
  };

  return (
    <div className="parameter-configuration">
      {Object.entries(groupedParameters).map(([group, params]) => (
        <Collapsible
          key={group}
          open={expandedGroups.has(group)}
          onOpenChange={(open) => {
            const newExpanded = new Set(expandedGroups);
            if (open) newExpanded.add(group);
            else newExpanded.delete(group);
            setExpandedGroups(newExpanded);
          }}
        >
          <CollapsibleTrigger className="flex items-center gap-2">
            <ChevronRight className="h-4 w-4" />
            <span className="font-medium">{group}</span>
            <Badge variant="secondary">{params.length}</Badge>
          </CollapsibleTrigger>

          <CollapsibleContent>
            <div className="space-y-4 mt-4">
              {params.map(param => (
                <ParameterEditor
                  key={param.name}
                  parameter={param}
                  onChange={(updates) => updateParameter(param.name, updates)}
                />
              ))}
            </div>
          </CollapsibleContent>
        </Collapsible>
      ))}

      <SearchSpaceEstimate parameters={parameters} />
    </div>
  );
}

// Individual parameter editor
function ParameterEditor({ parameter, onChange }: ParameterEditorProps) {
  if (parameter.type === 'numeric') {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <Label>{parameter.name}</Label>
              <Badge variant="outline">Numeric</Badge>
            </div>

            <p className="text-sm text-muted-foreground">
              {parameter.description}
            </p>

            <div className="grid grid-cols-3 gap-4">
              <div>
                <Label>Min</Label>
                <Input
                  type="number"
                  value={parameter.min}
                  onChange={(e) => onChange({ min: parseFloat(e.target.value) })}
                />
              </div>

              <div>
                <Label>Max</Label>
                <Input
                  type="number"
                  value={parameter.max}
                  onChange={(e) => onChange({ max: parseFloat(e.target.value) })}
                />
              </div>

              <div>
                <Label>Step</Label>
                <Input
                  type="number"
                  value={parameter.step}
                  onChange={(e) => onChange({ step: parseFloat(e.target.value) })}
                />
              </div>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">
                Values: {calculateNumericValues(parameter).length}
              </span>
              <Popover>
                <PopoverTrigger>
                  <Eye className="h-4 w-4" />
                </PopoverTrigger>
                <PopoverContent>
                  <div className="text-sm">
                    {calculateNumericValues(parameter).join(', ')}
                  </div>
                </PopoverContent>
              </Popover>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (parameter.type === 'categorical') {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <Label>{parameter.name}</Label>
              <Badge variant="outline">Categorical</Badge>
            </div>

            <p className="text-sm text-muted-foreground">
              {parameter.description}
            </p>

            <CategoricalValueEditor
              values={parameter.values || []}
              onChange={(values) => onChange({ values })}
            />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (parameter.type === 'boolean') {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            <div>
              <Label>{parameter.name}</Label>
              <p className="text-sm text-muted-foreground">
                {parameter.description}
              </p>
            </div>
            <Switch
              checked={parameter.values?.includes(true) ?? true}
              onCheckedChange={(checked) => {
                onChange({ values: checked ? [true, false] : [false] });
              }}
            />
          </div>
        </CardContent>
      </Card>
    );
  }
}
```

### Constraint Builder
```typescript
// components/optimization/ConstraintBuilder.tsx
interface Constraint {
  id: string;
  type: 'dependency' | 'range' | 'custom';
  expression: string;
  parameters: string[];
  description?: string;
}

export function ConstraintBuilder({
  parameters,
  constraints,
  onChange
}: ConstraintBuilderProps) {
  const [isAddingConstraint, setIsAddingConstraint] = useState(false);

  const addConstraint = (constraint: Constraint) => {
    onChange([...constraints, constraint]);
    setIsAddingConstraint(false);
  };

  return (
    <div className="constraint-builder">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-medium">Parameter Constraints</h3>
        <Button
          variant="outline"
          size="sm"
          onClick={() => setIsAddingConstraint(true)}
        >
          <Plus className="h-4 w-4 mr-2" />
          Add Constraint
        </Button>
      </div>

      <div className="space-y-4">
        {constraints.map(constraint => (
          <ConstraintCard
            key={constraint.id}
            constraint={constraint}
            parameters={parameters}
            onUpdate={(updated) => {
              onChange(constraints.map(c =>
                c.id === constraint.id ? updated : c
              ));
            }}
            onRemove={() => {
              onChange(constraints.filter(c => c.id !== constraint.id));
            }}
          />
        ))}
      </div>

      {isAddingConstraint && (
        <ConstraintEditor
          parameters={parameters}
          onSave={addConstraint}
          onCancel={() => setIsAddingConstraint(false)}
        />
      )}

      <ConstraintTemplates onSelect={addConstraint} />
    </div>
  );
}

// Constraint templates
function ConstraintTemplates({ onSelect }) {
  const templates = [
    {
      name: 'Stop Loss < Take Profit',
      type: 'dependency',
      expression: 'stop_loss < take_profit',
      parameters: ['stop_loss', 'take_profit']
    },
    {
      name: 'Risk-Reward Ratio',
      type: 'custom',
      expression: '(take_profit - entry) / (entry - stop_loss) >= 2',
      parameters: ['take_profit', 'entry', 'stop_loss']
    },
    {
      name: 'Position Size Limits',
      type: 'range',
      expression: 'position_size >= 1 && position_size <= 10',
      parameters: ['position_size']
    }
  ];

  return (
    <div className="mt-6">
      <h4 className="text-sm font-medium mb-2">Constraint Templates</h4>
      <div className="grid grid-cols-2 gap-2">
        {templates.map(template => (
          <Button
            key={template.name}
            variant="outline"
            size="sm"
            onClick={() => onSelect({
              ...template,
              id: generateId()
            })}
          >
            {template.name}
          </Button>
        ))}
      </div>
    </div>
  );
}
```

### Search Space Visualization
```typescript
// components/optimization/SearchSpacePreview.tsx
export function SearchSpacePreview({
  searchSpace,
  constraints
}: SearchSpacePreviewProps) {
  const [viewMode, setViewMode] = useState<'3d' | 'matrix' | 'summary'>('summary');
  const [selectedParams, setSelectedParams] = useState<string[]>([]);

  return (
    <div className="search-space-preview">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-medium">Search Space Preview</h3>
        <Select value={viewMode} onValueChange={setViewMode}>
          <SelectItem value="summary">Summary</SelectItem>
          <SelectItem value="3d">3D Visualization</SelectItem>
          <SelectItem value="matrix">Parameter Matrix</SelectItem>
        </Select>
      </div>

      {viewMode === 'summary' && (
        <SearchSpaceSummary searchSpace={searchSpace} />
      )}

      {viewMode === '3d' && (
        <SearchSpace3D
          searchSpace={searchSpace}
          selectedParams={selectedParams}
          onParamSelect={setSelectedParams}
        />
      )}

      {viewMode === 'matrix' && (
        <ParameterMatrix
          searchSpace={searchSpace}
          constraints={constraints}
        />
      )}
    </div>
  );
}

// Search space summary
function SearchSpaceSummary({ searchSpace }) {
  const stats = useMemo(() => {
    if (!searchSpace) return null;

    const totalCombinations = searchSpace.parameters.reduce((acc, param) => {
      return acc * param.values.length;
    }, 1);

    const estimatedTime = totalCombinations * searchSpace.avgBacktestTime;
    const estimatedCost = totalCombinations * searchSpace.costPerBacktest;

    return {
      totalCombinations,
      estimatedTime,
      estimatedCost,
      parametersCount: searchSpace.parameters.length,
      constrainedCombinations: searchSpace.validCombinations
    };
  }, [searchSpace]);

  if (!stats) return null;

  return (
    <div className="grid grid-cols-2 gap-4">
      <StatCard
        title="Total Combinations"
        value={stats.totalCombinations.toLocaleString()}
        description="Before constraints"
      />
      <StatCard
        title="Valid Combinations"
        value={stats.constrainedCombinations.toLocaleString()}
        description="After constraints"
      />
      <StatCard
        title="Estimated Time"
        value={formatDuration(stats.estimatedTime)}
        description="Sequential execution"
      />
      <StatCard
        title="Estimated Cost"
        value={`$${stats.estimatedCost.toFixed(2)}`}
        description="Compute resources"
      />

      <div className="col-span-2">
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Optimization Resources</AlertTitle>
          <AlertDescription>
            This optimization will require approximately {formatDuration(stats.estimatedTime)}
            and {(stats.totalCombinations * 0.1).toFixed(1)} GB of storage for results.
          </AlertDescription>
        </Alert>
      </div>
    </div>
  );
}

// 3D visualization of search space
function SearchSpace3D({ searchSpace, selectedParams, onParamSelect }) {
  const plotData = useMemo(() => {
    if (!searchSpace || selectedParams.length < 2) return null;

    const [xParam, yParam, zParam] = selectedParams;
    const xValues = searchSpace.parameters.find(p => p.name === xParam)?.values || [];
    const yValues = searchSpace.parameters.find(p => p.name === yParam)?.values || [];
    const zValues = zParam ?
      searchSpace.parameters.find(p => p.name === zParam)?.values || [] : [1];

    return {
      x: xValues,
      y: yValues,
      z: zParam ? createMeshGrid(xValues, yValues, zValues) : undefined,
      type: zParam ? 'surface' : 'scatter3d'
    };
  }, [searchSpace, selectedParams]);

  return (
    <div>
      <ParameterSelector
        parameters={searchSpace?.parameters || []}
        selected={selectedParams}
        onChange={onParamSelect}
        maxSelections={3}
      />

      {plotData && (
        <Plot
          data={[plotData]}
          layout={{
            scene: {
              xaxis: { title: selectedParams[0] },
              yaxis: { title: selectedParams[1] },
              zaxis: { title: selectedParams[2] || 'Count' }
            }
          }}
        />
      )}
    </div>
  );
}
```

### Backend Validation
```python
# api/optimization/grid_search_validator.py
from typing import List, Dict, Any
import numpy as np
from itertools import product

class GridSearchValidator:
    def __init__(self, config: OptimizationConfig):
        self.config = config
        self.parameters = config.parameters
        self.constraints = config.constraints

    def validate_search_space(self) -> SearchSpaceValidation:
        """Validate the search space configuration"""
        errors = []
        warnings = []

        # Check parameter ranges
        for param in self.parameters:
            if param.type == 'numeric':
                if param.min >= param.max:
                    errors.append(f"{param.name}: min must be less than max")
                if param.step <= 0:
                    errors.append(f"{param.name}: step must be positive")
                if (param.max - param.min) / param.step > 1000:
                    warnings.append(f"{param.name}: large number of values ({int((param.max - param.min) / param.step)})")

        # Validate constraints
        for constraint in self.constraints:
            try:
                self._validate_constraint(constraint)
            except Exception as e:
                errors.append(f"Constraint '{constraint.id}': {str(e)}")

        # Calculate search space size
        total_combinations = self._calculate_combinations()
        valid_combinations = self._count_valid_combinations()

        if total_combinations > 1000000:
            warnings.append(f"Large search space: {total_combinations:,} combinations")

        return SearchSpaceValidation(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            total_combinations=total_combinations,
            valid_combinations=valid_combinations
        )

    def _calculate_combinations(self) -> int:
        """Calculate total number of parameter combinations"""
        counts = []
        for param in self.parameters:
            if param.type == 'numeric':
                count = int((param.max - param.min) / param.step) + 1
            elif param.type == 'categorical':
                count = len(param.values)
            elif param.type == 'boolean':
                count = len(param.values) if param.values else 2
            counts.append(count)

        return np.prod(counts)

    def _count_valid_combinations(self) -> int:
        """Count combinations that satisfy all constraints"""
        # For large spaces, estimate using sampling
        if self._calculate_combinations() > 100000:
            return self._estimate_valid_combinations()

        # For small spaces, enumerate all
        valid_count = 0
        for combo in self._generate_combinations():
            if self._check_constraints(combo):
                valid_count += 1

        return valid_count

    def _check_constraints(self, combination: Dict[str, Any]) -> bool:
        """Check if a parameter combination satisfies all constraints"""
        for constraint in self.constraints:
            if not self._evaluate_constraint(constraint, combination):
                return False
        return True

# API endpoint
@router.post("/optimization/validate")
async def validate_optimization_config(config: OptimizationConfig):
    validator = GridSearchValidator(config)
    validation = validator.validate_search_space()

    # Estimate computational requirements
    avg_backtest_time = await estimate_backtest_time(config.strategy_id)
    total_time = validation.valid_combinations * avg_backtest_time

    # Estimate storage requirements
    result_size_mb = 0.1  # Average size per backtest result
    total_storage_gb = (validation.valid_combinations * result_size_mb) / 1024

    return {
        "validation": validation,
        "estimates": {
            "total_time_hours": total_time / 3600,
            "total_storage_gb": total_storage_gb,
            "cost_estimate": calculate_cost_estimate(total_time, total_storage_gb)
        }
    }
```

## UI/UX Considerations
- Visual parameter range sliders
- Real-time search space size updates
- Constraint validation feedback
- Parameter grouping for organization
- Import/export configuration files
- Preset optimization templates

## Testing Requirements
1. Parameter range validation
2. Constraint expression parsing
3. Search space calculation accuracy
4. Configuration save/load
5. UI responsiveness with many parameters
6. Cost estimation accuracy

## Dependencies
- UI_001: Next.js foundation
- UI_002: FastAPI backend
- UI_012: Strategy configuration

## Story Points: 13

## Priority: High

## Implementation Notes
- Use expression parser for constraints
- Implement incremental validation
- Cache search space calculations
- Support parameter dependencies
