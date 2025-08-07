# Story UI_012: Strategy Selection & Configuration

## Story Details
- **Story ID**: UI_012
- **Epic**: Epic 2 - Core Backtesting Features
- **Story Points**: 8
- **Priority**: Critical
- **Type**: User Interface + API Integration

## User Story
**As a** trading researcher
**I want** to select and configure strategies through a web form
**So that** I can set up backtests without writing configuration files manually

## Acceptance Criteria

### 1. Strategy Selection Interface
- [ ] Dropdown showing all registered strategies from Strategy Lab
- [ ] Strategy search and filtering capability
- [ ] Strategy documentation display when selected
- [ ] Strategy category grouping (if applicable)
- [ ] Recently used strategies quick access
- [ ] Strategy metadata display (author, version, description)

### 2. Dynamic Parameter Configuration
- [ ] Parameter input forms generated dynamically based on strategy
- [ ] Support for different parameter types (numeric, boolean, categorical, date)
- [ ] Parameter validation with real-time feedback
- [ ] Parameter descriptions and help tooltips
- [ ] Parameter dependencies and conditional visibility
- [ ] Default value population and reset functionality

### 3. Configuration Templates
- [ ] Save current configuration as named template
- [ ] Load previously saved configuration templates
- [ ] Template management (rename, delete, duplicate)
- [ ] Template sharing/export capability
- [ ] Auto-save of current configuration
- [ ] Last used configuration restoration

### 4. Configuration Validation
- [ ] Real-time parameter validation with error messages
- [ ] Cross-parameter validation rules
- [ ] Configuration completeness checking
- [ ] Warning indicators for potentially problematic settings
- [ ] Validation summary before backtest execution
- [ ] Suggested parameter ranges based on historical data

### 5. Configuration Preview
- [ ] Summary view of all configuration settings
- [ ] Parameter impact estimation (if available)
- [ ] Configuration comparison with templates
- [ ] Estimated backtest resource requirements
- [ ] Configuration export to JSON/YAML
- [ ] Configuration import from file

## Technical Requirements

### Strategy API Integration
```typescript
// Strategy registry API integration
interface Strategy {
  id: string;
  name: string;
  description: string;
  version: string;
  author: string;
  category: string;
  parameters: ParameterDefinition[];
  documentation?: string;
  defaultParams?: Record<string, any>;
}

interface ParameterDefinition {
  name: string;
  type: 'number' | 'boolean' | 'string' | 'select' | 'date' | 'range';
  description: string;
  required: boolean;
  default?: any;
  validation?: ValidationRule;
  options?: any[]; // For select type
  dependencies?: string[]; // Parameters this depends on
}

// API endpoints
GET /api/strategies - Get all available strategies
GET /api/strategies/{id} - Get specific strategy details
POST /api/strategies/{id}/validate - Validate parameter configuration
```

### Dynamic Form Generation
```typescript
const ParameterForm: React.FC<{
  strategy: Strategy;
  values: Record<string, any>;
  onChange: (values: Record<string, any>) => void;
  onValidate: (isValid: boolean, errors: ValidationError[]) => void;
}> = ({ strategy, values, onChange, onValidate }) => {

  const renderParameterInput = (param: ParameterDefinition) => {
    switch (param.type) {
      case 'number':
        return (
          <NumberInput
            name={param.name}
            value={values[param.name]}
            min={param.validation?.min}
            max={param.validation?.max}
            step={param.validation?.step}
            onChange={(value) => updateParameter(param.name, value)}
            error={getParameterError(param.name)}
          />
        );
      case 'select':
        return (
          <SelectInput
            name={param.name}
            value={values[param.name]}
            options={param.options}
            onChange={(value) => updateParameter(param.name, value)}
          />
        );
      case 'boolean':
        return (
          <BooleanInput
            name={param.name}
            value={values[param.name]}
            onChange={(value) => updateParameter(param.name, value)}
          />
        );
      // ... other parameter types
    }
  };

  return (
    <form className="parameter-form">
      {strategy.parameters.map(param => (
        <div key={param.name} className="parameter-group">
          <label>{param.name}</label>
          <div className="parameter-input">
            {renderParameterInput(param)}
          </div>
          {param.description && (
            <div className="parameter-help">{param.description}</div>
          )}
        </div>
      ))}
    </form>
  );
};
```

### Configuration Template System
```typescript
interface ConfigurationTemplate {
  id: string;
  name: string;
  strategyId: string;
  parameters: Record<string, any>;
  createdAt: string;
  lastUsed?: string;
  description?: string;
}

const useConfigurationTemplates = (strategyId: string) => {
  const [templates, setTemplates] = useState<ConfigurationTemplate[]>([]);

  const saveTemplate = async (name: string, parameters: Record<string, any>) => {
    const template: ConfigurationTemplate = {
      id: generateId(),
      name,
      strategyId,
      parameters: { ...parameters },
      createdAt: new Date().toISOString()
    };

    // Save to backend
    await fetch('/api/configuration-templates', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(template)
    });

    setTemplates(prev => [...prev, template]);
  };

  const loadTemplate = (templateId: string) => {
    const template = templates.find(t => t.id === templateId);
    return template?.parameters || {};
  };

  return { templates, saveTemplate, loadTemplate };
};
```

### Parameter Validation System
```typescript
interface ValidationRule {
  min?: number;
  max?: number;
  step?: number;
  required?: boolean;
  pattern?: string;
  custom?: (value: any, allValues: Record<string, any>) => string | null;
}

const useParameterValidation = (strategy: Strategy) => {
  const [errors, setErrors] = useState<Record<string, string>>({});

  const validateParameter = (name: string, value: any, allValues: Record<string, any>) => {
    const param = strategy.parameters.find(p => p.name === name);
    if (!param) return null;

    // Required validation
    if (param.required && (value === null || value === undefined || value === '')) {
      return `${name} is required`;
    }

    // Type-specific validation
    if (param.type === 'number' && param.validation) {
      const val = Number(value);
      if (param.validation.min !== undefined && val < param.validation.min) {
        return `${name} must be at least ${param.validation.min}`;
      }
      if (param.validation.max !== undefined && val > param.validation.max) {
        return `${name} must be at most ${param.validation.max}`;
      }
    }

    // Custom validation
    if (param.validation?.custom) {
      return param.validation.custom(value, allValues);
    }

    return null;
  };

  const validateAll = (values: Record<string, any>) => {
    const newErrors: Record<string, string> = {};

    strategy.parameters.forEach(param => {
      const error = validateParameter(param.name, values[param.name], values);
      if (error) {
        newErrors[param.name] = error;
      }
    });

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  return { errors, validateParameter, validateAll };
};
```

## Definition of Done
- [ ] Strategy selection dropdown populated from backend
- [ ] Dynamic form generation works for all parameter types
- [ ] Real-time validation provides immediate feedback
- [ ] Configuration templates can be saved and loaded
- [ ] All parameter types render and function correctly
- [ ] Form submission produces valid configuration object
- [ ] Error handling covers all validation scenarios
- [ ] Configuration can be exported/imported

## Testing Checklist
- [ ] Strategy dropdown loads all available strategies
- [ ] Parameter form generates correctly for different strategies
- [ ] Parameter validation catches invalid inputs
- [ ] Template save/load functionality works
- [ ] Form remembers values when switching between strategies
- [ ] Configuration export produces valid JSON/YAML
- [ ] All parameter types work with different input values
- [ ] Error messages are clear and actionable

## Integration Points
- **Strategy Registry**: Backend integration for strategy metadata
- **Validation Service**: Parameter validation API
- **Template Storage**: Configuration template persistence
- **Next Story**: Configuration feeds into UI_014 (Backtest Execution)

## Performance Requirements
- Strategy loading < 2 seconds
- Form generation < 500ms for complex strategies
- Parameter validation < 100ms per parameter
- Template operations < 1 second

## Follow-up Stories
- UI_013: Data Configuration Interface
- UI_014: Backtest Execution Control (uses configuration output)
